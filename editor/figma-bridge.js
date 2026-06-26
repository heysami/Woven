/*
 * Woven -> Figma bridge: browser-side DOM walker.
 *
 * Loaded before app.js. Exposes window.WovenFigma.domToScene(rootEl), which
 * walks a rendered (same-origin) prototype document into an intermediate
 * "scene" JSON that the Woven Figma plugin rebuilds as real, editable Figma
 * nodes (frames / text / rectangles / image fills). The daemon is only a relay
 * for this payload; all DOM measurement happens here, where getComputedStyle
 * and getBoundingClientRect see the actual rendered result.
 *
 * Scene schema (see SCENE.md in editor/tools/figma-bridge/ for the contract):
 *   scene = { version, name, width, height, root }
 *   node  = {
 *     type:     "FRAME" | "TEXT" | "IMAGE",
 *     name:     string,
 *     x, y:     number,            // relative to the parent node
 *     width, height: number,
 *     opacity:  number,            // 0..1, omitted when 1
 *     clipsContent: boolean,       // overflow:hidden
 *     fills:    Paint[],           // SOLID | IMAGE | GRADIENT_LINEAR
 *     strokes:  Paint[],           // SOLID only
 *     strokeWeight: number,
 *     cornerRadius: number | {tl,tr,br,bl},
 *     effects:  Effect[],          // DROP_SHADOW | INNER_SHADOW
 *     // TEXT only:
 *     characters, fontSize, fontFamily, fontStyle, letterSpacing,
 *     lineHeight, textAlign, textColor, textDecoration,
 *     // IMAGE only:
 *     image: { b64, mime },
 *     children: node[]
 *   }
 *
 * Coordinates are absolute-position (each node carries x/y inside its parent),
 * unless the node has a `layout` (Figma auto-layout, inferred from CSS flex or a
 * clean block stack). CSS transforms are baked into position by
 * getBoundingClientRect, so rotation is flattened (the node lands where it
 * visually renders, un-rotated). A node may also carry `component` +
 * `componentProps` so the plugin swaps it for a bound Figma library instance
 * instead of rebuilding it from primitives.
 */
(function () {
  "use strict";

  var SCENE_VERSION = 3;
  // Total inlined-image budget. Past this we stop inlining and emit a flat
  // fill instead, so a heavy page cannot produce a multi-hundred-MB POST.
  var IMAGE_BUDGET_BYTES = 40 * 1024 * 1024;
  // Largest edge we keep for an inlined raster; bigger images are downscaled.
  var MAX_IMAGE_EDGE = 2000;

  function clamp01(n) { return n < 0 ? 0 : n > 1 ? 1 : n; }
  function px(v) { var n = parseFloat(v); return isFinite(n) ? n : 0; }
  function round(n) { return Math.round(n * 100) / 100; }

  // "rgb(12, 34, 56)" / "rgba(12,34,56,0.5)" -> { r,g,b in 0..1, a }
  function parseColor(str) {
    if (!str) return null;
    str = str.trim();
    if (str === "transparent") return { r: 0, g: 0, b: 0, a: 0 };
    var m = str.match(/^rgba?\(([^)]+)\)$/i);
    if (!m) return null;
    var parts = m[1].split(",").map(function (s) { return s.trim(); });
    if (parts.length < 3) return null;
    var r = parseFloat(parts[0]) / 255;
    var g = parseFloat(parts[1]) / 255;
    var b = parseFloat(parts[2]) / 255;
    var a = parts.length > 3 ? parseFloat(parts[3]) : 1;
    if (!isFinite(r) || !isFinite(g) || !isFinite(b)) return null;
    return { r: clamp01(r), g: clamp01(g), b: clamp01(b), a: isFinite(a) ? clamp01(a) : 1 };
  }

  function solidPaint(col) {
    if (!col || col.a <= 0) return null;
    var p = { type: "SOLID", color: { r: round(col.r), g: round(col.g), b: round(col.b) } };
    if (col.a < 1) p.opacity = round(col.a);
    return p;
  }

  // ---- image inlining ---------------------------------------------------

  var _imageBytesUsed = 0;

  function blobToDataUrl(blob) {
    return new Promise(function (resolve, reject) {
      var fr = new FileReader();
      fr.onload = function () { resolve(String(fr.result || "")); };
      fr.onerror = function () { reject(fr.error || new Error("read failed")); };
      fr.readAsDataURL(blob);
    });
  }

  function splitDataUrl(dataUrl) {
    var m = /^data:([^;,]+)[^,]*,(.*)$/i.exec(dataUrl || "");
    if (!m) return null;
    var mime = m[1] || "image/png";
    var b64 = m[2];
    // Approximate decoded size for the budget check.
    var bytes = Math.floor(b64.length * 3 / 4);
    return { b64: b64, mime: mime, bytes: bytes };
  }

  // Draw an already-decoded element (an <img> or a freshly loaded Image) to a
  // canvas, downscaling past MAX_IMAGE_EDGE, and return a data URL. Returns null
  // if the canvas is tainted (cross-origin without CORS) or drawing fails.
  function rasterizeImageEl(imgEl, naturalW, naturalH) {
    try {
      var w = naturalW || imgEl.naturalWidth || imgEl.width;
      var h = naturalH || imgEl.naturalHeight || imgEl.height;
      if (!w || !h) return null;
      var scale = Math.min(1, MAX_IMAGE_EDGE / Math.max(w, h));
      var cw = Math.max(1, Math.round(w * scale));
      var ch = Math.max(1, Math.round(h * scale));
      var canvas = document.createElement("canvas");
      canvas.width = cw; canvas.height = ch;
      var ctx = canvas.getContext("2d");
      ctx.drawImage(imgEl, 0, 0, cw, ch);
      // PNG when the image has transparency (logos/icons - JPEG would fill the
      // transparent areas BLACK), JPEG for fully-opaque photos to keep size down.
      var alpha = false;
      try {
        var d = ctx.getImageData(0, 0, cw, ch).data;
        for (var i = 3; i < d.length; i += 40) { if (d[i] < 250) { alpha = true; break; } }
      } catch (e) { alpha = true; }   // tainted canvas -> assume alpha (PNG is safe)
      return alpha ? canvas.toDataURL("image/png") : canvas.toDataURL("image/jpeg", 0.86);
    } catch (e) {
      return null;
    }
  }

  // Resolve a CSS url() or <img> src into { b64, mime } honoring the budget.
  function loadImage(url, hintEl) {
    return new Promise(function (resolve) {
      if (_imageBytesUsed >= IMAGE_BUDGET_BYTES) return resolve(null);
      // Fast path: an <img> already decoded in the page. Draw it directly.
      if (hintEl && hintEl.tagName === "IMG" && hintEl.complete && hintEl.naturalWidth) {
        var direct = rasterizeImageEl(hintEl);
        if (direct) {
          var dd = splitDataUrl(direct);
          if (dd) { _imageBytesUsed += dd.bytes; return resolve({ b64: dd.b64, mime: dd.mime }); }
        }
      }
      if (!url) return resolve(null);
      // A raster data URL: split + budget directly. SVG data URLs fall through
      // to the Image path below so they get RASTERIZED to PNG (Figma's
      // createImage cannot take svg+xml).
      if (/^data:/i.test(url) && !/^data:image\/svg/i.test(url)) {
        var sd = splitDataUrl(url);
        if (sd && (_imageBytesUsed + sd.bytes) <= IMAGE_BUDGET_BYTES) {
          _imageBytesUsed += sd.bytes;
          return resolve({ b64: sd.b64, mime: sd.mime });
        }
        return resolve(null);
      }
      // Network fetch (same-origin /source/ assets succeed; cross-origin may
      // fail CORS and falls back to a flat fill upstream).
      var done = false;
      var img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = function () {
        if (done) return; done = true;
        var data = rasterizeImageEl(img);
        if (!data) return resolve(null);
        var sd2 = splitDataUrl(data);
        if (!sd2 || (_imageBytesUsed + sd2.bytes) > IMAGE_BUDGET_BYTES) return resolve(null);
        _imageBytesUsed += sd2.bytes;
        resolve({ b64: sd2.b64, mime: sd2.mime });
      };
      img.onerror = function () {
        if (done) return; done = true;
        // Fetch fallback for hosts that allow it but block <img crossorigin>.
        fetch(url).then(function (r) { return r.blob(); }).then(blobToDataUrl).then(function (durl) {
          var sd3 = splitDataUrl(durl);
          if (!sd3 || (_imageBytesUsed + sd3.bytes) > IMAGE_BUDGET_BYTES) return resolve(null);
          _imageBytesUsed += sd3.bytes;
          resolve({ b64: sd3.b64, mime: sd3.mime });
        }).catch(function () { resolve(null); });
      };
      img.src = url;
    });
  }

  // Serialize an inline <svg> to a data URL so it can be rasterized to PNG.
  // Sets explicit width/height + resolves `currentColor` to the computed color
  // (icons commonly stroke/fill with currentColor set via CSS).
  function svgToDataUrl(el, cs, rect) {
    try {
      var clone = el.cloneNode(true);
      clone.setAttribute("width", Math.max(1, Math.round(rect.width)));
      clone.setAttribute("height", Math.max(1, Math.round(rect.height)));
      if (cs && cs.color) clone.setAttribute("color", cs.color);   // currentColor resolves to this
      if (!clone.getAttribute("xmlns")) clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
      var xml = new XMLSerializer().serializeToString(clone);
      return "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(xml)));
    } catch (e) {
      return null;
    }
  }

  // ---- style extraction -------------------------------------------------

  function cssUrl(value) {
    if (!value || value === "none") return null;
    var m = /url\(\s*(['"]?)([^'")]+)\1\s*\)/i.exec(value);
    return m ? m[2] : null;
  }

  // Best-effort single linear-gradient -> Figma GRADIENT_LINEAR paint.
  // Falls back to null (caller uses background-color) when it cannot parse.
  function parseLinearGradient(value) {
    var m = /linear-gradient\(([^]*)\)/i.exec(value || "");
    if (!m) return null;
    var inner = m[1];
    var stops = [];
    // Split on commas not inside rgb()/rgba().
    var depth = 0, buf = "", segs = [];
    for (var i = 0; i < inner.length; i++) {
      var ch = inner[i];
      if (ch === "(") depth++;
      else if (ch === ")") depth--;
      if (ch === "," && depth === 0) { segs.push(buf); buf = ""; } else buf += ch;
    }
    if (buf.trim()) segs.push(buf);
    var angle = 180; // default "to bottom"
    var first = (segs[0] || "").trim();
    if (/deg/.test(first)) { angle = px(first); segs.shift(); }
    else if (/^to\s+/i.test(first)) {
      var dir = first.toLowerCase();
      if (dir.indexOf("right") >= 0) angle = 90;
      else if (dir.indexOf("left") >= 0) angle = 270;
      else if (dir.indexOf("top") >= 0) angle = 0;
      else angle = 180;
      segs.shift();
    }
    segs.forEach(function (seg, idx) {
      seg = seg.trim();
      var posM = /\s+([\d.]+)%\s*$/.exec(seg);
      var pos = posM ? parseFloat(posM[1]) / 100 : (segs.length > 1 ? idx / (segs.length - 1) : 0);
      var col = parseColor(posM ? seg.slice(0, posM.index) : seg);
      if (col) stops.push({ position: clamp01(pos), color: col });
    });
    if (stops.length < 2) return null;
    return { type: "GRADIENT_LINEAR", angle: angle, stops: stops };
  }

  function readCorner(cs) {
    var tl = px(cs.borderTopLeftRadius);
    var tr = px(cs.borderTopRightRadius);
    var br = px(cs.borderBottomRightRadius);
    var bl = px(cs.borderBottomLeftRadius);
    if (!tl && !tr && !br && !bl) return 0;
    if (tl === tr && tr === br && br === bl) return round(tl);
    return { tl: round(tl), tr: round(tr), br: round(br), bl: round(bl) };
  }

  function readStroke(cs) {
    var widths = [px(cs.borderTopWidth), px(cs.borderRightWidth), px(cs.borderBottomWidth), px(cs.borderLeftWidth)];
    var maxW = Math.max.apply(null, widths);
    if (maxW <= 0) return null;
    if (cs.borderTopStyle === "none" && cs.borderRightStyle === "none" &&
        cs.borderBottomStyle === "none" && cs.borderLeftStyle === "none") return null;
    var col = parseColor(cs.borderTopColor) || parseColor(cs.borderLeftColor);
    var paint = solidPaint(col);
    if (!paint) return null;
    return { paint: paint, weight: round(maxW) };
  }

  // Best-effort parse of the first box-shadow layer -> Figma effect.
  function readShadow(cs) {
    var raw = cs.boxShadow;
    if (!raw || raw === "none") return null;
    var inset = /inset/i.test(raw);
    var s = raw.replace(/inset/ig, "");
    var colM = /(rgba?\([^)]+\))/i.exec(s);
    var col = colM ? parseColor(colM[1]) : null;
    if (colM) s = s.replace(colM[1], "");
    var nums = (s.match(/-?[\d.]+px/g) || []).map(px);
    if (nums.length < 2) return null;
    var eff = {
      type: inset ? "INNER_SHADOW" : "DROP_SHADOW",
      offsetX: round(nums[0]),
      offsetY: round(nums[1]),
      radius: round(nums[2] || 0),
      spread: round(nums[3] || 0),
      color: col || { r: 0, g: 0, b: 0, a: 0.25 }
    };
    return eff;
  }

  function directText(el) {
    var out = "";
    for (var i = 0; i < el.childNodes.length; i++) {
      var n = el.childNodes[i];
      if (n.nodeType === 3) out += n.nodeValue;
    }
    return out.replace(/\s+/g, " ").trim();
  }

  function fontStyleFromWeight(weight, italic) {
    var w = parseInt(weight, 10) || 400;
    var name = w >= 800 ? "ExtraBold" : w >= 700 ? "Bold" : w >= 600 ? "SemiBold"
      : w >= 500 ? "Medium" : w <= 300 ? "Light" : "Regular";
    if (italic) name = name === "Regular" ? "Italic" : name + " Italic";
    return name;
  }

  function applyTextTransform(text, transform) {
    if (transform === "uppercase") return text.toUpperCase();
    if (transform === "lowercase") return text.toLowerCase();
    return text;
  }

  function textAlign(cs) {
    var a = (cs.textAlign || "left").toLowerCase();
    if (a.indexOf("center") >= 0) return "CENTER";
    if (a.indexOf("right") >= 0) return "RIGHT";
    if (a.indexOf("justify") >= 0) return "JUSTIFIED";
    return "LEFT";
  }

  function textDecoration(cs) {
    var d = (cs.textDecorationLine || cs.textDecoration || "").toLowerCase();
    if (d.indexOf("underline") >= 0) return "UNDERLINE";
    if (d.indexOf("line-through") >= 0) return "STRIKETHROUGH";
    return "NONE";
  }

  function makeTextChild(el, cs, rect, parentRect) {
    var text = applyTextTransform(directText(el), (cs.textTransform || "").toLowerCase());
    if (!text) return null;
    var fontFamily = (cs.fontFamily || "Inter").split(",")[0].replace(/['"]/g, "").trim() || "Inter";
    var lh = cs.lineHeight;
    var lineHeight = (!lh || lh === "normal") ? "AUTO" : round(px(lh));
    var ls = px(cs.letterSpacing);
    return {
      type: "TEXT",
      name: text.slice(0, 40),
      x: round(rect.left - parentRect.left),
      y: round(rect.top - parentRect.top),
      width: round(rect.width),
      height: round(rect.height),
      characters: text,
      fontSize: round(px(cs.fontSize) || 16),
      fontFamily: fontFamily,
      fontStyle: fontStyleFromWeight(cs.fontWeight, /italic|oblique/i.test(cs.fontStyle)),
      letterSpacing: isFinite(ls) ? round(ls) : 0,
      lineHeight: lineHeight,
      textAlign: textAlign(cs),
      textColor: solidPaint(parseColor(cs.color)) || { type: "SOLID", color: { r: 0, g: 0, b: 0 } },
      textDecoration: textDecoration(cs)
    };
  }

  // ---- layout inference -------------------------------------------------
  // CSS flexbox maps precisely to Figma auto-layout. Plain block containers go
  // through a guarded heuristic: a clean, evenly-spaced, non-overlapping stack
  // becomes auto-layout; anything irregular stays absolute so we never invent
  // a layout that mangles the rendered design.

  function median(arr) {
    if (!arr.length) return 0;
    var s = arr.slice().sort(function (a, b) { return a - b; });
    var m = Math.floor(s.length / 2);
    return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
  }

  function mapJustify(jc) {
    jc = (jc || "").toLowerCase();
    if (jc.indexOf("space-between") >= 0 || jc.indexOf("space-around") >= 0 || jc.indexOf("space-evenly") >= 0) return "SPACE_BETWEEN";
    if (jc.indexOf("center") >= 0) return "CENTER";
    if (jc.indexOf("end") >= 0 || jc.indexOf("right") >= 0) return "MAX";
    return "MIN";
  }

  function mapAlign(ai) {
    ai = (ai || "").toLowerCase();
    if (ai.indexOf("center") >= 0) return "CENTER";
    if (ai.indexOf("baseline") >= 0) return "BASELINE";
    if (ai.indexOf("end") >= 0) return "MAX";
    return "MIN"; // flex-start / stretch / normal
  }

  function readPadding(cs) {
    return {
      top: round(px(cs.paddingTop)), right: round(px(cs.paddingRight)),
      bottom: round(px(cs.paddingBottom)), left: round(px(cs.paddingLeft))
    };
  }

  function readFlexLayout(cs) {
    var disp = (cs.display || "");
    if (disp !== "flex" && disp !== "inline-flex") return null;
    var dir = (cs.flexDirection || "row");
    var vertical = dir.indexOf("column") === 0;
    var gv = function (v) { return (!v || v === "normal") ? 0 : px(v); };
    var colGap = gv(cs.columnGap), rowGap = gv(cs.rowGap);
    return {
      mode: vertical ? "VERTICAL" : "HORIZONTAL",
      gap: round(vertical ? rowGap : colGap),
      crossGap: round(vertical ? colGap : rowGap),
      padding: readPadding(cs),
      primaryAlign: mapJustify(cs.justifyContent),
      counterAlign: mapAlign(cs.alignItems),
      wrap: (cs.flexWrap || "nowrap").indexOf("wrap") === 0
    };
  }

  function sortByOrder(children) {
    // CSS `order` re-sequences flex items; stable-sort by it (default 0).
    children.forEach(function (c, i) { c.__i = i; });
    children.sort(function (a, b) {
      var d = (a._order || 0) - (b._order || 0);
      return d !== 0 ? d : a.__i - b.__i;
    });
    children.forEach(function (c) { delete c.__i; });
  }

  // Infer counter-axis alignment for a stack from where its in-flow children
  // sit in the content box (catches centered headings, right-aligned rows).
  function inferCounterAlign(node, mode) {
    var pad = node.layout.padding;
    var horizontal = mode === "VERTICAL";   // counter axis is the other one
    var inner = horizontal ? (node.width - pad.left - pad.right) : (node.height - pad.top - pad.bottom);
    if (inner <= 0) return "MIN";
    var ctr = 0, max = 0, total = 0;
    (node.children || []).forEach(function (c) {
      if (c.absolute) return;
      total++;
      var start = horizontal ? (c.x - pad.left) : (c.y - pad.top);
      var sz = horizontal ? c.width : c.height;
      var endSpace = inner - start - sz;
      if (Math.abs(start - endSpace) <= 3) ctr++;
      else if (endSpace <= 3 && start > 3) max++;
    });
    if (!total) return "MIN";
    if (ctr / total >= 0.6) return "CENTER";
    if (max / total >= 0.6) return "MAX";
    return "MIN";
  }

  function inferStackLayout(cs, node) {
    var all = node.children || [];
    var flow = all.filter(function (c) { return !c.absolute; });
    var abs = all.filter(function (c) { return c.absolute; });
    if (flow.length < 2) return;

    function tryAxis(axis) {                 // "y" (vertical) | "x" (horizontal)
      var sizeKey = axis === "y" ? "height" : "width";
      var sorted = flow.slice().sort(function (a, b) { return a[axis] - b[axis]; });
      var gaps = [];
      for (var i = 1; i < sorted.length; i++) {
        var g = sorted[i][axis] - (sorted[i - 1][axis] + sorted[i - 1][sizeKey]);
        if (g < -3) return null;             // overlap -> not a clean stack
        gaps.push(g);
      }
      var med = median(gaps), maxDev = 0;
      gaps.forEach(function (g) { maxDev = Math.max(maxDev, Math.abs(g - med)); });
      if (maxDev > Math.max(12, med * 0.6)) return null;   // gaps too irregular
      return { sorted: sorted, gap: Math.max(0, med) };
    }

    var v = tryAxis("y");
    var h = v ? null : tryAxis("x");         // prefer vertical (block default)
    var pick = v || h;
    if (!pick) return;
    var mode = v ? "VERTICAL" : "HORIZONTAL";

    node.layout = {
      mode: mode, gap: round(pick.gap), crossGap: 0,
      padding: readPadding(cs), primaryAlign: "MIN", counterAlign: "MIN", wrap: false
    };
    node.children = pick.sorted.concat(abs);
    node.layout.counterAlign = inferCounterAlign(node, mode);
  }

  function baseAutoLayout(cs, inline) {
    return {
      mode: inline ? "HORIZONTAL" : "VERTICAL",
      gap: 0, crossGap: 0,
      padding: readPadding(cs),
      primaryAlign: "MIN",
      counterAlign: inline ? "CENTER" : "MIN",
      wrap: false
    };
  }

  // CSS grid -> a horizontal auto-layout that WRAPS (cards keep their measured
  // size and reflow into rows). Keeps the grid in real auto-layout instead of
  // pinning children to ignore-auto-layout.
  function gridLayout(cs) {
    var gv = function (v) { return (!v || v === "normal") ? 0 : px(v); };
    return {
      mode: "HORIZONTAL",
      gap: round(gv(cs.columnGap)), crossGap: round(gv(cs.rowGap)),
      padding: readPadding(cs),
      primaryAlign: "MIN", counterAlign: "MIN",
      wrap: true
    };
  }

  // EVERY frame gets an auto-layout (mandate: no plain absolute frames). Flex ->
  // exact; clean stack -> inferred; otherwise a base auto-layout. For a grid or a
  // messy multi-child frame whose children would reflow, the children are pinned
  // ABSOLUTE so the visual is preserved while the frame still carries a layout.
  // node.hug marks inline-level boxes (buttons/tags/chips/inline spans) that
  // should genuinely hug their content (real hug, not fixed-width-looks-hugged).
  function decideLayout(cs, node) {
    if (node.type !== "FRAME") return;
    var disp = cs.display || "";

    // HTML tables -> nested auto-layout that keeps columns aligned: the table /
    // row-group stacks rows (rows FILL width); a row lays cells horizontally
    // (cells keep their measured column width + FILL the row height). A <td>/<th>
    // (table-cell) falls through to the normal path so its padding + text apply.
    if (disp === "table" || disp === "inline-table" || disp === "table-row-group" ||
        disp === "table-header-group" || disp === "table-footer-group") {
      node.layout = { mode: "VERTICAL", gap: 0, crossGap: 0, padding: readPadding(cs),
        primaryAlign: "MIN", counterAlign: "MIN", wrap: false };
      node.hug = false; node._tableRows = true;
      return;
    }
    if (disp === "table-row") {
      node.layout = { mode: "HORIZONTAL", gap: 0, crossGap: 0, padding: readPadding(cs),
        primaryAlign: "MIN", counterAlign: "MIN", wrap: false };
      node.hug = false; node._tableCells = true;
      return;
    }

    var inline = disp.indexOf("inline") >= 0;
    node.hug = inline;

    var flex = readFlexLayout(cs);
    if (flex) {
      node.layout = flex;
      if (node.children) sortByOrder(node.children);
    } else if (node.children && node.children.length >= 2) {
      var isGrid = disp.indexOf("grid") >= 0;
      if (!isGrid) inferStackLayout(cs, node);   // sets layout if a clean stack
      if (!node.layout) {
        // No clean stack (or a CSS grid): everything STILL flows in auto-layout -
        // we never pin children to ignore-auto-layout. A grid becomes a
        // horizontal wrap (cards keep their size and wrap); anything else gets a
        // base stack.
        if (isGrid) {
          node.layout = gridLayout(cs);
          node._gridWrap = true;
          sortByOrder(node.children);
        } else {
          node.layout = baseAutoLayout(cs, inline);
        }
      }
    } else {
      node.layout = baseAutoLayout(cs, inline);   // 0-1 children
    }
  }

  // Per-child sizing inside an auto-layout (plugin -> Figma layoutSizing +
  // textAutoResize). Text hugs its height; a frame hugs when inline (real hug)
  // else fills the column width; images keep their measured box.
  function assignChildSizing(node) {
    if (!node.layout || !node.children) return;
    var vertical = node.layout.mode === "VERTICAL";
    var parentHug = !!node.hug;
    for (var i = 0; i < node.children.length; i++) {
      var c = node.children[i];
      if (c.absolute) continue;
      // Tables: rows FILL the table width; cells keep their measured column
      // width (so columns line up across rows) and FILL the row height.
      if (node._tableRows) { c.sizing = { h: "FILL", v: "HUG" }; continue; }
      if (node._tableCells) { c.sizing = { h: "FIXED", v: "FILL" }; continue; }
      // Grid cards keep their measured box so they wrap instead of each filling a row.
      if (node._gridWrap) { c.sizing = { h: "FIXED", v: "FIXED" }; continue; }
      if (c.type === "TEXT") {
        c.sizing = { h: (parentHug || !vertical) ? "HUG" : "FILL", v: "HUG" };
      } else if (c.type === "IMAGE") {
        c.sizing = { h: "FIXED", v: "FIXED" };
      } else {
        if (c.hug) c.sizing = { h: "HUG", v: "HUG" };
        else c.sizing = { h: (vertical && !parentHug) ? "FILL" : "HUG", v: "HUG" };
      }
    }
  }

  // ---- component identity (hybrid) --------------------------------------
  // A node can be tagged as a design-system component so the plugin swaps it
  // for a bound Figma library instance. Identity is hybrid: an explicit
  // data-component / data-variant / data-prop-* attribute wins; otherwise the
  // user's selector rules (selector -> component + variants) are matched.

  var _componentRules = [];   // [{ selector, component, variants }]
  var _componentNames = {};   // set of names seen this run -> scene.components

  function detectComponent(el) {
    if (!el || el.nodeType !== 1) return null;
    var name = (el.getAttribute && (el.getAttribute("data-component") || el.getAttribute("data-figma-component"))) || "";
    if (name) {
      var props = {};
      var v = el.getAttribute("data-variant");
      if (v) props.Variant = v;
      var attrs = el.attributes || [];
      for (var i = 0; i < attrs.length; i++) {
        var a = attrs[i];
        if (a.name.indexOf("data-prop-") === 0) props[a.name.slice(10)] = a.value;
      }
      return { name: name.trim(), props: props };
    }
    for (var r = 0; r < _componentRules.length; r++) {
      var rule = _componentRules[r];
      if (!rule || !rule.selector || !rule.component) continue;
      try {
        if (el.matches(rule.selector)) {
          return { name: String(rule.component).trim(), props: (rule.variants && typeof rule.variants === "object") ? rule.variants : {} };
        }
      } catch (e) { /* invalid selector - skip */ }
    }
    return null;
  }

  // ---- Woven design-system components (by class) ------------------------
  // The default-design-system uses BEM classes: a base (.btn/.tag/.card/...)
  // + variant modifiers (.btn--primary, .tag--light). We map the base class to
  // a component name and the modifier(s) to Variant/Size props, so DS-built
  // prototypes come into Figma tagged + ready to map onto the real Figma
  // library components (most are already auto-layout via their inline-flex CSS).

  var WOVEN_DS_BASE = {
    btn: "Button", "btn-split": "Button", "btn-group": "ButtonGroup", "check-btn": "Button",
    link: "Link", tag: "Tag", badge: "Badge", status: "Status",
    avatar: "Avatar", "avatar-stack": "AvatarStack",
    input: "Input", select: "Select", textarea: "Textarea",
    "input-icon": "Input", "input-affix": "Input",
    checkbox: "Checkbox", radio: "Radio", switch: "Switch", chip: "Chip",
    progress: "Progress", tooltip: "Tooltip",
    field: "Field", segmented: "Segmented", tabs: "Tabs", tab: "Tab",
    breadcrumbs: "Breadcrumbs", alert: "Alert", toast: "Toast", menu: "Menu",
    pagination: "Pagination",
    card: "Card", "section-card": "SectionCard", list: "List", feed: "Feed",
    timeline: "Timeline", table: "Table", modal: "Modal", slideout: "Slideout",
    "blank-slate": "EmptyState", separator: "Divider", "separator-v": "Divider",
    kpi: "KPI", kv: "KeyValue"
  };
  var WOVEN_SIZE_MODS = { l: 1, s: 1, m: 1, sm: 1, xs: 1, lg: 1 };

  function detectWovenComponent(el) {
    if (!el.classList || !el.classList.length) return null;
    var classes = [];
    for (var i = 0; i < el.classList.length; i++) classes.push(el.classList[i]);
    var base = null;
    for (var b = 0; b < classes.length; b++) {
      var c = classes[b];
      if (c.indexOf("--") >= 0) continue;       // skip modifier classes
      if (WOVEN_DS_BASE[c]) { base = c; break; }
    }
    if (!base) return null;
    var props = {};
    var prefix = base + "--";
    for (var m = 0; m < classes.length; m++) {
      var cm = classes[m];
      if (cm.indexOf(prefix) === 0) {
        var mod = cm.slice(prefix.length);
        if (!mod) continue;
        if (WOVEN_SIZE_MODS[mod]) props.Size = mod;
        else props.Variant = mod;               // last appearance modifier wins
      }
    }
    return { name: WOVEN_DS_BASE[base], props: props };
  }

  // ---- interactive components (button / input / select / ...) -----------
  // Identified by tag (Woven prototypes use inline-styled <button>/<input>,
  // not consistent classes). These should become real auto-layout Figma
  // components - padded, content-centered - not flat boxes. `field` marks the
  // ones whose text lives in value/placeholder, not a DOM child.

  function interactiveComponent(el, tag, cs) {
    var role = (el.getAttribute && el.getAttribute("role")) || "";
    if (tag === "BUTTON" || role === "button") return { name: "Button", field: false };
    if (tag === "TEXTAREA") return { name: "Input", field: true };
    if (tag === "SELECT") return { name: "Select", field: true };
    if (tag === "INPUT") {
      var t = (el.getAttribute("type") || "text").toLowerCase();
      if (t === "button" || t === "submit" || t === "reset") return { name: "Button", field: false };
      if (t === "checkbox" || t === "radio") return { name: "Checkbox", field: false };
      return { name: "Input", field: true };
    }
    if (tag === "A") {
      // A link styled like a button (padding + a fill or border) -> Button.
      var pad = px(cs.paddingTop) + px(cs.paddingBottom) + px(cs.paddingLeft) + px(cs.paddingRight);
      var bg = parseColor(cs.backgroundColor);
      var boxed = (bg && bg.a > 0) || !!readStroke(cs);
      if (pad >= 8 && boxed) return { name: "Button", field: false };
    }
    return null;
  }

  // Build a TEXT node for a form field from its value (or placeholder, muted).
  function synthFieldText(el, cs, rect) {
    var val = "", muted = false;
    try {
      if (el.tagName === "SELECT") {
        var opt = el.options && el.options[el.selectedIndex];
        val = (opt && opt.text) || "";
      } else {
        val = el.value || "";
        if (!val) { val = (el.getAttribute && el.getAttribute("placeholder")) || ""; muted = true; }
      }
    } catch (e) {}
    val = (val || "").replace(/\s+/g, " ").trim();
    if (!val) return null;
    var col = parseColor(cs.color) || { r: 0.4, g: 0.4, b: 0.4, a: 1 };
    if (muted) col = { r: 0.56, g: 0.56, b: 0.58, a: 1 };   // approximate placeholder gray
    var fontFamily = (cs.fontFamily || "Inter").split(",")[0].replace(/['"]/g, "").trim() || "Inter";
    var ls = px(cs.letterSpacing);
    return {
      type: "TEXT",
      name: val.slice(0, 40),
      x: 0, y: 0,
      width: round(Math.max(1, rect.width - px(cs.paddingLeft) - px(cs.paddingRight))),
      height: round((px(cs.fontSize) || 14) * 1.4),
      characters: val,
      fontSize: round(px(cs.fontSize) || 14),
      fontFamily: fontFamily,
      fontStyle: fontStyleFromWeight(cs.fontWeight, /italic|oblique/i.test(cs.fontStyle)),
      letterSpacing: isFinite(ls) ? round(ls) : 0,
      lineHeight: "AUTO",
      textAlign: textAlign(cs),
      textColor: solidPaint(col) || { type: "SOLID", color: { r: 0.4, g: 0.4, b: 0.4 } },
      textDecoration: "NONE"
    };
  }

  // ---- node walk --------------------------------------------------------

  var SKIP_TAGS = { SCRIPT: 1, STYLE: 1, NOSCRIPT: 1, TEMPLATE: 1, LINK: 1, META: 1, HEAD: 1, TITLE: 1, BR: 1 };

  function isRendered(el, cs, rect) {
    if (!cs) return false;
    if (cs.display === "none" || cs.visibility === "hidden" || cs.visibility === "collapse") return false;
    if (parseFloat(cs.opacity) === 0) return false;
    if (rect.width <= 0 || rect.height <= 0) return false;
    return true;
  }

  // Does this frame carry any visible decoration of its own? Decorationless,
  // childless, textless frames are pruned so the Figma layer tree stays clean.
  function hasOwnPaint(node) {
    return (node.fills && node.fills.length) || (node.strokes && node.strokes.length) ||
      (node.effects && node.effects.length) || node.type === "IMAGE";
  }

  function walk(el, parentRect, win, pending) {
    var tag = el.tagName;
    if (!tag || SKIP_TAGS[tag]) return null;
    var rect = el.getBoundingClientRect();
    var cs = win.getComputedStyle(el);
    if (!isRendered(el, cs, rect)) return null;

    var node = {
      type: "FRAME",
      name: (tag.toLowerCase() + (el.id ? "#" + el.id : el.className && typeof el.className === "string" ? "." + el.className.split(" ")[0] : "")).slice(0, 40),
      x: round(rect.left - parentRect.left),
      y: round(rect.top - parentRect.top),
      width: round(rect.width),
      height: round(rect.height),
      fills: [],
      strokes: [],
      effects: [],
      children: []
    };

    var op = parseFloat(cs.opacity);
    if (isFinite(op) && op < 1) node.opacity = round(op);
    if (cs.overflow === "hidden" || cs.overflowX === "hidden" || cs.overflowY === "hidden") node.clipsContent = true;
    // Layout hints for the parent's auto-layout decision.
    var ord = parseInt(cs.order, 10);
    if (ord) node._order = ord;
    // NB: CSS position:absolute/fixed children are NOT pinned out of flow - we
    // never use Figma's ignore-auto-layout. They participate in the parent's
    // auto-layout like every other child (mandate: no absolute positioning).

    // Background: gradient takes precedence over color; an image overlays as a
    // deferred IMAGE paint (resolved after the synchronous walk).
    var bgImage = cs.backgroundImage;
    var grad = bgImage && /linear-gradient/i.test(bgImage) ? parseLinearGradient(bgImage) : null;
    var bgCol = solidPaint(parseColor(cs.backgroundColor));
    if (bgCol) node.fills.push(bgCol);
    if (grad) node.fills.push(grad);
    var bgUrl = cssUrl(bgImage);
    if (bgUrl) {
      var ip = { type: "IMAGE", scaleMode: "FILL", image: null };
      node.fills.push(ip);
      pending.push({ url: bgUrl, el: null, paint: ip });
    }

    var stroke = readStroke(cs);
    if (stroke) { node.strokes.push(stroke.paint); node.strokeWeight = stroke.weight; }

    var corner = readCorner(cs);
    if (corner) node.cornerRadius = corner;

    var shadow = readShadow(cs);
    if (shadow) node.effects.push(shadow);

    // <img> becomes an IMAGE node with a deferred fill.
    if (tag === "IMG") {
      node.type = "IMAGE";
      node.image = null;
      pending.push({ url: el.currentSrc || el.src, el: el, node: node });
    }
    // Inline <svg> (icons): rasterize the whole element to a PNG image fill -
    // do NOT recurse into its <path>/<g> children (they have no own box).
    var isSvg = (tag === "svg" || tag === "SVG");
    if (isSvg) {
      node.type = "IMAGE";
      node.image = null;
      pending.push({ url: svgToDataUrl(el, cs, rect), el: null, node: node });
    }

    // Interactive design-system component? (button / input / select / ...)
    var ic = interactiveComponent(el, tag, cs);

    // Children: recurse element children, then attach a TEXT child for the
    // element's own direct text (most leaves have text and no element kids).
    var elementKids = [];
    if (!isSvg) for (var i = 0; i < el.children.length; i++) elementKids.push(el.children[i]);
    if (elementKids.length) {
      for (var k = 0; k < elementKids.length; k++) {
        var child = walk(elementKids[k], rect, win, pending);
        if (child) node.children.push(child);
      }
    }
    if (tag !== "IMG" && !isSvg) {
      var t = makeTextChild(el, cs, rect, rect);
      if (t) node.children.push(t);
    }
    // Form fields carry no DOM child text - synthesize one from value/placeholder.
    if (ic && ic.field && !node.children.length) {
      var ft = synthFieldText(el, cs, rect);
      if (ft) node.children.push(ft);
    }

    decideLayout(cs, node);

    // Identity priority: explicit data-component / user rule -> Woven DS class
    // -> tag-based interactive fallback (inline-styled buttons/inputs).
    var comp = detectComponent(el) || detectWovenComponent(el);
    if (comp && comp.name) {
      node.component = comp.name;
      if (comp.props && Object.keys(comp.props).length) node.componentProps = comp.props;
      _componentNames[comp.name] = true;
    } else if (ic && ic.name) {
      // Tag-based default: a bare <button>/<input> reads as Button/Input so it
      // maps to the DS component (and names the layer) even without a rule.
      node.component = ic.name;
      _componentNames[ic.name] = true;
    }

    // Buttons / fields: refine the (already-assigned) auto-layout to horizontal,
    // content-centered, and set hug - a button HUGS its label (real hug); a form
    // field FILLs its container width.
    if (ic) {
      if (!node.layout) node.layout = baseAutoLayout(cs, true);
      var cg = (cs.columnGap && cs.columnGap !== "normal") ? px(cs.columnGap) : 0;
      node.layout.mode = "HORIZONTAL";
      node.layout.gap = round(cg) || (ic.field ? 0 : 8);
      node.layout.padding = readPadding(cs);
      node.layout.counterAlign = "CENTER";
      node.layout.primaryAlign = ic.field ? "MIN" : "CENTER";
      node.hug = ic.field ? false : true;
    }

    // Size children inside the auto-layout (text hugs height / fills column;
    // inline frames hug; block frames fill the column).
    assignChildSizing(node);

    // Prune empty decorationless containers (never prune a tagged component).
    if (node.type === "FRAME" && !node.component && !hasOwnPaint(node) && !node.children.length && !node.clipsContent) return null;
    if (!node.fills.length) delete node.fills;
    if (!node.strokes.length) delete node.strokes;
    if (!node.effects.length) delete node.effects;
    if (!node.children.length) delete node.children;
    return node;
  }

  /*
   * domToScene(rootEl, opts) -> Promise<scene>
   *   rootEl: an element in a SAME-ORIGIN document (e.g. iframe.contentDocument
   *           .body). opts.name names the top frame in Figma.
   */
  function domToScene(rootEl, opts) {
    opts = opts || {};
    _imageBytesUsed = 0;
    _componentRules = Array.isArray(opts.componentRules) ? opts.componentRules : [];
    _componentNames = {};
    var win = (rootEl.ownerDocument && rootEl.ownerDocument.defaultView) || window;
    var rootRect = rootEl.getBoundingClientRect();
    var pending = [];

    var root = {
      type: "FRAME",
      name: opts.name || "Woven export",
      x: 0, y: 0,
      width: round(rootRect.width || rootEl.scrollWidth || 0),
      height: round(rootRect.height || rootEl.scrollHeight || 0),
      clipsContent: true,
      fills: [],
      children: []
    };
    var rootBg = solidPaint(parseColor(win.getComputedStyle(rootEl).backgroundColor));
    // Default page surface to white when the body has no explicit background.
    root.fills.push(rootBg || { type: "SOLID", color: { r: 1, g: 1, b: 1 } });

    var kids = [];
    for (var i = 0; i < rootEl.children.length; i++) kids.push(rootEl.children[i]);
    for (var j = 0; j < kids.length; j++) {
      var n = walk(kids[j], rootRect, win, pending);
      if (n) root.children.push(n);
    }
    decideLayout(win.getComputedStyle(rootEl), root);
    root.hug = false;                 // the page frame is fixed-size, never hug
    assignChildSizing(root);

    // Resolve all deferred image fills concurrently.
    return Promise.all(pending.map(function (job) {
      return loadImage(job.url, job.el).then(function (img) {
        if (img && job.paint) job.paint.image = img;
        else if (img && job.node) job.node.image = img;
        else if (job.paint) {
          // Image failed: drop the empty IMAGE paint so it does not render black.
          var fills = null;
          // job.paint lives inside some node.fills; mark for removal via flag.
          job.paint._drop = true;
        } else if (job.node) {
          // <img> we could not inline: convert to a neutral placeholder frame.
          job.node.type = "FRAME";
          delete job.node.image;
          job.node.fills = [{ type: "SOLID", color: { r: 0.9, g: 0.9, b: 0.9 } }];
        }
      });
    })).then(function () {
      stripDroppedFills(root);
      return {
        version: SCENE_VERSION,
        name: root.name,
        width: root.width,
        height: root.height,
        imageBytes: _imageBytesUsed,
        dsRef: opts.dsRef || null,
        components: Object.keys(_componentNames),
        root: root
      };
    });
  }

  function stripDroppedFills(node) {
    if (node._order != null) delete node._order;   // temp fields, not part of the scene
    if (node._tableRows) delete node._tableRows;
    if (node._tableCells) delete node._tableCells;
    if (node._gridWrap) delete node._gridWrap;
    if (node.fills) {
      node.fills = node.fills.filter(function (f) { return !f._drop; });
      if (!node.fills.length) delete node.fills;
    }
    if (node.children) node.children.forEach(stripDroppedFills);
  }

  window.WovenFigma = {
    version: SCENE_VERSION,
    domToScene: domToScene,
    parseColor: parseColor // exported for tests
  };
})();
