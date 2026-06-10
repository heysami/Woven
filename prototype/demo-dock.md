---
name: demo-dock
description: The Demo dock spec — boilerplate HTML + inline CSS + inline JS for the floating prototype-only switcher. Loaded only when the source has ≥2 view variants of the same screen reachable from one state hook (stage / persona / lifecycle / status switcher; time scrubber; feature flag). **Test:** would a real shipped product have this control? Yes → inline (Overview / Documents tabs); No → use the dock from this file.

→ Decision lives in PROTOTYPE.md §11 "Demo dock — prototype-only controls".
---

# §11 — Demo dock: prototype-only controls (Woven-specific)

Anything that lets a viewer switch view / persona / stage / time is **demo scaffolding**, not product UI. Inline placement reads as a real control even with a "Demo:" caption. **The rule:** every prototype-only switcher goes in a single floating **demo dock** in a fixed corner. Never inline.

**Triggers when** source has ≥2 view variants of the same screen reachable from one state hook (stage / persona / lifecycle / status switcher; time scrubber; feature flag).

**Test for what stays inline:** would a real shipped product have this control? Yes → inline (Overview / Documents tabs). No, only for demo variance → dock.

**Visual rules** — must not look like product UI:
- Dashed 1px border (don't reuse `.btn-primary` / `.card`).
- `🧪` badge + monospace label + "DEMO" chip in panel header.
- Container is `<div class="demo-dock" data-demo-only="true">` so iframe context AND `?demo=off` hide it via one rule.

**Closed:** compact badge `🧪 6 views ▾`. **Open:** screen preamble (1 paragraph: what varies) + one row per variant (label + 1-sentence "what changes") + current row marked. Row click dispatches a `demoview` CustomEvent the page listens for.

**Editor coupling.** Each row maps 1:1 to a `state` / `substep` frame; dock self-hides when iframed (`window.self !== window.top`) so it doesn't compete with the editor's nav.

### Boilerplate

```html
<div class="demo-dock" data-demo-only="true">
  <button type="button" class="demo-dock-toggle" aria-expanded="false">
    <span class="demo-dock-flask">🧪</span><span>3 views</span><span>▾</span>
  </button>
  <div class="demo-dock-panel" hidden>
    <header>
      <span class="demo-dock-chip">DEMO</span>
      <h4>Class lifecycle — 3 views</h4>
      <button type="button" class="demo-dock-x" aria-label="Close">×</button>
    </header>
    <p class="demo-dock-preamble">
      This screen is the TC's view of one in-house class. Capabilities change
      across the run lifecycle — pick a stage to see what the TC can / can't do.
    </p>
    <ul class="demo-dock-views">
      <li data-view="application">
        <strong>During application</strong>
        <span>No pax yet, cancel disabled.</span>
      </li>
      <li data-view="post-application" data-current="true">
        <strong>Post application</strong>
        <span>Runs confirmed, pax editable.</span>
      </li>
      <li data-view="pre-class">
        <strong>Pre-class (final week)</strong>
        <span>100% cancellation fee window.</span>
      </li>
    </ul>
  </div>
</div>

<style>
.demo-dock {
  position: fixed; bottom: 16px; left: 16px; z-index: 9999;
  font-family: var(--font-mono, ui-monospace, monospace);
  font-size: 11.5px; color: var(--text, #1a1a1a);
}
.demo-dock-toggle {
  appearance: none; cursor: pointer;
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 10px;
  background: var(--surface, #fff);
  border: 1px dashed var(--text-muted, #888);
  border-radius: 0;  /* off-axis from product-UI radii */
  letter-spacing: 0.01em;
}
.demo-dock-toggle:hover { border-color: var(--text, #1a1a1a); }
.demo-dock-panel {
  display: block;
  max-width: 360px;
  background: var(--surface, #fff);
  border: 1px dashed var(--text-muted, #888);
  padding: 14px 16px 12px;
  margin-bottom: 6px;
}
.demo-dock-panel[hidden] { display: none; }
.demo-dock-panel header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 8px;
}
.demo-dock-panel h4 {
  margin: 0; font: 600 12px var(--font-mono, monospace);
  flex: 1; letter-spacing: 0.02em;
}
.demo-dock-chip {
  background: var(--text, #1a1a1a); color: var(--bg, #fff);
  padding: 1px 6px; font-weight: 700; letter-spacing: 0.08em; font-size: 9.5px;
}
.demo-dock-x {
  appearance: none; background: none; border: 0; cursor: pointer;
  font-size: 16px; color: var(--text-faint, #888); line-height: 1;
}
.demo-dock-preamble {
  margin: 0 0 10px; line-height: 1.55; color: var(--text-muted, #555);
}
.demo-dock-views { list-style: none; margin: 0; padding: 0; }
.demo-dock-views li {
  padding: 8px 0; border-top: 1px dashed var(--border, #ddd);
  cursor: pointer;
}
.demo-dock-views li:first-child { border-top: 0; }
.demo-dock-views li strong { display: block; font-weight: 600; }
.demo-dock-views li span { display: block; color: var(--text-muted, #555); margin-top: 1px; }
.demo-dock-views li[data-current="true"] { color: var(--accent, #5566ee); }
.demo-dock-views li[data-current="true"] strong::after {
  content: " ← current"; font-weight: 400; font-size: 10px; color: var(--accent, #5566ee);
}
/* Iframed (editor) or ?demo=off → hide every dock instance */
[data-demo-only="true"].is-hidden { display: none !important; }
</style>

<script>
(function () {
  // Hide when iframed (editor PrototypeView has its own nav) or ?demo=off.
  var hide = window.self !== window.top
          || /[?&]demo=off\b/.test(window.location.search);
  if (hide) {
    document.querySelectorAll('[data-demo-only="true"]').forEach(function (el) {
      el.classList.add("is-hidden");
    });
    return;
  }
  // Toggle open/close on the badge button.
  document.querySelectorAll(".demo-dock").forEach(function (dock) {
    var btn = dock.querySelector(".demo-dock-toggle");
    var panel = dock.querySelector(".demo-dock-panel");
    var closeBtn = dock.querySelector(".demo-dock-x");
    if (!btn || !panel) return;
    var toggle = function (open) {
      var willOpen = open != null ? open : panel.hasAttribute("hidden");
      if (willOpen) { panel.removeAttribute("hidden"); btn.setAttribute("aria-expanded", "true"); }
      else          { panel.setAttribute("hidden", "");  btn.setAttribute("aria-expanded", "false"); }
    };
    btn.addEventListener("click", function () { toggle(); });
    if (closeBtn) closeBtn.addEventListener("click", function () { toggle(false); });
    // Wire the rows — each one expects a data-view value that maps to the
    // page's view-switching mechanism. The page is responsible for the
    // actual state change; the dock just dispatches a CustomEvent the page
    // can listen for. This keeps the dock decoupled from page state.
    dock.querySelectorAll(".demo-dock-views li").forEach(function (li) {
      li.addEventListener("click", function () {
        var view = li.getAttribute("data-view");
        dock.dispatchEvent(new CustomEvent("demoview", { detail: { view: view }, bubbles: true }));
        // Mark current
        dock.querySelectorAll(".demo-dock-views li").forEach(function (x) { x.removeAttribute("data-current"); });
        li.setAttribute("data-current", "true");
        toggle(false);
      });
    });
  });
})();
</script>
```

---

