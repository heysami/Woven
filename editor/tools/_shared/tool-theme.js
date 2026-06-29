/* Woven app-node tool theme bridge.
 *
 * App-node tools render in same-origin iframes under /editor/tools/. The editor
 * sets data-theme on the TOP document's <html>, but that does not propagate into
 * an iframe's own document - so without this, tool chrome stays light while the
 * editor is dark. This file self-resolves the editor's scheme from the SHARED
 * (same-origin) localStorage - the exact key the editor boot script + app.js
 * loadEditorTheme use - and sets data-theme on this iframe's <html>, which
 * activates the :root[data-theme="dark"] block in _shared/woven-theme.css.
 *
 * Live updates need NO host involvement: localStorage `storage` events fire in
 * every OTHER same-origin document, so when the editor flips the theme this tool
 * is notified. "system" mode also follows the OS via matchMedia. A postMessage
 * fallback ({type:'th:theme'}) lets a host force a refresh if ever needed.
 *
 * Load this as the FIRST element in <head>, synchronously (no defer/async), so
 * the attribute is set before the tool's stylesheet paints - no light flash.
 *   <script src="/editor/tools/_shared/tool-theme.js"></script>
 * KEEP IN SYNC with the editor index.html boot script + app.js loadEditorTheme.
 */
(function () {
  function resolve() {
    var pref = "system";
    try {
      var s = JSON.parse(localStorage.getItem("th.editor.settings.v1") || "{}");
      if (s && (s.editorTheme === "light" || s.editorTheme === "dark" || s.editorTheme === "system")) pref = s.editorTheme;
    } catch (e) {}
    var dark = pref === "dark" || (pref === "system" && window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches);
    return dark ? "dark" : "light";
  }
  function apply() {
    try { document.documentElement.setAttribute("data-theme", resolve()); } catch (e) {}
  }
  apply();
  try {
    window.addEventListener("storage", function (e) {
      if (!e || e.key === null || e.key === "th.editor.settings.v1") apply();
    });
  } catch (e) {}
  try {
    var mq = window.matchMedia("(prefers-color-scheme: dark)");
    if (mq.addEventListener) mq.addEventListener("change", apply);
    else if (mq.addListener) mq.addListener(apply);
  } catch (e) {}
  try {
    window.addEventListener("message", function (e) {
      if (e && e.data && e.data.type === "th:theme") apply();
    });
  } catch (e) {}
  // Re-assert once the document is parsed, in case a tool's own inline boot
  // resets documentElement attributes after this synchronous run.
  try {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", apply, { once: true });
    }
  } catch (e) {}
})();
