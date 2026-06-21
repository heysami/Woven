# Step four - commit the token vocabulary

The token block at the top of `styles.css` is where most of "design quality" lives. Get it right once; every component below inherits correctness. The *categories* are universal; the *values* are genre-specific (see playbook).

### Categories every prototype needs


```css
:root {
  /* Surfaces */
  --bg: ...; --surface: ...; --surface-2: ...; --border: ...;

  /* Text */
  --text: ...; --text-muted: ...; --text-faint: ...;

  /* Semantic + paired -soft variant */
  --accent: ...;  --accent-soft: ...;
  --success: ...; --success-soft: ...;
  --warning: ...; --warning-soft: ...;
  --danger: ...;  --danger-soft: ...;

  /* Type - sans + one secondary with assigned job */
  --font-sans: "...", system-ui, sans-serif;
  --font-secondary: ...;   /* mono for state, serif for editorial, display for marketing */

  /* Radii - 3 steps */
  --radius-sm: ...; --radius: ...; --radius-lg: ...;

  /* Shadows - 3 steps */
  --shadow-sm: ...; --shadow-md: ...; --shadow-lg: ...;

  /* Spacing - hand-tuned, NOT 4/8/16 multipliers */
  --pad: ...; --pad-sm: ...; --gap: ...;

  /* Shape language - strokes, endcaps, corners, fills */
  --stroke-thin: 1px;
  --stroke: 1.4px;          /* default icon stroke */
  --stroke-bold: 1.75px;
  --endcap: round;          /* round | butt | square - pick ONE */
  --icon-fill: outline;     /* outline | solid | duotone - pick ONE */
}
```



### Universal rules

- **Prefer OKLCH for color.** Lightness is perceptually uniform - what you spec is what you get. RGB/hex lie about lightness and produce neon at "pastel" values.
- **Every semantic color has a paired soft.** Status indicators are always pale-bg + dark-fg or dark-bg + light-fg, never raw saturated fills.
- **Derive states with `color-mix(in oklch, …)`** instead of inventing tokens.
- **Theme switch by attribute**, not class proliferation: `[data-theme="dark"] { ... }`.
- **Type sizes: 5 maximum, hand-tuned**, not 4/8/16 multipliers. Exact sizes per genre (playbook).
- **Two fonts maximum.** The second font has an *assigned job*; never decorative.
- **Line-height does vertical rhythm**, not margins. `1.3-1.4` titles, `1.45-1.6` body.
- **Shape language is one of the tokens.** Pick stroke weight, endcap, corner treatment, icon fill style ONCE and apply across all icons, dividers, charts, image masks. Mixing breaks the system.

### Chroma discipline by genre

| Genre family | Greys chroma | Semantic chroma |
|---|---|---|
| Restrained product UI (Linear, Vercel, Read.cv) | 0.004-0.01 | 0.11-0.16 |
| Editorial / book / paper-feel | 0.002-0.008 | 0.10-0.14 |
| Vibrant marketing / consumer | 0.01-0.02 | 0.16-0.22 |
| Brand-led B2B SaaS | 0.005-0.015 | 0.14-0.20 |
| Y2K / Memphis / loud editorial | 0.02-0.04 | 0.22-0.32 |
| Brutalist | 0 (pure greyscale) | rare, 0.30+ when used |

**Never exceed 0.22 chroma** unless the genre explicitly calls for loudness.
