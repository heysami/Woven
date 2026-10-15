/* Find & replace logic of the Layers panel's Find tab (edit-controls.js). */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');

const context = vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'edit-controls.js'), 'utf8') +
  '\n;globalThis.api={wovenFindInSource,wovenFindApply,wovenRecordApply,wovenFindPattern,wovenFindLiteral};', context);
const { wovenFindInSource, wovenFindApply, wovenRecordApply, wovenFindLiteral } = context.api;
// Arrays built inside the vm context belong to another realm; compare plain copies.
const plain = v => JSON.parse(JSON.stringify(v));

// 1. A data.js record: the hit is a field, the record carries its siblings,
//    its path and a short list of literals it owns.
const data = `/* data.js */
(function () {
  const tc = { name: "Ray Charles", initials: "RC", agency: 'Ministry of Health' };
  const programmes = [
    {
      id: "pg-excel",
      name: "Programming Made Easy",
      price: 1500, active: true,
      schedule: ["Day 1: 10:00 AM", "Day 2: 11:00 AM"],
      runs: [{ id: "run-1", trainer: "Lee Wang Ming" }, { id: "run-2", trainer: "Lee Wang Ming" }],
    },
  ];
  // Lee Wang Ming in a comment is not text a screen shows
  const re = /Lee "Wang"/g;
  window.DEMO = { tc, programmes, greeting: \`Hello \${tc.name}, welcome\` };
})();
`;
let found = wovenFindInSource('source/demo/data.js', data, 'ray charles', false);
assert.equal(found.hits.length, 1);
assert.equal(found.records.length, 1);
let rec = found.records[0];
assert.equal(rec.data, true);
assert.equal(rec.where, 'tc');
assert.equal(rec.title, 'Ray Charles');
assert.deepEqual(plain(rec.fields.map(f => f.key)), ['name', 'initials', 'agency']);
assert.equal(rec.fields.find(f => f.hit).key, 'name');

found = wovenFindInSource('source/demo/data.js', data, 'Lee Wang Ming', true);
assert.equal(found.hits.length, 2, 'two runs, the comment is skipped');
assert.equal(found.records.length, 2, 'each run is its own record');
assert.deepEqual(plain(found.records.map(r => r.where)), ['programmes[0].runs[0]', 'programmes[0].runs[1]']);

found = wovenFindInSource('source/demo/data.js', data, 'Day 2', true);
rec = found.records[0];
assert.equal(rec.where, 'programmes[0]', 'a list of literals shows as part of its owning record');
assert.ok(rec.fields.some(f => f.key === 'schedule[1]' && f.hit));
assert.ok(rec.fields.some(f => f.key === 'price' && f.type === 'number'));
assert.ok(rec.fields.some(f => f.key === 'active' && f.type === 'boolean'));

// Template literal parts are searchable, but not records.
found = wovenFindInSource('source/demo/data.js', data, 'welcome', true);
assert.equal(found.hits.length, 1);
assert.equal(found.records.length, 0);

// 2. Editing a record rewrites only its literals, in their own quotes.
found = wovenFindInSource('source/demo/data.js', data, 'Ray Charles', true);
rec = found.records[0];
const name = rec.fields.find(f => f.key === 'name'), agency = rec.fields.find(f => f.key === 'agency');
let next = wovenRecordApply(data, rec, { [name.id]: 'Ray "The Genius" Charles', [agency.id]: "Ministry's Office" });
assert.ok(next.includes('name: "Ray \\"The Genius\\" Charles"'));
assert.ok(next.includes("agency: 'Ministry\\'s Office'"));
assert.equal(next.length - data.length, ('"Ray \\"The Genius\\" Charles"'.length - '"Ray Charles"'.length) + ("'Ministry\\'s Office'".length - "'Ministry of Health'".length));
assert.throws(() => wovenRecordApply(data.replace('Ray Charles', 'Ray Charlez'), rec, { [name.id]: 'X' }), /changed/);
assert.throws(() => wovenFindLiteral({ type: 'number', key: 'price' }, 'abc'), /number/);
assert.equal(wovenFindLiteral({ type: 'number', key: 'price' }, ' 1750 '), '1750');

// 3. Markup: entities, wrapped whitespace, text attributes, inline scripts.
const page = `<!doctype html><html><head><title>Tom &amp; Jerry</title>
<style>.tom-jerry::after { content: "Tom & Jerry"; }</style></head>
<body class="tom">
  <h1 data-th-id="x">Tom &amp;
     Jerry</h1>
  <img src="tom.png" alt="Tom &amp; Jerry">
  <!-- Tom & Jerry -->
  <button title='Tom & Jerry'>Go</button>
  <script>const cast = [{ name: "Tom & Jerry", role: "lead" }];</script>
  <script type="text/plain">Tom & Jerry</script>
</body></html>`;
found = wovenFindInSource('source/demo/index.html', page, 'Tom & Jerry', true);
assert.deepEqual(plain(found.hits.map(h => h.kind)), ['markup', 'markup', 'markup', 'markup', 'string'],
  'title, h1, alt, title attr, script data; never style, comments or plain scripts');
assert.equal(found.records.length, 1);
assert.equal(found.records[0].data, false, 'index.html is not a data file');
assert.equal(found.records[0].where, 'cast[0]');
next = wovenFindApply(page, found.hits, 'Bert & "Ernie"');
assert.ok(next.includes('<title>Bert &amp; "Ernie"</title>'));
assert.ok(next.includes('alt="Bert &amp; &quot;Ernie&quot;"'));
assert.ok(next.includes(`title='Bert &amp; "Ernie"'`));
assert.ok(next.includes('name: "Bert & \\"Ernie\\""'));
assert.ok(next.includes('content: "Tom & Jerry"') && next.includes('<!-- Tom & Jerry -->') && next.includes('<script type="text/plain">Tom & Jerry'));
assert.ok(next.includes('class="tom"'), 'attributes that are code are never rewritten');
assert.throws(() => wovenFindApply(page.replace('<title>', '<title> '), found.hits, 'x'), /changed/);

// 4. Escaped strings re-encode; untouched escapes elsewhere stay as they were.
const js = "const a = 'Don\\'t stop \\u2013 now';\nconst b = 'plain stop';\n";
found = wovenFindInSource('source/demo/app.js', js, 'stop', true);
assert.equal(found.hits.length, 2);
next = wovenFindApply(js, found.hits, 'go');
assert.equal(next, "const a = 'Don\\'t go \\u2013 now';\nconst b = 'plain go';\n", 'only the matched span changes; other escapes stay as written');
found = wovenFindInSource('source/demo/app.js', js, "Don't stop " + String.fromCharCode(0x2013), true);
assert.equal(found.hits.length, 1, 'a hit can span escapes');
assert.equal(wovenFindApply(js, found.hits, 'Keep going,'), "const a = 'Keep going, now';\nconst b = 'plain stop';\n");
found = wovenFindInSource('source/demo/app.js', js, 'stop', true);
next = wovenFindApply(js, [found.hits[1]], "it's");
assert.ok(next.includes("const b = 'plain it\\'s';"), 'only the chosen hit is written, in its own quotes');

// 5. Case: off by default in the panel, honoured when on.
assert.equal(wovenFindInSource('source/demo/app.js', "x = 'SUBMIT'", 'Submit', false).hits.length, 1);
assert.equal(wovenFindInSource('source/demo/app.js', "x = 'SUBMIT'", 'Submit', true).hits.length, 0);

// 6. JSON files are data.
found = wovenFindInSource('source/demo/users.json', '{"users":[{"name":"Ada","role":"admin"}]}', 'Ada', true);
assert.equal(found.records[0].data, true);
assert.equal(found.records[0].where, 'users[0]');

console.log('edit-find: ok');
