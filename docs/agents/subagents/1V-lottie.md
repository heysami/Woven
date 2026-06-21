# Subagent 1.V.lottie - Asset drawer (medium: Lottie JSON animation)

You own **ONE asset** of medium `lottie` - a narrative motion loop. Logo intro, mascot wave, illustrated state-change, section divider animation. Lottie's strength is sub-second vector animation that's tightly art-directed; its weakness is open-ended ambient loops (use `particle-2d` / `shader` instead).

Two paths:

| Path | When | Output |
|---|---|---|
| **Pathway A - vendor** | A Lottie-generation vendor is wired (rare today; no first-party API exists) | Prompt into the prompt node + skill node configured for that vendor |
| **Pathway B - LLM-writes-JSON** | Default. You write the Lottie JSON directly. | JSON written to `slot.outputPath` |

**Read [`../conventions.md`](../conventions.md) before starting.**

## Input (envelope only)

See [`1V-visual-orchestrator.md`](1V-visual-orchestrator.md) §Step 5.

```
pipeline=["prompt","lottie-gen"]
nodeIds: { prompt, skill, asset }
```

Slot is typically `<div class="lottie" data-anim="…">`. The runtime mount loop loads `lottie-web` (CDN), reads `data-anim`, fetches the JSON at `slot.outputPath`, and plays.

## Output

```json
{
  "assetId": "<id>",
  "promptText": "<full intent paragraph for the vendor, OR a 1-sentence design intent for Pathway B>",
  "skillCode": "<Lottie JSON as a single string>",
  "params": {
    "outputPath": "<slot.outputPath e.g. assets/lottie/hero-mascot.json>",
    "duration": "<seconds>",
    "loop": true | false,
    "implementation": "vendor" | "llm-json"
  },
  "slotEditDiff": "<diff or null>"
}
```

If `implementation: "vendor"`, `skillCode` is empty (vendor produces the JSON at Run time). If `implementation: "llm-json"`, `skillCode` is the full JSON string.

## Recipe

### 1. Decide the path

Default to `llm-json` unless the host environment has confirmed a Lottie-gen vendor. Reason: LLM-written Lottie JSON is reliable for short geometric loops (logo intro, simple mascot wave, divider sweep) - much faster iteration than a vendor round-trip, no BYOK needed.

For figurative subjects beyond geometric capability (a realistic mascot, a complex scene), if no vendor is available, return `error: "subject exceeds llm-json capability; needs vendor or static fallback"`.

### 2. Decide duration + loop

| Slot intent | Duration | Loop |
|---|---|---|
| Logo intro (mount-once) | 1.2 - 2.0s | `false` |
| Mascot wave (loop) | 2.0 - 4.0s | `true` |
| Divider sweep (scroll-triggered) | 0.6 - 1.0s | `false` |
| Empty-state nudge | 1.5 - 2.5s | `true` |

Read the slot's `data-motion` modifier - if it says `loop` or `ambient`, set `loop: true`. If `mount` or `enter`, set `loop: false`.

### 3. Write the Lottie JSON (Pathway B - `llm-json`)

Lottie JSON is verbose but follows a stable schema. Minimum-viable structure:

```json
{
  "v": "5.7.0",
  "fr": 60,
  "ip": 0,
  "op": 120,
  "w": 240,
  "h": 240,
  "nm": "<assetId>",
  "ddd": 0,
  "assets": [],
  "layers": [
    {
      "ddd": 0, "ind": 1, "ty": 4, "nm": "shape", "sr": 1,
      "ks": {
        "o": { "a": 0, "k": 100 },
        "r": {
          "a": 1,
          "k": [
            { "t": 0,   "s": [0]   },
            { "t": 120, "s": [360] }
          ]
        },
        "p": { "a": 0, "k": [120, 120, 0] },
        "a": { "a": 0, "k": [0, 0, 0] },
        "s": { "a": 0, "k": [100, 100, 100] }
      },
      "shapes": [
        {
          "ty": "gr",
          "it": [
            { "ty": "el", "p": { "a": 0, "k": [0, 0] }, "s": { "a": 0, "k": [80, 80] } },
            { "ty": "fl", "c": { "a": 0, "k": [0.27, 0.42, 0.68, 1] }, "o": { "a": 0, "k": 100 } },
            { "ty": "tr", "p": { "a": 0, "k": [0, 0] }, "a": { "a": 0, "k": [0, 0] },
              "s": { "a": 0, "k": [100, 100] }, "r": { "a": 0, "k": 0 }, "o": { "a": 0, "k": 100 } }
          ]
        }
      ],
      "ip": 0, "op": 120, "st": 0, "bm": 0
    }
  ]
}
```

Schema cheatsheet:

| Field | Meaning |
|---|---|
| `fr` | Frame rate |
| `ip` / `op` | In-point / out-point (frame numbers) |
| `w` / `h` | Composition width / height |
| `layers[].ty` | Layer type - `4` = shape, `2` = image, `0` = composition |
| `ks` | Transform - `o`=opacity, `r`=rotation, `p`=position, `a`=anchor, `s`=scale |
| `ks.<prop>.a` | `0` = static, `1` = animated keyframes |
| `ks.<prop>.k` | Static value OR keyframes array `[{ t, s }]` |
| `shapes[].ty` | Shape type - `el`=ellipse, `rc`=rect, `sh`=path, `fl`=fill, `st`=stroke, `tr`=transform, `gr`=group |

### 4. Build the animation - three patterns

**Logo intro (scale-in + fade)**:
- Layer with `ks.s` animated `0 → 100` over 30 frames
- Layer with `ks.o` animated `0 → 100` over 30 frames
- Optional `ks.r` animated `−15 → 0` for a tiny rotation kicker

**Mascot wave (loop)**:
- Group with rotation animated `0 → 15 → 0 → −15 → 0` across the loop duration
- Anchor point at the base of the waving element

**Divider sweep**:
- Trim-path animation on a `sh` shape - `tm.s` (start) animated `0 → 100`, `tm.e` (end) animated `0 → 100` with offset
- Linear easing; the sweep IS the animation

### 5. Palette anchoring

Lottie colors are normalized RGB arrays `[r, g, b, a]` in 0-1. Convert `:root` tokens to normalized RGB once and reuse:

```
--accent: oklch(48% 0.13 252) ≈ rgb(69, 107, 173) → [0.27, 0.42, 0.68, 1]
```

### 6. Slot diff

If the slot isn't declared:

```jsonc
"slotEditDiff": {
  "file": "<slot.file>",
  "find": "<div class=\"mascot\">",
  "replace": "<div class=\"mascot lottie\" data-anim=\"<assetId>\" data-loop=\"true\"></div>"
}
```

The runtime mount loop reads `data-anim` (path) and `data-loop` (boolean), instantiates `lottie-web`, plays.

## Self-audit

- [ ] JSON is valid (parses with `JSON.parse`).
- [ ] `fr` is 60 (or 30 if explicitly low-fps for cost reasons).
- [ ] `ip` / `op` define the right duration for the chosen `fr`.
- [ ] `w` / `h` match the slot's natural size (read CSS).
- [ ] All colors are normalized RGB `[r, g, b, a]` in 0-1 anchored to `:root` tokens.
- [ ] `loop` param matches the slot's intent (`mount` → false, `loop` → true).
- [ ] No raster images embedded (`assets[]` should be empty or vector only).
- [ ] Layer types are `4` (shape) only - no image layers, no comp layers, no text layers unless required.

## Don't

- Don't write a Lottie for a subject Lottie isn't good at (realistic mascot, complex character animation). If the subject is figurative and ≥3 colors with realistic shading, return `error: "subject exceeds llm-json capability"`.
- Don't embed raster images. The whole point of Lottie is vector - embedded raster defeats it.
- Don't use Lottie expressions (`x` property). They're parseable only by After Effects' renderer; web Lottie players don't reliably support them.
- Don't loop > 4s. Long Lottie loops are usually a sign the medium is wrong - should be `video` or `particle-2d`.
