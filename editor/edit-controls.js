/* Shared selection tools mounted by workflow and preview inspectors. */
function WovenSelectionTools({ element, onCommand, onStyle }) {
  const [query, setQuery] = useState("");
  const [position, setPosition] = useState("after");
  const [library, setLibrary] = useState({ definitions: [], version: null });
  const [error, setError] = useState("");
  const [property, setProperty] = useState("color");
  const [open, setOpen] = useState(false);
  const [revision, setRevision] = useState(0);
  const [busy, setBusy] = useState(false);
  const [dsDefinitions, setDsDefinitions] = useState([]);
  const [loadingDs, setLoadingDs] = useState(false);
  const [, setSessionTick] = useState(0);
  useEffect(() => {
    const listener = event => { if (WovenEdit.state(element?.ownerDocument) === event.detail.state) setSessionTick(n => n + 1); };
    window.addEventListener('woven:edit-session', listener);
    return () => window.removeEventListener('woven:edit-session', listener);
  }, [element]);
  const dsId = element && WovenComponents.dsIdFor(element.ownerDocument, typeof D !== 'undefined' ? D.meta?.dsRef : null);
  useEffect(() => {
    if (!dsId || !open) return;
    let live = true; setLoadingDs(true);
    WovenComponents.loadCatalog(dsId, apiUrl).then(rows => { if (live) setDsDefinitions(rows); })
      .catch(e => { if (live) setError(e.message); }).finally(() => { if (live) setLoadingDs(false); });
    return () => { live = false; };
  }, [dsId, open]);
  useEffect(() => {
    let live = true;
    fetch(apiUrl("/__edit_components"), { cache: "no-store" }).then(r => r.json()).then(value => {
      if (live) { if (value.error) setError(value.error); else setLibrary(value); }
    }).catch(e => { if (live) setError(e.message); });
    return () => { live = false; };
  }, [revision]);
  if (!element || !onCommand) return null;
  const C = WovenComponents;
  const session = WovenEdit.state(element.ownerDocument);
  const mirror = dsId && window['EDITOR_DS_' + dsId];
  const cached = C.catalog(mirror ? { ...mirror, meta: { dsRef: { id: dsId, version: mirror.version } } } : typeof D !== 'undefined' ? D : {});
  const definitions = [...new Map([...cached, ...dsDefinitions, ...library.definitions].map(d => [d.id, d])).values()];
  const host = C.owner(element);
  const current = host && (() => { try { return JSON.parse(host.getAttribute("data-woven-definition")); } catch { return null; } })();
  const latest = current && definitions.find(d => d.id === current.id);
  const tokens = WovenEdit.variables(element.ownerDocument);
  const modes = WovenEdit.modes(element.ownerDocument);
  const cssProperty = property.replace(/[A-Z]/g, c => "-" + c.toLowerCase());
  const matching = Object.entries(tokens).filter(([, token]) => element.ownerDocument.defaultView.CSS.supports(cssProperty, token.value));
  const currentValue = element.style[property] || "";
  const currentBinding = /^var\((--[^,)]+)/.exec(currentValue)?.[1] || "";
  const perform = async (action, value) => {
    setError("");
    try { await onCommand(action, value); setRevision(n => n + 1); }
    catch (e) { setError(e.message); }
  };
  const publish = async (update) => {
    setError(""); setBusy(true);
    try {
      const source = update ? host : element;
      const name = update ? current.name : await uiPrompt("Component name", "New component");
      if (!name?.trim()) return;
      const def = C.definition(update ? current.id : "local:" + WovenEdit.uid(), name.trim(), WovenEdit.cleanClone(source).outerHTML);
      const response = await fetch(apiUrl("/__edit_components"), {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ definition: def, expectedVersion: library.version }),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || "Could not publish component");
      setLibrary(result);
      await perform(update ? "publish-component" : "make-component", def);
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  };
  const createVariable = async () => {
    const name = await uiPrompt("Variable name (page scope)", "--space-custom");
    if (!name) return;
    if (!/^--[a-zA-Z][\w-]*$/.test(name)) { setError("Use a CSS variable name, for example --space-small."); return; }
    const value = await uiPrompt("Value or alias", "8px");
    if (value == null || !value.trim()) return;
    const raw = Object.fromEntries(Object.entries(tokens).map(([key, token]) => [key, token.raw]));
    raw[name] = value;
    const visited = new Set(); const stack = new Set();
    const check = key => {
      if (stack.has(key)) throw new Error("Variable aliases cannot contain a cycle.");
      if (visited.has(key)) return;
      stack.add(key);
      for (const m of (raw[key] || "").matchAll(/var\(\s*(--[\w-]+)/g)) check(m[1]);
      stack.delete(key); visited.add(key);
    };
    try { check(name); await perform("variable", { name, value }); }
    catch (e) { setError(e.message); }
  };
  const preview = def => {
    const doc = element.ownerDocument;
    const css = Array.from(doc.querySelectorAll('link[rel="stylesheet"],style')).filter(n => !n.hasAttribute('data-th-pick-style')).map(n => n.outerHTML).join('');
    return '<!doctype html><html><head><base href="' + doc.baseURI.replace(/"/g, '&quot;') + '">' + css + '<style>html,body{margin:0;padding:8px;min-width:0;background:transparent}body{display:flex;align-items:center;justify-content:center}body>*{max-width:100%;box-sizing:border-box}</style></head><body>' + def.html + '</body></html>';
  };
  return html`<div className="woven-edit-tools">
    ${session?.error && html`<div role="alert" className="woven-edit-error">${session.error}
      <button onClick=${() => WovenEdit.download(element.ownerDocument)}>Download pending edits</button>
      <button onClick=${async () => { if (await uiConfirm('Reload the latest source and discard these pending edits? Download them first if you want to keep a copy.')) WovenEdit.reload(element.ownerDocument); }}>Reload latest source</button>
    </div>`}
    ${session?.recoveryError && html`<div role="alert" className="woven-edit-error">${session.recoveryError}</div>`}
    ${session?.recovered && html`<small>Recovered pending edits from this browser.</small>`}
    ${session?.matchWarnings?.length > 0 && html`<small role="alert">${session.matchWarnings.length} saved change(s) could not match this page state. Ambiguous matches are left unchanged.</small>`}
    <div className="woven-edit-actions">
      <button type="button" onClick=${() => perform("copy")}>Copy</button>
      <button type="button" onClick=${() => perform("paste", { position })}>Paste</button>
      <button type="button" onClick=${() => perform("duplicate")}>Duplicate</button>
      <button type="button" onClick=${() => setOpen(v => !v)} aria-expanded=${open}>Add</button>
    </div>
    ${open && html`<div className="woven-edit-library">
      <label>Insert <select aria-label="Insert position" value=${position} onChange=${e => setPosition(e.target.value)}>
        <option value="before">Before selection</option><option value="after">After selection</option><option value="inside">Inside selection</option>
      </select></label>
      <div className="woven-edit-actions">
        <button onClick=${() => perform("insert", { html: "<p>Text</p>", position })}>Text</button>
        <button onClick=${() => perform("insert", { html: '<div style="display:flex;gap:8px;padding:16px;min-width:80px;min-height:48px"></div>', position })}>Frame</button>
      </div>
      <input aria-label="Search components" placeholder="Search components" value=${query} onChange=${e => setQuery(e.target.value)}/>
      ${loadingDs && html`<small>Loading design-system components...</small>`}
      <div className="woven-edit-component-list">
        ${definitions.filter(d => d.name.toLowerCase().includes(query.toLowerCase())).slice(0, 40).map(def => html`
          <button key=${def.id} title=${def.dsId ? "Design system: " + def.dsId : "Project component"}
            onClick=${() => perform("insert-component", { definition: def, position })}>
            <iframe className="woven-edit-component-preview" title=${def.name + " preview"} tabIndex="-1" sandbox="" srcDoc=${preview(def)}/>
            <span>${def.name}</span><small>${def.dsId || "Project"}</small>
          </button>`)}
        ${definitions.length === 0 && html`<small>No components are available yet. Create one from the selection.</small>`}
      </div>
    </div>`}
    <div className="woven-edit-component">
      <strong>${current ? current.name : "Reusable component"}</strong>
      ${current ? html`
        <small>Instance. Changes here override this copy.</small>
        ${host.hasAttribute('data-woven-component-conflict') && html`<small role="alert">${host.getAttribute('data-woven-component-conflict')}</small>`}
        ${[host, ...host.querySelectorAll('[data-woven-part]')].filter(n => !n.children.length && n.textContent.trim()).slice(0, 12).map(n => html`
          <label key=${WovenEdit.identify(n)}>Text (${n.tagName.toLowerCase()})
            <input aria-label=${"Component text " + n.getAttribute('data-woven-part')} defaultValue=${n.textContent}
              key=${n.textContent} onBlur=${e => { if (e.target.value !== n.textContent) perform('component-text', { id: WovenEdit.identify(n), text: e.target.value }); }}/>
          </label>`)}
        <div className="woven-edit-actions">
          <button onClick=${() => perform("refresh-component", latest || current)}>Update</button>
          <button onClick=${() => perform("reset-component", latest || current)}>Reset overrides</button>
          <button onClick=${() => perform("detach-component")}>Detach</button>
        </div>
        <label>Swap <select aria-label="Swap component" value=${current.id} onChange=${e => perform("refresh-component", definitions.find(d => d.id === e.target.value))}>
          ${!definitions.some(d => d.id === current.id) && html`<option value=${current.id}>${current.name}</option>`}
          ${definitions.map(def => html`<option key=${def.id} value=${def.id}>${def.name}</option>`)}
        </select></label>
        ${current.id.startsWith("local:") && html`<button disabled=${busy} onClick=${() => publish(true)}>Publish selection as main</button>`}
      ` : html`<button disabled=${busy} onClick=${() => publish(false)}>Create component from selection</button>
        ${element.querySelector('[data-woven-component]') && html`<small>Nested components are captured as part of the new definition.</small>`}`}
    </div>
    <div className="woven-edit-variables">
      <strong>Variable binding</strong>
      ${modes.length > 0 && html`<label>Page mode<select aria-label="Variable mode" value=${modes.find(m => element.ownerDocument.querySelector(m.target || 'html').getAttribute(m.attribute) === m.value)?.key || ''}
        onChange=${e => perform('mode', { mode: modes.find(m => m.key === e.target.value), attributes: [...new Set(modes.map(m => m.attribute))] })}>
        <option value="">Default</option>${modes.map(m => html`<option key=${m.key} value=${m.key}>${m.value}</option>`)}
      </select></label>`}
      <select aria-label="Variable property" value=${property} onChange=${e => setProperty(e.target.value)}>
        ${["color", "backgroundColor", "padding", "gap", "borderRadius", "width", "height", "fontSize", "lineHeight"].map(k => html`<option key=${k} value=${k}>${k.replace(/[A-Z]/g, c => " " + c.toLowerCase())}</option>`)}
      </select>
      <select aria-label="Bind variable" value=${currentBinding} onChange=${e => { onStyle({ [property]: e.target.value ? "var(" + e.target.value + ")" : null }); setRevision(n => n + 1); }}>
        <option value="">${currentValue ? "Local override" : "Inherited"}</option>
        ${matching.map(([name, token]) => html`<option key=${name} value=${name}>${name} = ${token.value}</option>`)}
      </select>
      <small>${currentBinding ? currentBinding + " = " + (tokens[currentBinding]?.value || "Unresolved") : currentValue || "Using the stylesheet value"}</small>
      <div className="woven-edit-actions">
        <button onClick=${() => { onStyle({ [property]: null }); setRevision(n => n + 1); }}>Reset</button>
        ${currentBinding && html`<button onClick=${() => { onStyle({ [property]: tokens[currentBinding]?.value || null }); setRevision(n => n + 1); }}>Unbind</button>`}
        <button onClick=${createVariable}>New variable</button>
      </div>
    </div>
    ${error && html`<div role="alert" className="woven-edit-error">${error}</div>`}
  </div>`;
}
