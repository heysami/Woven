/* Woven's own Visual QA (the daemon's turn-end check) as a Tasks & subagents
   entry: visual_qa events merged by id, running then done, carrying the
   criteria, the activity, every answer and the report link. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const app = fs.readFileSync(path.join(__dirname, '../app.js'), 'utf8');
function slice(name) {
  const start = app.indexOf('function ' + name + '(');
  assert.ok(start >= 0, 'missing ' + name);
  return app.slice(start, app.indexOf('\n}\n', start) + 2);
}
const { extractRunSubagents } = new Function(
  slice('visualQaAgent') + slice('extractRunSubagents') + 'return { extractRunSubagents };')();

const ev = (data) => ({ event: 'agent', data });
const running = ev({ type: 'visual_qa', id: 'vqa-1', status: 'running', label: 'Visual QA · a.html',
  actions: ['Opening a.html in a headless browser'] });
let [a] = extractRunSubagents([running]);
assert.equal(a.type, 'visual-qa');
assert.equal(a.done, false);
assert.equal(a.jobStatus, 'running');

const done = ev({ type: 'visual_qa', id: 'vqa-1', status: 'completed',
  label: 'Visual QA · a.html · pass · visual checks: 0 sure yes, 1 sure no, 0 unsure (shadow)',
  prompt: 'Criteria asked:\n- org_field: The image shows a text field.',
  actions: ['Opened a.html', 'Asked clef 1 question(s) in 1 call(s), 0.9 s'],
  result: 'SURE NO  org_field', report: '/__qa/visual-report?id=20261013-000000-abcdef' });
const all = extractRunSubagents([running, done]);
assert.equal(all.length, 1, 'one entry per page run, not one per event');
[a] = all;
assert.equal(a.done, true);
assert.equal(a.error, false);
assert.equal(a.result, 'SURE NO  org_field');
assert.equal(a.report, '/__qa/visual-report?id=20261013-000000-abcdef');
assert.deepEqual(a.actions, ['Opened a.html', 'Asked clef 1 question(s) in 1 call(s), 0.9 s']);
assert.match(a.label, /1 sure no/);

const failed = extractRunSubagents([ev({ type: 'visual_qa', id: 'vqa-2', status: 'failed', label: 'x' })]);
assert.equal(failed[0].error, true);
console.log('PASS: Visual QA runs are Tasks & subagents entries with their report.');
