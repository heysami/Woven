/* Shared selection tools mounted by workflow and preview inspectors. */
function WovenInspectorIcon({ name }) {
  const paths = {
    plus: 'M8 3v10M3 8h10', close: 'm4 4 8 8M12 4l-8 8',
    copy: 'M5 5h8v8H5zM3 10H2V2h8v1', paste: 'M5 3H3v11h10V3h-2M6 2h4v3H6zM5 8h6M5 11h4',
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
    <select aria-label=${label + ' resizing'} value=${mode === 'auto' ? 'hug' : mode} title="Fixed: use pixels. Hug: fit content. Fill: use the space available in the parent." onChange=${e => onChange(e.target.value, size)}>
      <option value="fixed">Fixed</option><option value="hug">Hug contents</option><option value="fill" disabled=${disabledFill}>Fill container</option>
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
  const instanceId = element && WovenComponents.owner(element)?.getAttribute(WovenComponents.REF);
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
      const result = await WovenEdit.readResponse(response, "Publish component");
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
      <${WovenIconButton} icon="component" label="Create component from selection" disabled=${busy} onClick=${() => publish(false)}/>
    </div>
    <div className="woven-selection-actions">
      <${WovenIconButton} icon="copy" label="Copy" onClick=${() => perform("copy")}/>
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
      ${loadingDs && html`<small>Loading design-system components...</small>`}
      <div className="woven-edit-component-list">
        ${definitions.filter(d => d.name.toLowerCase().includes(query.toLowerCase())).slice(0, 40).map(def => html`
          <button key=${def.id} title=${def.dsId ? "Design system: " + def.dsId : "Project component"}
            onClick=${() => perform("insert-component", { definition: def, position })}>
            <iframe className="woven-edit-component-preview" title=${def.name + " preview"} tabIndex="-1" sandbox="" srcDoc=${preview(def)}/>
            <span>${def.name}</span><small>${def.dsId || "Project"}</small>
          </button>`)}
        ${definitions.length === 0 && html`<small>No components yet. Create one from the selection.</small>`}
      </div>
    </div>`}
    ${current && html`<details className="woven-edit-component woven-inspector-section">
      <summary><${WovenInspectorIcon} name="component"/><strong>${current.name}</strong><span>Instance</span></summary>
      <div className="woven-section-content">
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
          <button onClick=${() => perform("refresh-component", latest || current)}>Update</button>
          <button onClick=${() => perform("reset-component", latest || current)}>Reset overrides</button>
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
    ${error && html`<div role="alert" className="woven-edit-error">${error}<button onClick=${() => setError("")}>Dismiss</button></div>`}
  </div>`;
}

function WovenPropertiesPanel({ picked, styles, computedStyles, onStyle, onMove, onNavigate, cssVars, tree, element, onCommand }) {
  if (!picked || !element) return null;
  const cs = element.ownerDocument.defaultView.getComputedStyle(element);
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
  return html`<div className="woven-inspector" onKeyDown=${e => { if (e.target.matches('input,textarea,select')) e.stopPropagation(); }}>
    <${WovenSelectionTools} element=${element} picked=${picked} onCommand=${onCommand} onStyle=${onStyle}/>
    ${(parentFlex || parentGrid) && html`<section className="woven-inspector-section">
      <div className="woven-section-heading"><strong>Position</strong><span className="woven-section-meta">In ${parentGrid ? 'grid' : 'auto layout'}</span></div>
      <div className="woven-alignment-toolbar">
        ${[['left','h','start'],['center','h','center'],['right','h','end'],['top','v','start'],['middle','v','center'],['bottom','v','end']].map(([icon,axis,value]) => html`<${WovenIconButton} key=${icon} icon=${icon} label=${'Align ' + icon} onClick=${() => align(axis, value)}/>`)}
        <span className="woven-toolbar-separator"/>
        <${WovenIconButton} icon="up" label="Move earlier" onClick=${() => onMove('prev')}/>
        <${WovenIconButton} icon="down" label="Move later" onClick=${() => onMove('next')}/>
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
        <${WovenDimension} axis="w" mode=${styles.widthMode || WovenEdit.sizeMode(element, 'width')} size=${styles.widthFixed ?? (parseFloat(cs.width) || 0)} disabledFill=${parentHugs('width')} onChange=${(mode,value) => size('w',mode,value)}/>
        <${WovenDimension} axis="h" mode=${styles.heightMode || WovenEdit.sizeMode(element, 'height')} size=${styles.heightFixed ?? (parseFloat(cs.height) || 0)} disabledFill=${parentHugs('height')} onChange=${(mode,value) => size('h',mode,value)}/>
      </div>
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

function WovenLayersPanel({ element, onNavigate }) {
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
  return html`<div className="woven-layers" ref=${ref}>
    <div className="woven-layers-header"><strong>Layers</strong><span>${doc.title || 'Page'}</span></div>
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
