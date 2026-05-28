// editor/prompts/directions.js
// Phase 3 — visual-direction library for the discovery flow.
//
// One source of truth, two consumers:
//   • `window.TH_DIRECTIONS` (this file) — read by app.js so the chat surface
//     renders direction tiles with real palette swatches + live font samples.
//     Palette colours and font URLs stay in JS so the iframe-free chat UI
//     can preview them without round-tripping through the agent.
//   • `editor/prompts/directions.py` — same data in Python form, fed to the
//     agent's system prompt so it knows which `value` strings to emit when
//     the user picks "Pick a direction for me". The Python module is the
//     authoritative copy at runtime; this JS copy is regenerated to match.
//     If they drift, the chat tiles render but the agent's reply may emit
//     unknown option values — keep them in sync.
//
// Each direction:
//   id          stable kebab-case slug (also the option value the agent emits)
//   label       human-readable title
//   mood        one-line vibe sentence (renders under the title)
//   references  3 short comparable products / sites / movements
//   displayFont Google Fonts family for headings
//   bodyFont    Google Fonts family for body
//   palette     6 hex colours, ordered roughly by visual weight
//                 [ink, page, surface, muted, accent, accent2]
//
// To add a direction: append below AND in `directions.py`. Keep `id` matching.
(function (root) {
  root.TH_DIRECTIONS = [
    {
      id: "editorial-mono",
      label: "Editorial Mono",
      mood: "Print magazine — generous whitespace, considered hierarchy, one warm accent against monochrome.",
      references: ["The Browser Company website", "Are.na", "Magazine-style longform editorial"],
      displayFont: "EB Garamond",
      bodyFont: "Inter",
      palette: ["#0a0a0a", "#fafafa", "#ffffff", "#8a8a8a", "#c2410c", "#f0ece4"],
    },
    {
      id: "trading-floor",
      label: "Trading Floor",
      mood: "Bloomberg-dense. Tabular data, dark panels, every pixel earns its place.",
      references: ["Bloomberg Terminal", "TradingView dark", "Polymarket"],
      displayFont: "IBM Plex Sans",
      bodyFont: "IBM Plex Mono",
      palette: ["#d4d8de", "#0a0e15", "#131822", "#6b7280", "#10b981", "#ef4444"],
    },
    {
      id: "warm-consumer",
      label: "Warm Consumer",
      mood: "Soft and welcoming. Off-white surfaces, terracotta accents, type with a little flourish.",
      references: ["Notion landing pages", "Substack newsletter UI", "Headspace"],
      displayFont: "Fraunces",
      bodyFont: "Inter",
      palette: ["#1f1612", "#fdf6e8", "#faedd6", "#a08570", "#d4634b", "#2e6f5e"],
    },
    {
      id: "control-room",
      label: "Control Room",
      mood: "Industrial control panel. Carbon surfaces, amber accents, mono-flavoured chrome.",
      references: ["NASA mission-control HUDs", "Linear dark theme", "Vercel observability"],
      displayFont: "JetBrains Mono",
      bodyFont: "Inter",
      palette: ["#e8eaed", "#1a1c1f", "#25282d", "#7a838f", "#ffaa00", "#ff3838"],
    },
    {
      id: "brutalist-pop",
      label: "Brutalist Pop",
      mood: "Big type, hard edges, accent-as-statement. The interface is the poster.",
      references: ["Off-White / Virgil Abloh web", "Are.na archive views", "Working Not Working"],
      displayFont: "Space Grotesk",
      bodyFont: "Inter",
      palette: ["#000000", "#f7f4ec", "#ffffff", "#555555", "#ff5500", "#0033ff"],
    },
  ];

  // Google-Fonts URL helper. The chat tile renders "Aa Bb 123" in each
  // direction's display + body fonts; we lazy-inject @font-face on first
  // appearance via the existing font-URL pipeline in app.js. Centralising
  // the URL here keeps the swatch logic dumb.
  root.TH_DIRECTIONS_FONT_URL = function (family) {
    var f = String(family || "").trim().replace(/\s+/g, "+");
    if (!f) return null;
    return "https://fonts.googleapis.com/css2?family=" + f + ":wght@400;600&display=swap";
  };

  // Map an option label/value the agent emitted back to the full direction
  // record. Falls back to a normalised slug match so the agent can phrase
  // labels loosely (e.g. "Editorial Mono", "editorial-mono", "editorialMono").
  root.TH_DIRECTIONS_LOOKUP = function (key) {
    if (!key) return null;
    var k = String(key).trim().toLowerCase()
      .replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
    for (var i = 0; i < root.TH_DIRECTIONS.length; i++) {
      var d = root.TH_DIRECTIONS[i];
      if (d.id === k) return d;
      var labelSlug = d.label.toLowerCase().replace(/\s+/g, "-").replace(/[^a-z0-9-]/g, "");
      if (labelSlug === k) return d;
    }
    return null;
  };
})(window);
