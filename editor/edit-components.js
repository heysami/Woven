/* Component definitions stay separate from each instance's overrides. */
(function (root) {
  "use strict";
  const E = root.WovenEdit;
  const REF = "data-woven-component";
  const KEY = "data-woven-part";
  function walk(el) { return [el, ...el.querySelectorAll("*")]; }
  function definition(id, name, html, extra = {}) {
    const t = document.createElement("template"); t.innerHTML = html;
    if (t.content.children.length !== 1) throw new Error("A component needs one root element. Wrap the selection in a frame first.");
    const el = E.cleanClone(t.content.firstElementChild);
    const used = new Set();
    walk(el).forEach((n, i) => {
      let key = n.getAttribute(KEY) || "part-" + i;
      while (used.has(key)) key += '-part';
      used.add(key); n.setAttribute(KEY, key);
      for (const a of [E.ID, REF, "data-woven-instance", "data-woven-overrides", "data-woven-definition", "data-th-ins", "data-th-rep", "data-th-clone-of"]) n.removeAttribute(a);
    });
    return { ...extra, id, name, html: el.outerHTML };
  }
  function instance(def, doc = document) {
    const t = doc.createElement("template"); t.innerHTML = def.html;
    const el = E.cleanClone(t.content.firstElementChild, true);
    el.setAttribute(REF, def.id);
    el.setAttribute("data-woven-instance", E.uid());
    el.setAttribute("data-woven-definition", JSON.stringify(def));
    el.setAttribute("data-woven-overrides", "{}");
    return el;
  }
  function owner(el) { return el?.closest?.("[" + REF + "]"); }
  function overrides(el) { try { return JSON.parse(el.getAttribute("data-woven-overrides") || "{}"); } catch { return {}; } }
  function capture(el, type, value, prop) {
    const host = owner(el); if (!host) return;
    const key = el.getAttribute(KEY); if (!key) return;
    const changes = overrides(host);
    changes[key] = { ...(changes[key] || {}) };
    if (type === "styles") changes[key].styles = { ...changes[key].styles, ...value };
    else changes[key][type] = value;
    if (type === 'text' && prop) changes[key].textProp = prop;
    host.setAttribute("data-woven-overrides", JSON.stringify(changes));
  }
  function refresh(el, def, reset = false) {
    const changes = reset ? {} : overrides(el);
    const next = instance(def, el.ownerDocument);
    next.setAttribute(E.ID, E.identify(el));
    next.setAttribute("data-woven-instance", el.getAttribute("data-woven-instance") || E.uid());
    for (const a of ["data-th-ins", "data-th-rep", "data-th-clone-of", "data-zoom-id"]) {
      if (el.hasAttribute(a)) next.setAttribute(a, el.getAttribute(a));
    }
    const oldParts = new Map(walk(el).map(n => [n.getAttribute(KEY), n]));
    const newParts = new Map(walk(next).map(n => [n.getAttribute(KEY), n]));
    const missing = Object.keys(changes).filter(k => !newParts.has(k));
    if (missing.length) throw new Error("This update removes overridden content. Keep the instance or detach it before updating.");
    for (const [key, node] of newParts) {
      const old = oldParts.get(key);
      if (old?.getAttribute(E.ID)) node.setAttribute(E.ID, old.getAttribute(E.ID));
      const change = changes[key]; if (!change) continue;
      if (change.text != null) {
        const prop = change.textProp;
        if (prop === 'value') { node.value = change.text; node.setAttribute('value', change.text); if (node.tagName === 'TEXTAREA') node.textContent = change.text; }
        else if (prop === 'placeholder' || prop === 'alt') node.setAttribute(prop, change.text);
        else if (prop === 'option') { const option = node.options?.[node.selectedIndex >= 0 ? node.selectedIndex : 0]; if (option) option.textContent = change.text; }
        else node.textContent = change.text;
      }
      for (const [prop, value] of Object.entries(change.styles || {})) {
        if (value == null) node.style.removeProperty(prop); else node.style.setProperty(prop, value);
      }
    }
    next.setAttribute("data-woven-overrides", JSON.stringify(changes));
    el.replaceWith(next);
    return next;
  }
  function detach(el) {
    walk(el).forEach(n => { for (const a of [REF, KEY, "data-woven-instance", "data-woven-overrides", "data-woven-definition"]) n.removeAttribute(a); });
    return el;
  }
  function catalog(data) {
    const ds = data?.meta?.dsRef;
    const result = [];
    for (const p of data?.primitives || []) {
      for (const variant of p.variants || []) {
        const markup = p.htmlByVariant?.[variant]; if (!markup) continue;
        try { result.push(definition((ds?.id || "prototype") + ":" + p.name + "." + variant,
          p.name + " / " + variant, markup, { dsId: ds?.id, dsVersion: ds?.version, family: p.name, variant, source: p.from?.[variant] })); } catch {}
      }
    }
    return result;
  }
  function dsIdFor(doc, fallback) {
    for (const link of doc.querySelectorAll('link[rel="stylesheet"]')) {
      const match = link.href.match(/\/design-systems\/([^/]+)\//);
      if (match) return decodeURIComponent(match[1]);
    }
    return typeof fallback === 'string' ? fallback : fallback?.id;
  }
  function catalogFromGallery(doc, dsId, mirror = {}) {
    const rows = catalog({ ...mirror, meta: { dsRef: { id: dsId, version: mirror.version } } });
    for (const row of rows) {
      try {
        const found = row.source?.selector && doc.querySelector(row.source.selector);
        if (found) Object.assign(row, definition(row.id, row.name, found.outerHTML, row));
      } catch {}
    }
    for (const section of doc.querySelectorAll('section[id]')) {
      const samples = [...section.querySelectorAll('.ds-sample')];
      samples.forEach((sample, i) => {
        const children = [...sample.children].filter(n => !n.matches('script,style,.ds-label,.ds-caption'));
        if (!children.length) return;
        const variant = sample.getAttribute('data-variant') || sample.id || String(i + 1);
        const id = dsId + ':' + section.id + '.' + variant;
        if (rows.some(r => r.id === id || r.html === children[0].outerHTML)) return;
        const markup = children.length === 1 ? children[0].outerHTML : '<div>' + children.map(n => n.outerHTML).join('') + '</div>';
        const title = section.querySelector('h2,h3')?.textContent.trim() || section.id;
        const label = sample.getAttribute('aria-label') || sample.querySelector('.ds-label,.ds-caption')?.textContent.trim() || variant;
        try { rows.push(definition(id, title + ' / ' + label, markup, { dsId, dsVersion: mirror.version, family: section.id, variant })); } catch {}
      });
    }
    return rows;
  }
  async function loadCatalog(dsId, apiUrl) {
    const mirror = root['EDITOR_DS_' + dsId] || {};
    const frame = document.createElement('iframe');
    frame.setAttribute('aria-hidden', 'true'); frame.tabIndex = -1;
    frame.style.cssText = 'position:fixed;left:-20000px;width:1440px;height:900px;visibility:hidden;pointer-events:none';
    frame.src = apiUrl('/design-systems/' + encodeURIComponent(dsId) + '/gallery.html');
    try {
      await new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error('The design-system gallery did not load.')), 8000);
        frame.onload = () => { clearTimeout(timer); resolve(); };
        frame.onerror = () => { clearTimeout(timer); reject(new Error('Cannot load the design-system gallery.')); };
        document.body.append(frame);
      });
      // Gallery React mounts and font layout can finish just after load.
      let result = [];
      for (let i = 0; i < 10; i++) {
        result = catalogFromGallery(frame.contentDocument, dsId, mirror);
        if (result.length) return result;
        await new Promise(resolve => setTimeout(resolve, 100));
      }
      return result;
    } finally { frame.remove(); }
  }
  // Standalone runtime embedded in saved pages. No editor or model dependency.
  function runtime(document) {
    const uid = () => 'w' + (globalThis.crypto?.randomUUID?.() || Date.now().toString(36) + Math.random().toString(36).slice(2));
    const library = document.querySelector('script[data-woven-library]');
    if (!library) return;
    let definitions; try { definitions = JSON.parse(library.textContent).definitions || []; } catch { return; }
    const byId = new Map(definitions.map(d => [d.id, d]));
    function apply() {
      for (const el of document.querySelectorAll('[data-woven-component]')) {
        const def = byId.get(el.getAttribute('data-woven-component'));
        if (!def || el.getAttribute('data-woven-definition') === JSON.stringify(def)) continue;
        let changes; try { changes = JSON.parse(el.getAttribute('data-woven-overrides') || '{}'); } catch { continue; }
        const t = document.createElement('template'); t.innerHTML = def.html;
        const next = t.content.firstElementChild; if (!next) continue;
        const nodes = [next, ...next.querySelectorAll('*')];
        const ids = new Map();
        for (const node of nodes) {
          if (node.id) { const id = uid(); ids.set(node.id, id); node.id = id; }
          node.setAttribute('data-woven-id', uid());
        }
        for (const node of nodes) {
          for (const attr of ['for', 'aria-labelledby', 'aria-describedby', 'aria-controls', 'aria-owns', 'headers', 'list', 'form']) {
            if (node.hasAttribute(attr)) node.setAttribute(attr, node.getAttribute(attr).split(/\s+/).map(id => ids.get(id) || id).join(' '));
          }
          for (const attr of ['href', 'xlink:href']) {
            const v = node.getAttribute(attr); if (v?.startsWith('#') && ids.has(v.slice(1))) node.setAttribute(attr, '#' + ids.get(v.slice(1)));
          }
          for (const attr of [...node.attributes]) if (attr.value.includes('url(#')) node.setAttribute(attr.name, attr.value.replace(/url\(#([^)]*)\)/g, (m, id) => 'url(#' + (ids.get(id) || id) + ')'));
        }
        const parts = new Map(nodes.map(n => [n.getAttribute('data-woven-part'), n]));
        if (Object.keys(changes).some(k => !parts.has(k))) { el.setAttribute('data-woven-component-conflict', 'Updated definition removes overridden content'); continue; }
        const old = new Map([el, ...el.querySelectorAll('*')].map(n => [n.getAttribute('data-woven-part'), n]));
        for (const [key, node] of parts) {
          const previous = old.get(key);
          if (previous?.hasAttribute('data-woven-id')) node.setAttribute('data-woven-id', previous.getAttribute('data-woven-id'));
          const change = changes[key]; if (!change) continue;
          if (change.text != null) {
            const prop = change.textProp;
            if (prop === 'value') { node.value = change.text; node.setAttribute('value', change.text); if (node.tagName === 'TEXTAREA') node.textContent = change.text; }
            else if (prop === 'placeholder' || prop === 'alt') node.setAttribute(prop, change.text);
            else if (prop === 'option') { const option = node.options?.[node.selectedIndex >= 0 ? node.selectedIndex : 0]; if (option) option.textContent = change.text; }
            else node.textContent = change.text;
          }
          for (const [prop, value] of Object.entries(change.styles || {})) {
            if (value == null) node.style.removeProperty(prop); else node.style.setProperty(prop, value);
          }
        }
        for (const a of ['data-woven-component', 'data-woven-id', 'data-woven-instance', 'data-woven-overrides', 'data-th-ins', 'data-th-rep', 'data-th-clone-of']) {
          if (el.hasAttribute(a)) next.setAttribute(a, el.getAttribute(a));
        }
        next.setAttribute('data-woven-definition', JSON.stringify(def)); el.replaceWith(next);
      }
    }
    let observer;
    const update = () => { apply(); observer?.takeRecords(); };
    observer = new MutationObserver(update);
    observer.observe(document.documentElement, { childList: true, subtree: true }); update();
  }
  root.WovenComponents = { REF, KEY, definition, instance, owner, overrides, capture, refresh, detach, catalog, catalogFromGallery, dsIdFor, loadCatalog, runtime };
})(window);
