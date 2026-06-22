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

This is the deep protocol for an interactive LOGIC-GRAPH piece (`mode=interactive`, which captures motion + simulates input). The SAME endpoint also verifies a composed page/app surface: `GET $TH_DAEMON_URL/__qa/run?project=$TH_PROJECT_ID&page=<slug>` runs `mode=render`, which passes a correctly painted page and catches a `blank`/unstyled render (broken `?project` stamping / 404'd DS imports). The always-on capabilities preamble documents both targets under "Verify your visual work before you tell the user it is done" - use `page=` for "does the app look right", `node=` for "does this piece move/react".

CAMERA / VISION pieces ARE verifiable - no webcam excuse. The QA injects a SYNTHETIC camera in place of `getUserMedia`: stock fixtures of a hand + a face that MediaPipe reliably detects, rendered into a moving canvas. So a `vision-detect` / `vision-ocr` / hand / face piece gets a REAL, detectable, moving feed under headless QA - a working camera piece ANIMATES (`pass`); a `static`/blank result means it is ACTUALLY broken, not "no camera". The QA also auto-grants camera/mic permission and waits for MediaPipe/tesseract to load before judging. Optional `&camera=hand|face|both|off` picks the fixture (default `both`). For mouse pieces the QA already simulates pointer move / click / drag / scroll / key.

HARD RULES (these caused real failures):
- NEVER say a camera / vision / pointer piece "can't be verified without a real webcam or a human." The QA feeds a synthetic detectable camera + synthetic input - run it and read the verdict.
- NEVER judge whether a capability works by reading a baked `.html` snapshot or the runtime source - those are frozen/partial. RUN the QA instead; it tests the live engine.
- NEVER delete the user's nodes to "start clean." Fix in place.
- The composer CAN do live camera, per-strand rope physics, and pointer-driven physics (via a `force` node). Do not claim otherwise and do not fall back to a hand-coded prototype iframe for these - build the native logic graph and verify it with QA.
