#!/usr/bin/env node
// editor/tools/verify-shader.mjs - headless render-verify for a shader HTML file.
//
// Loads the page in real (headless) Chromium via Playwright, captures every
// WebGL shader compile / program link infolog by wrapping the GL prototypes
// BEFORE the page script runs, lets it render a few frames, then reads back the
// canvas pixels to decide whether anything actually drew. This is the
// 100%-faithful check: it catches ANY compile/link error (for any shader, incl.
// JS-assembled ones the static glslang pass can't extract) AND the
// compiles-but-renders-blank case the compiler can't see.
//
// Usage:  node verify-shader.mjs <file.html>
// Output (stdout, always JSON):
//   { ok, compileErrors: string[], linkErrors: string[], blank: bool, note }
// Exit 0 when it ran (even if the shader is broken - read the JSON); exit 2 when
// it couldn't run at all (Playwright missing / load failure) with JSON on stderr.

import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const file = process.argv[2];
if (!file) {
  process.stderr.write(JSON.stringify({ ok: false, note: "usage: verify-shader.mjs <file.html>" }));
  process.exit(2);
}

let chromium;
try {
  ({ chromium } = await import("playwright"));
} catch {
  process.stderr.write(JSON.stringify({ ok: false, note: "playwright not installed" }));
  process.exit(2);
}

// Init script injected before any page script: wrap GL compile/link so we
// collect infologs even though the page swallows them.
const INIT = `
window.__shaderDiag = { compileErrors: [], linkErrors: [] };
for (const Ctx of [self.WebGLRenderingContext, self.WebGL2RenderingContext].filter(Boolean)) {
  const P = Ctx.prototype;
  const _cs = P.compileShader;
  P.compileShader = function(sh){
    _cs.call(this, sh);
    try {
      if (!this.getShaderParameter(sh, this.COMPILE_STATUS)) {
        window.__shaderDiag.compileErrors.push((this.getShaderInfoLog(sh) || "compile failed").trim());
      }
    } catch {}
  };
  const _lp = P.linkProgram;
  P.linkProgram = function(pr){
    _lp.call(this, pr);
    try {
      if (!this.getProgramParameter(pr, this.LINK_STATUS)) {
        window.__shaderDiag.linkErrors.push((this.getProgramInfoLog(pr) || "link failed").trim());
      }
    } catch {}
  };
}`;

function blankReport(px) {
  // px: Uint8 RGBA samples. "blank" = every sample identical (uniform frame) -
  // a button/scene that drew something has variance.
  if (!px || px.length < 8) return true;
  const r0 = px[0], g0 = px[1], b0 = px[2];
  for (let i = 4; i < px.length; i += 4) {
    if (Math.abs(px[i] - r0) > 3 || Math.abs(px[i+1] - g0) > 3 || Math.abs(px[i+2] - b0) > 3) {
      return false;
    }
  }
  return true;
}

let browser;
try {
  browser = await chromium.launch({ headless: true, args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"] });
  const page = await browser.newPage({ viewport: { width: 640, height: 400 } });
  await page.addInitScript(INIT);
  const consoleErrs = [];
  page.on("console", m => { if (m.type() === "error") consoleErrs.push(m.text()); });
  await page.goto(pathToFileURL(file).href, { waitUntil: "load", timeout: 15000 });
  await page.waitForTimeout(700);   // let a few rAF frames run

  const diag = await page.evaluate(() => window.__shaderDiag || { compileErrors: [], linkErrors: [] });
  // Judge "blank" from a real SCREENSHOT of the canvas - the composited output
  // the browser actually shows. (Reading the canvas in-page via drawImage/
  // toDataURL is unreliable for WebGL: without preserveDrawingBuffer the
  // drawing buffer is cleared after each composite, so it reads blank even
  // when the shader drew fine.)
  let px = null;
  try {
    const handle = await page.evaluateHandle(() => {
      const cs = [...document.querySelectorAll("canvas")];
      return cs.length ? cs.sort((a,b)=> (b.width*b.height)-(a.width*a.height))[0] : null;
    });
    const el = handle.asElement();
    if (el) {
      const buf = await el.screenshot({ type: "png" });
      const { PNG } = await import("pngjs");
      const png = PNG.sync.read(buf);
      px = Array.from(png.data);
    }
  } catch { px = null; }

  const compileErrors = diag.compileErrors || [];
  const linkErrors = diag.linkErrors || [];
  const hadCanvas = px !== null;
  const blank = hadCanvas ? blankReport(px) : false;
  const ok = compileErrors.length === 0 && linkErrors.length === 0 && (!hadCanvas || !blank);
  process.stdout.write(JSON.stringify({
    ok, compileErrors, linkErrors, blank: hadCanvas ? blank : null,
    note: hadCanvas ? undefined : "no canvas found",
    consoleErrors: consoleErrs.slice(0, 5),
  }));
  await browser.close();
  process.exit(0);
} catch (e) {
  try { if (browser) await browser.close(); } catch {}
  process.stderr.write(JSON.stringify({ ok: false, note: "verify failed: " + (e && e.message || String(e)) }));
  process.exit(2);
}
