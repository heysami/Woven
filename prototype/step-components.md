# Step seven - flat components, no premature abstractions

- **Copy-paste JSX is fine.** Don't extract `<Card>` / `<Button>` / `<Badge>` until the same pattern appears 5+ times.
- **Inline SVG icons** in a `const Icon = { … }` map. No icon library. ~12 icons covers most prototypes.
- **One CSS file.** Classes per component (`.panel`, `.row`, `.row-team`). No CSS-in-JS, no Tailwind in the output.
- **State is local `useState`** drilled freely. No Context, no Redux, no Zustand.
- **Tabs are `useState('home')`**, not a router.
- **Modals are conditional JSX overlays**, not a portal library.
- **Forms are `useState` per field**, not a form library.
