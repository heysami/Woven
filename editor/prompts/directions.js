/* Visual-direction library for the discovery flow.
   Exposes window.TH_DIRECTIONS (array) and window.TH_DIRECTIONS_LOOKUP (fn).
   Each record maps to a DirectionFormCard tile: palette swatches, font pair,
   mood line, reference tags.  Fonts must be in the DIRECTION_FONT_FAMILIES
   list in app.js so ensureDirectionFonts() loads them on first render. */
window.TH_DIRECTIONS = [
  {
    id:          "editorial-mono",
    label:       "Editorial Mono",
    mood:        "Authoritative and precise - long-form reading, editorial credibility, anchored in print tradition.",
    displayFont: "EB Garamond",
    bodyFont:    "IBM Plex Mono",
    palette:     ["#111111", "#F5F1EB", "#C8B89A", "#E8E2D9", "#6B5B45"],
    references:  ["The Atlantic", "New York Review of Books", "Monocle"],
  },
  {
    id:          "warm-craft",
    label:       "Warm Craft",
    mood:        "Tactile and considered - artisan goods, slow-made products, markets, studios.",
    displayFont: "Fraunces",
    bodyFont:    "Space Grotesk",
    palette:     ["#2C1A0E", "#F7F0E6", "#D4956A", "#A85C38", "#EDE0CF"],
    references:  ["Kinfolk", "Cereal", "Rapha", "Dwell"],
  },
  {
    id:          "minimal-tech",
    label:       "Minimal Tech",
    mood:        "Sharp and purposeful - SaaS dashboards, dev tools, data products, B2B.",
    displayFont: "IBM Plex Sans",
    bodyFont:    "IBM Plex Mono",
    palette:     ["#0F172A", "#F8FAFC", "#3B82F6", "#E2E8F0", "#64748B"],
    references:  ["Linear", "Vercel", "Notion", "Loom"],
  },
  {
    id:          "bold-type",
    label:       "Bold Type",
    mood:        "Loud and confident - agencies, launches, fashion, culture, high-contrast statement.",
    displayFont: "Fraunces",
    bodyFont:    "IBM Plex Sans",
    palette:     ["#0D0D0D", "#FFED00", "#FF2D55", "#FFFFFF", "#1A1A1A"],
    references:  ["A24", "Off-White", "Highsnobiety", "Pitchfork"],
  },
  {
    id:          "bright-modern",
    label:       "Bright Modern",
    mood:        "Optimistic and open - consumer apps, communities, education, wellness.",
    displayFont: "Space Grotesk",
    bodyFont:    "IBM Plex Sans",
    palette:     ["#18181B", "#F4F4F5", "#6366F1", "#A5B4FC", "#EDE9FE"],
    references:  ["Stripe", "Figma", "Duolingo", "Superhuman"],
  },
  {
    id:          "hacker-mono",
    label:       "Hacker Mono",
    mood:        "Terminal-native - CLI tools, open-source projects, technical documentation.",
    displayFont: "JetBrains Mono",
    bodyFont:    "JetBrains Mono",
    palette:     ["#0D1117", "#F0F6FC", "#39D353", "#21262D", "#7EE787"],
    references:  ["GitHub", "GitLab", "Warp", "Railway"],
  },
];

/* Fast lookup by id (and common label aliases). */
(function () {
  const map = {};
  window.TH_DIRECTIONS.forEach(d => { map[d.id] = d; map[d.label] = d; });
  window.TH_DIRECTIONS_LOOKUP = function (key) { return map[key] || null; };
})();
