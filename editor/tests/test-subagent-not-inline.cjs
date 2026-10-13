/* A subagent's own work (its tool calls, the images it Reads, its text) is
   never drawn inline in the thread: it belongs to its Tasks & subagents
   entry. The visual-qa subagent read 300 images in a suss-cal thread, and
   every one showed up in the transcript as if the thread had read it. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const app = fs.readFileSync(path.join(__dirname, '../app.js'), 'utf8');
const start = app.indexOf('function buildBlocks(events) {');
const src = app.slice(start, app.indexOf('\n}\n', start) + 2);
const buildBlocks = new Function(src + '\nreturn buildBlocks;')();

const ev = data => ({ event: 'agent', data });
const blocks = buildBlocks([
  ev({ type: 'text_delta', delta: 'Checking the screens.' }),
  ev({ type: 'tool_use', id: 'a1', name: 'Agent', input: { subagent_type: 'woven:visual-qa', description: 'Visual QA' } }),
  ev({ type: 'tool_use', id: 'r1', name: 'Read', input: { file_path: '/x/sheet_01.png' }, sidechain: true, parentToolUseId: 'a1' }),
  ev({ type: 'tool_result', toolUseId: 'r1', content: [{ type: 'image' }], sidechain: true, parentToolUseId: 'a1' }),
  ev({ type: 'text_delta', delta: 'subagent thinking out loud', sidechain: true }),
  ev({ type: 'tool_use', id: 'b1', name: 'Bash', input: { command: 'ls' } }),
]);
const kinds = blocks.map(b => b.kind);
assert.ok(!blocks.some(b => b.kind === 'tool' && b.toolUse && b.toolUse.name === 'Read'), 'no subagent Read in the thread');
assert.ok(!JSON.stringify(blocks).includes('subagent thinking out loud'), 'no subagent text in the thread');
assert.ok(blocks.some(b => b.kind === 'tool' && b.toolUse.name === 'Bash'), "the thread's own tools still show");
assert.ok(kinds.includes('agent_grid'), 'the dispatch itself is still there');
console.log('PASS: a subagent\'s reads and text stay out of the thread.');
