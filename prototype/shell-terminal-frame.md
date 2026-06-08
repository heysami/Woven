# Terminal frame shell

**Tag:** `[dev-tool · split-pane · mono-grid]`

## Structure

Dark canvas styled as terminal. Optional tmux-style split with box-drawing borders.

- Header line: ~/path · branch · time (shell prompt style)
- Main pane: text output, monospace grid
- Optional split: 2/3 panes with `─ │ ┌ ┐ └ ┘ ├ ┤ ┬ ┴ ┼`
- Status line: bottom row with exit code, time, status

Character grid. Padding 12-16px from edges.

## Mandatory interactions

Pseudo-prompt input (typewriter reveal). Tab completion visual. Cursor blink. Status line updates.

## Forbidden

border-radius > 0. box-shadow. Proportional fonts. Lucide icons (use ASCII / text pills `[OK]` `[FAIL]`).

## Best for

CLI marketing pages, dev-tool dashboards, deploy status, AI-coding-agent UIs.

## Pairs well with

Style: terminal-mono (mandatory pairing). Aesthetic: cyberpunk for hacker tone; cassette-futurism for retro corporate.
