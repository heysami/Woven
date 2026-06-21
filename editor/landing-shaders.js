// ============================================================================
// Landing-screen shader runtime - lifted verbatim from the `landing-diamonds`
// reference prototype (Documents/Woven IN USE/projects/projects/changing/source/
// landing-diamonds/shaders.js). Drives a single full-page WebGL canvas behind
// the Projects landing that draws, from ONE diamond grid:
//   • the dark header band + its faint diamond fretwork,
//   • the triangle-tooth boundary (the bottom row of dark diamonds), and
//   • the light diamond field with cursor-driven 3D lighting.
// Because the dark band, the teeth and the field share one grid, they can't
// drift apart and there's no DOM seam to leak a hairline.
// Uniforms: iResolution(px), iTime(s), iMouse(px,y-up), uScale(dpr),
//           uBoundary(px-from-top, set per-frame from the landing header height)
// Exposes:  window.mountShader(canvas, fragBody, opts)
//           window.SHADER_BG
// ============================================================================
(function () {
  if (window.mountShader) return;   // guard against double-load
  const VS = "attribute vec2 p;void main(){gl_Position=vec4(p,0.0,1.0);}";

  function compile(gl, type, src) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      console.error("shader error:", gl.getShaderInfoLog(s), "\n" + src); return null;
    }
    return s;
  }

  window.mountShader = function (canvas, fragBody, opts) {
    opts = opts || {};
    // opts.alpha = true → keeps the per-pixel alpha from mainImage's output
    // (used by the dark-band overlay canvas so its light-field area is
    // transparent and the cards behind it remain visible).
    const useAlpha = !!opts.alpha;
    const gl = canvas.getContext("webgl", { antialias: true, alpha: useAlpha, premultipliedAlpha: false });
    if (!gl) { console.warn("no webgl"); return; }

    const alphaExpr = useAlpha ? "c.a" : "1.0";
    const FS =
      "precision highp float;\n" +
      "uniform vec3 iResolution;uniform float iTime;uniform vec4 iMouse;uniform float uScale;uniform float uBoundary;\n" +
      fragBody + "\n" +
      "void main(){vec4 c;mainImage(c, gl_FragCoord.xy);gl_FragColor=vec4(c.rgb," + alphaExpr + ");}";

    const prog = gl.createProgram();
    gl.attachShader(prog, compile(gl, gl.VERTEX_SHADER, VS));
    gl.attachShader(prog, compile(gl, gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(prog); gl.useProgram(prog);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(prog, "p");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

    const uRes = gl.getUniformLocation(prog, "iResolution");
    const uTime = gl.getUniformLocation(prog, "iTime");
    const uMouse = gl.getUniformLocation(prog, "iMouse");
    const uScaleL = gl.getUniformLocation(prog, "uScale");
    const uBoundaryL = gl.getUniformLocation(prog, "uBoundary");

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const mouse = { x: -1e4, y: -1e4 };
    const q = new URLSearchParams(location.search);
    const forced = q.has("mx") && q.has("my")
      ? { x: parseFloat(q.get("mx")), y: parseFloat(q.get("my")) } : null;

    function resize() {
      const r = canvas.getBoundingClientRect();
      const w = Math.max(1, Math.round(r.width * dpr));
      const h = Math.max(1, Math.round(r.height * dpr));
      if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; gl.viewport(0, 0, w, h); }
    }
    function setMouseFromClient(cx, cy) {
      const r = canvas.getBoundingClientRect();
      mouse.x = (cx - r.left) * dpr;
      mouse.y = (r.height - (cy - r.top)) * dpr;
    }
    (opts.track || window).addEventListener("mousemove", e => setMouseFromClient(e.clientX, e.clientY));
    if (forced) setMouseFromClient(forced.x, forced.y);

    const t0 = performance.now();
    let raf = 0;
    let stopped = false;
    function frame(now) {
      if (stopped) return;
      resize();
      gl.uniform3f(uRes, canvas.width, canvas.height, 1.0);
      gl.uniform1f(uTime, (now - t0) / 1000);
      gl.uniform1f(uScaleL, dpr);
      gl.uniform1f(uBoundaryL, (opts.boundaryFn ? opts.boundaryFn() : 0) * dpr);
      gl.uniform4f(uMouse, mouse.x, mouse.y, 0, 0);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      raf = requestAnimationFrame(frame);
    }
    raf = requestAnimationFrame(frame);
    // Disposer - call when the landing unmounts (e.g. user enters a project)
    // so the RAF loop stops and the GL context can be reclaimed instead of
    // running invisibly behind every other screen.
    return function dispose() {
      stopped = true;
      if (raf) cancelAnimationFrame(raf);
    };
  };

  // ==========================================================================
  // Per-card shader runtime - same architecture as mountShader() but exposes
  // a `uTint` vec3 uniform the caller seeds from a per-project-ID palette
  // entry, and ignores the dark-band boundary (cards are pure light field).
  // Used by the projects landing to fill the 16:9 strip at the top of every
  // card that doesn't have a thumbnail prototype set. The cursor lighting
  // tracks mouse position relative to the canvas itself (not the window) so
  // each card lights up independently as the user moves between them.
  //
  // Signature: window.mountCardShader(canvas, fragBody, { tint: [r,g,b] })
  // Returns a dispose() function - call when the card unmounts.
  // ==========================================================================
  window.mountCardShader = function (canvas, fragBody, opts) {
    opts = opts || {};
    const tint = (opts.tint && opts.tint.length === 3) ? opts.tint : [0.962, 0.957, 0.947];
    const gl = canvas.getContext("webgl", { antialias: true, alpha: true, premultipliedAlpha: false });
    if (!gl) { console.warn("no webgl"); return function () { }; }

    const FS =
      "precision highp float;\n" +
      "uniform vec3 iResolution;uniform float iTime;uniform vec4 iMouse;uniform float uScale;uniform vec3 uTint;uniform float uHover;\n" +
      fragBody + "\n" +
      "void main(){vec4 c;mainImage(c, gl_FragCoord.xy);gl_FragColor=vec4(c.rgb,1.0);}";

    const prog = gl.createProgram();
    gl.attachShader(prog, compile(gl, gl.VERTEX_SHADER, VS));
    gl.attachShader(prog, compile(gl, gl.FRAGMENT_SHADER, FS));
    gl.linkProgram(prog); gl.useProgram(prog);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    const loc = gl.getAttribLocation(prog, "p");
    gl.enableVertexAttribArray(loc);
    gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

    const uRes = gl.getUniformLocation(prog, "iResolution");
    const uTime = gl.getUniformLocation(prog, "iTime");
    const uMouse = gl.getUniformLocation(prog, "iMouse");
    const uScaleL = gl.getUniformLocation(prog, "uScale");
    const uTintL = gl.getUniformLocation(prog, "uTint");
    const uHoverL = gl.getUniformLocation(prog, "uHover");

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    // Park the cursor far away by default so the lighting doesn't render
    // a hotspot in the middle when the user hasn't moved into this card yet.
    const mouse = { x: -1e4, y: -1e4 };
    let hover = 0;       // 0..1 - eases up while the cursor is inside the card

    function resize() {
      const r = canvas.getBoundingClientRect();
      const w = Math.max(1, Math.round(r.width * dpr));
      const h = Math.max(1, Math.round(r.height * dpr));
      if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; gl.viewport(0, 0, w, h); }
    }
    function setMouseFromClient(cx, cy) {
      const r = canvas.getBoundingClientRect();
      mouse.x = (cx - r.left) * dpr;
      mouse.y = (r.height - (cy - r.top)) * dpr;
    }
    // Track mouse on the card's parent so the lighting reaches the canvas
    // even when the cursor is over a child element (label, badge, button).
    const host = opts.track || canvas;
    function onMove(e) { setMouseFromClient(e.clientX, e.clientY); }
    function onEnter() { hoverTarget = 1; }
    function onLeave() { hoverTarget = 0; mouse.x = -1e4; mouse.y = -1e4; }
    let hoverTarget = 0;
    host.addEventListener("mousemove", onMove);
    host.addEventListener("mouseenter", onEnter);
    host.addEventListener("mouseleave", onLeave);

    const t0 = performance.now();
    let raf = 0;
    let stopped = false;
    function frame(now) {
      if (stopped) return;
      resize();
      // Ease the hover signal so the cursor halo blooms in / fades out.
      hover += (hoverTarget - hover) * 0.12;
      gl.uniform3f(uRes, canvas.width, canvas.height, 1.0);
      gl.uniform1f(uTime, (now - t0) / 1000);
      gl.uniform1f(uScaleL, dpr);
      gl.uniform3f(uTintL, tint[0], tint[1], tint[2]);
      gl.uniform1f(uHoverL, hover);
      gl.uniform4f(uMouse, mouse.x, mouse.y, 0, 0);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      raf = requestAnimationFrame(frame);
    }
    raf = requestAnimationFrame(frame);
    return function dispose() {
      stopped = true;
      if (raf) cancelAnimationFrame(raf);
      try {
        host.removeEventListener("mousemove", onMove);
        host.removeEventListener("mouseenter", onEnter);
        host.removeEventListener("mouseleave", onLeave);
      } catch { }
    };
  };

  // Curated on-brand palette for the no-thumbnail landing-card field. Every
  // tint is an identity-bearing pastel - saturated enough to read as a
  // distinct colour through a 10%-opacity glass overlay, muted enough to
  // sit alongside the editor accent green without clashing. Picked by
  // hashing the project ID so each card has a stable colour across reloads.
  // Lightness ~70-82% gives the diamond shader behind the glass a real
  // tint cast instead of disappearing into the cream base.
  window.LANDING_CARD_PALETTE = [
    [0.96, 0.84, 0.66], // peach
    [0.74, 0.86, 0.76], // sage
    [0.78, 0.82, 0.92], // periwinkle
    [0.92, 0.74, 0.78], // blush
    [0.86, 0.78, 0.92], // lilac
    [0.96, 0.92, 0.70], // butter
    [0.74, 0.88, 0.86], // mint
    [0.88, 0.80, 0.66], // honey
    [0.78, 0.78, 0.92], // hyacinth
    [0.94, 0.78, 0.70], // coral
    [0.82, 0.92, 0.78], // pistachio
    [0.96, 0.78, 0.86], // rose
    [0.70, 0.82, 0.90], // sky
    [0.92, 0.86, 0.72], // dune
    [0.84, 0.74, 0.86], // mauve
    [0.74, 0.90, 0.82], // seafoam
  ];

  // FNV-1a 32-bit string hash - small, deterministic, no dependency.
  window.landingCardTint = function (seed) {
    const pal = window.LANDING_CARD_PALETTE;
    if (!seed) return pal[0];
    let h = 0x811c9dc5 >>> 0;
    for (let i = 0; i < seed.length; i++) {
      h ^= seed.charCodeAt(i);
      h = Math.imul(h, 0x01000193) >>> 0;
    }
    return pal[h % pal.length];
  };

  // ==========================================================================
  // Per-card shader body - verbatim diamond grid + cursor lighting from the
  // landing background, but tinted by `uTint` (the project's seeded colour)
  // and with no dark-band boundary (cards are pure light field). The cursor
  // lighting fades with `uHover` so cards at rest just show the static
  // diamond field; cards under the cursor light up.
  // ==========================================================================
  window.SHADER_CARD = `
  const float PI = 3.14159265;
  const float CELLC = 28.0;     // tighter than the bg's 48px to fit the 16:9 card

  void mainImage(out vec4 o, in vec2 frag){
    float CELL = CELLC * uScale;
    vec2 fragT  = vec2(frag.x, iResolution.y - frag.y);
    vec2 mouseT = vec2(iMouse.x, iResolution.y - iMouse.y);
    vec2 uv = vec2(fragT.x + fragT.y, fragT.x - fragT.y) / CELL;
    vec2 id = floor(uv);
    vec2 f  = fract(uv) - 0.5;
    float edge = max(abs(f.x), abs(f.y));

    // ---- LIGHT: tinted diamond field + cursor lighting ---------------------
    vec3 base = uTint;
    float line = smoothstep(0.47, 0.5, edge);
    float dist = length(mouseT - fragT);
    vec3 fcol = base;

    // Gentle ambient drift - diamonds at the extreme corners pick up a
    // microscopic shade variation that breathes with iTime so the field
    // doesn't feel painted-on dead. ~1% modulation, period ~12s.
    float drift = 0.5 + 0.5 * sin(iTime * 0.5 + (id.x + id.y) * 0.6);
    fcol *= mix(0.985, 1.000, drift);

    // Pattern band that softens the diamond lines under the cursor - same
    // idea as the bg shader, scaled to the card.
    float pat = smoothstep(180.0 * uScale, 0.0, dist) * uHover;
    pat = pat * pat * (3.0 - 2.0 * pat);
    vec3 lineCol = base * 0.92;
    fcol = mix(fcol, mix(fcol, lineCol, line * 0.5), pat);

    // Diamond surface lighting - alternating-sign quilt with a 3D normal,
    // lit by a point above the cursor. Hover-gated so it only blooms when
    // the cursor is over this card.
    float sgn = mod(id.x + id.y, 2.0) < 0.5 ? 1.0 : -1.0;
    float HS  = 7.5 * uScale;
    float Z   = sgn * 0.5 * (cos(PI * f.x) + cos(PI * f.y)) * HS;
    float hx  = sgn * 0.5 * (-PI * sin(PI * f.x));
    float hy  = sgn * 0.5 * (-PI * sin(PI * f.y));
    vec2  g   = vec2(hx + hy, hx - hy) * (HS / CELL);
    vec3  N   = normalize(vec3(-g, 1.0));
    vec3  Ld  = normalize(vec3(mouseT, 80.0 * uScale) - vec3(fragT, Z));
    float diff = dot(N, Ld);
    float lit = smoothstep(120.0 * uScale, 0.0, dist);
    lit = lit * lit * lit * uHover;
    float shade = 1.0 + min(diff, 0.0) * 0.42;
    fcol *= mix(1.0, shade, lit);

    float innerBand = smoothstep(0.34, 0.40, edge) * (1.0 - smoothstep(0.40, 0.46, edge));
    bool fxEdge = abs(f.x) > abs(f.y);
    float sel = (sgn > 0.0) ? (fxEdge ? 1.0 : 0.0) : (fxEdge ? 0.0 : 1.0);
    vec3 hi = mix(base, vec3(1.0), 0.55);
    fcol = mix(fcol, hi, innerBand * sel * lit * 0.9);

    o = vec4(fcol, 1.0);
  }`;

  // ==========================================================================
  // Unified background shader - verbatim from landing-diamonds/shaders.js.
  // See landing-diamonds/README.md §1-§2 for the maths.
  // ==========================================================================
  window.SHADER_BG = `
  const float PI = 3.14159265;
  const float CELLC = 48.0;     // diamond module in CSS px

  // 1.0 if the diamond owning this fragment is above the boundary (dark side).
  // The dark/light split runs along shared diamond EDGES, so the boundary is a
  // grid-perfect zigzag = teeth. centreYT = the diamond centre's px-from-top.
  float darkAt(vec2 fr){
    float CELL = CELLC * uScale;
    vec2 ft = vec2(fr.x, iResolution.y - fr.y);
    vec2 uv = vec2((ft.x + ft.y), (ft.x - ft.y)) / CELL;
    vec2 id = floor(uv);
    float centreYT = 0.5 * (id.x - id.y) * CELL;
    return step(centreYT, uBoundary);
  }

  void mainImage(out vec4 o, in vec2 frag){
    float CELL = CELLC * uScale;
    vec2 fragT  = vec2(frag.x, iResolution.y - frag.y);
    vec2 mouseT = vec2(iMouse.x, iResolution.y - iMouse.y);
    vec2 uv = vec2(fragT.x + fragT.y, fragT.x - fragT.y) / CELL;
    vec2 id = floor(uv);
    vec2 f  = fract(uv) - 0.5;
    float edge = max(abs(f.x), abs(f.y));

    // ---- teeth boundary mask (4-tap AA along the zigzag edges) -------------
    float dm = 0.25 * (darkAt(frag + vec2(-0.3,-0.3)) + darkAt(frag + vec2(0.3,-0.3))
                     + darkAt(frag + vec2(-0.3, 0.3)) + darkAt(frag + vec2(0.3, 0.3)));

    // ---- DARK: header colour + faint diamond fretwork (same grid) ----------
    vec3 headerCol = vec3(0.071, 0.090, 0.086);
    float fret = smoothstep(0.44, 0.5, edge);
    vec3 darkCol = headerCol + vec3(0.05, 0.06, 0.055) * fret;

    // ---- LIGHT: flat diamond field + cursor lighting -----------------------
    vec3 base = vec3(0.962, 0.957, 0.947);
    float line = smoothstep(0.47, 0.5, edge);
    float dist = length(mouseT - fragT);
    vec3 fcol = base;

    float pat = smoothstep(460.0 * uScale, 0.0, dist);
    pat = pat * pat * (3.0 - 2.0 * pat);
    fcol = mix(fcol, mix(fcol, vec3(0.885, 0.875, 0.855), line * 0.5), pat);

    float sgn = mod(id.x + id.y, 2.0) < 0.5 ? 1.0 : -1.0;
    float HS  = 11.0 * uScale;
    float Z   = sgn * 0.5 * (cos(PI * f.x) + cos(PI * f.y)) * HS;
    float hx  = sgn * 0.5 * (-PI * sin(PI * f.x));
    float hy  = sgn * 0.5 * (-PI * sin(PI * f.y));
    vec2  g   = vec2(hx + hy, hx - hy) * (HS / CELL);
    vec3  N   = normalize(vec3(-g, 1.0));
    vec3  Ld  = normalize(vec3(mouseT, 110.0 * uScale) - vec3(fragT, Z));
    float diff = dot(N, Ld);
    float lit = smoothstep(200.0 * uScale, 0.0, dist);
    lit = lit * lit * lit;
    float shade = 1.0 + min(diff, 0.0) * 0.38;          // shadow-only, no hotspot
    fcol *= mix(1.0, shade, lit);

    float innerBand = smoothstep(0.34, 0.40, edge) * (1.0 - smoothstep(0.40, 0.46, edge));
    bool fxEdge = abs(f.x) > abs(f.y);
    float sel = (sgn > 0.0) ? (fxEdge ? 1.0 : 0.0) : (fxEdge ? 0.0 : 1.0);
    fcol = mix(fcol, vec3(0.995, 0.99, 0.984), innerBand * sel * lit * 0.9);

    o = vec4(mix(fcol, darkCol, dm), 1.0);
  }`;

  // ==========================================================================
  // Dark-band overlay shader - same body as SHADER_BG but outputs alpha = dm
  // so the canvas is opaque in the dark band + teeth zigzag (cards behind it
  // are hidden) and transparent in the light field (cards remain visible).
  // The teeth boundary follows the actual zigzag geometry per-pixel rather
  // than being cut at a flat horizontal CSS line.
  // Mounted at z-index above .landing-main, behind .landing-header content.
  // ==========================================================================
  window.SHADER_DARKBAND = `
  const float PI = 3.14159265;
  const float CELLC = 48.0;

  float darkAt(vec2 fr){
    float CELL = CELLC * uScale;
    vec2 ft = vec2(fr.x, iResolution.y - fr.y);
    vec2 uv = vec2((ft.x + ft.y), (ft.x - ft.y)) / CELL;
    vec2 id = floor(uv);
    float centreYT = 0.5 * (id.x - id.y) * CELL;
    return step(centreYT, uBoundary);
  }

  void mainImage(out vec4 o, in vec2 frag){
    float CELL = CELLC * uScale;
    vec2 fragT  = vec2(frag.x, iResolution.y - frag.y);
    vec2 uv = vec2(fragT.x + fragT.y, fragT.x - fragT.y) / CELL;
    vec2 f  = fract(uv) - 0.5;
    float edge = max(abs(f.x), abs(f.y));

    float dm = 0.25 * (darkAt(frag + vec2(-0.3,-0.3)) + darkAt(frag + vec2(0.3,-0.3))
                     + darkAt(frag + vec2(-0.3, 0.3)) + darkAt(frag + vec2(0.3, 0.3)));

    vec3 headerCol = vec3(0.071, 0.090, 0.086);
    float fret = smoothstep(0.44, 0.5, edge);
    vec3 darkCol = headerCol + vec3(0.05, 0.06, 0.055) * fret;

    o = vec4(darkCol, dm);
  }`;
})();
