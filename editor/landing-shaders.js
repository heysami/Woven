// ============================================================================
// Landing-screen shader runtime - drives a single full-page WebGL canvas
// behind the Projects landing that draws one uniform light diamond field
// with cursor-driven lighting. The header is a separate element over it.
// Uniforms: iResolution(px), iTime(s), iMouse(px,y-up), uScale(dpr)
// Exposes:  window.mountShader(canvas, fragBody, opts)
//           window.SHADER_BG
//           window.LANDING_CARD_PALETTE (consumed by app.js for CSS card tints)
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
      "uniform vec3 iResolution;uniform float iTime;uniform vec4 iMouse;uniform float uScale;\n" +
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

    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const mouse = { x: -1e4, y: -1e4 };

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

    const t0 = performance.now();
    let raf = 0;
    let stopped = false;
    function frame(now) {
      if (stopped) return;
      resize();
      gl.uniform3f(uRes, canvas.width, canvas.height, 1.0);
      gl.uniform1f(uTime, (now - t0) / 1000);
      gl.uniform1f(uScaleL, dpr);
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

  // ==========================================================================
  // Unified background shader - the LIGHT diamond field across the whole
  // landing (no dark band, no teeth boundary). See landing-diamonds/README.md
  // §1-§2 for the diamond-grid + cursor-lighting maths.
  // ==========================================================================
  window.SHADER_BG = `
  const float PI = 3.14159265;
  const float CELLC = 48.0;     // diamond module in CSS px

  void mainImage(out vec4 o, in vec2 frag){
    float CELL = CELLC * uScale;
    vec2 fragT  = vec2(frag.x, iResolution.y - frag.y);
    vec2 mouseT = vec2(iMouse.x, iResolution.y - iMouse.y);
    vec2 uv = vec2(fragT.x + fragT.y, fragT.x - fragT.y) / CELL;
    vec2 id = floor(uv);
    vec2 f  = fract(uv) - 0.5;
    float edge = max(abs(f.x), abs(f.y));

    // ---- LIGHT: pure-white diamond field + LIGHT-GREY cursor shine ---------
    // Background is pure white. Near the cursor the diamonds catch a subtle
    // LIGHT-GREY shine on one side of each edge. No dark shadow / face-shading.
    vec3 base = vec3(1.0, 1.0, 1.0);
    float line = smoothstep(0.47, 0.5, edge);
    float dist = length(mouseT - fragT);
    vec3 fcol = base;

    float pat = smoothstep(460.0 * uScale, 0.0, dist);
    pat = pat * pat * (3.0 - 2.0 * pat);
    fcol = mix(fcol, mix(fcol, vec3(0.90, 0.90, 0.90), line * 0.35), pat);

    float lit = smoothstep(200.0 * uScale, 0.0, dist);
    lit = lit * lit * lit;

    // Light-grey shine on the selected side of each diamond edge near the cursor.
    float sgn = mod(id.x + id.y, 2.0) < 0.5 ? 1.0 : -1.0;
    float innerBand = smoothstep(0.34, 0.40, edge) * (1.0 - smoothstep(0.40, 0.46, edge));
    bool fxEdge = abs(f.x) > abs(f.y);
    float sel = (sgn > 0.0) ? (fxEdge ? 1.0 : 0.0) : (fxEdge ? 0.0 : 1.0);
    fcol = mix(fcol, vec3(0.95, 0.95, 0.95), innerBand * sel * lit * 0.9);

    o = vec4(fcol, 1.0);
  }`;
})();
