// Plan-mode split fan-out (app.js spawnPlanSplitRuns), with fetch mocked.
//
// Regressions from suss-cal: one shared PLAN_SPLIT.json let a plan's click
// open ANOTHER plan's threads (2026-10-02, three plans at once), and the
// split refused nothing about overlapping claims (2026-09-29/30).
//
// Run: node editor/tests/test-plan-split-client.cjs
const fs = require("fs");
const path = require("path");
const assert = require("assert");

const src = fs.readFileSync(path.join(__dirname, "..", "app.js"), "utf8");
const start = src.indexOf("async function spawnPlanSplitRuns(");
const fnSrc = src.slice(start, src.indexOf("\n}\n", start) + 3);

const RUN_START = 1790900000;   // the planning run's startedAt (epoch s)
const httpDate = (s) => new Date(s * 1000).toUTCString();

function harness({ perRun, legacy, legacyAt }) {
  const posts = [];
  const fetch = async (url, opts) => {
    if (url.startsWith("/plan-splits/plan1.json"))
      return perRun ? { ok: true, text: async () => JSON.stringify(perRun) } : { ok: false, status: 404 };
    if (url.startsWith("/PLAN_SPLIT.json"))
      return legacy ? { ok: true, headers: { get: () => httpDate(legacyAt) },
                        text: async () => JSON.stringify(legacy) } : { ok: false, status: 404 };
    if (url.startsWith("/__run/plan1")) return { ok: true, json: async () => ({ startedAt: RUN_START + 0.4 }) };
    posts.push(JSON.parse(opts.body));
    return { ok: true, json: async () => ({ runId: "r" + posts.length }) };
  };
  const fn = new Function("apiUrl", "fetch", fnSrc + "\nreturn spawnPlanSplitRuns;")((p) => p + "?project=x", fetch);
  return fn("plan1").then((o) => ({ ok: true, o, posts }), (e) => ({ ok: false, e: e.message, posts }));
}

const item = (title, owns) => ({ title, owns, brief: "b" });

(async () => {
  // 1. The plan's own manifest wins, even when the shared file holds another plan.
  let r = await harness({ perRun: { items: [item("Mine", ["a.html"])] },
                          legacy: { items: [item("Other plan", ["z.html"])] }, legacyAt: RUN_START + 99 });
  assert.ok(r.ok, r.e);
  assert.deepStrictEqual(r.posts.map((p) => p.title), ["Mine"]);

  // 2. Legacy shared file: accepted only when written during this run.
  r = await harness({ legacy: { items: [item("Legacy", ["a.html"])] }, legacyAt: RUN_START + 30 });
  assert.ok(r.ok, r.e);
  r = await harness({ legacy: { items: [item("Stale", ["a.html"])] }, legacyAt: RUN_START - 3600 });
  assert.ok(!r.ok && /no split manifest from this plan/.test(r.e) && r.posts.length === 0, r.e);
  r = await harness({});
  assert.ok(!r.ok && r.posts.length === 0);

  // 3. One group: shared id, claims normalised, siblings see each other.
  r = await harness({ perRun: { items: [
    item("Award date", ["form.html#awardDueCard()", "model.js#validators: award date"]),
    item("Quota copy", ["./form.html#quota field", "model.js#labels: quota"]),
    item("Components", ["form.html#componentForm()"])] } });
  assert.ok(r.ok, r.e);
  assert.strictEqual(new Set(r.posts.map((p) => p.split.id)).size, 1);
  assert.deepStrictEqual(r.posts[1].split.items[1].owns, ["form.html#quota field", "model.js#labels: quota"]);
  assert.deepStrictEqual(r.posts.map((p) => p.split.index), [0, 1, 2]);

  // 4. Collisions are refused before any thread opens.
  for (const [a, b] of [[["f.html"], ["./f.html"]], [["f.html"], ["f.html#x()"]],
                        [["f.html#x()"], ["f.html"]], [["f.html#X()"], ["f.html#x()"]]]) {
    r = await harness({ perRun: { items: [item("A", a), item("B", b)] } });
    assert.ok(!r.ok && /both claim/.test(r.e) && r.posts.length === 0, `${a} vs ${b}: ${r.e}`);
  }
  // 5. The mark that tells the planning thread, its split items and the check
  //    apart: an existing icon (no pill), plus "2/3" on a split item.
  const bStart = src.indexOf("function planRoleBadge(");
  const Icon = { DocPencil: "DocPencil", Fork: "Fork", CheckList: "CheckList" };
  const badge = new Function("Icon", src.slice(bStart, src.indexOf("\n}\n", bStart) + 3) + "\nreturn planRoleBadge;")(Icon);
  assert.strictEqual(badge({ planRole: { role: "plan" } }).icon, "DocPencil");
  const sp = badge({ planRole: { role: "split", index: 1, count: 3, parentTitle: "offers" } });
  assert.deepStrictEqual([sp.icon, sp.count, sp.label], ["Fork", "2/3", "Split 2 of 3"]);
  assert.ok(sp.title.includes('"offers"'));
  const one = badge({ planRole: { role: "split", index: 0, count: 1, parentTitle: "under scheme config :\nunder monitoring" } });
  assert.strictEqual(one.count, undefined);
  assert.ok(!one.title.includes("\n") && !one.title.includes("other items"), one.title);
  assert.strictEqual(badge({ planRole: { role: "check" } }).icon, "CheckList");
  assert.strictEqual(badge({ planRole: null }), null);
  assert.strictEqual(badge({}), null);
  console.log("PASS: per-run manifest, guarded legacy fallback, one group, region claims, collisions refused, role icons");
})().catch((e) => { console.error("FAIL", e.message || e); process.exit(1); });
