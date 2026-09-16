# Context and cost controls

Open **Settings > Context and cost**. The section uses Woven's existing settings
components, typography, colors, and controls. Its preferences persist through the
daemon and apply across this installation. The context popover retains a quick
compaction control and points here for model settings.

## Which task uses which model

| Work | Behavior |
| --- | --- |
| Setup to prototype work | Summary model, with scope, checks, model, and runtime transferred |
| Changing QA settings | Same summary model and state transfer |
| Compaction | Same summary model; messages arriving during generation remain outside its coverage boundary |
| Normal resume | Saved session or replay, without a new summary call |
| Worker briefs | Assigned task model; recipient-specific decisions and artifact paths |
| Agent playbooks | Orchestrators retain routing judgment; drawers receive leaf context; art direction loads its current phase |
| Research and creative handoffs | Assigned creative model; reference saved work instead of repeating it |
| Art contract assembly | Code fills shared fields and preserves all supplied creative values exactly; no formatting model call |

**Fast** uses `gpt-5.6-luna` with low reasoning for Codex and `claude-haiku-4-5`
for Claude. **Same model as thread** preserves the chosen model. Summary failures
retain the conversation, with no silent switch to a larger model or paid API.
Claude's summary request replaces the coding system prompt, disables tools and
MCP, and isolates the fast model from user settings. The fast Codex request omits
user tool configuration, disables tool features, and uses an ephemeral scratch
session. Explicit inherit mode continues to honor the runtime's model settings.

Summary prose targets 400-700 words for long histories, fewer for short ones.
Each fact should appear once. Tool-call-shaped output is rejected; summary
headings do not certify assistant claims as independently verified results.
No summarizer provides a mathematical guarantee of semantic fidelity. The full
conversation remains in its original event log.

## What is smaller

- Full bound `DESIGN.md` appears once during generation and QA when DS QA is on,
  with no size cutoff. DS QA off omits the full catalog and automatic DS drift
  gate; the DS binding and vocabulary still apply.
- Normal chat uses the smaller existing model, endpoint, and node catalogs.
  Setup retains the routing rules needed for judgment.
- Delegated drawers use leaf context. Orchestrators retain setup context.
  Exact subagent model overrides, prototype scope, and checks survive dispatch
  and resume. A build card no longer changes the prompt tier by itself.
- Transcript replay retains the checkpoint and user messages. Large file bodies
  become paths and fingerprints. Omitted observations are labeled.
- Identical canvas inputs from the same source/version/payload are emitted once.
  Different sources or changed payloads remain separate. Typed outputs share one
  schema per type while retaining every destination ID.
- Art direction has separate plate, finalize, schema, and optional motion files.
  Creative descriptions remain free-form. Approval, crop inspection, typography
  reconciliation, medium commitments, and the final quality gate remain required.
- Contract assembly preserves custom fields, exact tokens, references, and long
  creative descriptions. It checks required decision groups and reference files,
  writes atomically, and rejects stale revisions. Handoffs return paths and hashes
  instead of copying the contract and its consumer instructions.

## References and QA

**Reuse unchanged reference extractions** caches successful image descriptions by
image contents, exact request, provider, model, and options. `refresh: true` forces
new extraction. Disabling reuse bypasses the cache.

Figma workers can reuse task-specific notes through the project-local reference
endpoint after verifying the same immutable file version and node ID. An unknown
revision requires a fresh extraction. This is a worker protocol, not interception
of external MCP traffic. The actual Figma connector was not exercised in this
implementation test. Details: [reference protocol](../agents/context-artifacts.md).

**Concise QA results** executes the same checks, retains failures, skipped and
unknown results, metrics, and frame references, and returns brief passing-case
receipts. The full report and canonical hash are returned as `evidence`. Request
`detail=full` or disable the preference for the complete inline response. Failure
to save a compact report falls back to returning the full result. QA verdicts are
never reused as if a fresh check had run.

Repair briefs carry current failures, evidence, changed files, and acceptance
checks. They report new/resolved findings after repair and keep required final
checks. Creative and QA judgment models are unchanged.

## Verification on 2026-09-16

- 28 context regressions cover settings persistence and validation, scoped
  dispatch/resume, full catalogs across six profiles, handoff reuse, late messages,
  file-body suppression, CLI options, reference invalidation, image-description
  cache hits and refresh, lossless contracts, concurrent revision protection,
  complete QA evidence, and phase-specific playbook loading.
- JavaScript composer checks, seven existing history checks, two routing checks,
  syntax checks, and diff whitespace checks pass.
- Browser review verified the new section at desktop and narrow widths, all
  choices saving, and values surviving reload. Review uses a disposable project
  and separate settings. No real project or global preference was modified.
- A live Luna trial returned a 126-word state summary in 10.1 seconds and reported
  3,561 tokens. It retained the budget, scoped path, approval ID, plate path, DS
  toggle, typography exception, accessibility constraints, 3D commitment, clipping
  defect, pending video approval, and unverified camera testing.
- The first Haiku trial exposed coding-role leakage. Replacing the system prompt
  fixed it. The revised trial returned an 81-word summary in 9.8 seconds with the
  same critical facts. Its overly confident heading led to the deterministic
  reported-state heading correction and a regression test. These are small
  synthetic smoke tests, not a full design-quality or billed-cost benchmark.

The unrelated existing `python3 -m editor.kinds.test_io_contract` failure remains
at `test_layer_specs_flow_through_layer_except_no_layer_position_hosts` for
`layer-group.pos`, `.trigger`, and `.effect`. Its registry and test are unchanged.

## Measured prompt sizes

Compared with commit `1f3c88f`, using a synthetic project, empty provider/default
availability, and no bound DS:

| Capability preamble | Before characters | After characters | Change |
| --- | ---: | ---: | ---: |
| Normal chat | 92,034 | 69,207 | 24.8% smaller |
| Delegated drawer, previously full | 249,507 | 58,449 | 76.6% smaller |
| Setup orchestrator | 248,676 | 250,064 | 0.6% larger, common writing/reuse guidance added |

Art direction's common plus plate-phase instructions are about 33,200 characters,
compared with the previous 77,448-character monolith. Finalization retrieves its
schema separately; motion instructions load only when eligible and approved.
These are character counts, not billed tokens or total build savings. Images,
reasoning, model output, tool schemas, and provider caching add to total cost.

## Test the complete flow

Restart the normal Woven daemon and refresh the editor before trying these backend
changes in your own projects. Existing model sessions retain their old instructions
until a new session or handoff. The isolated review page already uses the new code;
it permits settings and artifact testing but blocks model dispatches.

1. Open Settings > Context and cost. Try both summary choices, reference reuse,
   concise QA, and the compaction threshold. Reload and verify the saved values.
2. In a disposable prototype, record a specific constraint and approved direction.
   Make an edit with DS QA on, then turn it off and send the next edit. The new
   thread must retain scope, checks, model, and the decision.
3. Compact a chat and send a follow-up while the summary runs. The follow-up must
   remain after the summary boundary. Try setup-to-working handoff as well.
4. Describe the same image twice with the same request: the second response has
   `cacheHit: true`. Change the image or request and verify another extraction.
5. Finalize an approved plate. Inspect the assembled contract and concise receipt.
   Run QA with concise results on and compare its evidence file with `detail=full`.

Repeat automated checks from the repository root:

```sh
python3 -m unittest discover -s editor/tests -p 'test_context*.py' -v
node editor/tests/test-context-policy.cjs
python3 editor/tests/test_chat_rehydrate.py
python3 editor/kinds/test_routing.py
python3 -m py_compile editor/serve.py editor/context_policy.py editor/context_artifacts.py editor/kinds/capabilities.py
node --check editor/app.js
node --check editor/context-policy.js
git diff --check
```
