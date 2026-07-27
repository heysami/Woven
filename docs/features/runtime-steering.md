# Runtime steering parity: codex app-server + opencode serve

Status: PLAN (living document - refine before building; nothing here is committed behavior yet)
Created: 2026-07-27
Owner surface: `editor/serve.py` (runtime spawn/drive layer), `editor/app.js` (chat composer queue/steer UI)

## 0. Why this exists

The chat composer's queued-message cards now carry a bolt button that force-steers
a queued message into the agent's in-progress turn. Today that only truly works on
the `claude` runtime (stream-json user frame written to the live process stdin).
`codex` and `opencode` runs are spawned through one-shot non-interactive surfaces
(`codex exec`, `opencode run`) that have NO mid-turn input channel, so the bolt
fails safe (error + requeue) on those runs.

That limitation is OUR spawn choice, not the CLIs' design: the Codex desktop app
steers mid-turn over the same `codex app-server` protocol that ships in the CLI we
already invoke, and opencode ships a headless HTTP server (`opencode serve`) whose
API accepts prompts into a busy session. Migrating both runtimes to their
long-lived server surfaces buys steering, real interrupt, real resume, and a
proper approvals channel - parity with the claude runtime.

## 1. Verified facts (as of 2026-07-27 - reverify before each phase)

### 1.1 codex (local codex-cli 0.142.5)

Verified locally via `codex app-server generate-json-schema` (schema generated
from the INSTALLED binary, so it always matches the running version) and against
the official docs (developers.openai.com/codex/app-server, redirects to
learn.chatgpt.com/docs/app-server).

- `codex app-server` is a JSON-RPC 2.0 protocol over stdio (a control socket /
  proxy mode also exists: `codex app-server proxy`, `codex remote-control`).
- The protocol is what "powers every surface" including the Codex desktop app.
  Core methods are production-oriented; the "experimental" label in `codex --help`
  overstates it. Truly experimental pieces are opt-in gated behind
  `capabilities.experimentalApi = true` (process spawning, env inspection, some
  thread-history pagination) and WebSocket transport. We need NONE of the gated
  pieces for steering.
- Key methods (all present in the 0.142.5 schema, none capability-gated):
  - `thread/start` - params include `cwd`, `sandbox` (SandboxMode incl.
    dangerFullAccess), `approvalPolicy`, `baseInstructions`,
    `developerInstructions`, `config` (object - config.toml overrides, i.e. MCP
    servers), `model`, `modelProvider`, `ephemeral`.
  - `thread/resume` - reopen an existing thread BY ID; later `turn/start` calls
    append. Real resume, no transcript rebuild.
  - `thread/fork` - branch history into a new thread id.
  - `turn/start` - begin a turn; params include `input` (array), `model`,
    `effort`, `outputSchema`, per-turn `sandboxPolicy`/`approvalPolicy`.
  - `turn/steer` - append user input to the CURRENTLY IN-FLIGHT turn without
    creating a new turn. Params: `threadId`, `expectedTurnId` (race guard),
    `input`. This is the bolt button's exact semantics.
  - `turn/interrupt` - cancel the in-flight turn (a real Stop).
  - Approvals arrive as server->client JSON-RPC requests we must answer:
    `ExecCommandApproval`, `ApplyPatchApproval`, `FileChangeRequestApproval`,
    `PermissionsRequestApproval` (schema files of the same names).
  - MCP: full bidirectional support; servers come from config
    (`-c mcp_servers.*` CLI overrides work on app-server too, or the `config`
    object on thread/start). `mcpServer/oauth/login`, `config/mcpServer/reload`
    exist. NOTE: a failed REQUIRED MCP server blocks thread/start + thread/resume
    - our spawn must mark Woven MCP servers optional or handle that error.
- Stability story: no SemVer commitment documented. `generate-json-schema` +
  `generate-ts` emit artifacts that "match that version exactly" - i.e. the
  supported workflow is regenerate-per-version. Unknown experimental methods
  error cleanly when not opted in (forward-compat mechanism).
- `codex exec resume <id>` also exists now (one-shot resume) - a cheaper interim
  improvement to our fake-resume even before any app-server work.

### 1.2 opencode (local 1.17.13)

Verified locally via `opencode --help` and against opencode.ai/docs/server.

- `opencode serve` runs a headless HTTP server; OpenAPI 3.1 spec self-served at
  `/doc` (generate or inspect clients from it). `opencode attach <url>` attaches
  a TUI to a running server. `opencode acp` speaks Agent Client Protocol (Zed's)
  - an alternative integration path, not chosen here (HTTP API is richer).
- Key endpoints:
  - `POST /session` - create session (optional `parentID`, `title`).
  - `POST /session/:id/message` - send prompt and WAIT for the response.
  - `POST /session/:id/prompt_async` - fire-and-forget send (204). Accepts
    sends while the session is busy: they QUEUE server-side.
  - `POST /session/:id/abort` - stop the active run.
  - `POST /session/:id/permissions/:permissionID` - answer a permission ask
    (`{ response, remember? }`).
  - `GET /event` / `GET /global/event` - SSE stream of session events.
- Mid-turn semantics today: a prompt sent while busy is QUEUED, not steered.
  True steer-vs-queue distinction is an OPEN upstream feature request
  (anomalyco/opencode #32157, #21388), and queueing has known bugs: queued
  prompt can start before the active response finishes (#28375), queued-message
  serialization breaks prompt caching (#21518), `prompt_async` without explicit
  agent/model fields silently overrides the session's agent/model (#21728 -
  ALWAYS pass agent+model explicitly on every prompt_async).
- So: opencode migration buys server-side queueing, real abort, permissions
  channel, and SSE events NOW; true mid-turn steering lands whenever upstream
  ships it (our layer then just flips which endpoint semantics it advertises).

### 1.3 What stays true regardless of surface

- Both CLIs' agent cores (tools: shell, apply_patch/edit, web search, MCP tools
  incl. our browser/screenshot/preview MCP servers) are IDENTICAL across their
  interactive and server surfaces - the server protocols are control planes over
  the same engine. No tool capability is lost by migrating.
- Woven's MCP wiring already flows through config translation
  (`_codex_mcp_spawn_args` -> `-c mcp_servers.*`; `_ensure_opencode_mcp_config`
  -> OPENCODE_CONFIG). Both carry over to the server surfaces unchanged
  (codex: same `-c` flags / `config` object; opencode: same config file the
  server loads).

## 2. Target architecture

One new seam in serve.py: a per-runtime DRIVER abstraction over "how do we talk
to a live agent", so RunState stops assuming a subprocess with a stdin pipe.

```
RunState.driver:
  claude   -> StdioStreamJsonDriver   (today's proc.stdin frames - unchanged)
  codex    -> CodexAppServerDriver    (JSON-RPC over the app-server child's stdio)
  opencode -> OpencodeHttpDriver      (HTTP calls against a managed `opencode serve`)

Driver interface (minimum):
  spawn(initial_prompt, opts)      -> starts/attaches process or server session
  send_user(text)                  -> follow-up message (idle: new turn)
  steer(text) -> bool              -> mid-turn injection; False if unsupported
  interrupt()                      -> stop current turn without killing context
  resume(text)                     -> continue after process/turn death
  capabilities()                   -> { steerable, interruptible, realResume }
```

The HTTP handlers (`/user-message`, `/resume`, `/stop`) route through the
driver instead of touching `state.proc.stdin` directly. `is_live` becomes a
driver question ("can you take a message right now"), which also fixes the
codex/opencode "is_live is False their whole lifetime" wart.

Capabilities surface to the client: extend the run snapshot (or
`/__capabilities`) with `steerable: true|false` per run. The composer's bolt
renders only when the run says steerable (or when idle, where bolt = send now
for every runtime). No more offering what the runtime cannot do.

## 3. Phased plan

Each phase is independently shippable and reversible. The old exec/run spawn
path STAYS as the fallback until the new driver has survived real use; a config
flag (`WOVEN_CODEX_DRIVER=exec|app-server`, default exec initially) picks per
daemon boot, so one `-c`-style toggle rolls back.

### Phase 0 - groundwork + honesty UI (no runtime change) - DONE 2026-07-27
- [x] Capability plumbing: `AGENT_DEFS[*]["steerable"]` (claude True,
  codex/opencode False) surfaced as `steerable_agents` on GET /__media_config.
  Client falls back to `["claude"]` when the key is absent (older daemon).
- [x] Composer honesty: bolt on queue cards renders mid-turn ONLY for
  steerable runtimes (`useSteerableAgents` + the run's `agentId`, passed
  from the drawer). Idle bolt (= send now) still renders for every runtime.
- [x] codex real resume: `_CodexStderrParser` captures the banner
  `session id: <uuid>` (top-of-feed, strict-UUID, first-wins - survives the
  fell-through-banner flow when pre-banner noise has continuation lines);
  `_drain_stderr` copies it to `state.session_id` + persists a
  `codex-session` status event (rehydrator: codex latest-wins);
  `_run_resume_codex` spawns `codex exec resume <sid> <msg>` (with
  `-c sandbox_mode="danger-full-access"` + MCP `-c` overrides + model) when
  the CLI supports it (probed once via `--help`) AND the rollout file exists
  in the child's CODEX_HOME - else transcript-rebuild fallback (opencode
  always). Kill switch: env `WOVEN_CODEX_EXEC_RESUME=off`.
  NOT yet live-verified end-to-end (the local codex login was expired at
  build time - refresh_token_reused); parser + preconditions unit-tested
  against a real captured stderr. First real codex chat after `codex login`
  is the live test; on any misbehavior set the kill switch.
- Schema snapshot + boot-time drift detection: MOVED to Phase 1 (it guards
  the app-server driver; nothing consumes the schema until that exists).

### Phase 1 - codex app-server driver, happy path
- Snapshot the codex app-server schema (`generate-json-schema`) into
  `editor/tools/appserver-schema/<version>/` at first driver boot; on daemon
  start with a NEW codex version, diff method names/param shapes we depend on
  and surface "codex updated - protocol drifted" in the runs UI instead of
  failing mid-conversation. (Moved from Phase 0.)
- Spawn `codex app-server` per run (stdio JSON-RPC; one child per run keeps the
  blast radius identical to today's model).
- initialize -> thread/start (cwd, sandbox=dangerFullAccess equivalent,
  baseInstructions = Woven preamble - REPLACES prompt-prefixing,
  config = MCP servers marked optional) -> turn/start with the user prompt.
- Event normalization: map app-server notifications onto the existing agent
  event vocabulary (`_drain_stderr_codex`'s output shape) so app.js needs ZERO
  changes to render. Keep the old parser for the exec fallback path.
- Approvals: auto-answer per the run's permission mode (bypass -> approve), the
  same policy the exec sandbox flag encodes today. Interactive approval UI is a
  LATER phase; do not block on it.

### Phase 2 - steer + interrupt (the user-facing payoff)
- `/user-message` on a mid-turn codex run -> driver.steer() -> `turn/steer`
  with `expectedTurnId` from the last turn-started notification. On the
  turn-id race (steer lands after the turn ended) fall back to a normal
  `turn/start` - same message, next turn, matching claude-queue semantics.
- Stop button -> `turn/interrupt` (context survives; a follow-up continues the
  thread) instead of SIGTERM. Process kill remains the hard-stop fallback.
- Flip `steerable: true` for codex runs on the new driver; bolt appears.

### Phase 3 - real resume
- Replace `_run_resume_codex` for app-server runs: respawn `codex app-server`
  (or reuse a living one) -> `thread/resume <threadId>` -> `turn/start` with
  the user's message. Delete the transcript-rebuild path for these runs.
- Persist threadId in run state / chat.jsonl the way claude session ids are.

### Phase 4 - opencode driver
- Manage ONE `opencode serve` child per daemon (or per project root - decide by
  testing cwd semantics; sessions carry their own context). Health-check +
  respawn like any managed child. Daemon owns its lifecycle; it is an
  agent-runtime child, not a user-facing daemon.
- Runs map to sessions: `POST /session` -> `prompt_async` (ALWAYS with explicit
  agent+model per #21728) -> consume `GET /event` SSE, normalize onto the
  existing opencode event vocabulary (today's `_OpenCodeStreamParser` shapes).
- `/user-message` mid-turn -> `prompt_async` (server-side queue - honest label:
  this is QUEUE, not steer; capabilities say steerable:false until upstream
  ships steer semantics, then flip). Stop -> `/abort`. Resume -> sessions are
  persistent server-side; a follow-up prompt IS resume. Permission asks ->
  `/session/:id/permissions/:permissionID` wired to the existing gate UI.
- Watch upstream: anomalyco/opencode #32157 (queue vs steer), #28375 + #21518
  (queue bugs) - reverify at implementation time.

### Phase 5 - approvals UX + cleanup
- Map codex approval requests / opencode permission asks onto the chat
  permission-gate cards (the claude-path pattern) for non-bypass modes.
- Retire fallback paths that have proven unnecessary; collapse the drift-net
  code that existed only because exec-mode couldn't be driven.

## 4. Risk register

| Risk | Phase | Mitigation |
|---|---|---|
| codex protocol drift on `codex update` (no SemVer promise) | 1+ | schema snapshot + boot-time diff of the methods we use; `WOVEN_CODEX_DRIVER=exec` rollback flag; pin-version advice in onboarding |
| Required-MCP-server failure blocks thread/start | 1 | mark Woven MCP servers optional in config; on block error, retry once without MCP + surface a warning event |
| app-server child lifecycle differs from exec (long-lived, idle) | 1 | reuse existing RunState child management; idle-kill timer mirrors claude's process lifetime policy |
| Steer turn-id race (turn ends as steer lands) | 2 | `expectedTurnId` + fall back to `turn/start` with the same text |
| opencode queued prompt fires early / breaks caching (upstream bugs) | 4 | keep client-side queue as the default; `prompt_async`-while-busy only behind the bolt (explicit user intent); reverify bugs at build time |
| `prompt_async` silently swaps agent/model (#21728) | 4 | always send explicit agent+model on every prompt |
| Two sources of truth for events during migration | 1,4 | normalizers emit the EXISTING event vocabulary; app.js untouched until both drivers are proven |
| Daemon restart orphans app-server/serve children | 1,4 | same reap-on-boot logic as claude children; opencode sessions survive server restarts by design (but see upstream #19023 - stuck sessions after restart) |

## 5. Decision log

- 2026-07-27: chose codex app-server over `codex mcp-server` (app-server is the
  richer, purpose-built control plane; mcp-server frames codex as a tool, wrong
  shape for a chat runtime).
- 2026-07-27: chose opencode HTTP server over `opencode acp` (HTTP API exposes
  permissions + abort + SSE natively and is self-documenting via /doc; ACP is a
  second protocol to learn with no steering advantage today).
- 2026-07-27: per-run app-server child for codex (not one shared server) to
  keep run isolation identical to today; revisit if spawn cost matters.
- 2026-07-27: opencode advertises steerable:false until upstream ships true
  steer semantics; bolt-on-idle still works (send now).

## 6. Reverify-before-build checklist (run at the top of every phase)

- [ ] `codex --version` + regenerate schema; diff against the snapshot in this
      repo; update §1.1 if methods/params moved.
- [ ] `opencode --version`; fetch `http://localhost:<port>/doc` from a
      test-spawned `opencode serve`; update §1.2 endpoints.
- [ ] Check upstream issues: openai/codex app-server stability notes;
      anomalyco/opencode #32157 #28375 #21518 #21728 #19023.
- [ ] Confirm Python 3.9 compatibility of any new serve.py code
      (editor/check-compat.sh) - fresh-install floor is 3.9.
- [ ] Daemon-restart note: serve.py changes only land for the user after THEY
      restart their daemon - sequence UI changes accordingly.
