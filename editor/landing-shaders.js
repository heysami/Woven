// ============================================================================
// Landing-screen shader runtime — lifted verbatim from the `landing-diamonds`
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
    const gl = canvas.getContext("webgl", { antialias: true, alpha: false });
    if (!gl) { console.warn("no webgl"); return; }

    const FS =
      "precision highp float;\n" +
      "uniform vec3 iResolution;uniform float iTime;uniform vec4 iMouse;uniform float uScale;uniform float uBoundary;\n" +
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
    // Disposer — call when the landing unmounts (e.g. user enters a project)
    // so the RAF loop stops and the GL context can be reclaimed instead of
    // running invisibly behind every other screen.
    return function dispose() {
      stopped = true;
      if (raf) cancelAnimationFrame(raf);
    };
  };

  // ==========================================================================
  // Unified background shader — verbatim from landing-diamonds/shaders.js.
  // See landing-diamonds/README.md §1–§2 for the maths.
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
})();
