---
name: woven-repo-conventions
description: Woven-specific overlay on Step three (the stack) - the `prototype.json` declarative manifest (frames / arrows / lanes / links / IA, read by the editor's Canvas / Flow / IA / Entities views), the multi-HTML `index.html` storyboard pattern (when a prototype spans multiple actors / personas / distinct workflows), the file-layout map, and the strong-default / hard-rule distinction. Loaded when writing Step three (the stack) inside this Woven repo.

→ Decision lives in PROTOTYPE.md §"Woven repo conventions - manifests + storyboard".
---

# Woven repo conventions - manifests + storyboard

These overlay Step three (the stack) with Woven-specific orchestration the global skill doesn't carry.

These overlay Step three (the stack) with Woven-specific orchestration the global skill doesn't carry.

### File layout

```
prototype.json   Declarative manifest of frames / arrows / lanes / links / IA (see AGENTS.md)
index.html       CDN scripts (React UMD + htm), loads app.js
data.js          window.DEMO - all mock data here
styles.css       :root token block + every class
*.js             Components by region (or single app.js for small)
```

**`prototype.json` is what the editor reads** to build Canvas / Flow / IA / Entities views - it carries the things that can't be inferred from JSX (which `useState`s are frames, which frames belong to which lane, entity↔entity cardinality, etc.). Write it alongside the source whenever you author a prototype. Shape and round-trip rules live in `AGENTS.md → Source manifests`.

### Multi-HTML layout - `index.html` is the storyboard

When the prototype spans multiple actors / personas / distinct workflows, split into per-page HTMLs and make `index.html` itself the Step 0b storyboard. The editor reads `index.html` as the landing page (`meta.sourceEntry`) AND as the workflow-level documentation that lanes / cross-actor arrows / page inventory are extracted from:

```
prototype.json            Manifest - same shape, but frames declare `entry: "<file>.html"`
index.html                Storyboard: personas, workflows, links to every workflow page
                          ↳ NOT a regular UI page; documents the system at the workflow level
                          ↳ See AGENTS.md → Workflow 1 Step 0b for what to include
data.js                   window.DEMO - shared across all pages (loaded by each)
styles.css                shared token block + every class (loaded by each)
tc-application.html       Workflow page (e.g. TC submits an application)
pxp-applications.html     Workflow page (e.g. PXP reviews the queue)
pxp-cancellation.html     Workflow page (e.g. PXP determines a cancellation fee)
...
```

What the storyboard `index.html` must include for Step 0b to parse cleanly:

- **Personas list** - either a `personas: [...]` array exposed in script, or visible persona-tagged sections in the DOM. Names + roles, e.g. `{ id: "TC", label: "Training Coordinator" }`, `{ id: "PXP", label: "Programme Experience Partner" }`.
- **Workflow cards** - each card tags 1+ personas and links to 1+ pages. A card naming 2+ personas is the signal for a cross-lane handoff arrow. Quote the workflow number / title in the card so it can be lifted into the arrow's `action`.
- **Page inventory** - every workflow page reachable in the prototype, linked from a card. The editor uses this as the canonical frame list (more trustworthy than "every `.html` is a frame").
- **No regular UI chrome.** The storyboard is metadata, not a screen the user dwells on. Style it as documentation - no nav shell, no app affordances.

**The storyboard never appears as editor data.** The information it carries flows *into* `meta.lanes`, `arrows[].action`, and the frame inventory - but the storyboard page itself is **not** a Canvas frame, not a Prototype iframe, not a Flow node, not an IA node, not an entity. It's a spec, like `prototype.json` or `STORYBOARD.md`: it shapes what gets written into `editor/branches/<slug>.js` and then steps out of the picture. Write `index.html` purely for the agent and the human readers; never for the editor's five views.

This pattern is **a strong default for multi-HTML projects, not a hard rule.** If your project is single-HTML or single-actor, skip it - `index.html` is just the landing page (and the editor renders it normally). The storyboard pattern appears the moment you have two or more actors handing work off through the data layer (see AGENTS.md → "Test for cross-actor handoff"). When unsure, either draft the storyboard up front or expect Step 0b's fallback to surface the ambiguity for the human to resolve.

---

