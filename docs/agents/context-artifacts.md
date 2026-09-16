# Reusing reference observations

Keep raw images and Figma dumps out of a long-lived conversation when a worker
can inspect them. Return the facts needed for the current task and their source.
Preserve uncertainty, exact measurements, token names, constraints, and exceptions.
Do not paraphrase the same extraction again in each downstream brief.

Before extracting a local reference, POST `/__context/reference?project=<id>`:

```json
{"action":"get","inputPath":"attachments/reference.png","request":"Exact extraction task, including the required detail and scope"}
```

The daemon hashes the file contents. A hit returns the prior `value`. If the task
needs a detail it does not contain, change the request to include that detail and
inspect the source. After a successful extraction, POST the same fields with
`action: "put"` and `value` containing the observations and evidence paths. A
new source image, different task, or disabled reuse yields a miss. Do not cache
errors, guesses, incomplete retrievals, or visual QA verdicts as source facts.

For Figma, use `source` containing the file key AND node ID, `revision` containing
the verified immutable file version, and the exact `request`. Include extraction
options and any design-system version the interpretation depends on in `request`.
Verify the current version through Figma metadata before lookup, unless the user
linked an immutable version. An unversioned URL, local timestamp, or remembered
revision does not prove freshness. If the MCP cannot expose a reliable revision,
fetch again. Do not invent a revision to obtain a cache hit. Raw MCP payloads stay
in the extracting worker; store only its task-specific structured observations.
The daemon cannot intercept external MCP calls, so the worker performs this lookup.

The image-description endpoint (`/__llm_run`, skill `describe`) caches successful
results automatically by image contents, prompt, provider, model, and options.
Pass `refresh: true` to re-extract; Settings > Context and cost can disable reuse.
Cache files are project-local under `workflow/context-cache/`. Deleting that
directory clears the notes; source files and model choices are unaffected.

# QA evidence and repair handoffs

`/__qa/run` still executes the full required battery. With concise QA results on,
passing cases return small receipts. Failure details, frame paths, metrics, and
unknown/skipped results remain available. `evidence.path` is the complete report,
with a canonical JSON SHA-256. Use `detail=full` when the whole response is needed.
Read actual frames for visual judgments, including passing case frame references.

For repair handoffs, send current failures with their evidence paths, the files
changed, and the acceptance checks. Cite the saved report for prior passing work.
After repair, return new/resolved findings and the fresh report path. Do not copy
every previous report into another prompt. Re-run affected checks and all checks
required by the final gate; reuse of source observations never waives those checks.
