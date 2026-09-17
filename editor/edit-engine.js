/* Shared, build-free editing primitives. The host supplies UI and project URLs. */
(function (root) {
  "use strict";
  const ID = "data-woven-id";
  const docs = new WeakMap();
  const sessions = new Map();
  let clipboard = null;
  const draftKey = key => 'woven.edit.v1:' + encodeURIComponent(key);
  function remember(state) {
    try {
      if (!state.dirty) { root.localStorage?.removeItem(draftKey(state.key)); return; }
      if (!state.source) return;
      const ops = state.history.slice(0, state.cursor + 1).map(e => e.op);
      root.localStorage?.setItem(draftKey(state.key), JSON.stringify({
        schemaVersion: 1, path: state.path, source: state.source, baseSource: state.baseSource,
        version: state.version, snapshot: state.snapshot, savedSnapshot: state.savedSnapshot,
        before: state.history[0]?.before || state.snapshot, ops,
      }));
      state.recoveryError = null;
    } catch { state.recoveryError = 'Browser draft storage is full. Save or download your edits before closing the app.'; }
  }
  const uid = () => "w" + (root.crypto?.randomUUID?.() || Date.now().toString(36) + Math.random().toString(36).slice(2));
  const selector = id => '[' + ID + '="' + String(id).replace(/["\\]/g, "\\$&") + '"]';
  function identify(el) {
    if (!el?.getAttribute) return null;
    if (!el.getAttribute(ID)) el.setAttribute(ID, uid());
    return el.getAttribute(ID);
  }
  function isTextInput(el) {
    return !!el && (el.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(el.tagName) || !!el.closest?.('[contenteditable="true"]'));
  }
  function serialize(doc) {
    const clone = doc.documentElement.cloneNode(true);
    clone.querySelectorAll('[data-th-pick-style], [data-zoom-injected], .th-inspect-overlay').forEach(n => n.remove());
    [clone, ...clone.querySelectorAll('*')].forEach(n => {
      n.classList?.remove('th-pick-hover', 'th-pick-selected', 'th-pick-mode');
      n.removeAttribute('contenteditable'); n.removeAttribute('spellcheck');
    });
    return '<!doctype html>\n' + clone.outerHTML;
  }
  function restore(doc, html) {
    const parsed = new doc.defaultView.DOMParser().parseFromString(html, 'text/html');
    const chrome = [...doc.querySelectorAll('[data-th-pick-style], [data-zoom-injected]')];
    const picking = doc.body?.classList.contains('th-pick-mode');
    for (const attr of Array.from(doc.documentElement.attributes)) doc.documentElement.removeAttribute(attr.name);
    for (const attr of Array.from(parsed.documentElement.attributes)) doc.documentElement.setAttribute(attr.name, attr.value);
    doc.head.replaceWith(doc.importNode(parsed.head, true));
    doc.body.replaceWith(doc.importNode(parsed.body, true));
    chrome.forEach(node => doc.head.append(node));
    if (picking) doc.body.classList.add('th-pick-mode');
  }
  function sourcePath(frame) {
    try {
      const marked = frame.contentDocument?.querySelector('meta[name="woven-authoring"]')?.content;
      if (marked) return marked;
      const path = new URL(frame.contentWindow.location.href).pathname.replace(/^\//, '');
      if (path.startsWith('source/')) return path.endsWith('/') ? path + 'index.html' : path;
      const fallback = new URL(frame.getAttribute('src'), root.location.href).pathname.replace(/^\//, '');
      return fallback.startsWith('source/') ? fallback : null;
    } catch { return null; }
  }
  function isolate(frame, path, apiUrl) {
    const doc = frame.contentDocument;
    if (!doc?.body || !path || doc.location.href === 'about:blank') return false;
    if (doc.querySelector('meta[name="woven-authoring"]')) { bind(doc, path, apiUrl); return false; }
    const state = bind(doc, path, apiUrl);
    if (!state.dirty) state.matchWarnings = doc.defaultView.__wovenEditConflicts || [];
    const parsed = new doc.defaultView.DOMParser().parseFromString(state.dirty ? state.snapshot : serialize(doc), 'text/html');
    parsed.querySelectorAll('script:not([type="application/json"]), meta[http-equiv="refresh"]').forEach(n => n.remove());
    parsed.querySelectorAll('*').forEach(n => {
      for (const a of Array.from(n.attributes)) if (/^on/i.test(a.name)) n.removeAttribute(a.name);
    });
    if (!parsed.querySelector('base')) {
      const base = parsed.createElement('base'); base.href = doc.baseURI; parsed.head.prepend(base);
    }
    const policy = parsed.createElement('meta'); policy.httpEquiv = 'Content-Security-Policy'; policy.content = "script-src 'none'";
    const marker = parsed.createElement('meta'); marker.name = 'woven-authoring'; marker.content = path;
    parsed.head.prepend(policy, marker);
    const freeze = parsed.createElement('style'); freeze.setAttribute('data-woven-authoring-style', '');
    freeze.textContent = '*{animation-play-state:paused!important;transition:none!important}'; parsed.head.append(freeze);
    const originalCanvases = [...doc.querySelectorAll('canvas')];
    [...parsed.querySelectorAll('canvas')].forEach((canvas, i) => {
      try { const img = parsed.createElement('img'); img.src = originalCanvases[i].toDataURL(); img.width = originalCanvases[i].width; img.height = originalCanvases[i].height; img.alt = 'Canvas preview'; canvas.replaceWith(img); } catch {}
    });
    frame.setAttribute('srcdoc', '<!doctype html>' + parsed.documentElement.outerHTML);
    return true;
  }
  function release(frame) {
    if (!frame.hasAttribute('srcdoc') || !frame.contentDocument?.querySelector('meta[name="woven-authoring"]')) return;
    const state = docs.get(frame.contentDocument);
    if (!state?.dirty) frame.removeAttribute('srcdoc');
  }
  function notify(state, doc) {
    remember(state);
    for (const ref of state.documents) {
      const other = ref.deref();
      if (!other) { state.documents.delete(ref); continue; }
      if (other !== doc && other.defaultView?.frameElement?.isConnected && other.querySelector('meta[name="woven-authoring"]')) restore(other, state.snapshot);
    }
    root.dispatchEvent?.(new CustomEvent('woven:edit-session', { detail: { state, doc } }));
  }
  function cleanClone(el, fresh = false) {
    const clone = el.cloneNode(true);
    const nodes = [clone, ...clone.querySelectorAll("*")];
    // HTML IDs must be unique after paste. Preserve authored declarations
    // targeting those IDs before remapping them, including var() bindings.
    if (el.isConnected) {
      const originals = [el, ...el.querySelectorAll('*')];
      const ids = originals.filter(n => n.id).map(n => '#' + CSS.escape(n.id));
      const inline = nodes.map(n => n.getAttribute('style') || '');
      const visit = rules => {
        for (const rule of rules || []) {
          if (rule.media && !el.ownerDocument.defaultView.matchMedia(rule.conditionText).matches) continue;
          if (rule.selectorText && ids.some(id => rule.selectorText.includes(id))) {
            originals.forEach((original, i) => {
              try {
                if (original.matches(rule.selectorText)) nodes[i].style.cssText += ';' + rule.style.cssText;
              } catch {}
            });
          }
          try { if (rule.cssRules) visit(rule.cssRules); } catch {}
        }
      };
      for (const sheet of el.ownerDocument.styleSheets) { try { visit(sheet.cssRules); } catch {} }
      nodes.forEach((n, i) => { if (inline[i]) n.style.cssText += ';' + inline[i]; });
    }
    const htmlIds = new Map();
    for (const n of nodes) {
      n.classList?.remove("th-pick-hover", "th-pick-selected", "th-pick-mode");
      for (const a of ["data-zoom-id", "contenteditable", "spellcheck"]) n.removeAttribute(a);
      if (n.tagName === 'IFRAME' && n.getAttribute('srcdoc')?.includes('woven-authoring')) n.removeAttribute('srcdoc');
      if (!fresh) continue;
      n.setAttribute(ID, uid());
      for (const a of ["data-th-ins", "data-th-rep", "data-th-clone-of", "data-th-rkey-el", "data-th-rkey-sib"]) n.removeAttribute(a);
      if (n.hasAttribute("data-woven-instance")) n.setAttribute("data-woven-instance", uid());
      if (n.id) { const next = uid(); htmlIds.set(n.id, next); n.id = next; }
    }
    for (const n of nodes) {
      for (const a of ["for", "aria-labelledby", "aria-describedby", "aria-controls", "aria-owns", "headers", "list", "form"]) {
        if (n.hasAttribute(a)) n.setAttribute(a, n.getAttribute(a).split(/\s+/).map(v => htmlIds.get(v) || v).join(" "));
      }
      for (const a of ["href", "xlink:href"]) {
        const v = n.getAttribute(a);
        if (v?.startsWith("#") && htmlIds.has(v.slice(1))) n.setAttribute(a, "#" + htmlIds.get(v.slice(1)));
      }
      for (const a of Array.from(n.attributes || [])) {
        if (a.value.includes("url(#")) n.setAttribute(a.name, a.value.replace(/url\(#([^)]*)\)/g, (m, id) => "url(#" + (htmlIds.get(id) || id) + ")"));
      }
    }
    return clone;
  }
  function copy(el, extras = {}) {
    const clone = cleanClone(el);
    const base = el.ownerDocument.baseURI;
    const portable = raw => {
      if (!raw || /^(?:[a-z]+:|\/\/|#)/i.test(raw)) return raw;
      try {
        const url = new URL(raw, base), source = new URL(base);
        if (url.origin !== source.origin) return url.href;
        const project = source.searchParams.get('project');
        if (project && !url.searchParams.has('project')) url.searchParams.set('project', project);
        return url.pathname + url.search + url.hash;
      } catch { return raw; }
    };
    for (const node of [clone, ...clone.querySelectorAll('*')]) {
      for (const name of ['src', 'href', 'poster', 'data']) {
        const value = node.getAttribute(name); if (value) node.setAttribute(name, portable(value));
      }
      const srcset = node.getAttribute('srcset');
      if (srcset && !srcset.includes('data:')) node.setAttribute('srcset', srcset.split(',').map(part => {
        const bits = part.trim().split(/\s+/); bits[0] = portable(bits[0]); return bits.join(' ');
      }).join(', '));
    }
    clipboard = Object.freeze({ sourcePath: docs.get(el.ownerDocument)?.path, tagName: el.tagName.toLowerCase(), ...extras, type: "html-element", outerHTML: clone.outerHTML });
    return clipboard;
  }
  function setClipboard(value) { clipboard = value ? Object.freeze({ ...value }) : null; return clipboard; }
  function paste(target, value = clipboard, position = "after", selectorFor) {
    if (!target?.parentElement || !value?.outerHTML) throw new Error("Select a destination before pasting.");
    const doc = target.ownerDocument;
    const template = doc.createElement("template");
    template.innerHTML = value.outerHTML;
    const interactive = template.content.querySelector('button,a,input,select,textarea');
    const block = template.content.querySelector('div,section,article,main,p,h1,h2,form');
    const invalidParent = n => !!n && ((interactive && n.closest('button,a')) || (block && n.closest('p')));
    if (position === 'inside' && invalidParent(target)) throw new Error('This insertion would nest incompatible HTML elements. Choose before or after.');
    if (position !== 'inside') while (target.parentElement && invalidParent(target.parentElement)) target = target.parentElement;
    const anchor = selectorFor ? selectorFor(target) : null;
    const fragment = doc.createDocumentFragment();
    const key = uid();
    const nodes = Array.from(template.content.children).map(n => cleanClone(n, true));
    if (!nodes.length) throw new Error("The clipboard has no editable elements.");
    for (const node of nodes) { node.setAttribute("data-th-ins", key); fragment.append(node); }
    const html = nodes.map(n => n.outerHTML).join("");
    if (position === "inside") target.append(fragment);
    else if (position === "before") target.before(fragment);
    else target.after(fragment);
    return { nodes, key, html, target, anchor };
  }
  const cssName = name => name.replace(/[A-Z]/g, c => "-" + c.toLowerCase());
  const CSS_KEYS = new Set(("width height minWidth minHeight maxWidth maxHeight display flexGrow flexShrink flexBasis flexDirection flexWrap gridTemplateColumns gridTemplateRows gap rowGap columnGap justifyContent alignItems justifySelf alignSelf background backgroundColor borderColor borderWidth borderStyle borderRadius padding paddingTop paddingRight paddingBottom paddingLeft margin marginLeft marginRight marginTop marginBottom color fontFamily fontSize fontWeight lineHeight letterSpacing textAlign boxShadow filter opacity overflow").split(" "));
  function applyStyles(el, patch) {
    const applied = {};
    for (const [name, raw] of Object.entries(patch)) {
      if (!CSS_KEYS.has(name) && !name.startsWith("--")) continue;
      const key = cssName(name);
      const value = raw == null ? "" : String(raw);
      if (value === "") el.style.removeProperty(key);
      else el.style.setProperty(key, value);
      applied[key] = value === "" ? null : value;
    }
    for (const axis of ["width", "height"]) {
      if (patch[axis + "Mode"]) el.setAttribute("data-woven-" + axis, patch[axis + "Mode"]);
      else if (axis in patch) el.removeAttribute("data-woven-" + axis);
    }
    return applied;
  }
  function sizing(axis, mode, fixed, parent = {}, self = {}) {
    parent = parent || {}; self = self || {};
    const width = axis === "w" || axis === "width";
    const k = width ? "width" : "height";
    const flex = /^(inline-)?flex$/.test(parent.display || "");
    const grid = /^(inline-)?grid$/.test(parent.display || "");
    const main = flex && (width !== (parent.flexDirection || "row").startsWith("column"));
    const out = { [k + "Mode"]: mode };
    if (self.display === "inline") out.display = "inline-block";
    if (main) Object.assign(out, { flexGrow: "0", flexShrink: "0", flexBasis: "auto" });
    if (mode === "fixed") {
      out[k] = Math.max(0, Number(fixed) || 0) + "px";
      out[k + "Fixed"] = Math.max(0, Number(fixed) || 0);
      if (flex && !main) out.alignSelf = "start";
      if (grid) out[width ? "justifySelf" : "alignSelf"] = "start";
    } else if (mode === "hug") {
      out[k] = "fit-content";
      if (flex && !main) out.alignSelf = "start";
      if (grid) out[width ? "justifySelf" : "alignSelf"] = "start";
    } else if (mode === "fill") {
      if (main) Object.assign(out, { [k]: "auto", flexGrow: "1", flexShrink: "1", flexBasis: "0px", [width ? "minWidth" : "minHeight"]: "0px" });
      else if (flex) Object.assign(out, { [k]: "auto", alignSelf: "stretch" });
      else if (grid) Object.assign(out, { [k]: "auto", [width ? "justifySelf" : "alignSelf"]: "stretch" });
      else out[k] = "100%";
    } else out[k] = null;
    return out;
  }
  function sizeMode(el, axis) {
    const explicit = el.getAttribute("data-woven-" + axis);
    if (explicit) return explicit;
    const v = el.style[axis];
    if (v === "fit-content" || v === "max-content") return "hug";
    if (v === "100%") return "fill";
    if (/px$/.test(v)) return "fixed";
    const p = el.parentElement && el.ownerDocument.defaultView.getComputedStyle(el.parentElement);
    if (p && /flex/.test(p.display)) {
      const main = (axis === "width") !== p.flexDirection.startsWith("column");
      if (main && Number(el.style.flexGrow) > 0 || !main && el.style.alignSelf === "stretch") return "fill";
    }
    if (p && /grid/.test(p.display) && el.style[axis === 'width' ? 'justifySelf' : 'alignSelf'] === 'stretch') return 'fill';
    return "auto";
  }
  function variables(doc) {
    const declared = new Map();
    const win = doc.defaultView;
    function visit(rules) {
      for (const rule of rules || []) {
        if (rule.media && !win.matchMedia(rule.conditionText).matches) continue;
        if (rule.selectorText && rule.style) {
          let matches = false;
          try { matches = doc.documentElement.matches(rule.selectorText) || doc.body.matches(rule.selectorText); } catch {}
          if (matches) for (const key of rule.style) if (key.startsWith("--")) declared.set(key, rule.style.getPropertyValue(key).trim());
        }
        try { if (rule.cssRules) visit(rule.cssRules); } catch {}
      }
    }
    for (const sheet of doc.styleSheets) { try { visit(sheet.cssRules); } catch {} }
    const computed = win.getComputedStyle(doc.documentElement);
    for (const key of computed) if (key.startsWith("--") && !declared.has(key)) declared.set(key, computed.getPropertyValue(key).trim());
    return Object.fromEntries([...declared].map(([key, raw]) => [key, { raw, value: computed.getPropertyValue(key).trim() || raw }]));
  }
  function modes(doc) {
    const result = new Map();
    const visit = rules => {
      for (const rule of rules || []) {
        for (const match of (rule.selectorText || '').matchAll(/\[(data-(?:theme|mode))\s*=\s*["']?([\w-]+)["']?\]/g)) {
          const key = match[1] + '=' + match[2]; result.set(key, { key, attribute: match[1], value: match[2], target: /body\s*\[/.test(rule.selectorText) ? 'body' : 'html' });
        }
        try { if (rule.cssRules) visit(rule.cssRules); } catch {}
      }
    };
    for (const sheet of doc.styleSheets) { try { visit(sheet.cssRules); } catch {} }
    return [...result.values()];
  }
  async function digest(text) {
    const bytes = await root.crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
    return [...new Uint8Array(bytes)].map(b => b.toString(16).padStart(2, "0")).join("").slice(0, 16);
  }
  function bind(doc, path, apiUrl) {
    let state = docs.get(doc);
    if (state && state.path === path) return state;
    const key = apiUrl('/' + path);
    if (sessions.has(key)) {
      state = sessions.get(key); docs.set(doc, state);
      const loaded = doc.querySelector('meta[name="woven-source-revision"]')?.content;
      const authoring = doc.querySelector('meta[name="woven-authoring"]');
      if (state.dirty || authoring || !loaded || !state.version || loaded === state.version) {
        state.documents.add(new WeakRef(doc));
        if (!state.dirty && !state.history.length && authoring) state.snapshot = serialize(doc);
        if (state.dirty && authoring) setTimeout(() => notify(state, doc), 0);
        return state;
      }
      // A clean session can adopt a newer source. Pending work keeps its old
      // revision so saving produces a conflict rather than losing either edit.
      sessions.delete(key);
    }
    state = { key, path, source: null, baseSource: null, version: null, pending: [], saving: false, revision: 0, history: [], cursor: -1,
      snapshot: serialize(doc), dirty: false, savedCursor: -1, documents: new Set([new WeakRef(doc)]) };
    try {
      const draft = JSON.parse(root.localStorage?.getItem(draftKey(key)) || 'null');
      if (draft?.schemaVersion === 1 && draft.path === path && Array.isArray(draft.ops) && typeof draft.source === 'string') {
        Object.assign(state, { source: draft.source, baseSource: draft.baseSource, version: draft.version,
          snapshot: draft.snapshot, savedSnapshot: draft.savedSnapshot, dirty: true, recovered: true,
          history: [{ before: draft.before, after: draft.snapshot, op: { type: 'batch', ops: draft.ops } }], cursor: 0 });
      }
    } catch {}
    docs.set(doc, state);
    sessions.set(key, state);
    const url = apiUrl("/__edit_source") + "&path=" + encodeURIComponent(path);
    state.retry = () => {
      state.error = null;
      state.baselineReady = false;
      state.ready = fetch(url.replace("/__edit_source&", "/__edit_source?"), { cache: "no-store" })
        .then(r => readResponse(r, "Read page for editing"))
        .then(data => {
          if (typeof data.html !== 'string' || typeof data.version !== 'string') throw new Error('The editing service returned an invalid page. Restart Woven and retry.');
          if (state.recovered) {
            if (data.version !== state.version) state.error = 'The source changed while these edits were closed. Download the recovered edits before reloading the latest source.';
            state.baselineReady = true;
            return state;
          }
          const loaded = doc.querySelector('meta[name="woven-source-revision"]')?.content;
          if (loaded && loaded !== data.version) throw new Error("This frame is older than the source file. Reload it before editing.");
          state.source = data.html; state.baseSource = data.html; state.version = data.version;
          state.baselineReady = true;
          remember(state); return state;
        });
      // Preserve rejection for Save and expose recovery without discarding edits.
      state.ready.then(() => notify(state, doc), error => { state.error = error.message; notify(state, doc); });
      return state.ready;
    };
    state.retry();
    return state;
  }
  function stage(doc, op) {
    const state = docs.get(doc);
    if (state && op) {
      const capture = item => {
        if (item.type === 'batch') return item.ops.forEach(capture);
        const target = item.id ? doc.querySelector(selector(item.id)) : null;
        if (target && root.WovenComponents) {
          if (item.type === 'text') root.WovenComponents.capture(target, 'text', item.text, item.prop);
          if (item.type === 'style') root.WovenComponents.capture(target, 'styles', item.styles);
        }
      };
      capture(op);
      const before = state.snapshot;
      state.pending.push(op); state.revision++;
      state.history = state.history.slice(0, state.cursor + 1);
      if (state.savedCursor > state.cursor) state.savedCursor = -2;
      state.history.push({ before, after: serialize(doc), op }); state.cursor++;
      state.snapshot = serialize(doc); state.dirty = true;
      notify(state, doc);
    }
  }
  function history(doc, direction) {
    const state = docs.get(doc); if (!state) return false;
    const entry = direction < 0 ? state.history[state.cursor] : state.history[state.cursor + 1];
    if (!entry) return false;
    restore(doc, direction < 0 ? entry.before : entry.after);
    state.cursor += direction; state.revision++;
    state.snapshot = serialize(doc);
    state.dirty = state.cursor !== state.savedCursor;
    state.pending = state.history.slice(0, state.cursor + 1).map(e => e.op);
    notify(state, doc); return true;
  }
  function discard(doc) {
    const state = docs.get(doc); if (!state) return;
    const snapshot = state.savedSnapshot || state.history[0]?.before || state.snapshot;
    restore(doc, snapshot); state.snapshot = snapshot; state.dirty = false;
    state.baseSource = state.source; state.pending = []; state.history = []; state.cursor = -1; state.savedCursor = -1;
    state.revision++; notify(state, doc);
  }
  async function save(doc, path, apiUrl, ops, inject, serialized, wholeSession = false) {
    const state = bind(doc, path, apiUrl);
    try { await state.ready; } catch (error) { state.error = error.message; notify(state, doc); throw error; }
    if (state.saving) throw new Error("A save is already in progress.");
    state.saving = true; state.error = null;
    const revision = state.revision;
    try {
      // Source remains source. Rendered application markup is never baked over
      // a React mount when a replayable edit is available.
      const commands = state.history.length ? state.history.slice(0, state.cursor + 1).map(e => e.op) : ops;
      const html = Array.isArray(commands) ? inject(state.history.length || wholeSession ? state.baseSource : state.source, commands) : serialized;
      const savedCursor = state.cursor;
      const savedSnapshot = serialize(doc);
      const response = await fetch(apiUrl("/__html_save"), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path, html, expectedVersion: state.version }),
      });
      const result = await readResponse(response, "Save changes");
      state.source = html; state.version = result.version;
      for (const ref of state.documents) {
        const marker = ref.deref()?.querySelector('meta[name="woven-source-revision"]');
        if (marker) marker.content = result.version;
      }
      state.savedCursor = savedCursor; state.savedSnapshot = savedSnapshot;
      if (state.revision === revision) { state.pending = []; state.dirty = false; }
      notify(state, doc);
      return { ...result, revision, newerEdits: state.revision !== revision };
    } catch (error) { state.error = error.message; notify(state, doc); throw error; }
    finally { state.saving = false; }
  }
  function download(doc) {
    const state = docs.get(doc); if (!state) return;
    const value = { schemaVersion: 1, path: state.path, expectedVersion: state.version,
      ops: state.history.slice(0, state.cursor + 1).map(e => e.op), source: state.baseSource, renderedSnapshot: state.snapshot };
    const url = URL.createObjectURL(new Blob([JSON.stringify(value, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a'); link.href = url; link.download = 'woven-pending-edits.json'; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function reload(doc) {
    const state = docs.get(doc), frame = doc.defaultView?.frameElement;
    if (!state || !frame) return;
    sessions.delete(state.key);
    const frames = [];
    for (const ref of state.documents) {
      const other = ref.deref(); if (!other) continue;
      docs.delete(other);
      const host = other.defaultView?.frameElement;
      if (host?.isConnected && host.contentDocument === other) frames.push(host);
    }
    state.documents.clear();
    try { root.localStorage.removeItem(draftKey(state.key)); } catch {}
    state.dirty = false; state.pending = []; state.history = []; state.cursor = -1;
    notify(state, doc);
    for (const host of frames) {
      host.removeAttribute('srcdoc');
      const url = new URL(host.getAttribute('src'), root.location.href); url.searchParams.set('_editReload', Date.now()); host.src = url.href;
    }
  }
  root.addEventListener?.('beforeunload', event => {
    if ([...sessions.values()].some(state => state.dirty)) { event.preventDefault(); event.returnValue = ''; }
  });
  async function readResponse(response, action = "Load editor data") {
    const text = await response.text();
    let data;
    try { data = JSON.parse(text); }
    catch {
      if (/^\s*</.test(text)) throw new Error("Editing services are unavailable. Restart Woven's daemon, then retry. Keep this editor open while restarting.");
      throw new Error(action + " failed: the server returned an unreadable response. Please retry.");
    }
    if (!response.ok || data?.error) throw new Error(data?.error || action + " failed (" + response.status + "). Please retry.");
    if (!data || typeof data !== "object" || Array.isArray(data)) throw new Error(action + " failed: the server returned an invalid response.");
    return data;
  }
  root.WovenEdit = { ID, uid, identify, selector, cleanClone, isTextInput, copy, setClipboard, readResponse,
    retry: doc => !docs.get(doc)?.baselineReady ? docs.get(doc)?.retry?.() : Promise.resolve(),
    getClipboard: () => clipboard, paste, applyStyles, sizing, sizeMode, variables, modes, bind, stage, save, digest,
    state: doc => docs.get(doc), serialize, restore, sourcePath, isolate, release, history, discard, download, reload };
  if (typeof module !== "undefined") module.exports = root.WovenEdit;
})(typeof window !== "undefined" ? window : globalThis);
