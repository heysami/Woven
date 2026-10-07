# Shared contract and brief writer

Every orchestrator delegates contract descriptions and subagent-brief prose to
the shared writer. The originating orchestrator keeps research, creative and
technical decisions, decomposition, constraints, and acceptance criteria.
Do not draft a verbose finished document and then ask another model to repeat it.
Record the necessary decisions once as short notes in the existing contract's
fields. Creativity stays free-form; this protocol imposes no creative schema.
Code still assembles shared boilerplate and exact values without a model call.

The writer runs in its own tool-free model context. Settings > Context and cost
sets the global writer model; every expanded Orchestrators card can override it.
Never copy the orchestration model into a writer request or choose the writer
yourself. The daemon resolves the user's setting. Same-model mode still uses a
separate writing context with low reasoning. No silent model or API fallback.

## Prepare

Save the decision draft in a project-local file separate from the final output.
Keep exact paths, identifiers, tokens, values, approvals, exceptions, commitments,
and acceptance checks in their original fields. Select only descriptive string
fields for writing, using JSON pointers (escape `~` as `~0`, `/` as `~1`).
Unselected fields never reach the writer and are copied exactly by code.
Batch all descriptions and worker briefs for one phase into one request, rather
than starting a writer for each field or each worker. Do not repeat source files,
playbooks, or full research in the selected notes.

POST `$TH_DAEMON_URL/__context/writer/prepare?project=$TH_PROJECT_ID&parent=$TH_RUN_ID`:

```json
{
  "orchestrator": "simulation-orchestrator",
  "draftPath": "workflow/simulation-decisions.json",
  "outputPath": "workflow/simulation-contract.json",
  "format": "json",
  "prosePaths": ["/scene/description", "/workers/0/brief"]
}
```

Use your own orchestrator ID and task-specific paths. A Markdown/plain-text brief
uses `format: "text"`, a `.md` draft/output pair, and `prosePaths: ["/text"]`.
For exact strings embedded in prose, quote them; prefer structured fields for
binding requirements. Plain-text briefs require careful semantic review since
their requirements cannot be protected by field boundaries.

For a revision include `previousHash`, the digest of the current output value:
SHA-256 of UTF-8 JSON with sorted keys, `ensure_ascii=False`, and separators
`(',', ':')`. For text, the value is the entire string, including final newline.
A repeat with identical decisions, model, and output revision reuses its review.

The response returns `reviewPath`, `reviewHash`, `decisionsPath`, `model`, and
only the changed prose entries (`path`, `before`, `text`). The final artifact has
not been written. The full decision draft remains on disk, including on failure.

## Review and publish

Review the returned edits against your decisions. Preserve every condition,
relationship, exception, and unresolved choice. Reject an edit that changes meaning
by leaving its path out of `acceptedPaths`; its original wording survives. This
is an orchestrator review, not another user approval gate. Do not rerun research
or reread unchanged boilerplate merely to approve wording.

POST `$TH_DAEMON_URL/__context/writer/publish?project=$TH_PROJECT_ID`:

```json
{
  "reviewPath": "workflow/writing/<receipt-id>/review.json",
  "reviewHash": "<from prepare>",
  "acceptedPaths": ["/scene/description"]
}
```

An explicit empty list retains every original description. The daemon validates
the saved review and source revision, applies only accepted edits, and writes the
final artifact atomically. Concurrent output changes return 409; reread and prepare
a new revision. Invalid writing returns an error with the decisions retained;
do not silently bypass the writer or switch to a larger model.

Art direction publishes to `workflow/art-direction-contract.json` through this
same path. Its existing schema validation, shared-field assembly, and plate/crop
existence checks also run. Select its narrative fields; do not select palette,
font resolution, references, promised formats, or approved exceptions.

Use the published path and hash in worker envelopes. Include required scope,
recipient, and acceptance checks. If a node requires the brief in its text,
read the published brief and insert that text without rewriting it. The writer
is a drafting service, not an orchestrator: it cannot run tools, choose assets,
change a pipeline, waive QA, or approve its own wording.
