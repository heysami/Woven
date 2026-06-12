---
techniqueId: threshold-ritual
name: Threshold ritual (entry gate as a designed moment)
category: scene-choreography
subCategory: dom-or-canvas
role: entrance
binding: user-gesture
medium: hybrid
pairsPrototypes: [aesthetic-luxury-cinematic-dark, aesthetic-sculptural-minimal, recipe-brand-story-journey, shell-scroll-journey-scene, aesthetic-japanese-poster-layout]
notForUseWhen: Conversion-critical or utility surfaces (anything a user visits to DO something — dashboards, docs, checkout, support), repeat-visit products (the ritual delights once and obstructs forever), or briefs where nothing behind the gate justifies the withholding.
images:
  - src: motion-threshold-ritual.png
    reason: Representative technique still.
---

# Threshold ritual (entry gate as a designed moment)

The site withholds itself until the visitor makes a choice or watches an
opening — entering is staged as a ceremony, borrowing the mental model of a
theatre curtain or a TV title sequence. Recurrent on high-craft Japanese
experience sites in three forms: a **sound-consent gate** ("Sound: On / Off"
composed as the opening screen), a **counter ceremony** (a %-preloader styled
as deliberate pause, not apology), and a **skippable title film** (a 6–12s
opening animation with an explicit SKIP chip).

## Motion signature

- The gate is a full-viewport composition in the site's own type system — it
  IS the first page, not a spinner over a blank one. On milez.jp the
  three-column "On | Sound | Off" choice in display serif on black is the
  homepage until you answer.
- Sound-gate variant: two (or three) large text targets; choosing either
  dissolves the gate (600–900ms crossfade) AND seeds the audio policy for the
  whole session. The choice doubles as the user gesture that legally unlocks
  `AudioContext` / unmuted autoplay — the ritual is load-bearing, not
  decorative.
- Title-film variant: a vector or video opening plays with a `SKIP` chip in a
  corner from second 1 (never hide it); SKIP seeks the timeline to its final
  frame and fires the same "loaded" choreography the full watch would — both
  paths converge on identical page state.
- Counter variant: a numeral counting 0→100 in display type, ideally tied to
  REAL asset bytes; on completion the counter itself transforms into the first
  composition (scale/morph), never just disappears.
- The reveal after the gate must be worth the wait: the gate's last frame
  should hand off into the hero with continuity (a shared element, color, or
  motion vector), not a hard cut to an unrelated page.

## Asset requirements

- Title film: 6–12s maximum, designed to be skipped without loss (it sets
  mood, never delivers sole-source information); separate portrait cut for
  mobile.
- Gate typography: the site's display face at hero scale. A generic spinner or
  progress bar voids the entire device.

## Interaction binding

```js
const gate = document.querySelector('.threshold');
function enter(soundOn) {
  sessionStorage.setItem('rituallyEntered', '1');   // once per session, ever
  if (soundOn) audio.unlock();                       // the gesture IS consent
  gate.classList.add('is-leaving');                  // 800ms crossfade
  gate.addEventListener('transitionend', () => gate.remove(), { once: true });
  page.begin();                                      // same entry state for all paths
}
soundOnBtn .addEventListener('click', () => enter(true));
soundOffBtn.addEventListener('click', () => enter(false));
skipChip  ?.addEventListener('click', () => { film.currentTime = film.duration; });
if (sessionStorage.getItem('rituallyEntered')) gate.remove();  // never twice
```

- Fire the ritual ONCE per session (`sessionStorage`); returning visitors and
  internal navigation skip it entirely.
- `prefers-reduced-motion`: collapse to an instant gate (the choice remains,
  the film does not autoplay).
- The gate must be keyboard-operable and the SKIP chip focusable from load.

## UI composition rules

- Nothing else competes on the gate screen: gate composition + at most one
  brand mark.
- SKIP is always visible, always honest (it really skips), styled as a quiet
  chip — never a dark-pattern countdown.
- The audio choice persists site-wide and is reversible via a small persistent
  toggle after entry.

## When to use

- Sound-designed experiences that legally need a gesture anyway — staging the
  consent AS the design converts a browser constraint into brand theatre.
- Brand films, anniversary/microsite one-offs, museum-register pieces, scroll
  journeys where arrival pacing is part of the narrative.

## When NOT to use

- Anything visited twice a day. The ritual is for pilgrimage pages, not tools.
- When the budget can't make the gate itself beautiful — a plain preloader
  pretending to be a ceremony is worse than none.

## Performance notes

- The gate buys real loading time: preload the hero scene behind it. But cap
  the forced wait at ~3s — past that, even a beautiful counter is a spinner.
- Ship the gate's markup inline in the HTML (it must paint instantly, before
  bundles).

## Pairs with (prototype slugs)

- `aesthetic-luxury-cinematic-dark`
- `aesthetic-sculptural-minimal`
- `recipe-brand-story-journey`
- `shell-scroll-journey-scene`

<!-- image: sample-1.png -->
<!-- reason: representative reference — a black viewport holding only "On | Sound | Off" in display serif, with a small SKIP chip variant inset -->
