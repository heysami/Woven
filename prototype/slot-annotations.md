---
name: slot-annotations
description: Woven-specific overlay on Step nine (graphics) — `img-placeholder` for static imagery and `motion-placeholder` for decorative animated loops, with `data-slot` + (`data-asset-intent` or `data-motion`) modifiers. Loaded when writing source HTML that contains visual slots Subagent 1.V (the visual orchestrator) will fill after build. Includes the `data-motion` prefix → medium classifier routing table (particles → particle-2d/gl, loop → lottie, clip → video, wash/aurora/noise → shader, scene → 3d).

→ Decision lives in PROTOTYPE.md §"Slot annotations — handing off to Subagent 1.V".
---

# Slot annotations — handing off to Subagent 1.V (the visual orchestrator)

This overlays Step nine (graphics) with Woven's visual-orchestrator handoff. You don't decide the *medium* per visual slot (raster vs vector vs shader vs particles vs 3D vs lottie vs video). That decision is owned by [`docs/agents/subagents/1V-visual-orchestrator.md`](docs/agents/subagents/1V-visual-orchestrator.md), which runs after you finish source. Your job is to annotate each slot so the orchestrator's classifier can pick correctly.

**For static-imagery slots** — use `img-placeholder`:

```html
<div class="img-placeholder" data-aspect="4:3"
     data-slot="hero-cafe-floorplan"
     data-asset-intent="foreground · hand-drawn pencil sketch of a café floor plan, top-down view, isolated subject">
  PHOTO · café interior
</div>
```

**For motion / animated-loop slots** — use `motion-placeholder` (the sibling pattern):

```html
<div class="motion-placeholder" data-aspect="16:9"
     data-slot="bg-drift-particles"
     data-motion="particles · slow drift · 40 dots warm white">
  MOTION · ambient drift particles
</div>
```

The `data-motion` modifier drives the orchestrator's motion classifier:

| `data-motion` prefix | Routes to |
|---|---|
| `particles · …` (density hint optional) | `particle-2d` (default) or `particle-gl` (if density > 200 or explicitly `gl`) |
| `loop · …` (figurative subject like a mascot / logo intro / scene transition) | `lottie` |
| `clip · …` (cinematic narrative) | `video` |
| `wash · …` / `aurora · …` / `noise · …` (gradient or shader pattern) | `shader` |
| `scene · …` (3D scene with depth) | `3d` |

**Functional motion stays inline.** Hover transitions, state changes, progress bars, "running" pulses — write them in `styles.css` with `@keyframes` per [`step-motion.md`](./prototype/step-motion.md). Don't wrap them in a `motion-placeholder`; that's reserved for decorative loops that get a workflow node.

**Voice / specificity rule applies to `data-asset-intent` and `data-motion` strings.** "Hand-drawn pencil sketch of a café floor plan, top-down view, warm graphite on warm paper" beats "hero illustration". The orchestrator forwards your annotation to the per-medium drawer; specificity in equals specificity out.

The genre guardrail propagates: Subagent 1.V's classifier reads the same motion-budget table as [`step-motion.md`](./prototype/step-motion.md) and refuses to scaffold decorative-loop nodes when the genre forbids them. A brutalist prototype that handed Subagent 1.V a `motion-placeholder` would get a `drop:genre-forbidden` decision; the static fallback is left to you.

---

