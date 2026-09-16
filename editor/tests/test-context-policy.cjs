const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");
const policy = require("../context-policy.js");

const source = { sourceId: "brief", sourceVersion: "v1", kind: "text", label: "Direct", text: "Approved copper" };
const inputs = policy.dedupeInputs([source, { ...source, label: "Via section" },
  { ...source, sourceVersion: "v2" }, { ...source, sourceId: "other" },
  { ...source, text: "Updated constraint" }]);
assert.equal(inputs.length, 4);
assert.equal(inputs[0].label, "Direct / Via section");
assert.equal(policy.dedupeInputs([{ text: "same" }, { text: "same" }]).length, 2);
const options = policy.handoffOptions({ branch: "atlas", prototype: "atlas", tier: "scoped",
  guards: { dsGuard: true }, model: "chosen", agent_id: "codex" }, { guards: { dsGuard: false } });
assert.equal(options.prototype, "atlas");
assert.equal(options.tier, "scoped");
assert.equal(options.model, "chosen");
assert.equal(options.agentId, "codex");
assert.equal(options.guards.dsGuard, false);
const working = policy.handoffOptions({ branch: "main", agent_id: "codex" },
  { prototype: "atlas", tier: "normal" });
assert.equal(working.branch, "atlas");
assert.equal(working.model, "codex-default");

// Exercise the actual UI composer without loading React or starting a run.
const app = fs.readFileSync(path.join(__dirname, "../app.js"), "utf8");
const begin = app.indexOf("function workflowComposeAgentPrompt(");
const end = app.indexOf("\n// Per-target-type schemas", begin);
const context = { WovenContext: policy,
  AGENT_OUTPUT_SCHEMAS: { typography: '{ "fontFamily": "SCHEMA_SENTINEL" }' },
  AGENT_OUTPUT_GUIDANCE: { typography: "Use the committed font." } };
vm.createContext(context);
vm.runInContext(app.slice(begin, end), context);
const prompt = context.workflowComposeAgentPrompt({ wiredInputs: [source, { ...source, label: "Via section" }],
  wiredOutputs: ["a", "b"].map(id => ({ targetNodeId: id, targetType: "typography", label: id })),
  userText: "Keep it concise." });
assert.equal(prompt.split("Approved copper").length - 1, 1);
assert.equal(prompt.split("SCHEMA_SENTINEL").length - 1, 1);
assert.ok(prompt.includes('"targetId": "a"'));
assert.ok(prompt.includes('"targetId": "b"'));
console.log("PASS: input identity/version, aliases, handoff scope/model/checks, actual typed-output composer");
