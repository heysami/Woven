// ============================================================================
// Landing-header diamond-halftone glass runtime.
//
// Makes the Projects-landing header a SEE-THROUGH diamond halftone of the
// content behind it - the same trick the design-system glass uses
// (themes/glassmorphism.js): you cannot sample live DOM in a shader, so we
// RASTERISE the landing content once into a texture (html2canvas) and a WebGL2
// canvas glued to the header samples that texture, PANNED by the scroll offset.
// The shader renders the sampled content as a field of diamond dots whose size
// tracks the local luminance (dark content -> big diamonds, light -> small) -
// a real halftone of the real cards, not a fixed screen stamped on top.
//
// Texture discipline (the "don't let it build up" rule):
//   * ONE GL texture per header, created once; every capture re-uploads into
//     that same handle via texImage2D (the driver frees the old pixels) - no
//     new texture, no growth.
//   * exactly ONE capture canvas is held at a time (the previous is dropped).
//   * captures fire ONLY on explicit triggers - tab-switch (recapture()),
//     resize, and after-scroll-settle - never per frame, never on DOM mutation
//     (html2canvas mutates the DOM while capturing; observing that = infinite
//     capture loop). Per frame we only PAN the existing texture.
//
// Falls back to the CSS frost (styles.css .landing-header) when WebGL2 or
// html2canvas is unavailable: this runtime just returns null and never paints.
//
// API: window.mountLandingHalftone(canvas, headerEl, scrollEl)
//        -> { recapture(), dispose() }  |  null when unsupported
// ============================================================================
(function () {
  if (window.mountLandingHalftone) return;            // guard double-load
  var DPR = Math.min(2, window.devicePixelRatio || 1);
  var CELL_CSS = 22;                                  // diamond module in CSS px
  var PAPER = [0.962, 0.957, 0.947];                  // matches the field base

  var VS =
    "#version 300 es\n" +
    "in vec2 p; void main(){ gl_Position = vec4(p, 0.0, 1.0); }";

  var FS =
    "#version 300 es\n" +
    "precision highp float; out vec4 o;\n" +
    "uniform sampler2D uPage;\n" +
    "uniform vec2 uPagePx, uCanvas, uCardTL; uniform float uScroll, uCell;\n" +
    "uniform vec3 uPaper;\n" +
    "void main(){\n" +
    "  vec2 frag = vec2(gl_FragCoord.x, uCanvas.y - gl_FragCoord.y);     // top-left origin\n" +
    "  vec2 docPx = vec2(uCardTL.x + frag.x, uCardTL.y + frag.y + uScroll);\n" +
    "  // diamond cell coords (rotate the grid 45deg so cells are diamonds)\n" +
    "  vec2 uv = vec2(docPx.x + docPx.y, docPx.x - docPx.y) / uCell;\n" +
    "  vec2 f = fract(uv) - 0.5;\n" +
    "  float edge = max(abs(f.x), abs(f.y));\n" +
    "  // sample the ACTUAL content behind the glass\n" +
    "  vec3 src = texture(uPage, docPx / uPagePx).rgb;\n" +
    "  float L = dot(src, vec3(0.299, 0.587, 0.114));\n" +
    "  float ink = clamp(1.0 - L, 0.0, 1.0);\n" +
    "  float r = sqrt(ink) * 0.5;                       // dot radius tracks darkness\n" +
    "  float aa = 1.5 / uCell;\n" +
    "  float dotm = 1.0 - smoothstep(r - aa, r + aa, edge);\n" +
    "  vec3 inkc = mix(src * 0.72, vec3(0.10, 0.12, 0.11), 0.22);  // colored ink, slightly deepened\n" +
    "  vec3 col = mix(uPaper, inkc, dotm);\n" +
    "  o = vec4(col, 1.0);\n" +
    "}";

  function compile(gl, t, src) {
    var s = gl.createShader(t); gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      throw new Error(gl.getShaderInfoLog(s));
    }
    return s;
  }
  function debounce(fn, ms) {
    var t; return function () { clearTimeout(t); t = setTimeout(fn, ms); };
  }

  window.mountLandingHalftone = function (canvas, headerEl, scrollEl) {
    if (!canvas || !headerEl || !scrollEl) return null;
    if (typeof window.html2canvas !== "function") return null;  // -> CSS frost fallback
    var gl;
    try { gl = canvas.getContext("webgl2", { alpha: true, premultipliedAlpha: false }); } catch (e) { gl = null; }
    if (!gl) return null;

    var prog, buf, tex, U = {};
    try {
      prog = gl.createProgram();
      gl.attachShader(prog, compile(gl, gl.VERTEX_SHADER, VS));
      gl.attachShader(prog, compile(gl, gl.FRAGMENT_SHADER, FS));
      gl.linkProgram(prog);
      if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(prog));
    } catch (e) { if (window.console) console.warn("[landing-halftone] " + e.message); return null; }
    gl.useProgram(prog);
    buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    tex = gl.createTexture();   // THE one texture - reused for every capture
    ["uPage", "uPagePx", "uCanvas", "uCardTL", "uScroll", "uCell", "uPaper"]
      .forEach(function (k) { U[k] = gl.getUniformLocation(prog, k); });

    var pageW = 1, pageH = 1, cardL = 0, cardT = 0;
    var ready = false, capturing = false, disposed = false, raf = 0, cw = 0, ch = 0;

    // Cache the header/main geometry - re-read only on resize/recapture, NOT per
    // frame (per-frame getBoundingClientRect thrashes layout). uScroll is the only
    // thing that changes every frame and scrollTop is a cheap read.
    function measure() {
      var hr = headerEl.getBoundingClientRect();
      var mr = scrollEl.getBoundingClientRect();
      cardL = (hr.left - mr.left + (scrollEl.scrollLeft || 0)) * DPR;
      cardT = (hr.top - mr.top) * DPR;       // scrollTop is added in-shader as uScroll
    }

    var MAXTEX = (function () { try { return gl.getParameter(gl.MAX_TEXTURE_SIZE) || 8192; } catch (e) { return 8192; } })();

    function capture() {
      if (capturing || disposed) return;
      var w = Math.max(scrollEl.scrollWidth, 1), h = Math.max(scrollEl.scrollHeight, 1);
      // Cap the rasterise scale so the capture fits one texture (a very tall
      // landing would otherwise blow past MAX_TEXTURE_SIZE and upload broken).
      var sc = Math.min(DPR, MAXTEX / w, MAXTEX / h);
      capturing = true;
      try {
        window.html2canvas(scrollEl, {
          backgroundColor: "#f5f4f1",   // cream = field base, so gaps read light
          scale: sc, logging: false, useCORS: true,
          // Hide the header (and its halftone canvas child) in the CLONE so the
          // texture is the clean content the glass sits over - never itself.
          onclone: function (doc) {
            var hs = doc.querySelectorAll(".landing-header");
            for (var i = 0; i < hs.length; i++) { try { hs[i].style.visibility = "hidden"; } catch (e) {} }
          }
        }).then(function (cap) {
          if (disposed) { capturing = false; return; }
          gl.bindTexture(gl.TEXTURE_2D, tex);
          gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, false);
          gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, cap);  // OVERWRITE in place
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
          gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
          // Derive the device-px extent the texture spans from the ACTUAL capture
          // size (cap.{width,height} = capturedCSS * sc), not an assumed
          // scrollHeight - so sampling stays correct whatever region html2canvas
          // returned. docPx (DPR space) / uPagePx then normalises into the texture.
          pageW = (cap.width / sc) * DPR; pageH = (cap.height / sc) * DPR;
          measure();
          ready = true; capturing = false;
        }).catch(function () { capturing = false; });
      } catch (e) { capturing = false; }
    }
    var scheduleCapture = debounce(capture, 250);

    function frame() {
      if (disposed) return;
      raf = requestAnimationFrame(frame);
      if (!ready) return;
      var hr = headerEl.getBoundingClientRect();   // header is static; rect is stable, read for size only
      var w = Math.max(1, Math.round(hr.width * DPR)), h = Math.max(1, Math.round(hr.height * DPR));
      if (cw !== w || ch !== h) { canvas.width = w; canvas.height = h; cw = w; ch = h; }
      gl.viewport(0, 0, cw, ch);
      gl.useProgram(prog);
      gl.bindBuffer(gl.ARRAY_BUFFER, buf); gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tex); gl.uniform1i(U.uPage, 0);
      gl.uniform2f(U.uPagePx, pageW, pageH);
      gl.uniform2f(U.uCanvas, cw, ch);
      gl.uniform2f(U.uCardTL, cardL, cardT);
      gl.uniform1f(U.uScroll, (scrollEl.scrollTop || 0) * DPR);
      gl.uniform1f(U.uCell, CELL_CSS * DPR);
      gl.uniform3f(U.uPaper, PAPER[0], PAPER[1], PAPER[2]);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    }

    // ── triggers ────────────────────────────────────────────────────────────
    var onResize = function () { measure(); scheduleCapture(); };
    var onScroll = function () { scheduleCapture(); };   // debounced -> fires after scroll SETTLES
    window.addEventListener("resize", onResize, { passive: true });
    scrollEl.addEventListener("scroll", onScroll, { passive: true });

    measure();
    raf = requestAnimationFrame(frame);
    setTimeout(capture, 250);     // initial rasterise once content has painted
    setTimeout(capture, 1200);    // one retry after late content / fonts / card shaders settle

    return {
      // Called by the landing on tab-switch / projects-list change. Debounced +
      // guarded, overwrites the single texture - no buildup.
      recapture: function () { measure(); scheduleCapture(); },
      dispose: function () {
        disposed = true;
        if (raf) cancelAnimationFrame(raf);
        window.removeEventListener("resize", onResize);
        try { scrollEl.removeEventListener("scroll", onScroll); } catch (e) {}
        try { var lo = gl.getExtension("WEBGL_lose_context"); if (lo) lo.loseContext(); } catch (e) {}
      }
    };
  };
})();
