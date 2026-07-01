/* editor/compress.js - client-side asset compression with open-source WASM codecs.

   Raster: jSquash (https://github.com/jamsinclair/jSquash) - the maintained WASM
           packaging of Google Squoosh's reference encoders. JPEG -> MozJPEG,
           WebP -> libwebp, PNG -> OxiPNG (lossless). Best quality-per-byte in the
           open-source world.
   Video:  ffmpeg.wasm (https://ffmpegwasm.netlify.app) - single-thread core, so
           no SharedArrayBuffer / cross-origin-isolation headers are required.

   Codecs lazy-load from a CDN at first use - the same convention index.html uses
   for React / htm / mermaid (unpkg <script> tags). Nothing is committed to the
   repo, and the heavy WASM only downloads when the user actually compresses
   something (ffmpeg's core is only fetched on the first VIDEO compress).

   Every compress fn returns { dataUrl, mime, after } so the caller can write the
   bytes back via /__write_binary (exactly like the crop modal) and report the
   savings. Container/extension is always preserved, so paths + references that
   point at the file keep resolving. Throws on unsupported input or codec-load
   failure; the caller decides how to surface it.

   Exposes window.WovenCompress. No build step (dynamic import() of CDN ESM). */
(function () {
  "use strict";

  // Quality presets. Higher preset = better fidelity, larger file. `png` is the
  // OxiPNG effort level (1-6, lossless); `crf` is the video constant-rate-factor
  // (lower = higher quality). jpeg/webp are 0-100 quality.
  var PRESETS = {
    high:       { label: "High",       jpeg: 82, webp: 82, png: 3, crf: 23 },
    balanced:   { label: "Balanced",   jpeg: 72, webp: 72, png: 4, crf: 28 },
    aggressive: { label: "Aggressive", jpeg: 58, webp: 55, png: 6, crf: 32 },
  };

  var JSQUASH = {
    jpeg:   "https://esm.sh/@jsquash/jpeg@1.6.0",
    webp:   "https://esm.sh/@jsquash/webp@1.5.0",
    oxipng: "https://esm.sh/@jsquash/oxipng@2.3.0",
  };
  // ffmpeg.wasm is loaded from its UMD build (NOT esm.sh): the ESM build spins
  // up a Worker whose sub-imports don't resolve through esm.sh ("Failed to fetch
  // dynamically imported module"). We load only the @ffmpeg/ffmpeg UMD bundle
  // (exposes FFmpegWASM.FFmpeg) and drive it directly - @ffmpeg/util is skipped
  // because its UMD bundle throws "Object.defineProperty called on non-object"
  // on execution here, and all we need from it (toBlobURL + fetchFile) is two
  // trivial fetch helpers, inlined below. The worker chunk (814.ffmpeg.js) is
  // handed to load() as a SAME-ORIGIN blob via classWorkerURL (a Worker script
  // can't be loaded cross-origin straight from a CDN).
  var FFMPEG_UMD  = "https://unpkg.com/@ffmpeg/ffmpeg@0.12.15/dist/umd";
  var FFMPEG_CORE = "https://cdn.jsdelivr.net/npm/@ffmpeg/core@0.12.10/dist/umd";

  // The two @ffmpeg/util helpers we actually use, inlined (see note above).
  async function toBlobURL(url, mimeType) {
    var resp = await fetch(url);
    if (!resp.ok) throw new Error("failed to fetch " + url + " (HTTP " + resp.status + ")");
    return URL.createObjectURL(new Blob([await resp.arrayBuffer()], { type: mimeType }));
  }
  async function fetchFile(url) {
    var resp = await fetch(url);
    if (!resp.ok) throw new Error("failed to fetch " + url + " (HTTP " + resp.status + ")");
    return new Uint8Array(await resp.arrayBuffer());
  }

  var RASTER = { png: 1, jpg: 1, jpeg: 1, webp: 1 };
  // Video containers we can round-trip while PRESERVING the extension (so the
  // on-disk path never changes). ogv/others are intentionally excluded.
  var VIDEO = { mp4: 1, m4v: 1, mov: 1, webm: 1 };

  function extOf(path) { return (String(path || "").split(".").pop() || "").toLowerCase(); }
  function isRaster(path) { return !!RASTER[extOf(path)]; }
  function isVideo(path) { return !!VIDEO[extOf(path)]; }
  function canCompress(path) { return isRaster(path) || isVideo(path); }

  // Memoised dynamic imports so a batch loads each codec module once.
  var _mods = {};
  function load(url) {
    if (!_mods[url]) _mods[url] = import(url);
    return _mods[url];
  }

  // Load a UMD bundle and return its browser global, robustly. A plain <script>
  // tag lets the UMD wrapper's own environment detection run against the host
  // page - and the Woven editor exposes module/exports/define shims, which
  // divert the export to a CommonJS/AMD branch instead of window (symptom:
  // "failed to expose its globals"). So we fetch the source and execute it with
  // module/exports/define shadowed to undefined, forcing the wrapper's plain
  // `self.<Global> = ...` branch. Memoised per URL.
  var _umd = {};
  function loadUmdGlobal(url, globalName) {
    if (window[globalName]) return Promise.resolve(window[globalName]);
    if (!_umd[url]) {
      _umd[url] = (async function () {
        var resp = await fetch(url);
        if (!resp.ok) throw new Error("failed to fetch " + url + " (HTTP " + resp.status + ")");
        var code = await resp.text();
        // module/exports/define -> undefined inside; `self`/`window` stay real.
        (new Function("module", "exports", "define", code))();
        if (!window[globalName]) throw new Error(globalName + " was not exposed by " + url);
        return window[globalName];
      })();
    }
    return _umd[url];
  }

  function loadImageEl(src) {
    return new Promise(function (res, rej) {
      var im = new Image();
      im.decoding = "async";
      im.onload = function () { res(im); };
      im.onerror = function () { rej(new Error("could not decode the image")); };
      im.src = src;
    });
  }

  // Decode any browser-renderable raster to ImageData. Using the browser's own
  // decoder (rather than a jSquash decoder) means every input type - including
  // ones jSquash can't decode - funnels through one path, and the encoders below
  // only ever see raw RGBA pixels.
  async function imageDataFrom(src) {
    var im = await loadImageEl(src);
    var w = im.naturalWidth, h = im.naturalHeight;
    if (!w || !h) throw new Error("image reported zero dimensions");
    var c = document.createElement("canvas");
    c.width = w; c.height = h;
    var cx = c.getContext("2d");
    if (!cx) throw new Error("no 2d canvas context");
    cx.drawImage(im, 0, 0);
    return cx.getImageData(0, 0, w, h);
  }

  function u8ToDataUrl(u8, mime) {
    var bin = "", CH = 0x8000;
    for (var i = 0; i < u8.length; i += CH) {
      bin += String.fromCharCode.apply(null, u8.subarray(i, Math.min(i + CH, u8.length)));
    }
    return "data:" + mime + ";base64," + btoa(bin);
  }

  // ── Raster ────────────────────────────────────────────────────────────────
  // `src` is a loadable URL for the current bytes; `path` supplies the extension
  // (which decides the encoder and is preserved). Returns the re-encoded bytes.
  async function compressImage(src, path, presetName) {
    var p = PRESETS[presetName] || PRESETS.balanced;
    var e = extOf(path);
    var id = await imageDataFrom(src);
    var buf, mime;
    if (e === "jpg" || e === "jpeg") {
      var jpeg = await load(JSQUASH.jpeg);
      buf = await jpeg.encode(id, { quality: p.jpeg });      // MozJPEG
      mime = "image/jpeg";
    } else if (e === "webp") {
      var webp = await load(JSQUASH.webp);
      buf = await webp.encode(id, { quality: p.webp });      // libwebp
      mime = "image/webp";
    } else if (e === "png") {
      var oxi = await load(JSQUASH.oxipng);
      buf = await oxi.optimise(id, { level: p.png, optimiseAlpha: true }); // lossless
      mime = "image/png";
    } else {
      throw new Error("unsupported image type ." + e);
    }
    var u8 = new Uint8Array(buf);
    return { dataUrl: u8ToDataUrl(u8, mime), mime: mime, after: u8.length };
  }

  // ── Video ─────────────────────────────────────────────────────────────────
  var _ff = null; // { ff } singleton (core is ~30MB - load once, reuse)
  async function ffmpeg() {
    if (_ff) return _ff;
    var FFmpegWASM = await loadUmdGlobal(FFMPEG_UMD + "/ffmpeg.js", "FFmpegWASM");
    if (!FFmpegWASM || !FFmpegWASM.FFmpeg) {
      throw new Error("ffmpeg UMD loaded but is missing the FFmpeg constructor");
    }
    var ff = new FFmpegWASM.FFmpeg();
    // classWorkerURL: same-origin blob of the UMD worker chunk (a cross-origin
    // Worker script from a CDN is blocked by the browser). core/wasm likewise
    // wrapped as blobs so they load same-origin.
    await ff.load({
      classWorkerURL: await toBlobURL(FFMPEG_UMD + "/814.ffmpeg.js", "text/javascript"),
      coreURL: await toBlobURL(FFMPEG_CORE + "/ffmpeg-core.js", "text/javascript"),
      wasmURL: await toBlobURL(FFMPEG_CORE + "/ffmpeg-core.wasm", "application/wasm"),
    });
    _ff = { ff: ff };
    return _ff;
  }

  // Re-encode a video in place, KEEPING the container (extension). mp4/m4v/mov ->
  // H.264 + AAC; webm -> VP9 + Opus. CRF from the preset controls quality/size.
  async function compressVideo(src, path, presetName) {
    var p = PRESETS[presetName] || PRESETS.balanced;
    var e = extOf(path);
    if (!VIDEO[e]) throw new Error("unsupported video container ." + e);
    var api = await ffmpeg();
    var ff = api.ff;
    var inName = "in." + e, outName = "out." + e;
    await ff.writeFile(inName, await fetchFile(src));
    var args;
    if (e === "webm") {
      args = ["-i", inName, "-c:v", "libvpx-vp9", "-crf", String(p.crf + 3), "-b:v", "0",
              "-c:a", "libopus", "-b:a", "96k", outName];
      var vmime = "video/webm";
    } else {
      args = ["-i", inName, "-c:v", "libx264", "-crf", String(p.crf), "-preset", "medium",
              "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", outName];
      var vmime = "video/mp4";
    }
    await ff.exec(args);
    var data = await ff.readFile(outName);
    try { await ff.deleteFile(inName); await ff.deleteFile(outName); } catch (_e) {}
    var u8 = (data instanceof Uint8Array) ? data : new Uint8Array(data);
    if (!u8.length) throw new Error("ffmpeg produced an empty file");
    return { dataUrl: u8ToDataUrl(u8, vmime), mime: vmime, after: u8.length };
  }

  window.WovenCompress = {
    presets: PRESETS,
    presetKeys: ["high", "balanced", "aggressive"],
    canCompress: canCompress,
    isRaster: isRaster,
    isVideo: isVideo,
    extOf: extOf,
    compressImage: compressImage,
    compressVideo: compressVideo,
  };
})();
