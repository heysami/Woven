# Lens calibration suite

Hand-authored fixture set + comparison script that validate the three quality
lenses (`craft-lens`, `aesthetic-lens`, `concept-lens`) score known-quality
artefacts in the expected order before the lenses are deployed against real
user projects.

Without calibration, the lenses are untested guesses. Real user projects pay
the cost of miscalibration. With calibration, you have a confidence floor +
a regression-catch when someone edits a lens playbook.

## What's in here

```
.claude/lens-calibration/
├── README.md                     ← this file (the runbook)
├── compare.py                    ← reads verdicts, emits confusion matrix
└── fixtures/
    ├── sim-01-loop-perf-now-block/        ← craft fail: perf.now() in tick
    │   ├── runtime.html                    ← the artefact the lens scores
    │   ├── creative-brief.json             ← project creative brief
    │   ├── prd-row.json                    ← PRD simulation/interactive row
    │   └── expected.json                   ← ground-truth verdicts
    ├── sim-02-clean-accumulator-all-pass/ ← clean: all 3 lenses pass
    ├── sim-03-paradigm-mismatch/          ← concept fail: paradigm wrong
    ├── sim-04-aesthetic-mismatch/         ← aesthetic fail: vibe wrong
    ├── sim-05-flat-no-readability/        ← concept fail: no 5-sec intuition
    ├── im-01-direct-echo-bad/             ← aesthetic + concept fail
    ├── im-02-accumulator-clean/           ← clean: all 3 lenses pass
    ├── im-03-permission-leak-block/       ← craft fail: getUserMedia at load
    ├── im-04-audio-wrong-vibe/            ← aesthetic fail: bright synth vs warm brief
    └── im-05-flat-no-surprise/            ← concept fail: no observable response
```

Each fixture's `expected.json` declares what each of the three lenses
SHOULD return for that runtime. The calibration run dispatches each lens
against each fixture, writes the lens's actual verdict, and `compare.py`
emits a confusion matrix.

## Running the calibration

Two steps:

### Step 1 — Dispatch all 30 lens runs (3 lenses × 10 fixtures)

The lens agents are already registered as Claude Code subagent types
(see `.claude/agents/{craft,aesthetic,concept}-lens.md`). For each
fixture, dispatch three lens runs by sending each lens the calibration
envelope below.

Calibration envelope template (substitute `<fixture-id>` and `<lens>`):

```
=== ENVELOPE ===
componentId:   "calib-<fixture-id>"
componentKind: "runtime"
family:        "<from prd-row.json>"
iteration:     1
artefactPath:  ".claude/lens-calibration/fixtures/<fixture-id>/runtime.html"

# Read creativeBrief + slotIntent + successFeel from JSON files:
creativeBrief: "<contents of fixtures/<fixture-id>/creative-brief.json verbatim>"
slotIntent:    "<from prd-row.json's 'subject' (sim) or 'concept' (im)>"
successFeel:   "<from prd-row.json's 'successFeel'>"
prdSubject:    "<from prd-row.json's 'subject'>"           # sim only
prdParadigm:   "<from prd-row.json's 'paradigm'>"          # sim only
prdConcept:    "<from prd-row.json's 'concept'>"           # im only

reportPath:    ".claude/lens-calibration/fixtures/<fixture-id>/<lens>-verdict.json"
                # CALIBRATION OVERRIDE: write your verdict to this path
                # directly. Do NOT POST to /__workflow/node/<id>/commit —
                # this is calibration, not production.
=== END ENVELOPE ===
```

The lens reads the envelope, runs preview tools against the runtime.html,
scores against its rubric, writes a single verdict JSON to `reportPath`.
Verdict shape (per the lens playbooks):

```jsonc
{
  "iso":         "<utc iso>",
  "componentId": "calib-<fixture-id>",
  "iteration":   1,
  "lens":        "<craft | aesthetic | concept>",
  "verdict":     "pass" | "fail",
  "reason":      "<one short sentence on fail; null on pass>",
  "failures":    [ /* per-check failure entries */ ]
}
```

**Dispatch shortcut** — if you're running this from a Claude Code session,
fire all 30 in parallel as a single message with 30 `Task(...)` calls.
Total wall-clock ~5-10 minutes (lenses run in parallel; each uses
preview tools against a small runtime).

### Step 2 — Run compare.py

```bash
cd /Users/sami/Documents/Woven
python3 .claude/lens-calibration/compare.py
```

The script walks each fixture, reads its `expected.json`, reads the three
`<lens>-verdict.json` files the lenses wrote, and emits a confusion matrix
+ per-lens summary.

Example output (showing a calibration run with one regression):

```
═══ Lens calibration report ═══

PER-LENS SUMMARY
  craft-lens     : 10/10 correct  (precision=1.00, recall=1.00)
  aesthetic-lens :  9/10 correct  (1 false-fail — fixture sim-04-aesthetic-mismatch)
  concept-lens   :  7/10 correct  (3 false-pass — fixtures im-01, im-05, sim-05)
                                   → concept-lens §4 "Mapping non-triviality"
                                     check is too weak; sharpen the rubric.

PER-FIXTURE DETAIL
  sim-01-loop-perf-now-block:
    craft     pass-expected:fail → got:fail ✓
    aesthetic pass-expected:n/a  → got:pass (lens skipped per its rules; ok)
    concept   pass-expected:n/a  → got:pass (lens skipped; ok)
  ...

═══ Recommended actions ═══
  • Sharpen concept-lens §4 "Mapping non-triviality" check — the rubric
    accepts direct-echo mappings when it should reject them. Quote the
    brief's verbatim antiPatterns string in the check.
  • Investigate aesthetic-lens false-fail on sim-04 — the lens may be
    too strict on borderline DS palette match.
```

When the report is clean (≥9/10 per lens), the calibration is shippable.
When it isn't, update the failing lens playbook and re-dispatch ONLY the
affected fixtures.

## Authoring new fixtures

Each new fixture is one directory with four files. The runtime.html must
be self-contained (no external assets beyond CDN imports), expose the
§12.3 devtools globals (`window.__sim` or `window.__im`) so concept-lens
can drive synthetic inputs, and exhibit ONE specific quality property
(positive or negative) the fixture is designed to test.

Suggested fixture coverage per lens:
- **craft**: 2 clear-pass + 2 clear-fail + 1 borderline = 5 cases
- **aesthetic**: 2 clear-pass + 2 clear-fail + 1 borderline = 5 cases
- **concept**: 2 clear-pass + 2 clear-fail + 1 borderline = 5 cases

The existing 10 fixtures cover most combinations across both families
(simulation + interactive) with enough variety to detect rubric drift.

## When the calibration regresses

If `compare.py` reports a regression after editing a lens playbook:
1. Read the per-fixture detail to find which specific check fired wrong.
2. Open the lens playbook + the offending fixture's runtime.html.
3. Re-author the check's wording until the lens makes the correct call.
4. Re-dispatch just the affected lens × affected fixture pairs.
5. Re-run `compare.py`. Loop until 10/10.

## Why this isn't a real automated test runner

Calibration runs the lens agents through Claude Code's Task tool — same
mechanism production uses. Wrapping that in a CI runner would require:
- Spawning Claude Code subprocesses programmatically (possible but heavy)
- Caching past verdicts to avoid re-dispatching identical inputs
- Pinning model versions so verdicts are reproducible

The runbook approach above is simpler: a human (or a Claude session) runs
the 30 Task dispatches manually when calibration is needed, then runs
compare.py to see the result. Total cost ~10 minutes per run. Future
work could automate this if the suite grows.
