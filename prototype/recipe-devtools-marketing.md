# Dev-tools marketing

A `(shell + style + voice)` bundle for **developer-tool and infrastructure-API landing pages** where the marketing surface itself reads like a dashboard.

## Picks

- **Shell:** `hero-stack` — read `shell-hero-stack.md`
- **Style:** `dense-mono-dark` — read `style-dense-mono-dark.md` (currently the Bloomberg-style; this recipe brings it out of canvas-floating into hero-stack marketing)
- **Aesthetic:** *(optional — `cyberpunk-synthwave` for hacker tone if the brief wants it; otherwise none)*
- **Voice:** terse spec-sheet, code-snippet-heavy, exit-code-aware. Documentation as marketing. Numbers without commentary ("99.99% uptime", "<50ms p99").

## Pattern

- Dark surface (`#0E1116` / `oklch(15% 0.01 240)`)
- Hero headline in mono or geist-mono (modest size — 48–64px, not 96+); spec-sheet typography over marketing display
- Live code block at hero or in first feature section — syntax-highlighted, actual API call, copy-to-clipboard
- Mono numerals throughout for any metric (latency, throughput, region count, build times)
- Status pills in semantic colors (success-green, warn-amber, error-red)
- Logo wall as monochrome customer marks
- Optional terminal-frame embedded mid-page for CLI demo

## Best for

API and SDK landing pages, dev-platform marketing (CI/CD, deploy, observability, databases-as-service), infra-SaaS hero pages, crypto-infra marketing (RPC providers, indexers, node services), AI-API marketing where the product is a programmable surface.

## What distinguishes this from existing recipes

- `bloomberg-dashboard` is the app surface (canvas-floating dashboard) — this is the marketing-page for that kind of tool, in hero-stack form.
- `terminal-on-web` is full-bleed terminal frame — this is a marketing scroll with terminal elements embedded.
- `linear-product-ui` is the app, not the page-selling-the-app.
