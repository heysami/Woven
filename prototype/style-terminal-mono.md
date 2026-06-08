# Terminal monospace + box-drawing (style)

**Tag:** `style-terminal-mono`

**Canonical references:** Charm lineage (Bubble Tea, Glamour); Fly.io docs; Warp; Vercel CLI output; tmux + Tokyo Night / Catppuccin / Dracula palettes.

## Surface treatment

**Palette — dark, never near-white background.** Pick one base:
- Tokyo Night `#1a1b26` · Dracula `#282a36` · Catppuccin Mocha `#1e1e2e` · true black `#000000`

**Foreground** is warm off-white — `#c0caf5` or `#cdd6f4`. Never pure `#fff`.
**Dim grey** for secondary text — `#565f89` range.
**Accents** come from the ANSI-16 / 256 palette. Pick ONE as primary, use the others sparingly for status:
- magenta `#bb9af7` · cyan `#7dcfff` · green `#9ece6a` · yellow `#e0af68` · red `#f7768e`

No OKLCH curves. No `color-mix()`. No gradients. Flat indexed colour only.

**Type — monospace ONLY.** JetBrains Mono, Berkeley Mono, IBM Plex Mono, Geist Mono, or MonoLisa. One face for everything — body, headings, code, labels, numerals. Never pair a proportional face for "warmth."

**Sizes:** a single tight grid — 13 / 14 / 16 px. A rare 24 px display size is allowed. Nothing else.
**Line-height:** 1.2–1.3 — terminal-tight, not "readable web body."
**Radius:** `0`. Characters are pixels; nothing curves.
**Borders:** drawn with box-drawing glyphs as text — `─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼ ═ ║ ╔ ╗ ╚ ╝`. CSS `border: 1px solid` is a fallback at best; the real grammar is glyph borders.
**Shadow:** none. No `box-shadow`, no `filter: drop-shadow`, no glow except the natural CRT-style accent text colour itself.

**Decoration grammar:**
- ASCII-art banners / splash blocks at the top of sections.
- Status as bracketed text: `[OK]`, `[WARN]`, `[FAIL]`, `[ ]` / `[x]` for checkboxes.
- Progress bars as `████░░░░ 50%` — never an SVG arc or animated div.
- Diff-style `+` / `-` prefixes for added/removed lines.
- A blinking block / underscore caret where input is expected.

**Forbidden:**
- Any `border-radius > 0`.
- Any `box-shadow`, `text-shadow` (except scanline / CRT effects done deliberately).
- Proportional fonts anywhere — including "just the H1."
- Lucide / Heroicons SVG icons. Use Unicode glyphs (`✓ ✗ → ⚠ ●`) or Nerd Font glyphs only.
- Gradients, glassmorphism, blur.
- Emoji as decoration (technical Unicode glyphs are fine).

**Motion budget:**
- Typewriter reveal — ~20 ms per character for hero strings.
- Caret blink — 1 s square-wave, no fade.
- Spinner glyphs cycling `⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏` at ~80 ms/frame for in-progress states.
- Instant state swaps (`[ ]` → `[x]`) — no transition.
- No CSS `transform: scale()`, no spring physics, no parallax, no ease-in-out curves on anything.

## Failure mode

Monospace text on a white rounded card with a Lucide terminal icon = SaaS cosplaying as a terminal. Any `border-radius > 0`, any `box-shadow`, any second typeface, any "let's add a subtle gradient to the accent" — you've quit the genre. If a designer would call it "elevated," it's wrong.

## Best for

Dev tools, deploy dashboards, CLI marketing pages, infra and database products, AI-coding-agent UIs, self-hosted-app landings, status pages, log viewers, anything where the audience already lives in a real terminal.

## Pairs well with

- Shells: `shell-terminal-frame` (native fit), `shell-three-column-app` (tmux-style panes), `shell-two-column-app`, `shell-top-bar-canvas`, `shell-centered-column` (CLI marketing), `shell-bento-grid` (only if each cell is a `┌─┐` box).
- Aesthetics: `aesthetic-cyberpunk`, `aesthetic-cassette-futurism`, `aesthetic-atompunk`, `aesthetic-pc-98`, `aesthetic-vaporwave` (dark variant), `aesthetic-anti-design`.
