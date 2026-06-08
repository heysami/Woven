# Three-column app shell

**Tag:** `[desktop-app · nav + canvas + inspector · high-density]`

## Structure

Linear/Bloomberg/Vercel-style dense product UI.

```css
.app { display: grid; grid-template-columns: 240-280px 1fr 320-360px; height: 100vh; }
```

- Left nav (240-280px): workspaces, projects, filters
- Center canvas (1fr): list, detail, table, kanban
- Right inspector (320-360px): properties, comments, history (collapsible)

## Macro proportions

Recalled: 260+1fr+340 or 280+1fr+360. Don't invent.

## Density

High. Hairline rows (28-32px), tabular numerals, status pills.

## Mandatory interactions

Nav row click swaps center content. List row click loads detail OR opens inspector. Inspector collapse/expand. Cmd+K palette. Filter/sort. Multi-select.

## Forbidden

Marketing hero. Full-bleed images. Mobile tab bar.

## Best for

Productivity tools, project trackers, observability, CRM, BI tools.

## Pairs well with

Style: restrained-hairline (Linear), dense-mono-dark (Bloomberg), glassmorphism. Aesthetic: typically none.
