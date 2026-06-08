# Two-column app shell

**Tag:** `[desktop-app · nav + canvas · medium-density]`

## Structure

Sidebar + main content, no inspector.

```css
.app { display: grid; grid-template-columns: 240-280px 1fr; }
```

- Left nav (240-280px): sections, categories, recents
- Center canvas (1fr): content (docs, settings, table) max-width 720-960px

## Density

Medium. Comfortable line-height on docs; compact on admin tables.

## Mandatory interactions

Nav row click swaps content. Active-state highlight. Optional nav search filter. Form save/cancel for settings. Table sort/filter for admin.

## Best for

Documentation sites, CRUD admin, settings panels, helpcenter.

## Pairs well with

Style: restrained-hairline, serif-warm-paper, dense-mono-dark. Aesthetic: typically none.
