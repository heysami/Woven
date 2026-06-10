---
# Sample-image references for the System-tab design library. Images sit
# next to this file in prototype/ and were generated via image_gen.
images:
  - src: recipe-scientific-infra-marketing-ui.png
    reason: Full recipe UI mockup.
---
# Scientific infrastructure marketing

A `(shell + style + voice)` bundle for **protocol-paper / HPC / scientific-infrastructure marketing pages** where the brand reads as "published research, not marketed product."

## Picks

- **Shell:** `hero-stack` — read `shell-hero-stack.md`
- **Style:** `restrained-hairline` with `agate-broadsheet` accents — read `style-restrained-hairline.md` and `style-agate-broadsheet.md`
- **Aesthetic:** *(none — the citation discipline is the identity)*
- **Voice:** scientific, paper-citation tone. Headlines reference physics / network / engineering terms ("Sub-microsecond consensus", "Coherent global state propagation"). Authors / contributors / institutional logos visible. Math equations rendered inline.

## Pattern

- Warm off-white surface (`#FAFAFA` / `oklch(98.5% 0.003 80)`) for paper-feel
- Hero with paper-title-style headline (medium weight, no overscaling)
- Author / contributor row directly under the headline (small, monospace or italic serif)
- Math equations rendered with KaTeX or MathJax inline AND as display blocks at section breaks
- Performance dashboards with agate-numeric readouts (latency percentiles, throughput, uptime, geographic distribution) at near-bottom of hero or mid-page
- Sections separated by `1px solid oklch(85% 0.005 80)` hairlines OR by `2px solid black` heavier rules at top-level boundaries (broadsheet-style)
- Figure-numbered diagrams ("Fig. 1: Network topology") with figure captions in mono or italic
- References / footnotes / bibliography section at the end of the page (links to actual papers)
- Optional signature accent (deep red, electric orange) reserved for emphasis only

## Best for

Protocol whitepapers translating to marketing, distributed-systems infrastructure marketing, scientific-compute platform landings, research-tooling brand pages, post-doctoral-spin-out company sites, anywhere the brand wants to read as "this is engineering with citations, not a startup."

## What distinguishes this from existing recipes

- `newspaper-of-record` is editorial-broken-grid + agate-broadsheet — this is hero-stack with agate accents embedded in a marketing scroll.
- `restrained-ai-marketing` is the same shell + style without the math / citation discipline.
- `linear-product-ui` is the app surface, not the paper-as-marketing scroll.
