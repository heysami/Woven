/* Shared selection tools mounted by workflow and preview inspectors. */
function WovenInspectorIcon({ name }) {
  const paths = {
    plus: 'M8 3v10M3 8h10', close: 'm4 4 8 8M12 4l-8 8',
    copy: 'M5 5h8v8H5zM3 10H2V2h8v1', cut: 'M6 12a2 2 0 1 1-4 0 2 2 0 0 1 4 0Zm8 0a2 2 0 1 1-4 0 2 2 0 0 1 4 0ZM5.4 10.6 12 2M10.6 10.6 4 2', paste: 'M5 3H3v11h10V3h-2M6 2h4v3H6zM5 8h6M5 11h4',
    duplicate: 'M6 6h8v8H6zM3 10H2V2h8v1M10 8v4M8 10h4',
    component: 'm8 1 3 3-3 3-3-3 3-3Zm-4 4 3 3-3 3-3-3 3-3Zm8 0 3 3-3 3-3-3 3-3Zm-4 4 3 3-3 3-3-3 3-3Z',
    variables: 'm8 2 6 6-6 6-6-6 6-6ZM5 8h6M8 5v6',
    frame: 'M5 1v14M11 1v14M1 5h14M1 11h14', text: 'M3 3h10M8 3v10M5 13h6',
    row: 'M2 8h12m-4-4 4 4-4 4', column: 'M8 2v12m-4-4 4 4 4-4',
    grid: 'M2 2h5v5H2zM9 2h5v5H9zM2 9h5v5H2zM9 9h5v5H9z',
    flow: 'M2 3h12M2 8h8M2 13h12', wrap: 'M2 4h9a3 3 0 0 1 0 6H5m3-3-3 3 3 3',
    left: 'M3 2v12M6 4h7v3H6zM6 10h4v3H6z', center: 'M8 1v14M3 4h10v3H3zM5 10h6v3H5z',
    right: 'M13 2v12M3 4h7v3H3zM6 10h4v3H6z',
    top: 'M2 3h12M4 6h3v7H4zM10 6h3v4h-3z', middle: 'M1 8h14M4 3h3v10H4zM10 5h3v6h-3z',
    bottom: 'M2 13h12M4 3h3v7H4zM10 6h3v4h-3z',
    up: 'M8 13V3m-4 4 4-4 4 4', down: 'M8 3v10m-4-4 4 4 4-4',
    radius: 'M3 13V8a5 5 0 0 1 5-5h5', opacity: 'M8 2a6 6 0 1 0 0 12V2Zm0 0a6 6 0 0 1 0 12',
    replace: 'M3 5.5h9M9.5 3l2.5 2.5L9.5 8M13 10.5H4M6.5 8 4 10.5 6.5 13',
    data: 'M3 4c0-1 2.2-1.8 5-1.8s5 .8 5 1.8-2.2 1.8-5 1.8S3 5 3 4Zm0 0v8c0 1 2.2 1.8 5 1.8s5-.8 5-1.8V4M3 8c0 1 2.2 1.8 5 1.8s5-.8 5-1.8',
  };
  return html`<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d=${paths[name] || paths.frame}/></svg>`;
}

function WovenIconButton({ icon, label, onClick, active, disabled }) {
  return html`<button type="button" className="woven-icon-button" aria-label=${label} title=${label} aria-pressed=${active} disabled=${disabled} onClick=${onClick}><${WovenInspectorIcon} name=${icon}/></button>`;
}

function WovenVariableButton({ element, property, label, onStyle }) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState('');
  const ref = React.useRef(null);
  useEffect(() => {
    if (!open) return;
    const close = e => { if (!ref.current?.contains(e.target)) setOpen(false); };
    document.addEventListener('pointerdown', close);
    return () => document.removeEventListener('pointerdown', close);
  }, [open]);
  useEffect(() => { setOpen(false); setQuery(''); }, [element]);
  const tokens = open ? WovenEdit.variables(element.ownerDocument) : {};
  const css = property.replace(/[A-Z]/g, c => '-' + c.toLowerCase());
  const value = element.style[property] || '';
  const binding = /^var\((--[^,)]+)/.exec(value)?.[1];
  const matches = Object.entries(tokens).filter(([name, token]) => name.toLowerCase().includes(query.toLowerCase()) && element.ownerDocument.defaultView.CSS.supports(css, token.value));
  return html`<div ref=${ref} className="woven-variable-control" onKeyDown=${e => { if (e.key === 'Escape') { setOpen(false); ref.current?.querySelector('button')?.focus(); } }}>
    <${WovenIconButton} icon="variables" label=${'Bind variable to ' + label} active=${!!binding} onClick=${() => setOpen(v => !v)}/>
    ${open && html`<div className="woven-variable-popover" role="dialog" aria-label=${label + ' variables'}>
      <strong>${label} variable</strong>
      <input autoFocus aria-label="Search variables" placeholder="Search variables..." value=${query} onChange=${e => setQuery(e.target.value)}/>
      <div className="woven-variable-options">
        ${matches.map(([name, token]) => html`<button key=${name} title=${token.raw + ' = ' + token.value} onClick=${() => { onStyle({ [property]: 'var(' + name + ')' }); setOpen(false); }}><span>${name}</span><small>${token.value}</small></button>`)}
        ${!matches.length && html`<small>No matching variables.</small>`}
      </div>
      ${binding && html`<button onClick=${() => { onStyle({ [property]: tokens[binding]?.value || null }); setOpen(false); }}>Detach variable</button>`}
      <button onClick=${() => { onStyle({ [property]: null }); setOpen(false); }}>Reset to stylesheet</button>
    </div>`}
  </div>`;
}

function WovenProperty({ label, property, element, onStyle, children }) {
  return html`<div className="woven-property"><div className="woven-property-label"><span>${label}</span>
    <${WovenVariableButton} element=${element} property=${property} label=${label} onStyle=${onStyle}/></div>${children}</div>`;
}

function WovenDimension({ axis, mode, size, disabledFill, onChange }) {
  const label = axis === 'w' ? 'Width' : 'Height';
  const rounded = Math.round(size * 100) / 100;
  const [draft, setDraft] = useState(String(rounded));
  useEffect(() => { setDraft(String(rounded)); }, [rounded, mode]);
  const commit = () => {
    const n = Number(draft);
    if (draft.trim() && Number.isFinite(n) && n >= 0) {
      if (n !== rounded) onChange('fixed', n);
    } else setDraft(String(rounded));
  };
  return html`<div className="woven-dimension">
    <label className="woven-dimension-value"><span>${axis.toUpperCase()}</span><input aria-label=${label} inputMode="decimal" value=${draft} onChange=${e => setDraft(e.target.value)} onBlur=${commit} onKeyDown=${e => { if (e.key === 'Enter') e.target.blur(); }}/><span className="woven-unit">px</span></label>
    <select aria-label=${label + ' resizing'} value=${mode} title="From stylesheet: use the page's sizing rule. Fixed: use pixels. Hug: fit content. Fill: use available parent space." onChange=${e => onChange(e.target.value, size)}>
      <option value="auto">From stylesheet</option><option value="fixed">Fixed</option><option value="hug">Hug contents</option><option value="fill" disabled=${disabledFill}>Fill container</option>
    </select>
  </div>`;
}

function WovenSelectionTools({ element, picked, onCommand, onStyle }) {
  const [query, setQuery] = useState("");
  const [position, setPosition] = useState("after");
  const [library, setLibrary] = useState({ definitions: [], version: null });
  const [error, setError] = useState("");
  const [property, setProperty] = useState("color");
  const [open, setOpen] = useState(false);
  const [variablesOpen, setVariablesOpen] = useState(false);
  const [libraryError, setLibraryError] = useState("");
  const [libraryAttempt, setLibraryAttempt] = useState(0);
  const [revision, setRevision] = useState(0);
  const [busy, setBusy] = useState(false);
  const [dsDefinitions, setDsDefinitions] = useState([]);
  const [loadingDs, setLoadingDs] = useState(false);
  const [dsError, setDsError] = useState('');
  const [dsAttempt, setDsAttempt] = useState(0);
  const [libraryScope, setLibraryScope] = useState('all');
  const [, setSessionTick] = useState(0);
  useEffect(() => {
    const listener = event => { if (WovenEdit.state(element?.ownerDocument) === event.detail.state) setSessionTick(n => n + 1); };
    window.addEventListener('woven:edit-session', listener);
    return () => window.removeEventListener('woven:edit-session', listener);
  }, [element]);
  const dsId = element && WovenComponents.dsIdFor(element.ownerDocument, typeof D !== 'undefined' ? D.meta?.dsRef : null);
  const instanceId = element && WovenComponents.owner(element)?.getAttribute(WovenComponents.REF);
  useEffect(() => {
    setDsDefinitions([]); setDsError('');
    if (!dsId || (!open && (!instanceId || instanceId.startsWith('local:')))) { setLoadingDs(false); return; }
    let live = true; setLoadingDs(true);
    WovenComponents.loadCatalog(dsId, apiUrl).then(rows => { if (live) { setDsDefinitions(rows); setDsError(''); } })
      .catch(e => { if (live) setDsError(e.message); }).finally(() => { if (live) setLoadingDs(false); });
    return () => { live = false; };
  }, [dsId, open, instanceId, dsAttempt]);
  useEffect(() => {
    if (!open && !instanceId) return;
    let live = true;
    fetch(apiUrl("/__edit_components"), { cache: "no-store" }).then(r => WovenEdit.readResponse(r, "Load components")).then(value => {
      if (!Array.isArray(value.definitions)) throw new Error("The component library could not be loaded. Please retry.");
      if (live) { setLibrary(value); setLibraryError(""); }
    }).catch(e => { if (live) setLibraryError(e.message); });
    return () => { live = false; };
  }, [open, instanceId, libraryAttempt]);
  if (!element || !onCommand) return null;
  const C = WovenComponents;
  const session = WovenEdit.state(element.ownerDocument);
  const mirror = dsId && window['EDITOR_DS_' + dsId];
  const cached = C.catalog(mirror ? { ...mirror, meta: { dsRef: { id: dsId, version: mirror.version } } } : typeof D !== 'undefined' ? D : {});
  const definitions = [...new Map([...cached, ...dsDefinitions, ...library.definitions].map(d => [d.id, d])).values()];
  const host = C.owner(element);
  const current = host && (() => { try { return JSON.parse(host.getAttribute("data-woven-definition")); } catch { return null; } })();
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
      const result = await WovenEdit.readResponse(response, "Publish component");
      setLibrary(result);
      await perform(update ? "publish-component" : "make-component", def);
    } catch (e) { setError(e.message); }
    finally { setBusy(false); }
  };
  const updateInstance = async (reset = false) => {
    setBusy(true); setError('');
    try {
      let fresh;
      if (current.dsId) {
        const rows = await C.loadCatalog(current.dsId, apiUrl); setDsDefinitions(rows);
        fresh = rows.find(d => d.id === current.id);
      } else {
        const value = await fetch(apiUrl('/__edit_components'), { cache: 'no-store' }).then(r => WovenEdit.readResponse(r, 'Load components'));
        setLibrary(value); fresh = value.definitions?.find(d => d.id === current.id);
      }
      if (!fresh) throw new Error('This component is missing from its source library. Keep the current instance, swap it, or detach it.');
      await perform(reset ? 'reset-component' : 'refresh-component', fresh);
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
    const css = def.dsId && def.stylesheets?.length
      ? def.stylesheets.map(href => '<link rel="stylesheet" href="' + apiUrl(href).replace(/"/g, '&quot;') + '">').join('')
      : Array.from(doc.querySelectorAll('link[rel="stylesheet"],style')).filter(n => !n.hasAttribute('data-th-pick-style')).map(n => n.outerHTML).join('');
    return '<!doctype html><html><head><base href="' + doc.baseURI.replace(/"/g, '&quot;') + '">' + css + '<style>html,body{margin:0;padding:8px;min-width:0;background:transparent}body{display:flex;align-items:center;justify-content:center}body>*{max-width:100%;box-sizing:border-box}</style></head><body>' + def.html + '</body></html>';
  };
  const selectionName = element.getAttribute('data-name') || element.getAttribute('aria-label') ||
    element.id || Array.from(element.classList).find(c => !c.startsWith('th-pick-')) || ({ DIV: "Frame", P: "Text", SPAN: "Text", A: "Link", BUTTON: "Button", IMG: "Image" }[element.tagName] || element.tagName.toLowerCase());
  return html`<div className="woven-edit-tools">
    <div className="woven-inspector-header"><strong>Design</strong>
      <span className="woven-inspector-status">${session?.saving ? "Saving..." : session?.dirty ? "Unsaved" : ""}</span>
      <${WovenIconButton} icon="variables" label="Variables" active=${variablesOpen} onClick=${() => setVariablesOpen(v => !v)}/>
      <button className="woven-insert-trigger" type="button" onClick=${() => setOpen(v => !v)} aria-expanded=${open}><${WovenInspectorIcon} name="plus"/>Add</button>
    </div>
    <div className="woven-selection-heading"><${WovenInspectorIcon} name=${current ? "component" : "frame"}/>
      <strong title=${picked?.label || selectionName}>${selectionName}</strong>
      <${WovenIconButton} icon="component" label="Create project component from selection" disabled=${busy} onClick=${() => publish(false)}/>
    </div>
    <div className="woven-selection-actions">
      <${WovenIconButton} icon="copy" label="Copy" onClick=${() => perform("copy")}/>
      <${WovenIconButton} icon="cut" label="Cut" onClick=${() => perform("cut")}/>
      <${WovenIconButton} icon="paste" label="Paste" onClick=${() => perform("paste", { position })}/>
      <${WovenIconButton} icon="duplicate" label="Duplicate" onClick=${() => perform("duplicate")}/>
      <span className="woven-selection-kind">${current ? "Component instance" : element.tagName.toLowerCase()}</span>
    </div>
    ${session?.error && html`<div role="alert" className="woven-edit-error">${session.error}
      <div className="woven-edit-actions">
        ${!session.baselineReady && html`<button onClick=${() => WovenEdit.retry(element.ownerDocument).catch(() => {})}>Retry editing services</button>`}
        <button onClick=${() => WovenEdit.download(element.ownerDocument)}>Download edits</button>
        <button onClick=${async () => { if (await uiConfirm('Reload the latest source and discard these pending edits? Download them first if you want to keep a copy.')) WovenEdit.reload(element.ownerDocument); }}>Reload source</button>
      </div>
    </div>`}
    ${session?.recoveryError && html`<div role="alert" className="woven-edit-error">${session.recoveryError}</div>`}
    ${session?.recovered && html`<small className="woven-edit-note">Recovered pending edits.</small>`}
    ${session?.matchWarnings?.length > 0 && html`<small className="woven-edit-note" role="alert">${session.matchWarnings.length} saved change(s) could not match this page state.</small>`}
    ${open && html`<div className="woven-edit-library woven-edit-drawer">
      <div className="woven-section-heading"><strong>Insert</strong><${WovenIconButton} icon="close" label="Close insert" onClick=${() => setOpen(false)}/></div>
      <label className="woven-labeled-row">Placement <select aria-label="Insert position" value=${position} onChange=${e => setPosition(e.target.value)}>
        <option value="before">Before selection</option><option value="after">After selection</option><option value="inside">Inside selection</option>
      </select></label>
      <div className="woven-edit-actions">
        <button onClick=${() => perform("insert", { html: "<p>Text</p>", position })}><${WovenInspectorIcon} name="text"/>Text</button>
        <button onClick=${() => perform("insert", { html: '<div style="display:flex;gap:8px;padding:16px;min-width:80px;min-height:48px"></div>', position })}><${WovenInspectorIcon} name="frame"/>Frame</button>
      </div>
      <input aria-label="Search components" placeholder="Search components..." value=${query} onChange=${e => setQuery(e.target.value)}/>
      <label className="woven-labeled-row">Library<select aria-label="Component library" value=${libraryScope} onChange=${e => setLibraryScope(e.target.value)}>
        <option value="all">All components</option><option value="ds">Design system${dsId ? ': ' + dsId : ''}</option><option value="project">Project components</option>
      </select></label>
      ${dsId ? html`<small className="woven-edit-note">Connected to <a href=${apiUrl('/design-systems/' + encodeURIComponent(dsId) + '/gallery.html')} target="_blank" rel="noopener">${dsId}</a>. Inserted DS components keep their library link.</small>` : html`<small className="woven-edit-note">No design system is bound to this page. Bind one in the project to browse its components.</small>`}
      <small className="woven-edit-note">Create component saves to this project. Shared components are managed in the design-system library.</small>
      ${loadingDs && html`<small>Loading design-system components...</small>`}
      <div className="woven-edit-component-list">
        ${definitions.filter(d => (libraryScope === 'all' || (libraryScope === 'ds' ? !!d.dsId : !d.dsId)) && d.name.toLowerCase().includes(query.toLowerCase())).slice(0, 40).map(def => html`
          <button key=${def.id} title=${def.dsId ? "Design system: " + def.dsId : "Project component"}
            onClick=${() => perform("insert-component", { definition: def, position })}>
            <iframe className="woven-edit-component-preview" title=${def.name + " preview"} tabIndex="-1" sandbox="" srcDoc=${preview(def)}/>
            <span>${def.name}</span><small>${def.dsId ? 'DS: ' + def.dsId : "Project"}</small>
          </button>`)}
        ${definitions.length === 0 && html`<small>No components yet. Create one from the selection.</small>`}
      </div>
    </div>`}
    ${current && html`<details className="woven-edit-component woven-inspector-section">
      <summary><${WovenInspectorIcon} name="component"/><strong>${current.name}</strong><span>Instance</span></summary>
      <div className="woven-section-content">
        <small className="woven-edit-note">${current.dsId ? html`Design system: <a href=${apiUrl('/design-systems/' + encodeURIComponent(current.dsId) + '/gallery.html') + '#' + encodeURIComponent(current.family || '')} target="_blank" rel="noopener">${current.dsId}</a>${current.dsVersion ? ' / ' + current.dsVersion : ''}` : 'Project component'}${loadingDs ? ' / Loading library...' : ''}</small>
        ${host.hasAttribute('data-woven-component-conflict') && html`<small role="alert">${host.getAttribute('data-woven-component-conflict')}</small>`}
        ${[host, ...host.querySelectorAll('[data-woven-part]')].filter(n => !n.children.length && n.textContent.trim()).slice(0, 12).map((n, i) => html`
          <label key=${WovenEdit.identify(n)} className="woven-labeled-row">Text ${i + 1}
            <input aria-label=${"Component text " + n.getAttribute('data-woven-part')} defaultValue=${n.textContent}
              key=${n.textContent} onBlur=${e => { if (e.target.value !== n.textContent) perform('component-text', { id: WovenEdit.identify(n), text: e.target.value }); }}/>
          </label>`)}
        <label className="woven-labeled-row">Swap <select aria-label="Swap component" value=${current.id} onChange=${e => perform("refresh-component", definitions.find(d => d.id === e.target.value))}>
          ${!definitions.some(d => d.id === current.id) && html`<option value=${current.id}>${current.name}</option>`}
          ${definitions.map(def => html`<option key=${def.id} value=${def.id}>${def.name}</option>`)}
        </select></label>
        <div className="woven-edit-actions">
          <button disabled=${busy} onClick=${() => updateInstance()}>Update</button>
          <button disabled=${busy} onClick=${() => updateInstance(true)}>Reset overrides</button>
          <button onClick=${() => perform("detach-component")}>Detach</button>
        </div>
        ${current.id.startsWith("local:") && html`<button disabled=${busy} onClick=${() => publish(true)}>Publish selection as main</button>`}
      </div>
    </details>`}
    ${variablesOpen && html`<div className="woven-edit-variables woven-edit-drawer">
      <div className="woven-section-heading"><strong>Variables</strong><${WovenIconButton} icon="close" label="Close variables" onClick=${() => setVariablesOpen(false)}/></div>
      ${modes.length > 0 && html`<label className="woven-labeled-row">Mode<select aria-label="Variable mode" value=${modes.find(m => element.ownerDocument.querySelector(m.target || 'html').getAttribute(m.attribute) === m.value)?.key || ''}
        onChange=${e => perform('mode', { mode: modes.find(m => m.key === e.target.value), attributes: [...new Set(modes.map(m => m.attribute))] })}>
        <option value="">Default</option>${modes.map(m => html`<option key=${m.key} value=${m.key}>${m.value}</option>`)}
      </select></label>`}
      <select aria-label="Variable property" value=${property} onChange=${e => setProperty(e.target.value)}>
        ${["color", "backgroundColor", "padding", "gap", "borderRadius", "width", "height", "fontSize", "lineHeight"].map(k => html`<option key=${k} value=${k}>${k.replace(/[A-Z]/g, c => " " + c.toLowerCase())}</option>`)}
      </select>
      <select aria-label="Bind variable" value=${currentBinding} onChange=${e => { onStyle({ [property]: e.target.value ? "var(" + e.target.value + ")" : null }); setRevision(n => n + 1); }}>
        <option value="">${currentValue ? "Local override" : "From stylesheet"}</option>
        ${matching.map(([name, token]) => html`<option key=${name} value=${name}>${name} = ${token.value}</option>`)}
      </select>
      <small>${currentBinding ? currentBinding + " = " + (tokens[currentBinding]?.value || "Unresolved") : currentValue || "Using the stylesheet value"}</small>
      <div className="woven-edit-actions">
        <button onClick=${() => { onStyle({ [property]: null }); setRevision(n => n + 1); }}>Reset</button>
        ${currentBinding && html`<button onClick=${() => { onStyle({ [property]: tokens[currentBinding]?.value || null }); setRevision(n => n + 1); }}>Unbind</button>`}
        <button onClick=${createVariable}>New variable</button>
      </div>
    </div>`}
    ${libraryError && (open || current) && html`<div role="alert" className="woven-edit-error">${libraryError}<button onClick=${() => setLibraryAttempt(n => n + 1)}>Retry component library</button></div>`}
    ${dsError && (open || current) && html`<div role="alert" className="woven-edit-error">${dsError}<button onClick=${() => setDsAttempt(n => n + 1)}>Retry design system</button></div>`}
    ${error && html`<div role="alert" className="woven-edit-error">${error}<button onClick=${() => setError("")}>Dismiss</button></div>`}
  </div>`;
}

function useWovenMovement(element, onCommand) {
  const [feedback, setFeedback] = useState(null);
  const panel = React.useRef(null);
  const move = (direction, step = 1) => {
    try {
      const result = onCommand('move', { direction, step });
      setFeedback({ message: result?.message || 'Moved layer' });
    } catch (error) { setFeedback({ error: true, message: error.message }); }
  };
  useEffect(() => { setFeedback(null); }, [element]);
  useEffect(() => {
    if (!element || !onCommand) return;
    const doc = element.ownerDocument;
    const onKey = e => {
      if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey || !/^Arrow(Left|Right|Up|Down)$/.test(e.key)) return;
      if (WovenEdit.isTextInput(e.target) || e.target.closest?.('[role="tree"],[role="dialog"],[role="slider"],[role="listbox"],[role="menu"]')) return;
      const overlay = document.querySelector('.zoom-overlay');
      if (overlay && !overlay.contains(panel.current)) return;
      // A focused control outside this editing surface keeps its own arrows.
      if (e.target.ownerDocument === document && e.target !== document.body && !panel.current?.contains(e.target) && !e.target.closest?.('.zoom-overlay,.workflow-node')) return;
      e.preventDefault(); e.stopImmediatePropagation();
      move(e.key.slice(5).toLowerCase(), e.shiftKey ? 10 : 1);
    };
    window.addEventListener('keydown', onKey, true);
    if (doc !== document) doc.addEventListener('keydown', onKey, true);
    return () => { window.removeEventListener('keydown', onKey, true); if (doc !== document) doc.removeEventListener('keydown', onKey, true); };
  }, [element, onCommand]);
  return { move, feedback, panel };
}

function WovenPropertiesPanel({ picked, styles, computedStyles, onStyle, onNavigate, cssVars, tree, element, onCommand }) {
  const { move, feedback, panel } = useWovenMovement(element, onCommand);
  const win = element?.ownerDocument?.defaultView;
  if (!picked || !win || !element.isConnected) return null;
  const cs = win.getComputedStyle(element);
  const parent = picked.parent?.layout;
  const self = picked.self?.layout;
  const display = styles.display || cs.display;
  const flex = display === 'flex' || display === 'inline-flex';
  const grid = display === 'grid' || display === 'inline-grid';
  const parentFlex = /^(inline-)?flex$/.test(parent?.display || '');
  const parentGrid = /^(inline-)?grid$/.test(parent?.display || '');
  const direction = styles.flexDirection || cs.flexDirection;
  const column = direction.startsWith('column');
  const raw = key => styles[key] || element.style[key] || '';
  const effective = key => computedStyles?.[key] || cs[key] || '';
  const set = (key, value) => {
    const lengths = /^(gap|rowGap|columnGap|padding|borderWidth|borderRadius|minWidth|maxWidth|minHeight|maxHeight|fontSize|lineHeight|letterSpacing)$/;
    if (lengths.test(key) && value && !/[()]/.test(value)) value = value.trim().split(/\s+/).map(v => /^-?[\d.]+$/.test(v) && key !== 'lineHeight' ? v + 'px' : v).join(' ');
    onStyle({ [key]: value });
  };
  const size = (axis, mode, value) => onStyle(WovenEdit.sizing(axis, mode, value, parent, self));
  const parentHugs = axis => element.parentElement && WovenEdit.sizeMode(element.parentElement, axis) === 'hug';
  const field = (key, label, placeholder) => html`<${PickedTextField} label=${label} value=${raw(key)} inherited=${effective(key)} placeholder=${placeholder} onChange=${v => set(key, v)}/>`;
  const property = (key, label, child) => html`<${WovenProperty} key=${key} label=${label} property=${key} element=${element} onStyle=${onStyle}>${child || field(key, label)}<//>`;
  const align = (axis, value) => {
    if (parentFlex) {
      const row = !(parent.flexDirection || 'row').startsWith('column');
      if (axis === 'h' ? row : !row) {
        const first = axis === 'h' ? 'marginLeft' : 'marginTop';
        const last = axis === 'h' ? 'marginRight' : 'marginBottom';
        onStyle({ [first]: value === 'start' ? '0px' : 'auto', [last]: value === 'end' ? '0px' : 'auto' });
      } else set('alignSelf', value);
    } else set(axis === 'h' ? 'justifySelf' : 'alignSelf', value);
  };
  const justify = styles.justifyContent || cs.justifyContent;
  const items = styles.alignItems || cs.alignItems;
  const alignValue = n => ['flex-start', 'center', 'flex-end'][n];
  const positionName = (r, c) => ['Top', 'Center', 'Bottom'][r] + ' ' + ['left', 'center', 'right'][c];
  const layoutName = flex ? 'Auto layout' : grid ? 'Grid layout' : 'Layout';
  const hasText = !!element.textContent.trim() || /^(INPUT|TEXTAREA|SELECT)$/.test(element.tagName);
  const directText = !element.children.length || Array.from(element.childNodes).some(n => n.nodeType === 3 && n.textContent.trim());
  const TypographySection = directText ? 'section' : 'details';
  const summary = name => html`<summary><strong>${name}</strong><span className="woven-disclosure-mark">⌄</span></summary>`;
  const sizeNote = WovenEdit.sizingNote(element);
  return html`<div ref=${panel} className="woven-inspector" onKeyDown=${e => { if (e.target.matches('input,textarea,select')) e.stopPropagation(); }}>
    <${WovenSelectionTools} element=${element} picked=${picked} onCommand=${onCommand} onStyle=${onStyle}/>
    ${feedback && html`<div className=${feedback.error ? 'woven-edit-error' : 'woven-edit-note'} role=${feedback.error ? 'alert' : 'status'}>${feedback.message}</div>`}
    ${(parentFlex || parentGrid) && html`<section className="woven-inspector-section">
      <div className="woven-section-heading"><strong>Position</strong><span className="woven-section-meta">In ${parentGrid ? 'grid' : 'auto layout'}</span></div>
      <div className="woven-alignment-toolbar">
        ${[['left','h','start'],['center','h','center'],['right','h','end'],['top','v','start'],['middle','v','center'],['bottom','v','end']].map(([icon,axis,value]) => html`<${WovenIconButton} key=${icon} icon=${icon} label=${'Align ' + icon} onClick=${() => align(axis, value)}/>`)}
        <span className="woven-toolbar-separator"/>
        <${WovenIconButton} icon="up" label="Move earlier" onClick=${() => move('prev')}/>
        <${WovenIconButton} icon="down" label="Move later" onClick=${() => move('next')}/>
      </div>
    </section>`}
    <section className="woven-inspector-section">
      <div className="woven-section-heading"><strong>${layoutName}</strong>
        <span className="woven-section-help" tabIndex="0" title="Hug fits content. Fill uses available parent space. Fixed uses CSS pixels. Size limits still apply." aria-label="Sizing help">?</span>
      </div>
      <div className="woven-layout-flow" role="group" aria-label="Layout flow">
        ${[['flow','Flow','block',false],['row','Horizontal','flex',false],['column','Vertical','flex',true],['grid','Grid','grid',false]].map(([icon,label,value,vertical]) => html`
          <${WovenIconButton} key=${icon} icon=${icon} label=${label + ' layout'} active=${value === 'flex' ? flex && column === vertical : value === 'grid' ? grid : !flex && !grid}
            onClick=${() => onStyle(value === 'flex' ? { display: 'flex', flexDirection: vertical ? 'column' : 'row' } : { display: value })}/>`)}
        ${flex && html`<span className="woven-toolbar-separator"/><${WovenIconButton} icon="wrap" label="Wrap children" active=${(styles.flexWrap || cs.flexWrap) !== 'nowrap'} onClick=${() => set('flexWrap', cs.flexWrap === 'nowrap' ? 'wrap' : 'nowrap')}/>`}
      </div>
      <div className="woven-property-grid woven-dimensions">
        <${WovenDimension} axis="w" mode=${styles.widthMode || WovenEdit.sizeMode(element, 'width')} size=${WovenEdit.dimension(element, 'width')} disabledFill=${parentHugs('width')} onChange=${(mode,value) => size('w',mode,value)}/>
        <${WovenDimension} axis="h" mode=${styles.heightMode || WovenEdit.sizeMode(element, 'height')} size=${WovenEdit.dimension(element, 'height')} disabledFill=${parentHugs('height')} onChange=${(mode,value) => size('h',mode,value)}/>
      </div>
      ${sizeNote && html`<small className="woven-edit-note" role="status">${sizeNote}</small>`}
      <small className="woven-edit-note">Arrows reorder in auto layout and grid. Elsewhere they nudge 1 px, or 10 px with Shift.</small>
      ${flex && html`<div className="woven-auto-layout">
        <div className="woven-alignment-matrix" role="group" aria-label="Align children">
          ${Array.from({length:9},(_,i) => {
            const r = Math.floor(i / 3), c = i % 3;
            const main = column ? r : c, cross = column ? c : r;
            const mainValue = direction.endsWith('reverse') ? alignValue(2 - main) : alignValue(main);
            const active = justify === mainValue && items === alignValue(cross);
            return html`<button key=${i} type="button" aria-label=${positionName(r,c)} title=${positionName(r,c)} aria-pressed=${active} onClick=${() => onStyle({justifyContent:mainValue,alignItems:alignValue(cross)})}><span/><span/><span/></button>`;
          })}
        </div>
        <div className="woven-layout-spacing">
          ${property('gap','Gap')}
          <select aria-label="Distribution" value=${justify} onChange=${e => set('justifyContent',e.target.value)}>
            <option value="normal">Packed</option><option value="flex-start">Packed at start</option><option value="center">Packed at center</option><option value="flex-end">Packed at end</option><option value="space-between">Space between</option><option value="space-around">Space around</option><option value="space-evenly">Space evenly</option>
          </select>
        </div>
      </div>`}
      ${grid && html`<div className="woven-property-grid">${property('columnGap','Column gap')}${property('rowGap','Row gap')}</div>`}
      ${property('padding','Padding',html`<${PickedBoxField} label="Padding" value=${raw('padding')} inherited=${effective('padding')} onChange=${v => set('padding',v)}/>`)}
      <details className="woven-inspector-more">
        ${summary('Layout settings')}
        <div className="woven-section-content">
          <div className="woven-property-grid">${['minWidth','maxWidth','minHeight','maxHeight'].map(key => property(key,({minWidth:'Min width',maxWidth:'Max width',minHeight:'Min height',maxHeight:'Max height'})[key]))}</div>
          ${flex && html`<label className="woven-labeled-row">Cross-axis<select aria-label="Cross-axis alignment" value=${items} onChange=${e => set('alignItems',e.target.value)}>
            <option value="normal">Automatic</option><option value="stretch">Stretch</option><option value="flex-start">Start</option><option value="center">Center</option><option value="flex-end">End</option><option value="baseline">Text baseline</option>
          </select></label><label className="woven-labeled-row">Order<select aria-label="Child order" value=${direction.endsWith('reverse') ? 'reverse' : 'normal'} onChange=${e => set('flexDirection',(column ? 'column' : 'row') + (e.target.value === 'reverse' ? '-reverse' : ''))}><option value="normal">Normal</option><option value="reverse">Reversed</option></select></label>`}
          ${grid && html`${property('gridTemplateColumns','Columns')}${property('gridTemplateRows','Rows')}`}
          <p className="woven-edit-note">Fill needs available space in the parent. Hug follows the content. Size limits still apply.</p>
          ${(parentHugs('width') || parentHugs('height')) && html`<p className="woven-edit-note">Fill is unavailable where the parent hugs its content.</p>`}
        </div>
      </details>
    </section>
    <section className="woven-inspector-section">
      <div className="woven-section-heading"><strong>Appearance</strong></div>
      <div className="woven-property-grid">
        ${property('opacity','Opacity',html`<${PickedTextField} label="Opacity" value=${raw('opacity')} inherited=${Math.round(+cs.opacity * 100) + '%'} onChange=${v => set('opacity', /^\d+(\.\d+)?%?$/.test(v) ? Math.max(0,Math.min(100,parseFloat(v))) + '%' : v)}/>`)}
        ${property('borderRadius','Corner radius',html`<${PickedBoxField} label="Corner radius" corners=${true} value=${raw('borderRadius')} inherited=${effective('borderRadius')} onChange=${v => set('borderRadius',v)}/>`)}
      </div>
    </section>
    ${hasText && html`<${TypographySection} className="woven-inspector-section">
      ${directText ? html`<div className="woven-section-heading"><strong>Typography</strong></div>` : summary('Typography')}
      <div className=${directText ? '' : 'woven-section-content'}>
      ${field('fontFamily','Font family')}
      <div className="woven-property-grid">${property('fontSize','Size')}${property('fontWeight','Weight')}</div>
      <div className="woven-property-grid">${property('lineHeight','Line height')}${property('letterSpacing','Letter spacing')}</div>
      <div className="woven-property-color"><${PickedColorField} label="Text color" value=${raw('color')} inherited=${effective('color')} cssVars=${cssVars} onChange=${v => set('color',v)}/><${WovenVariableButton} element=${element} property="color" label="Text color" onStyle=${onStyle}/></div>
      </div>
    <//>`}
    <section className="woven-inspector-section">
      <div className="woven-section-heading"><strong>Fill</strong><${WovenVariableButton} element=${element} property="background" label="Fill" onStyle=${onStyle}/></div>
      <${PickedColorField} label="Fill" value=${raw('background')} inherited=${effective('background')} cssVars=${cssVars} onChange=${v => set('background',v)}/>
    </section>
    <section className="woven-inspector-section">
      <div className="woven-section-heading"><strong>Stroke</strong><${WovenVariableButton} element=${element} property="borderColor" label="Stroke" onStyle=${onStyle}/></div>
      <${PickedColorField} label="Stroke" value=${raw('borderColor')} inherited=${effective('borderColor')} cssVars=${cssVars} onChange=${v => set('borderColor',v)}/>
      <div className="woven-property-grid">
        ${property('borderWidth','Weight',html`<${PickedBoxField} label="Stroke weight" value=${raw('borderWidth')} inherited=${effective('borderWidth')} onChange=${v => set('borderWidth',v)}/>`)}
        <label className="woven-property"><span className="woven-property-label">Style</span><select aria-label="Stroke style" value=${raw('borderStyle') || effective('borderStyle')} onChange=${e => set('borderStyle',e.target.value)}><option value="none">None</option><option value="solid">Solid</option><option value="dashed">Dashed</option><option value="dotted">Dotted</option><option value="double">Double</option></select></label>
      </div>
    </section>
    <details className="woven-inspector-section">
      ${summary('Effects')}
      <div className="woven-section-content">${property('boxShadow','Shadow')}${property('filter','Filter')}</div>
    </details>
  </div>`;
}

function WovenLayersPanel({ element, onNavigate, find }) {
  const [query, setQuery] = useState('');
  const [expanded, setExpanded] = useState(new Set());
  const [collapsed, setCollapsed] = useState(new Set());
  const [, refresh] = useState(0);
  const ref = React.useRef(null);
  const doc = element?.ownerDocument;
  useEffect(() => {
    if (!doc?.body) return;
    const observer = new MutationObserver(() => refresh(n => n + 1));
    observer.observe(doc.body, { subtree:true, childList:true, characterData:true, attributes:true, attributeFilter:['data-name','id','hidden','data-woven-component'] });
    return () => observer.disconnect();
  }, [doc]);
  useEffect(() => {
    if (!element) return;
    const parents = [];
    for (let n = element.parentElement; n && n !== doc.body; n = n.parentElement) parents.push(WovenEdit.identify(n));
    setExpanded(prev => new Set([...prev, ...parents]));
    setCollapsed(prev => new Set([...prev].filter(id => !parents.includes(id))));
  }, [element, doc]);
  // Find tab state lives in wovenFindMemo; the Find search bar follows the
  // selected element's own text and any text highlighted in the page, so it
  // is filled in by the time the tab is opened. A pick the Find tab made
  // itself (stepping through on-screen hits) must not rewrite the query.
  const [, rerenderFind] = useState(0);
  const setFind = patch => { Object.assign(wovenFindMemo, patch); rerenderFind(n => n + 1); };
  const findPick = React.useRef(null);
  useEffect(() => {
    if (!element || element === findPick.current) return;
    const text = wovenFindOwnText(element);
    if (text && text.length <= 200) setFind({ query: text });
  }, [element]);
  useEffect(() => {
    if (!doc) return;
    const onSelect = () => {
      const sel = doc.getSelection && doc.getSelection();
      const text = sel && !sel.isCollapsed ? String(sel).replace(/\s+/g, ' ').trim() : '';
      if (text && text.length <= 200 && text !== wovenFindMemo.query) setFind({ query: text });
    };
    doc.addEventListener('selectionchange', onSelect);
    return () => doc.removeEventListener('selectionchange', onSelect);
  }, [doc]);
  if (!doc?.body) return null;
  const names = {DIV:'Frame',MAIN:'Main',SECTION:'Section',NAV:'Navigation',HEADER:'Header',FOOTER:'Footer',BUTTON:'Button',A:'Link',P:'Text',SPAN:'Text',IMG:'Image',SVG:'Vector',IFRAME:'Embedded page',INPUT:'Input'};
  const label = n => n.getAttribute('data-name') || n.getAttribute('aria-label') || n.id ||
    (!n.children.length && n.textContent.trim().slice(0,70)) || Array.from(n.classList).find(c => !c.startsWith('th-pick-')) || names[n.tagName] || n.tagName.toLowerCase();
  const children = n => /^(svg|canvas|iframe)$/i.test(n.tagName) ? [] : Array.from(n.children).filter(c => !/^(SCRIPT|STYLE|LINK|META|TEMPLATE|NOSCRIPT)$/.test(c.tagName) && !c.hasAttribute('data-th-pick-style'));
  const needle = query.trim().toLowerCase();
  const tree = n => {
    const name = label(n), descendants = children(n).map(tree);
    return {el:n,id:WovenEdit.identify(n),name,children:descendants,match:name.toLowerCase().includes(needle) || descendants.some(c => c.match)};
  };
  const nodes = children(doc.body).map(tree);
  const rows = [];
  const walk = (nodes, depth, parentId) => nodes.forEach(n => {
    if (needle && !n.match) return;
    const open = needle || !collapsed.has(n.id) && (expanded.has(n.id) || depth < 1);
    rows.push({...n,depth,parentId,open});
    if (open) walk(n.children,depth+1,n.id);
  });
  walk(nodes,0,null);
  const selectedVisible = rows.some(n => n.el === element);
  const toggle = row => {
    if (row.open) { setCollapsed(s => new Set([...s,row.id])); setExpanded(s => new Set([...s].filter(id => id !== row.id))); }
    else { setExpanded(s => new Set([...s,row.id])); setCollapsed(s => new Set([...s].filter(id => id !== row.id))); }
  };
  const focus = index => ref.current?.querySelectorAll('[role="treeitem"]')[index]?.focus();
  const keyboard = (e,row,index) => {
    if (!['ArrowDown','ArrowUp','ArrowLeft','ArrowRight','Home','End','Enter',' '].includes(e.key)) return;
    e.preventDefault(); e.stopPropagation();
    if (e.key === 'ArrowDown') focus(Math.min(index+1,rows.length-1));
    else if (e.key === 'ArrowUp') focus(Math.max(index-1,0));
    else if (e.key === 'Home') focus(0);
    else if (e.key === 'End') focus(rows.length-1);
    else if (e.key === 'ArrowRight') { if (row.children.length && !row.open) toggle(row); else if (row.children.length) focus(index+1); }
    else if (e.key === 'ArrowLeft') { if (row.children.length && row.open) toggle(row); else focus(rows.findIndex(n => n.id === row.parentId)); }
    else onNavigate(row.el);
  };
  const tab = wovenFindMemo.tab;
  const tabs = html`<div className="woven-layers-header" role="tablist" aria-label="Layers panel">
    ${[['layers', 'Layers'], ['find', 'Find']].map(([id, label]) => html`<button key=${id} type="button" role="tab" className="woven-layers-tab"
      aria-selected=${tab === id} onClick=${() => setFind({ tab: id })}>${label}</button>`)}
    <span>${doc.title || 'Page'}</span>
  </div>`;
  if (tab === 'find') return html`<div className="woven-layers" ref=${ref}>${tabs}
    <${WovenFindPanel} doc=${doc} find=${find} memo=${wovenFindMemo} setFind=${setFind} onNavigate=${el => { findPick.current = el; onNavigate(el); }}/>
  </div>`;
  return html`<div className="woven-layers" ref=${ref}>
    ${tabs}
    <div className="woven-layer-search"><input type="search" aria-label="Find layer" placeholder="Find a layer..." value=${query} onChange=${e => setQuery(e.target.value)}/></div>
    <div className="woven-layer-tree" role="tree" aria-label="Page layers">
      ${rows.map((row,i) => html`<div key=${row.id} className="woven-layer-row" role="treeitem" aria-level=${row.depth+1} aria-label=${row.name} aria-selected=${row.el===element} aria-expanded=${row.children.length ? !!row.open : undefined} tabIndex=${row.el===element || !selectedVisible && i===0 ? 0 : -1} title=${row.el.tagName.toLowerCase() + ' · ' + row.name} style=${{paddingLeft:8+Math.min(row.depth,12)*12+'px'}} onClick=${() => onNavigate(row.el)} onKeyDown=${e => keyboard(e,row,i)}>
        <button tabIndex="-1" className="woven-layer-chevron" aria-label=${(row.open ? 'Collapse ' : 'Expand ') + row.name} disabled=${!row.children.length} onClick=${e => {e.stopPropagation();toggle(row);}}>${row.children.length ? row.open ? '⌄' : '›' : ''}</button>
        <${WovenInspectorIcon} name=${row.el.hasAttribute('data-woven-component') ? 'component' : /^(P|SPAN|H[1-6]|LABEL|A)$/.test(row.el.tagName) ? 'text' : 'frame'}/>
        <span>${row.name}</span>
      </div>`)}
      ${!rows.length && html`<small>No matching layers.</small>`}
    </div>
  </div>`;
}

/* ── Find & replace across one prototype ──────────────────────────────────────
   The Layers panel's Find tab. Text on a screen is either typed into a page
   (markup, a template string) or read from data (a record in data.js, or any
   object literal). Search reads every text file under source/<prototype>/; a
   hit inside an object literal is shown as its RECORD, so editing that one
   literal updates every screen that renders it. Pure functions first (tests in
   tests/test-edit-find.cjs), the panel after. Nothing here asks an agent:
   replacements are literal writes, conflict-checked against the bytes read. */
const WOVEN_FIND_EXTS = ['html', 'htm', 'svg', 'js', 'mjs', 'cjs', 'jsx', 'ts', 'tsx', 'json'];
const WOVEN_FIND_SKIP = /(^|\/)(QUALITY_REPORT|FIX_PROPOSALS|test-cases)\.json$|\.min\.js$|(^|\/)(node_modules|vendor)\//i;
const WOVEN_FIND_DATA_FILE = /(^|[-_.])(data|seed|seeds|mock|mocks|fixtures?|db|database|records?|demo)([-_.]|$)/i;
const WOVEN_FIND_ENTITIES = {
  '&': ['&amp;'], '<': ['&lt;'], '>': ['&gt;'], '"': ['&quot;'], "'": ['&apos;'], '\u00a0': ['&nbsp;'],
  '\u2013': ['&ndash;'], '\u2014': ['&mdash;'], '\u2018': ['&lsquo;'], '\u2019': ['&rsquo;'], '\u201c': ['&ldquo;'],
  '\u201d': ['&rdquo;'], '\u2026': ['&hellip;'], '\u00a9': ['&copy;'], '\u00ae': ['&reg;'], '\u2122': ['&trade;'],
  '\u00d7': ['&times;'], '\u00b7': ['&middot;'], '\u2022': ['&bull;'], '\u2192': ['&rarr;'], '\u2190': ['&larr;'],
};
// Attributes whose values are text a person reads. Everything else in a tag
// (class, href, path data) is code, and a word query must not rewrite it.
const WOVEN_FIND_TEXT_ATTR = /^(alt|title|placeholder|aria-label|aria-description|aria-placeholder|value|label|content|summary|data-(?!th-|woven|zoom)[\w-]+)$/i;

/* A whitespace-tolerant regex for `query`. Rendered text collapses runs of
   whitespace that the source may wrap across lines. `markup` also accepts each
   character's HTML entity spellings, since the DOM shows "&" where the file
   says "&amp;". */
function wovenFindPattern(query, matchCase, markup) {
  const text = String(query || '').replace(/\s+/g, ' ').trim();
  if (!text) return null;
  const esc = s => s.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&');
  let source = '';
  for (const ch of text) {
    if (ch === ' ') { source += markup ? '(?:\\s|&nbsp;|&#160;)+' : '\\s+'; continue; }
    const alts = [esc(ch)];
    if (markup) {
      const cp = ch.codePointAt(0);
      for (const e of WOVEN_FIND_ENTITIES[ch] || []) alts.push(esc(e));
      if (cp > 127 || WOVEN_FIND_ENTITIES[ch]) alts.push('&#0*' + cp + ';', '&#[xX]0*' + cp.toString(16) + ';', '&#[xX]0*' + cp.toString(16).toUpperCase() + ';');
    }
    source += alts.length > 1 ? '(?:' + alts.join('|') + ')' : alts[0];
  }
  return new RegExp(source, 'gu' + (matchCase ? '' : 'i'));
}

/* Decodes a JS string literal body. `map[i]` is the raw offset where decoded
   unit i starts (null when there is no escape, so raw IS the value): a hit in
   the decoded text maps back to exactly the bytes that spell it, and a replace
   leaves every other escape in the string as the author wrote it. */
function wovenFindDecode(raw) {
  if (!raw.includes('\\')) return { value: raw, map: null };
  const breaks = ['\r\n', '\n', '\r', String.fromCharCode(0x2028), String.fromCharCode(0x2029)];
  const named = { n: '\n', t: '\t', r: '\r', b: '\b', f: '\f', v: '\v', 0: '\0' };
  let value = '';
  const map = [];
  for (let i = 0; i < raw.length;) {
    let out = raw[i], len = 1;
    if (raw[i] === '\\' && i + 1 < raw.length) {
      const e = /^(u\{[0-9a-fA-F]+\}|u[0-9a-fA-F]{4}|x[0-9a-fA-F]{2}|\r\n|[\s\S])/.exec(raw.slice(i + 1, i + 12))[0];
      len = 1 + e.length;
      if (e[0] === 'u' && e.length > 1) { try { out = String.fromCodePoint(parseInt(e[1] === '{' ? e.slice(2, -1) : e.slice(1), 16)); } catch { out = e; } }
      else if (e[0] === 'x' && e.length > 1) out = String.fromCharCode(parseInt(e.slice(1), 16));
      else out = breaks.includes(e) ? '' : named[e] ?? e;
    }
    for (let k = 0; k < out.length; k++) map.push(i);
    value += out; i += len;
  }
  map.push(raw.length);
  return { value, map };
}
function wovenFindEncode(value, quote) {
  const s = String(value).replace(/\\/g, '\\\\');
  if (quote === '`') return s.replace(/`/g, '\\`').replace(/\$\{/g, '\\${');
  return s.replace(quote === '"' ? /"/g : /'/g, '\\' + quote).replace(/\n/g, '\\n').replace(/\r/g, '\\r')
    .replace(/\t/g, '\\t').replace(/\u2028/g, '\\u2028').replace(/\u2029/g, '\\u2029');
}
function wovenFindEscapeMarkup(value, quote) {
  const s = String(value).replace(/&/g, '&amp;');
  if (quote === '"') return s.replace(/"/g, '&quot;');
  if (quote === "'") return s.replace(/'/g, '&#39;');
  return s.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(quote === '' ? /["'\s]/g : /$^/g, c => '&#' + c.charCodeAt(0) + ';');
}
function wovenFindUnescapeMarkup(s) {
  const named = { amp: '&', lt: '<', gt: '>', quot: '"', apos: "'", nbsp: ' ', ndash: '\u2013', mdash: '\u2014', lsquo: '\u2018', rsquo: '\u2019', ldquo: '\u201c', rdquo: '\u201d', hellip: '\u2026', copy: '\u00a9', reg: '\u00ae', trade: '\u2122', times: '\u00d7', middot: '\u00b7', bull: '\u2022', rarr: '\u2192', larr: '\u2190' };
  return String(s).replace(/&(#[xX][0-9a-fA-F]+|#\d+|[a-zA-Z]+);/g, (m, e) => {
    try {
      if (e[0] === '#') return String.fromCodePoint(e[1] === 'x' || e[1] === 'X' ? parseInt(e.slice(2), 16) : parseInt(e.slice(1), 10));
    } catch { return m; }
    return named[e] ?? m;
  });
}

/* Tokenizes JavaScript (or JSON) between `from` and `to`. Returns every string
   segment (quoted strings, and each static part of a template literal) and the
   top-level token stream the record pass reads. Tokens inside a template's
   `${...}` are not structure, so they stay out of `tokens`; their strings are
   still searchable. */
function wovenScanJs(src, from = 0, to = src.length) {
  const strings = [], tokens = [];
  let prev = null;
  const regexAllowed = () => !prev || (prev.t === 'p' && !/^[)\]}]$/.test(prev.v)) ||
    (prev.t === 'id' && /^(return|typeof|instanceof|in|of|new|delete|void|throw|case|do|else|yield|await)$/.test(prev.v));
  const emit = (tok, nested) => { if (!nested) tokens.push(tok); prev = tok; };
  function template(i, nested) {
    const parts = [];
    let j = i + 1, part = j;
    while (j < to && src[j] !== '`') {
      if (src[j] === '\\') { j += 2; continue; }
      if (src[j] === '$' && src[j + 1] === '{') { parts.push([part, j]); j = code(j + 2, true); part = j; continue; }
      j++;
    }
    parts.push([part, Math.min(j, to)]);
    const simple = parts.length === 1;
    const tok = { t: simple ? 'str' : 'tpl', q: '`', start: i, end: Math.min(j + 1, to), si: simple ? strings.length : -1 };
    for (const [a, b] of parts) { const raw = src.slice(a, b); strings.push({ start: a, end: b, q: '`', raw, ...wovenFindDecode(raw) }); }
    emit(tok, nested);
    return tok.end;
  }
  function code(i, nested) {
    let depth = 0;
    while (i < to) {
      const c = src[i];
      if (c === ' ' || c === '\n' || c === '\t' || c === '\r') { i++; continue; }
      if (c === '/' && src[i + 1] === '/') { const e = src.indexOf('\n', i); i = e < 0 || e > to ? to : e; continue; }
      if (c === '/' && src[i + 1] === '*') { const e = src.indexOf('*/', i + 2); i = e < 0 || e > to ? to : e + 2; continue; }
      if (c === '"' || c === "'") {
        let j = i + 1;
        while (j < to && src[j] !== c && src[j] !== '\n') j += src[j] === '\\' ? 2 : 1;
        const raw = src.slice(i + 1, Math.min(j, to));
        emit({ t: 'str', q: c, start: i, end: Math.min(j + 1, to), si: strings.length }, nested);
        strings.push({ start: i + 1, end: i + 1 + raw.length, q: c, raw, ...wovenFindDecode(raw) });
        i = Math.min(j + 1, to); continue;
      }
      if (c === '`') { i = template(i, nested); continue; }
      if (c === '/' && regexAllowed()) {
        let j = i + 1, cls = false;
        while (j < to && src[j] !== '\n') {
          if (src[j] === '\\') { j += 2; continue; }
          if (src[j] === '[') cls = true; else if (src[j] === ']') cls = false; else if (src[j] === '/' && !cls) break;
          j++;
        }
        j++; while (j < to && /[a-z]/i.test(src[j])) j++;
        prev = { t: 're' }; i = j; continue;
      }
      if (/[0-9]/.test(c) || (c === '.' && /[0-9]/.test(src[i + 1] || ''))) {
        const m = /^(?:0[xXbBoO][0-9a-fA-F_]+|(?:\d[\d_]*\.?[\d_]*|\.\d[\d_]*)(?:[eE][+-]?\d+)?)n?/.exec(src.slice(i, i + 64));
        const len = m ? m[0].length : 1;
        emit({ t: 'num', v: src.slice(i, i + len), start: i, end: i + len }, nested);
        i += len; continue;
      }
      if (/[A-Za-z_$]/.test(c) || c.charCodeAt(0) > 127) {
        let j = i + 1;
        while (j < to && (/[\w$]/.test(src[j]) || src.charCodeAt(j) > 127)) j++;
        emit({ t: 'id', v: src.slice(i, j), start: i, end: j }, nested);
        i = j; continue;
      }
      if (nested && c === '{') depth++;
      if (nested && c === '}') { if (depth === 0) return i + 1; depth--; }
      const v = src.startsWith('...', i) ? '...' : c;
      emit({ t: 'p', v, start: i, end: i + v.length }, nested);
      i += v.length;
    }
    return i;
  }
  code(from, false);
  return { strings, tokens };
}

/* Object and array literals in a token stream, each with its primitive
   members: `key: "literal"` for objects, bare literals for arrays. A string
   that is one of those members is DATA - the record it sits in is what a
   screen reads. Function bodies parse as memberless objects and fall away. */
function wovenJsRecords(tokens, strings) {
  const containers = [], stack = [], fieldOf = new Map();
  const isKey = t => t && (t.t === 'id' || t.t === 'num' || (t.t === 'str' && t.q !== '`'));
  const keyName = t => t.t === 'str' ? strings[t.si].value : t.v;
  const opens = t => t && t.t === 'p' && (t.v === '{' || t.v === ',');
  const literal = t => t && (t.t === 'str' || t.t === 'num' || (t.t === 'id' && /^(true|false|null)$/.test(t.v)));
  for (let k = 0; k < tokens.length; k++) {
    const t = tokens[k], prev = tokens[k - 1], prev2 = tokens[k - 2], top = stack[stack.length - 1];
    const keyed = top && top.kind === 'object' && prev && prev.t === 'p' && prev.v === ':' && isKey(prev2) && opens(tokens[k - 3]);
    const listed = top && top.kind === 'array' && prev && prev.t === 'p' && (prev.v === '[' || prev.v === ',');
    if (t.t === 'p' && (t.v === '{' || t.v === '[')) {
      const c = { id: containers.length, kind: t.v === '[' ? 'array' : 'object', start: t.start, end: -1,
        parent: top ? top.id : -1, key: null, name: null, fields: [], children: [], commas: 0 };
      if (keyed) c.key = keyName(prev2);
      else if (listed) c.key = top.commas;
      else if (prev && prev.t === 'p' && prev.v === '=' && prev2 && prev2.t === 'id') c.name = prev2.v;
      if (top) top.children.push(c.id);
      containers.push(c); stack.push(c); continue;
    }
    if (t.t === 'p' && (t.v === '}' || t.v === ']')) { if (top) { top.end = t.end; stack.pop(); } continue; }
    if (t.t === 'p' && t.v === ',') { if (top) top.commas++; continue; }
    if (!literal(t)) continue;
    const next = tokens[k + 1];
    if (!next || next.t !== 'p' || (next.v !== ',' && next.v !== (top && top.kind === 'array' ? ']' : '}'))) continue;
    if (!keyed && !listed) continue;
    const field = { key: keyed ? keyName(prev2) : top.commas, tok: t };
    top.fields.push(field);
    if (t.t === 'str') fieldOf.set(t.si, { cid: top.id, field });
  }
  return { containers, fieldOf };
}

/* The record a data string belongs to, flattened for the editor: an object's
   own literals plus any short list of literals it holds (`schedule[0]`). */
function wovenFindRecord(text, structure, strings, si) {
  const at = structure.fieldOf.get(si);
  if (!at) return null;
  const { containers } = structure;
  let owner = containers[at.cid];
  if (owner.kind === 'array' && owner.parent >= 0 && owner.key != null && containers[owner.parent].kind === 'object') owner = containers[owner.parent];
  const fieldRow = (key, f) => {
    const t = f.tok, raw = text.slice(t.start, t.end);
    const type = t.t === 'str' ? 'string' : t.t === 'num' ? 'number' : t.v === 'null' ? 'null' : 'boolean';
    return { id: t.start, key: String(key), start: t.start, end: t.end, raw, type, q: t.q || null,
      value: t.t === 'str' ? strings[t.si].value : t.v, hit: t.si === si };
  };
  const label = c => c.name != null ? c.name : typeof c.key === 'number' ? '[' + c.key + ']' : c.key;
  const fields = owner.fields.map(f => fieldRow(owner.kind === 'array' ? '[' + f.key + ']' : f.key, f));
  for (const cid of owner.children) {
    const list = containers[cid];
    if (list.kind !== 'array' || list.children.length || !list.fields.length || list.fields.length > 20) continue;
    for (const f of list.fields) fields.push(fieldRow(label(list) + '[' + f.key + ']', f));
  }
  const chain = [];
  for (let c = owner; c; c = c.parent >= 0 ? containers[c.parent] : null) {
    const seg = label(c);
    if (seg == null) continue;
    chain.unshift(typeof c.key === 'number' && c.name == null ? seg : (chain.length || c.parent >= 0 ? '.' : '') + seg);
  }
  const named = fields.find(f => f.type === 'string' && /^(name|title|label|fullName|displayName|heading|subject)$/i.test(f.key));
  return { key: owner.start, where: chain.join('').replace(/^\./, ''), title: (named || fields.find(f => f.hit) || {}).value || '',
    fields: fields.slice(0, 40), more: Math.max(0, fields.length - 40) };
}

/* The searchable parts of an HTML/SVG file: text between tags, the values of
   text attributes, and the bodies of JavaScript script blocks (searched as
   code). Styles and comments are skipped. */
function wovenScanMarkup(src, from = 0, to = src.length) {
  const ranges = [], scripts = [], lower = src.toLowerCase();
  let i = from, textStart = from;
  const text = (a, b) => { if (b > a) ranges.push({ start: a, end: b, quote: null }); };
  while (i < to) {
    const lt = src.indexOf('<', i);
    if (lt < 0 || lt >= to) break;
    if (src.startsWith('<!--', lt)) { text(textStart, lt); const e = src.indexOf('-->', lt + 4); i = textStart = e < 0 || e >= to ? to : e + 3; continue; }
    const m = /^<\/?([A-Za-z][\w:-]*)|^<[!?]/.exec(src.slice(lt, lt + 64));
    if (!m) { i = lt + 1; continue; }
    text(textStart, lt);
    let j = lt + 1, q = null;
    while (j < to) { const c = src[j]; if (q) { if (c === q) q = null; } else if (c === '"' || c === "'") q = c; else if (c === '>') break; j++; }
    const tagEnd = Math.min(j + 1, to), tag = src.slice(lt, tagEnd), name = (m[1] || '').toLowerCase();
    if (name && tag[1] !== '/') {
      const attr = /\s([^\s"'=<>\/`]+)\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s"'=<>`]+))/g;
      let a;
      while ((a = attr.exec(tag))) {
        if (!WOVEN_FIND_TEXT_ATTR.test(a[1])) continue;
        const value = a[2] ?? a[3] ?? a[4], quote = a[2] != null ? '"' : a[3] != null ? "'" : '';
        const start = lt + a.index + a[0].length - value.length - (quote ? 1 : 0);
        ranges.push({ start, end: start + value.length, quote });
      }
      if (name === 'script' || name === 'style') {
        const close = lower.indexOf('</' + name, tagEnd), end = close < 0 || close > to ? to : close;
        const type = ((/\stype\s*=\s*["']?([^"'\s>]+)/i.exec(tag) || [])[1] || '').toLowerCase();
        if (name === 'script' && (!type || /javascript|ecmascript|module|babel|jsx|json/.test(type))) scripts.push([tagEnd, end]);
        else if (name === 'script' && /html|template/.test(type)) { const inner = wovenScanMarkup(src, tagEnd, end); ranges.push(...inner.ranges); scripts.push(...inner.scripts); }
        i = textStart = end; continue;
      }
    }
    i = textStart = tagEnd;
  }
  text(textStart, to);
  return { ranges, scripts };
}

/* Every hit of `query` in one file. String hits carry their segment so a
   replace can re-encode it; hits inside an object literal also carry their
   record. */
function wovenFindInSource(path, text, query, matchCase) {
  const plain = wovenFindPattern(query, matchCase, false), markup = wovenFindPattern(query, matchCase, true);
  const out = { hits: [], records: [] };
  if (!plain || typeof text !== 'string') return out;
  const ext = (path.split('.').pop() || '').toLowerCase();
  const base = path.split('/').pop().replace(/\.[^.]+$/, '');
  const dataFile = ext === 'json' || WOVEN_FIND_DATA_FILE.test(base);
  const newlines = [];
  for (let i = text.indexOf('\n'); i >= 0; i = text.indexOf('\n', i + 1)) newlines.push(i);
  const lineAt = pos => { let lo = 0, hi = newlines.length; while (lo < hi) { const mid = (lo + hi) >> 1; if (newlines[mid] < pos) lo = mid + 1; else hi = mid; } return lo + 1; };
  const clip = (s, tail) => { const v = s.replace(/\s+/g, ' '); return tail ? (v.length > 32 ? v.slice(0, 32) + '...' : v) : (v.length > 32 ? '...' + v.slice(-32) : v); };
  const records = new Map();
  const searchJs = (from, to) => {
    const scan = wovenScanJs(text, from, to);
    const structure = wovenJsRecords(scan.tokens, scan.strings);
    scan.strings.forEach((seg, si) => {
      plain.lastIndex = 0;
      for (let m; (m = plain.exec(seg.value));) {
        if (!m[0]) { plain.lastIndex++; continue; }
        const at = k => seg.start + (seg.map ? seg.map[k] : k), start = at(m.index);
        const hit = { id: path + ':' + start, kind: 'string', path, seg: { start: seg.start, end: seg.end, q: seg.q, raw: seg.raw },
          start, end: at(m.index + m[0].length), line: lineAt(start),
          before: clip(seg.value.slice(Math.max(0, m.index - 40), m.index), false), match: m[0], after: clip(seg.value.slice(m.index + m[0].length, m.index + m[0].length + 40), true) };
        const record = structure.fieldOf.has(si) && wovenFindRecord(text, structure, scan.strings, si);
        if (record) {
          hit.record = record.key;
          const known = records.get(record.key);
          if (!known) records.set(record.key, { ...record, path, data: dataFile });
          else known.fields.forEach(f => { if (f.id === record.fields.find(r => r.hit)?.id) f.hit = true; });
        }
        out.hits.push(hit);
      }
    });
  };
  if (/^(html?|svg)$/.test(ext)) {
    const { ranges, scripts } = wovenScanMarkup(text);
    for (const r of ranges) {
      const slice = text.slice(r.start, r.end);
      markup.lastIndex = 0;
      for (let m; (m = markup.exec(slice));) {
        if (!m[0]) { markup.lastIndex++; continue; }
        const start = r.start + m.index;
        out.hits.push({ id: path + ':' + start, kind: 'markup', path, quote: r.quote, start, end: start + m[0].length, raw: m[0], line: lineAt(start),
          before: clip(wovenFindUnescapeMarkup(slice.slice(Math.max(0, m.index - 40), m.index)), false), match: wovenFindUnescapeMarkup(m[0]),
          after: clip(wovenFindUnescapeMarkup(slice.slice(m.index + m[0].length, m.index + m[0].length + 40)), true) });
      }
    }
    for (const [a, b] of scripts) searchJs(a, b);
  } else searchJs(0, text.length);
  out.hits.sort((a, b) => a.start - b.start);
  out.records = [...records.values()];
  return out;
}

/* Applies the chosen hits of ONE file. Throws when the bytes under a hit moved
   since the search, so a stale result can never write over newer work. */
function wovenFindApply(text, hits, replacement) {
  const edits = hits.map(h => {
    const stale = h.kind === 'markup' ? text.slice(h.start, h.end) !== h.raw : text.slice(h.seg.start, h.seg.end) !== h.seg.raw;
    if (stale) throw new Error('The file changed since the search. Search again.');
    return { start: h.start, end: h.end, text: h.kind === 'markup' ? wovenFindEscapeMarkup(replacement, h.quote) : wovenFindEncode(replacement, h.seg.q) };
  });
  return wovenFindSplice(text, edits);
}
function wovenFindSplice(text, edits) {
  edits.sort((a, b) => b.start - a.start);
  for (let i = 1; i < edits.length; i++) if (edits[i].end > edits[i - 1].start) throw new Error('Two replacements overlap. Search again.');
  let out = text;
  for (const e of edits) out = out.slice(0, e.start) + e.text + out.slice(e.end);
  return out;
}
/* A record field's new source literal, in the field's own type and quotes. */
function wovenFindLiteral(field, value) {
  if (field.type === 'string') return field.q + wovenFindEncode(value, field.q) + field.q;
  const v = String(value).trim();
  if (field.type === 'number') {
    if (!/^-?(\d[\d_]*\.?\d*|\.\d+)([eE][+-]?\d+)?$/.test(v)) throw new Error('"' + field.key + '" must be a number.');
    return v;
  }
  if (field.type === 'boolean') {
    if (v !== 'true' && v !== 'false') throw new Error('"' + field.key + '" must be true or false.');
    return v;
  }
  return field.raw;
}
function wovenRecordApply(text, record, values) {
  const edits = [];
  for (const f of record.fields) {
    if (!(f.id in values) || values[f.id] === f.value) continue;
    if (text.slice(f.start, f.end) !== f.raw) throw new Error('The data file changed since the search. Search again.');
    edits.push({ start: f.start, end: f.end, text: wovenFindLiteral(f, values[f.id]) });
  }
  return wovenFindSplice(text, edits);
}

/* ── Find tab: IO + panel ──────────────────────────────────────────────────── */
// One Find state for the editor: it outlives the panel, which unmounts when a
// write reloads the page under it (and on every tool switch in edit mode).
const wovenFindMemo = { tab: 'layers', query: '', replacement: '', replaceOpen: false, matchCase: false,
  root: '', results: null, excluded: new Set(), collapsed: new Set(), busy: false, notice: null };

function wovenFindOwnText(el) {
  if (!el || !el.tagName) return '';
  if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') return (el.value || el.getAttribute('placeholder') || '').trim();
  if (el.tagName === 'IMG') return (el.getAttribute('alt') || '').trim();
  let own = '';
  for (const n of el.childNodes) if (n.nodeType === 3) own += n.nodeValue;
  return own.replace(/\s+/g, ' ').trim();
}
function wovenFindOnScreen(doc, query, matchCase) {
  const re = wovenFindPattern(query, matchCase, false);
  if (!re || !doc || !doc.body) return [];
  const found = [], walk = doc.createTreeWalker(doc.body, 1);
  for (let el = walk.nextNode(); el; el = walk.nextNode()) {
    if (/^(SCRIPT|STYLE|TEMPLATE|NOSCRIPT)$/.test(el.tagName)) continue;
    const own = wovenFindOwnText(el);
    re.lastIndex = 0;
    if (own && re.test(own)) found.push(el);
  }
  return found;
}
async function wovenFindRead(path) {
  // HTML goes through the edit store: its version makes the write conflict-checked.
  if (/\.html?$/i.test(path)) { const d = await WovenEdit.readSource(path, apiUrl); return { text: d.html, version: d.version }; }
  const url = apiUrl('/' + path.split('/').map(encodeURIComponent).join('/'));
  const r = await fetch(url + (url.includes('?') ? '&' : '?') + '_c=' + Date.now(), { cache: 'no-store' });
  if (!r.ok) throw new Error('could not be read (' + r.status + ')');
  return { text: await r.text(), version: null };
}
async function wovenFindSearch(root, query, matchCase) {
  const r = await fetch(apiUrl('/__list_files?root=' + root.split('/').map(encodeURIComponent).join('/') + '&exts=' + WOVEN_FIND_EXTS.join(',')));
  const listing = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(listing.error || 'Could not list the prototype files (' + r.status + ')');
  const paths = (listing.files || []).filter(f => f.size <= 1500000 && !WOVEN_FIND_SKIP.test(f.path)).map(f => f.path);
  const files = [];
  let next = 0;
  const worker = async () => {
    while (next < paths.length) {
      const path = paths[next++];
      try {
        const { text, version } = await wovenFindRead(path);
        const found = wovenFindInSource(path, text, query, matchCase);
        if (found.hits.length) files.push({ path, text, version, ...found });
      } catch {}
    }
  };
  await Promise.all(Array.from({ length: Math.min(6, paths.length) }, worker));
  return { files, scanned: paths.length };
}
async function wovenFindWrite(file, text) {
  const name = file.path.split('/').pop();
  if (file.version != null) {
    const r = await fetch(apiUrl('/__html_save'), { method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: file.path, html: text, expectedVersion: file.version }) });
    const j = await r.json().catch(() => ({}));
    if (r.status === 409) throw new Error(name + ' changed since the search. Search again.');
    if (!r.ok) throw new Error(name + ': ' + (j.error || 'save failed (' + r.status + ')'));
    return;
  }
  const fresh = await wovenFindRead(file.path);
  if (fresh.text !== file.text) throw new Error(name + ' changed since the search. Search again.');
  const r = await fetch(apiUrl('/__write_text'), { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: file.path, text }) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(name + ': ' + (j.error || 'save failed (' + r.status + ')'));
}

/* One data record, editable in place. Its literals are the only bytes a save
   touches; every screen that reads the record picks the change up. */
function WovenFindRecord({ file, record, disabled, onSave }) {
  const [values, setValues] = useState({});
  const [error, setError] = useState('');
  const changed = record.fields.filter(f => f.id in values && values[f.id] !== f.value);
  const set = (f, v) => { setError(''); setValues(prev => ({ ...prev, [f.id]: v })); };
  const save = async () => {
    if (disabled || !changed.length) return;
    const out = {};
    try { for (const f of changed) { wovenFindLiteral(f, values[f.id]); out[f.id] = values[f.id]; } }
    catch (e) { setError(e.message); return; }
    if (await onSave(out)) setValues({});
  };
  return html`<div className=${'woven-find-record' + (record.data ? ' is-data' : '')}>
    <div className="woven-find-record-head" title=${file.path + (record.where ? ' > ' + record.where : '')}>
      <${WovenInspectorIcon} name="data"/>
      <strong>${record.title || record.where || 'Record'}</strong>
    </div>
    <div className="woven-find-record-where">${file.path.split('/').pop()}${record.where ? ' · ' + record.where : ''}</div>
    ${record.fields.map(f => html`<label key=${f.id} className=${'woven-find-field' + (f.hit ? ' is-hit' : '')}>
      <span title=${f.key}>${f.key}</span>
      ${f.type === 'boolean'
        ? html`<select value=${values[f.id] ?? f.value} disabled=${disabled} onChange=${e => set(f, e.target.value)}><option value="true">true</option><option value="false">false</option></select>`
        : html`<input value=${values[f.id] ?? f.value} title=${values[f.id] ?? f.value} disabled=${disabled || f.type === 'null'} inputMode=${f.type === 'number' ? 'decimal' : undefined}
            onChange=${e => set(f, e.target.value)} onKeyDown=${e => { e.stopPropagation(); if (e.key === 'Enter') save(); }}/>`}
    </label>`)}
    ${record.more > 0 && html`<small className="woven-find-more">${record.more} more fields not shown</small>`}
    <div className="woven-find-record-foot">
      <span>${record.data ? 'Seed data' : 'Inline data'}, linked to every screen that reads it</span>
      <button type="button" className="woven-find-action" disabled=${disabled || !changed.length} onClick=${save}>Save${changed.length > 1 ? ' ' + changed.length : ''}</button>
    </div>
    ${error && html`<div className="woven-find-notice is-error"><span>${error}</span></div>`}
  </div>`;
}

/* `find` (from the host surface): { branch?, path?, pendingCount,
   onSavePending, onDiscardPending, onSourcesChanged(paths) }. Writes are
   refused while the page has unsaved edits: they would race the replay ops. */
function WovenFindPanel({ doc, onNavigate, find, memo, setFind }) {
  const page = (find && find.path) || doc.querySelector('meta[name="woven-authoring"]')?.content || '';
  const slug = (find && find.branch) || (/^source\/([^/]+)\//.exec(page) || [])[1] || '';
  const root = slug ? 'source/' + slug : '';
  if (memo.root !== root) Object.assign(memo, { root, results: null, excluded: new Set(), collapsed: new Set(), notice: null });
  const [screenIdx, setScreenIdx] = useState(0);
  const onScreen = useMemo(() => wovenFindOnScreen(doc, memo.query, memo.matchCase), [doc, memo.query, memo.matchCase, memo.results]);
  const pending = (find && find.pendingCount) || 0;
  const results = memo.results;
  const stale = !!results && (results.query !== memo.query.trim() || results.matchCase !== memo.matchCase);
  const plural = (n, word) => n + ' ' + word + (n === 1 ? '' : word.endsWith('ch') ? 'es' : 's');

  const search = async (query = memo.query.trim()) => {
    if (!query || !root) return;
    setFind({ busy: true, notice: null });
    try {
      const { files, scanned } = await wovenFindSearch(root, query, memo.matchCase);
      const rank = f => (f.path === page ? 0 : f.records.some(r => r.data) ? 1 : 2);
      files.sort((a, b) => rank(a) - rank(b) || a.path.localeCompare(b.path));
      setFind({ results: { query, matchCase: memo.matchCase, files, scanned }, excluded: new Set(), collapsed: new Set() });
    } catch (e) { setFind({ notice: { error: true, text: e.message } }); }
    finally { setFind({ busy: false }); }
  };
  const afterWrite = async (paths, errors, message) => {
    if (paths.length) try { window.dispatchEvent(new CustomEvent('th:asset-refresh', { detail: { paths } })); } catch {}
    await search(results ? results.query : undefined);
    const text = [message, errors.length ? 'Not written: ' + errors.join(' ') : ''].filter(Boolean).join('. ');
    setFind({ notice: text ? { error: errors.length > 0, text } : null });
    if (paths.length && find && find.onSourcesChanged) find.onSourcesChanged(paths);
  };
  const chosen = results ? results.files.map(file => ({ file, hits: file.hits.filter(h => !memo.excluded.has(h.id)) })).filter(c => c.hits.length) : [];
  const chosenCount = chosen.reduce((n, c) => n + c.hits.length, 0);
  const replace = async () => {
    if (pending || stale || !chosenCount || memo.busy) return;
    const ok = await uiConfirm('Replace ' + plural(chosenCount, 'match') + ' in ' + plural(chosen.length, 'file') + ' with "' + memo.replacement + '"? The files are written directly, no agent.',
      { title: 'Replace in prototype', okLabel: 'Replace' });
    if (!ok) return;
    setFind({ busy: true });
    const done = [], errors = [];
    let count = 0;
    for (const { file, hits } of chosen) {
      try { await wovenFindWrite(file, wovenFindApply(file.text, hits, memo.replacement)); done.push(file.path); count += hits.length; }
      catch (e) { errors.push(e.message); }
    }
    setFind({ busy: false });
    await afterWrite(done, errors, done.length ? 'Replaced ' + count + ' in ' + plural(done.length, 'file') : '');
  };
  const saveRecord = async (file, record, values) => {
    if (pending || memo.busy) return false;
    setFind({ busy: true });
    try {
      await wovenFindWrite(file, wovenRecordApply(file.text, record, values));
      setFind({ busy: false });
      await afterWrite([file.path], [], 'Saved to ' + file.path.split('/').pop() + '. Screens reading this record now show it');
      return true;
    } catch (e) { setFind({ busy: false, notice: { error: true, text: e.message } }); return false; }
  };
  const toggleHit = id => { const ex = new Set(memo.excluded); if (ex.has(id)) ex.delete(id); else ex.add(id); setFind({ excluded: ex }); };
  const toggleFile = file => {
    const ex = new Set(memo.excluded), all = file.hits.every(h => !ex.has(h.id));
    for (const h of file.hits) { if (all) ex.add(h.id); else ex.delete(h.id); }
    setFind({ excluded: ex });
  };
  const toggleOpen = path => { const c = new Set(memo.collapsed); if (c.has(path)) c.delete(path); else c.add(path); setFind({ collapsed: c }); };
  const records = results ? results.files.flatMap(file => file.records.map(record => ({ file, record }))).sort((a, b) => b.record.data - a.record.data) : [];
  const total = results ? results.files.reduce((n, f) => n + f.hits.length, 0) : 0;
  const keys = e => { e.stopPropagation(); };

  return html`<div className="woven-find">
    <div className="woven-find-fields">
      <div className="woven-find-row">
        <input type="search" aria-label="Find text in this prototype" placeholder="Find text in this prototype" value=${memo.query}
          onChange=${e => setFind({ query: e.target.value })} onKeyDown=${e => { keys(e); if (e.key === 'Enter') { e.preventDefault(); search(); } }}/>
        <button type="button" className="woven-find-toggle" aria-pressed=${memo.matchCase} title="Match case" onClick=${() => setFind({ matchCase: !memo.matchCase })}>Aa</button>
        <button type="button" className="woven-find-toggle" aria-pressed=${memo.replaceOpen} aria-label="Replace" title="Replace" onClick=${() => setFind({ replaceOpen: !memo.replaceOpen })}><${WovenInspectorIcon} name="replace"/></button>
      </div>
      ${memo.replaceOpen && html`<div className="woven-find-row">
        <input aria-label="Replace with" placeholder="Replace with" value=${memo.replacement} onChange=${e => setFind({ replacement: e.target.value })} onKeyDown=${keys}/>
        <button type="button" className="woven-find-action" disabled=${!results || stale || !chosenCount || pending > 0 || memo.busy}
          title=${stale ? 'Search first' : 'Write the ticked matches to their files'} onClick=${replace}>Replace${chosenCount && !stale ? ' ' + chosenCount : ''}</button>
      </div>`}
      <div className="woven-find-row woven-find-meta">
        ${onScreen.length
          ? html`<button type="button" className="woven-find-link" title="Select the next one on this screen" onClick=${() => { const i = screenIdx % onScreen.length; setScreenIdx(i + 1); onNavigate(onScreen[i]); }}>${onScreen.length} on this screen</button>`
          : html`<span>${memo.query.trim() ? 'Not on this screen' : ''}</span>`}
        <button type="button" className="woven-find-action" disabled=${!memo.query.trim() || !root || memo.busy} onClick=${() => search()}>${memo.busy ? 'Working...' : 'Search prototype'}</button>
      </div>
    </div>
    ${pending > 0 && html`<div className="woven-find-notice">
      <span>${plural(pending, 'unsaved edit')} on this page. Save or discard before writing files.</span>
      ${find.onSavePending && html`<button type="button" className="woven-find-action" onClick=${find.onSavePending}>Save</button>`}
      ${find.onDiscardPending && html`<button type="button" className="woven-find-action" onClick=${find.onDiscardPending}>Discard</button>`}
    </div>`}
    ${memo.notice && html`<div className=${'woven-find-notice' + (memo.notice.error ? ' is-error' : '')}><span>${memo.notice.text}</span></div>`}
    <div className="woven-find-results">
      ${!root && html`<p className="woven-find-summary">Find works on prototype pages, under source/.</p>`}
      ${results && html`<p className="woven-find-summary">${stale ? 'The text changed. Search again.'
        : total ? plural(total, 'match') + ' in ' + plural(results.files.length, 'file') : 'No matches in ' + plural(results.scanned, 'file') + '.'}</p>`}
      ${!stale && records.length > 0 && html`<div className="woven-find-group">
        <div className="woven-find-heading"><strong>Linked data</strong><span>${records.length}</span></div>
        ${records.map(({ file, record }) => html`<${WovenFindRecord} key=${file.path + '#' + record.key} file=${file} record=${record}
          disabled=${pending > 0 || memo.busy} onSave=${values => saveRecord(file, record, values)}/>`)}
      </div>`}
      ${!stale && results && results.files.length > 0 && html`<div className="woven-find-group">
        <div className="woven-find-heading"><strong>Matches</strong><span>${total}</span></div>
        ${results.files.map(file => {
          const open = !memo.collapsed.has(file.path), included = file.hits.filter(h => !memo.excluded.has(h.id)).length;
          return html`<div key=${file.path} className="woven-find-file">
            <div className="woven-find-file-row" onClick=${() => toggleOpen(file.path)}>
              <span className="woven-layer-chevron" aria-hidden="true">${open ? '⌄' : '›'}</span>
              <span className="woven-find-file-name" title=${file.path}>${file.path.slice(root.length + 1)}</span>
              <span className="woven-find-count">${file.hits.length}</span>
              ${memo.replaceOpen && html`<input type="checkbox" aria-label=${'Replace in ' + file.path} checked=${included === file.hits.length}
                ref=${el => { if (el) el.indeterminate = included > 0 && included < file.hits.length; }}
                onClick=${e => e.stopPropagation()} onChange=${() => toggleFile(file)}/>`}
            </div>
            ${open && file.hits.map(h => html`<label key=${h.id} className="woven-find-hit" title=${'Line ' + h.line + (h.record != null ? ', linked data' : '')}>
              <span className="woven-find-line">${h.line}</span>
              ${h.record != null && html`<${WovenInspectorIcon} name="data"/>`}
              <span className="woven-find-snippet">${h.before}<mark>${h.match}</mark>${h.after}</span>
              ${memo.replaceOpen && html`<input type="checkbox" checked=${!memo.excluded.has(h.id)} onChange=${() => toggleHit(h.id)}/>`}
            </label>`)}
          </div>`;
        })}
      </div>`}
    </div>
  </div>`;
}
