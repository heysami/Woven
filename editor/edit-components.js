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
    const seen = new Set();
    const find = sheet => {
      if (!sheet || seen.has(sheet)) return;
      seen.add(sheet);
      const match = sheet.href?.match(/\/design-systems\/([^/]+)\//);
      if (match) return decodeURIComponent(match[1]);
      try { for (const rule of sheet.cssRules || []) { const id = find(rule.styleSheet); if (id) return id; } } catch {}
    };
    for (const sheet of doc.styleSheets) { const id = find(sheet); if (id) return id; }
    for (const link of doc.querySelectorAll('link[rel="stylesheet"]')) {
      const match = link.href.match(/\/design-systems\/([^/]+)\//); if (match) return decodeURIComponent(match[1]);
    }
    return typeof fallback === 'string' ? fallback : fallback?.id;
  }
  function catalogFromGallery(doc, dsId, mirror = {}) {
    const base = new URL('/design-systems/' + encodeURIComponent(dsId) + '/gallery.html', /^https?:/.test(root.location.href) ? root.location.href : 'http://woven.local');
    const portable = raw => {
      if (!raw || /^(data:|#)/.test(raw)) return raw;
      const url = new URL(raw, base); return url.origin === base.origin ? url.pathname + url.search + url.hash : url.href;
    };
    const stylesheets = [...doc.querySelectorAll('link[rel="stylesheet"]')].map(n => portable(n.getAttribute('href'))).filter(href => href?.startsWith('/design-systems/' + encodeURIComponent(dsId) + '/'));
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
    // The bundled DS uses .comp sections with a class vocabulary in its bar.
    // Extract only outermost component roots, never gallery frames/headings or
    // the cells of a real component table. Explicit .ds-sample stays supported.
    for (const section of doc.querySelectorAll('section.comp[id]')) {
      if (section.querySelector('.ds-sample')) continue;
      const title = section.querySelector('.comp__bar h2,.comp__bar h3')?.textContent.trim() || section.id;
      const vocabulary = section.querySelector('.comp__bar > code')?.textContent || '';
      const classes = [...new Set([...vocabulary.matchAll(/\.([a-zA-Z][\w-]*)(\*)?/g)].map(m => m[1]))];
      if (!classes.length) continue;
      const matches = n => classes.some(c => [...n.classList].some(k => c.endsWith('-') ? k.startsWith(c) : k === c));
      const candidates = [...section.querySelectorAll('[class]')].filter(n => !n.closest('.comp__bar') && matches(n));
      const roots = candidates.filter(n => !candidates.some(p => p !== n && p.contains(n)));
      const used = new Set();
      for (const node of roots) {
        if (/^(TR|TD|TH|OPTION|OPTGROUP)$/.test(node.tagName)) continue;
        const cell = node.closest('table.matrix td');
        const rowLabel = cell?.parentElement.querySelector('th')?.textContent.trim();
        const columnLabel = cell && cell.closest('table').querySelectorAll('thead th')[cell.cellIndex]?.textContent.trim();
        const group = node.closest('.vgroup')?.querySelector('h5')?.textContent.trim();
        const signature = [...node.classList].filter(c => !c.startsWith('th-')).sort().join(' ');
        const label = [group, rowLabel, columnLabel, node.getAttribute('data-variant') || signature].filter(Boolean).join(' / ');
        const slug = label.toLowerCase().replace(/[^a-z0-9_-]+/g, '-').replace(/^-|-$/g, '') || 'default';
        let variant = slug, i = 2;
        while (used.has(variant)) variant = slug + '-' + i++;
        used.add(variant);
        try { rows.push(definition(dsId + ':' + section.id + '.' + variant, title + ' / ' + label, node.outerHTML, { dsId, dsVersion: mirror.version, family: section.id, variant })); } catch {}
      }
    }
    for (const row of rows) {
      row.stylesheets = stylesheets;
      row.gallery = base.pathname;
      const t = doc.createElement('template'); t.innerHTML = row.html;
      t.content.querySelectorAll('script').forEach(n => n.remove());
      for (const n of t.content.querySelectorAll('*')) {
        for (const attr of [...n.attributes]) if (/^on/i.test(attr.name)) n.removeAttribute(attr.name);
        for (const attr of ['src', 'href', 'poster']) if (n.hasAttribute(attr)) n.setAttribute(attr, portable(n.getAttribute(attr)));
      }
      row.html = t.innerHTML;
    }
    return rows;
  }
  async function loadCatalog(dsId, apiUrl) {
    const mirror = { ...(root['EDITOR_DS_' + dsId] || {}) };
    try {
      const response = await fetch(apiUrl('/design-systems/' + encodeURIComponent(dsId) + '/meta.json'), { cache: 'no-store' });
      if (response.ok) { const meta = await response.json(); if (meta.version) mirror.version = meta.version; }
    } catch {}
    const frame = document.createElement('iframe');
    frame.setAttribute('aria-hidden', 'true'); frame.tabIndex = -1;
    frame.style.cssText = 'position:fixed;left:-20000px;width:1440px;height:900px;visibility:hidden;pointer-events:none';
    const url = new URL(apiUrl('/design-systems/' + encodeURIComponent(dsId) + '/gallery.html'), root.location.href);
    url.searchParams.set('woven-library-refresh', Date.now()); frame.src = url.href;
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
      throw new Error('No components were found in design system "' + dsId + '". Open its gallery to check the component samples.');
    } finally { frame.remove(); }
  }
  function ensureStyles(def, doc, apiUrl = href => href, apply = true) {
    const existing = dsIdFor(doc);
    if (def.dsId && existing && existing !== def.dsId) throw new Error('This page uses design system "' + existing + '". Insert a component from that system.');
    const ops = [];
    for (const path of def.stylesheets || []) {
      const href = apiUrl(path);
      const absolute = new URL(href, doc.baseURI).href;
      if ([...doc.querySelectorAll('link[rel="stylesheet"]')].some(n => n.href === absolute || new URL(n.href).pathname === new URL(absolute).pathname)) continue;
      if (apply) { const link = doc.createElement('link'); link.rel = 'stylesheet'; link.href = href; doc.head.append(link); }
      ops.push({ type: 'stylesheet', href });
    }
    return ops;
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
  root.WovenComponents = { REF, KEY, definition, instance, owner, overrides, capture, refresh, detach, catalog, catalogFromGallery, dsIdFor, loadCatalog, ensureStyles, runtime };
})(window);
