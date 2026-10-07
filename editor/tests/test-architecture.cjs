/* Execute the production Architecture model and handlers with isolated IO. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const app = fs.readFileSync(path.join(__dirname, '../app.js'), 'utf8');
const appStart = app.indexOf('function App() {');
function source(start, end, offset = 0) {
  const a = app.indexOf(start, offset), b = app.indexOf(end, a);
  assert.ok(a >= 0 && b > a, 'Production handler markers must exist: ' + start);
  return app.slice(a, b);
}
function context(globals, code) {
  const ctx = vm.createContext(globals);
  vm.runInContext(code, ctx);
  return ctx;
}
const plain = value => JSON.parse(JSON.stringify(value));
const model = context({ modelUid: () => 'generated', snapToCell: () => ({ col: 0, row: 0 }) },
  source('function applyModelEdits(D, edits) {', '/* ────────── Type-sample renderer'));
const data = {
  meta: { sourceRoot: '../source/alternate/', lanes: [{ id: 'user', label: 'User' }] },
  entities: [{ id: 'Record', fields: [{ name: 'name', type: 'string' }] }, { id: 'Group', fields: [] }],
  frames: [{ id: 'home', label: 'Home', kind: 'page', col: 0, row: 0, entities: ['Record'] },
    { id: 'detail', label: 'Details', kind: 'page', parent: 'home', col: 1, row: 0 }],
  links: [{ id: 'owns', from: 'Group', to: 'Record', cardinality: '1:N', label: 'Contains' }],
  arrows: [{ id: 'open', from: 'home', to: 'detail', action: 'Open' }],
  stateMachines: [{ id: 'life', states: [{ id: 'draft' }, { id: 'done' }], transitions: [{ from: 'draft', to: 'done', on: 'Save' }] }],
  timelines: [{ id: 'reminder', events: [{ id: 'send', at: 'T+1d' }] }],
  grids: [{ id: 'access', cells: [{ row: 'name', col: 'draft', render: 'editable' }] }],
};
const pristine = JSON.stringify(data);
const baseline = model.applyModelEdits(data, []);
assert.deepEqual(plain(baseline.links), data.links);
assert.deepEqual(plain(baseline.framesEntities.home), ['Record']);
assert.equal(baseline.framesRank.get('detail'), 1);
const renamed = model.applyModelEdits(data, [{ target: 'entity', kind: 'rename', entityId: 'Record', newId: 'Item' }]);
assert.equal(renamed.links[0].to, 'Item');
assert.deepEqual(plain(renamed.framesEntities.home), ['Item']);
assert.deepEqual(plain(renamed.frames[0].entities), ['Item']);
const detached = model.applyModelEdits(data, [{ target: 'ia', kind: 'entity.unassign', frameId: 'home', entityId: 'Record' },
  { target: 'link', kind: 'delete', id: 'owns' }]);
assert.equal(detached.links.length, 0);
assert.equal(detached.framesEntities.home.length, 0);
const deleted = model.applyModelEdits(data, [{ target: 'entity', kind: 'delete', entityId: 'Record' }]);
assert.equal(deleted.links.length, 0);
assert.equal(deleted.frames[0].entities.length, 0);
const updated = model.applyModelEdits(data, [{ target: 'link', kind: 'update', id: 'owns', label: 'Owns' },
  { target: 'stateMachine', kind: 'transition.rename', machineId: 'life', fromId: 'draft', toId: 'done', matchOn: 'Save', newOn: 'Finish' }]);
assert.equal(updated.links[0].label, 'Owns');
assert.equal(updated.stateMachines[0].transitions[0].on, 'Finish');
assert.equal(updated.timelines[0].events[0].at, 'T+1d');
assert.equal(updated.grids[0].cells[0].render, 'editable');
const added = model.applyModelEdits(data, [{ target: 'frame', kind: 'add', frame: { id: 'new', entities: ['Group'] } },
  { target: 'arrow', kind: 'split', arrowId: 'open', newFrame: { id: 'middle', entities: ['Record'] } }]);
assert.deepEqual(plain(added.framesEntities.new), ['Group']);
assert.deepEqual(plain(added.framesEntities.middle), ['Record']);
assert.equal(JSON.stringify(data), pristine, 'Editing must not mutate boot data');

const bootCode = source('function isEditorBootDataPath(', '// Resolve the editor data file');
const boot = context({}, bootCode);
for (const file of ['editor/data.js', 'editor/alternate.data.js', '/project/editor/alternate.data.js',
  'C:\\project\\editor\\alternate.data.js', 'editor/design-systems/suss.js', 'editor/branches/main.js']) {
  assert.equal(boot.isEditorBootDataPath(file), true, file);
}
for (const file of ['editor/app.js', 'source/alternate/data.js', 'workflow/workflow.json', null]) {
  assert.equal(boot.isEditorBootDataPath(file), false, String(file));
}
// Exercise both actual consumers, not just the path helper.
let reloads = 0;
const history = context({ useCallback: fn => fn, onAfterRestore: undefined,
  isEditorBootDataPath: boot.isEditorBootDataPath, setTimeout: fn => fn(),
  window: { location: { reload: () => reloads++ } } },
  source('  const applyRestoreSideEffects = useCallback(', '  const step = useCallback(') + '\nthis.restore = applyRestoreSideEffects;');
history.restore(['editor/alternate.data.js'], 'Undo layout');
assert.equal(reloads, 1);
const session = new Map();
const completion = context({ useCallback: fn => fn, setRunFinished: () => {}, setLastRun: () => {}, saveSettings: () => {},
  isEditorBootDataPath: boot.isEditorBootDataPath, sessionStorage: { getItem: k => session.get(k), setItem: (k, v) => session.set(k, v) },
  window: { location: { reload: () => reloads++ } }, document: { querySelectorAll: () => [] } },
  source('  const handleRunComplete = useCallback(', '  // On startup, see if a prior run', appStart) + '\nthis.complete = handleRunComplete;');
const done = { runId: 'generated', status: 'done', didModifyFiles: true, modifiedPaths: ['editor/alternate.data.js'] };
completion.complete(done);
completion.complete(done);
assert.equal(reloads, 2, 'Generation refreshes once; replay must not loop');

async function main() {
  const submitCode = source('  const submit = async () => {', '  const updateSource = async () => {', appStart);
  for (const state of [{ chatRun: { runId: 'finished', done: true }, runFinished: true },
    { chatRun: { isNew: true }, runFinished: false },
    { chatRun: { runId: 'busy' }, runFinished: false, blocked: true },
    { chatRun: null, runFinished: true, agentBusy: true, blocked: true }]) {
    const events = [];
    const globals = { ...state, agentBusy: state.agentBusy || false, capturing: false,
      edits: [{ target: 'frame', kind: 'rename', frameId: 'home', newLabel: 'Workspace' }], strokes: {},
      D: { meta: { project: 'Fixture', sourceRoot: '../source/alternate/' } },
      setCapturing: () => {}, captureAnnotations: async () => ({ annotations: [], failures: [] }),
      saveFile: async (file, contents) => { events.push({ file, contents }); return { server: true }; },
      triggerRun: async opts => { events.push(opts); return { runId: 'next' }; },
      activePrototypeSlug: () => 'alternate', agentId: 'codex', permissionMode: 'test',
      setChatRun: () => {}, setLastRun: () => {}, setRunFinished: () => {}, saveSettings: () => {}, setEdits: () => {}, console };
    const c = context(globals, source('  const runActive = ', '  const permissionMode = ', appStart) + submitCode + '\nthis.submit = submit;');
    await c.submit();
    if (state.blocked) assert.equal(events.length, 0);
    else {
      assert.equal(events.length, 2);
      assert.equal(events[0].file, 'edits.json');
      assert.equal(JSON.parse(events[0].contents).sourceRoot, '../source/alternate/');
      assert.equal(events[1].branch, 'alternate');
      assert.equal(events[1].prototype, 'alternate');
    }
  }

  const generationCode = source('async function requestViewGeneration(', 'function GenerateRequestButton(');
  for (const [kind, filename] of Object.entries({ stateMachine: 'STATEMACHINE_REQUEST.md', timeline: 'TIMELINE_REQUEST.md', grid: 'GRID_REQUEST.md' })) {
    const events = [];
    const c = context({ activePrototypeSlug: () => 'alternate', editorDataTargetInstruction: slug => `Resolve editor/${slug}.data.js`,
      loadChatGuards: () => ({ visual: true }), saveFile: async (file, body) => { events.push({ file, body }); return { server: true }; },
      triggerRun: async opts => { events.push(opts); return { runId: 'generated' }; } }, generationCode);
    const result = await c.requestViewGeneration(kind, 'Write source/prototype.json and editor/data.js.');
    assert.equal(events[0].file, filename);
    assert.ok(events[0].body.includes('source/alternate/prototype.json'));
    assert.ok(events[0].body.includes('editor/alternate.data.js'));
    assert.ok(!events[0].body.includes('Write source/prototype.json'));
    assert.equal(events[1].branch, 'alternate');
    assert.equal(events[1].prototype, 'alternate');
    assert.equal(events[1].prompt, events[0].body);
    assert.equal(result.run.runId, 'generated');
    c.saveFile = async () => ({ cancelled: true });
    assert.equal((await c.requestViewGeneration(kind, '')).cancelled, true);
    c.saveFile = async () => ({ server: false });
    assert.equal((await c.requestViewGeneration(kind, '')).manual, true);
    assert.equal(events.length, 2, 'Cancelled/downloaded requests must not spawn');
    c.saveFile = async () => ({ server: true });
    c.triggerRun = async () => { throw new Error('runtime unavailable'); };
    await assert.rejects(c.requestViewGeneration(kind, ''), /Request saved.*runtime unavailable/);
  }

  const opened = [];
  const generation = context({ useRef: value => ({ current: value }), useCallback: fn => fn, runActive: false, agentBusy: false,
    requestViewGeneration: async () => ({ ok: true, run: { runId: 'new-generation' } }),
    setChatRun: run => opened.push(run.runId), setLastRun: () => {}, setRunFinished: value => assert.equal(value, false), saveSettings: () => {} },
    source('  const generationPending = useRef(', '  // Spawn Workflow 6', appStart) + '\nthis.generate = generateView;');
  await generation.generate('grid', 'fixture');
  assert.deepEqual(opened, ['new-generation'], 'Generation opens progress in the Architecture chat');
  generation.agentBusy = true;
  assert.equal((await generation.generate('timeline', '')).cancelled, true);

  console.log('PASS: persisted model, cascades, Undo/Redo, regeneration refresh, submission, prototype scope, all three generation requests, failure/cancel/manual paths, and chat handoff');
}
main().catch(error => { console.error(error); process.exitCode = 1; });
