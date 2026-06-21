## Verify the effect (visual QA) - MANDATORY before claiming success

Building the graph is not the same as the effect happening. After you build + BAKE an interactive piece, VERIFY it with the visual QA endpoint, which loads the baked runtime headless, captures it across several moments AND simulates interaction (pointer / click / drag / scroll / key), then reports whether the effect actually occurred:

  `GET $TH_DAEMON_URL/__qa/run?project=$TH_PROJECT_ID&node=<composerNodeId>[&judge=<one-line expected effect>]`

Read the `verdict`:
- `pass` - it animates and/or reacts. Only now may you tell the user it is done.
- `static` - nothing renders or moves. The piece failed; fix it and re-run.
- `no-reaction` - it ignores input. Your input wiring is wrong; fix and re-run.
- `error` - console / page errors; read `consoleErrors` / `pageErrors`, fix, re-run.
- `effect-wrong` - pixels move but the `judge` says it is the wrong thing; revise and re-run.
- `unbaked` - bake the node first, then re-run.

HARD RULES (these caused real failures):
- NEVER judge whether a capability works by reading a baked `.html` snapshot or the runtime source - those are frozen/partial. RUN the QA instead; it tests the live engine.
- NEVER delete the user's nodes to "start clean." Fix in place.
- The composer CAN do live camera, per-strand rope physics, and pointer-driven physics (via a `force` node). Do not claim otherwise and do not fall back to a hand-coded prototype iframe for these - build the native logic graph and verify it with QA.
