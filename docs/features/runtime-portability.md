# Model routing and CLI portability

Implemented 2026-09-17. The model registry, helper policies, job tracking, and
review evidence changes apply on daemon restart. The Codex app-server and
OpenCode HTTP transports are opt-in previews; existing CLI command transports
remain the defaults.

## Add models without editing code

Open **Settings > Context and cost > Models and economy presets**. Choose the
runtime and **Add model**, then enter the exact ID accepted by that CLI. For
example, register `gpt-6-astra` under Codex. For Fable, use the exact ID supplied
by the runtime that serves it. Registration does not establish account access
or invent an ID from a display name.

Registered models appear in the agent, assistant, worker override, summary,
and writer pickers. They are marked as CLI models and are not offered as API
models for unrelated media calls. OpenCode IDs retain their `provider/model`
form. Full Claude IDs pass through unchanged instead of being rewritten into
the aliases opus, sonnet, or haiku.

Model pickers load registered and cached runtime models independently of chat.
On opening a picker or returning to the window, installed Codex and OpenCode
runtimes refresh automatically when discovery data is missing or over six hours
old. Concurrent picker mounts share one request. Cached models remain selectable
while discovery runs or if it fails. Discovery does not start a model turn.
Saving context settings preserves discovered models without copying them into
the manual registry or changing the selected model.

**Refresh models** checks immediately using Codex's authenticated `model/list`,
including pagination, or OpenCode's runtime catalog. The OpenCode catalog is not
evidence that this account can access every listed model. Claude has no verified standalone model
listing command in this implementation; manual registration remains available.
Discovery records retain the runtime version, source, and check time.

Every runtime has an editable **Economy model**. `fast` in older settings now
means this preset. Migration defaults retain Haiku for Claude, Luna for Codex,
and the configured OpenCode default. These defaults are ordinary data, not
conditions scattered through execution code. Register a replacement and point
the preset at it, or enter its exact native ID directly.

Summary and writer settings also support **Custom model**. A runtime-qualified
selection explicitly chooses a different CLI, such as `codex:gpt-6-astra` or
`opencode:provider/model`. Unqualified legacy IDs remain accepted. For a custom
name whose runtime cannot be inferred, register it or use the explicit prefix.

The persisted configuration is `~/.test-harness/compact-config.json`. Its public
GET/POST endpoint is `/__compact_config`. Example patch:

```json
{
  "modelCatalog": [
    {"id": "codex:gpt-6-astra", "runtime": "codex", "model": "gpt-6-astra", "label": "Astra"}
  ],
  "economyModels": {"codex": "gpt-5.6-luna"},
  "summaryModel": "fast",
  "contractWriterModel": "inherit",
  "runtimeDrivers": {"codex": "exec", "opencode": "run"},
  "helperConcurrency": {"claude": 2, "codex": 2, "opencode": 2}
}
```

`modelCatalog` replaces the whole registered list. Other maps merge the supplied
keys. Registration is capped at 500 entries. Optional `modalities` and `efforts`
are metadata, not proof that a runtime can execute a capability. Removing a
registration does not cancel existing work or rewrite its saved profile.

## Execution profiles and helpers

New runs record the requested selection, native model ID, runtime, transport,
role, and isolation policy. A resolved model is recorded only when the runtime
reports it. A CLI default remains unknown until then. The connection currently
identifies one local CLI per runtime, not a multi-account connection pool.

Delegation precedence is the explicit node/worker/orchestrator override, then
the parent's model and runtime, then installation defaults for an unparented
run. Children do not silently switch to another installed CLI. Normal resume
uses the saved runtime transport. Changing the settings affects new work.

Summary and contract-writing jobs use a separate text-only role regardless of
whether their model is cheap, expensive, custom, or inherited. Claude disables
tools, MCP, and user setting sources; Codex uses an ephemeral scratch session
with tool features and user configuration disabled; OpenCode uses its pure
text agent with tools denied. Available model capability metadata controls
Claude's optional effort flag. Inheritance selects the model, not a tool grant.

These helpers have queued/running/completed/failed events, an execution profile,
duration, and output size. Concurrency is limited per runtime, from 1 to 16.
Stopping their parent cancels queued helpers and terminates active helper
process groups. Unknown token usage or cost remains null. This is not yet a
complete cost ledger for every internal LLM call.

Contract prepare requests include the execution profile and writer prompt
version in their cache identity. Concurrent identical prepares coalesce into
one call. Existing exact-value protection, required review, revision checks,
and atomic publication remain in place.

## Native workers and completion

Run records distinguish parent turn completion, subprocess liveness, and
required worker jobs. A tool result acknowledging a background launch is not
worker completion. Supported signals include Claude task lifecycle events,
Codex collaboration and child-turn notifications, and OpenCode session/task
events. Claude child text retains its parent tool ID and is excluded from the
planner's final synthesized answer.

Woven bridge children and helper jobs are also represented in the parent's job
ledger. Their lifecycle survives JSONL replay. A disconnected runtime leaves
unresolved jobs marked unknown, which blocks success rather than assuming the
children completed. Child sessions receiving a new native turn reopen their
job; delayed completion from an older Codex turn cannot close the new work.

Completion hooks and compaction wait for required jobs. A parent response can
finish first, with its final worker event settling the run later. Stop and
delete traverse same-project logical children as well as native process groups.
A live process is stoppable even when its CLI does not expose writable stdin.

The legacy Codex stderr parser cannot provide the same native-worker evidence
as app-server. OpenCode run mode also lacks a durable background event channel.
Use a persistent transport for native background worker testing. Unknown jobs
require investigation or an explicit stop; they are not silently cleared after
a daemon restart.

## Persistent transport previews

Choose the connection in the same settings section, then start a new run.

| Runtime mode | Mid-turn input | Stop | Resume |
| --- | --- | --- | --- |
| Claude stream-json | Native user frame | Process group and child runs | Existing session path |
| Codex exec, default | Queued until the next turn | Process group and child runs | Existing exec resume path |
| Codex app-server, preview | `turn/steer` with the expected turn ID | Interrupt root and native child turns | `thread/resume` |
| OpenCode run, default | Queued until the next turn | Process group and child runs | Existing run resume path |
| OpenCode HTTP, preview | Queued; busy prompts are not treated as steering | Abort root and child sessions | Saved session ID |

The transport is recorded at spawn and retained on resume. The queue's steering
control follows that run's transport, even after the installation setting
changes. An uncertain send is not automatically retried inside a driver.

Codex normalizes structured text, tools, MCP calls, collaboration, usage, and
turn events. OpenCode starts one authenticated loopback server per run and
subscribes before sending a prompt. Its HTTP mode needs an explicit
`provider/model` or a configured default. Root and child sessions share the
same event subscription but keep separate lifecycle state.

Current previews retain the existing unattended permission policy. They do not
provide an interactive approval inbox. Unsupported Codex client requests are
answered with an error, and MCP content elicitation is declined with a visible
status. OpenCode handles permission requests with a one-time response. SSE
loss is reported and the owned server is stopped; reconnect/resynchronization
and durable delivery receipts for arbitrary user messages remain future work.

Rollback for new runs: choose **CLI command**, or set
`WOVEN_CODEX_DRIVER=exec` / `WOVEN_OPENCODE_DRIVER=run` before starting the daemon.
Environment overrides take precedence for new runs; saved runs retain their
transport. This implementation did not restart the user's running daemon.

## MCP and preview evidence

Shared MCP definitions translate local commands and remote URLs separately.
Codex receives startup/tool timeouts in seconds; OpenCode receives tool-discovery
timeouts in milliseconds. JSONC parsing preserves URL strings, comments, and
trailing commas. Environment references for remote headers do not embed their
secret values in OpenCode configuration. This follows OpenCode's documented
[config substitution](https://opencode.ai/docs/config/#env-vars) and
[remote MCP options](https://opencode.ai/docs/mcp-servers/#remote).

Unsupported transport or policy fields fail explicitly: for example, legacy
SSE for Codex, or per-server tool timeouts and tool filters for OpenCode. OAuth
authentication still belongs to the runtime; this change does not add Woven
OAuth account-management UI. Managed local MCP processes receive project/run
scope and visual-guard settings. Turning off the visual guard no longer leaves
the Codex preview denial enabled by accident.

QA reports keep `renderVerdict` separate from `visualReview`. If requested vision
review is unavailable or inconclusive, successful rendering alone cannot
produce an overall pass. Evidence includes the expectation, reported judge,
frame references, and a before/after hash of the reviewed source directory.
Changes during review make the receipt stale. Hashing currently covers that
directory's regular files, not dependencies outside it or symlink targets.
There is no universal image-capability probe or later receipt-reuse service.

## Validation and CLI upgrades

Run the compatibility probe after updating a CLI:

```sh
python3 editor/runtime_probe.py --opencode-server
```

It checks the installed Claude and OpenCode flags, exports and checks Codex's
installed app-server schema, and optionally starts a private OpenCode server
to read its HTTP schema. It sends no model prompts and creates no sessions.
Missing runtimes are reported separately. This detects missing interfaces;
it does not prove behavioral compatibility or automatically gate production
runs by version.

The implementation was checked against Codex 0.154.0, OpenCode 1.17.13, and
Claude Code 2.1.260. Separate read-only smoke checks exercised authenticated
Codex model discovery and empty-session startup, and OpenCode health, session
creation, and event subscription. No generation turn was started in those
checks. Full paid-model builds, native fan-out, tool image delivery, MCP OAuth,
and approval workflows still need runtime trials before promoting the preview
transports to defaults.

Automated regression coverage includes opaque IDs, inheritance, helper routing,
background launch acknowledgements, late completion, restarted children,
process-tree stopping, MCP translation, structured event replay, ambiguous
steering delivery, review provenance, and concurrent writer preparation.
Browser tests exercise economy, transport, registration, and writer controls,
plus automatic discovery across seven pickers with empty, fresh, stale, and
failed discovery states. They also cover preference saves and picker remounts.

```sh
python3 -m unittest discover -s editor/tests -p 'test_*.py'
node editor/tests/test-context-policy.cjs
node editor/tests/test-runtime-settings.cjs
node editor/tests/test-runtime-model-catalog.cjs
editor/check-compat.sh
node --check editor/app.js
git diff --check
```

For the wider pytest suite, `test_image_providers.py` and `test_hosted_delta.py`
are standalone scripts whose main functions install their fixtures. Run those
with Python directly, and exclude them from pytest collection.

The next rollout gate is a disposable real task per runtime: a filesystem edit,
preview/image review, two native workers that outlive the parent's response,
stop/resume, and an unavailable MCP server. Keep the existing transport as the
default until those trials pass. Multi-account routing, automatic cost budgets,
an approval inbox, and reconnect-safe message delivery are not claimed here.
Elevated workspace system threads still require Claude. Claude-specific hook
enforcement also does not yet have a complete equivalent on every runtime;
shared preview policy and prompt routing are not a substitute for that work.
