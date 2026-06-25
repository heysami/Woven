/* ───────────────────────────────────────────────────────────────────────────
   Woven asset-controls shim — the in-asset half of "auto-exposed controls".

   A generated asset (shader / motion / 3D / any HTML) opts in to the editor's
   floating right-hand control panel by REGISTERING the knobs it wants exposed:

     <script src="/editor/tools/_shared/asset-controls.js"></script>
     <script>
       window.__wovenControls.register({
         key: "speed", label: "Speed", type: "range",
         min: 0, max: 4, step: 0.01, default: 1, group: "Motion",
         apply: v => { SPEED = v; }            // the asset's own live setter
       });
       window.__wovenControls.register({
         key: "tint", label: "Tint", type: "color", default: "#7c5cff",
         apply: v => { uTint = hexToRgb(v); }
       });
     </script>

   The HOST (editor app.js) reads `window.__wovenControls.schema()` directly
   (asset iframes are same-origin in the editor) to build the panel, and calls
   `.set(key, value)` on every input. A postMessage bridge is also installed for
   the rare cross-origin / export-preview case.

   When an asset does NOT include this shim, the host falls back to scanning the
   document's `:root` custom properties for common knobs — so this file is only
   needed for assets that want PRECISE, labelled controls with bespoke setters.

   Pure, self-contained, no deps. Load it WITHOUT `defer` and BEFORE the asset's
   own register() calls so `window.__wovenControls` exists when they run. Every
   register/set is wrapped in try/catch so a broken `apply` never blanks the asset.
   ─────────────────────────────────────────────────────────────────────────── */
(function () {
  "use strict";
  if (window.__wovenControls && window.__wovenControls.__installed) return;

  // Insertion-ordered registry. Each entry keeps its `apply` fn (never sent to
  // the host) plus the last value we pushed through it.
  var order = [];               // [key, …] in registration order
  var defs = Object.create(null);   // key → def (incl. apply)
  var vals = Object.create(null);   // key → current value

  function inferType(def) {
    if (def.type) return def.type;
    if (Array.isArray(def.options) && def.options.length) return "select";
    if (typeof def.default === "boolean") return "toggle";
    if (typeof def.default === "string" && /^#[0-9a-f]{3,8}$/i.test(def.default)) return "color";
    if (typeof def.default === "number") return "range";
    return "text";
  }

  function register(def) {
    if (!def || typeof def.key !== "string" || !def.key) return;
    try {
      var key = def.key;
      var entry = {
        key: key,
        label: def.label || key,
        type: inferType(def),
        group: def.group || "Controls",
        min: def.min,
        max: def.max,
        step: def.step,
        options: def.options,
        default: def.default,
        hint: def.hint || "",
        apply: typeof def.apply === "function" ? def.apply : null,
      };
      if (!(key in defs)) order.push(key);
      defs[key] = entry;
      // Apply the default immediately so the asset's initial frame matches the
      // value the panel will show.
      var v = (def.default !== undefined ? def.default : null);
      vals[key] = v;
      if (entry.apply && v !== null) { try { entry.apply(v); } catch (e) {} }
      return entry;
    } catch (e) { return null; }
  }

  function set(key, value) {
    var entry = defs[key];
    if (!entry) return false;
    vals[key] = value;
    if (entry.apply) { try { entry.apply(value); } catch (e) { return false; } }
    return true;
  }

  function applyAll(values) {
    if (!values || typeof values !== "object") return;
    // Apply in registration order so dependent knobs settle deterministically.
    for (var i = 0; i < order.length; i++) {
      var k = order[i];
      if (k in values) set(k, values[k]);
    }
  }

  function getAll() {
    var out = {};
    for (var i = 0; i < order.length; i++) { var k = order[i]; out[k] = vals[k]; }
    return out;
  }

  // Serializable schema for the host (drops the apply fn). Carries the live
  // value so the panel hydrates to the asset's current state, not just defaults.
  function schema() {
    var out = [];
    for (var i = 0; i < order.length; i++) {
      var k = order[i], d = defs[k];
      out.push({
        key: d.key, label: d.label, type: d.type, group: d.group,
        min: d.min, max: d.max, step: d.step, options: d.options,
        default: d.default, hint: d.hint, value: vals[k],
      });
    }
    return out;
  }

  var api = {
    __installed: true,
    register: register,
    set: set,
    applyAll: applyAll,
    getAll: getAll,
    schema: schema,
  };
  window.__wovenControls = api;

  // ── postMessage bridge (robustness for non-same-origin hosts) ──────────────
  // The editor reads the registry directly (same-origin); this only matters for
  // export/share previews served from a different origin. Inert otherwise.
  function reply(source, msg) { try { source && source.postMessage(msg, "*"); } catch (e) {} }
  window.addEventListener("message", function (ev) {
    var d = ev && ev.data;
    if (!d || typeof d !== "object") return;
    if (d.type === "th-controls-query") {
      reply(ev.source, { type: "th-controls-schema", schema: schema(), values: getAll() });
    } else if (d.type === "th-controls-set") {
      set(d.key, d.value);
    } else if (d.type === "th-controls-apply") {
      applyAll(d.values);
    }
  });
})();
