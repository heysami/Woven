// Phase 4b — Single source of truth for media providers, models, and skills.
// Modelled on open-design's catalog (apps/daemon/src/media-models.ts) but
// scoped to what the test-harness daemon actually integrates. Loaded into
// window.TH_MEDIA before app.js so React components can read it synchronously.
//
// Adding a new provider/model/skill:
//   1. Append a row in the matching array below.
//   2. If the provider needs a new HTTP shape, add a renderer in serve.py and
//      register it in the RENDERERS dispatch table.
//   3. The UI (skill node, library, settings dialog) picks it up automatically
//      via window.TH_MEDIA — no app.js change required for catalog-only adds.

(function () {
  const PROVIDERS = {
    openai: {
      id: "openai",
      label: "OpenAI",
      hint: "gpt-image-1 · dall-e",
      envKey: "TH_OPENAI_API_KEY",
      docsUrl: "https://platform.openai.com/api-keys",
      integrated: true,
      testable: true,
    },
    anthropic: {
      id: "anthropic",
      label: "Anthropic",
      hint: "Claude Sonnet 4.5 · Haiku 4.5 (text models for `llm` / `describe`)",
      envKey: "TH_ANTHROPIC_API_KEY",
      docsUrl: "https://console.anthropic.com/settings/keys",
      integrated: true,
      testable: true,
    },
    fal: {
      id: "fal",
      label: "fal.ai",
      hint: "FLUX · rembg · upscale · video · 3D (one key, many models)",
      envKey: "TH_FAL_API_KEY",
      docsUrl: "https://fal.ai/dashboard/keys",
      integrated: true,
      testable: false, // fal has no free test endpoint; first real Run validates the key
    },
    xai: {
      id: "xai",
      label: "xAI Grok Imagine",
      hint: "grok-imagine-image (2K)",
      envKey: "TH_XAI_API_KEY",
      docsUrl: "https://console.x.ai/",
      integrated: false, // listed but not yet wired — surfaces in Settings as "coming soon"
      testable: false,
    },
    volcengine: {
      id: "volcengine",
      label: "Volcengine Ark (Doubao)",
      hint: "Seedream image · Seedance video",
      envKey: "TH_VOLCENGINE_API_KEY",
      docsUrl: "https://www.volcengine.com/docs/82379",
      integrated: false,
      testable: false,
    },
    bfl: {
      id: "bfl",
      label: "Black Forest Labs",
      hint: "FLUX 1.1 Pro / Pro / Dev / Schnell · direct",
      envKey: "TH_BFL_API_KEY",
      docsUrl: "https://api.bfl.ai/",
      integrated: false,
      testable: false,
    },
    recraft: {
      id: "recraft",
      label: "Recraft",
      hint: "Vector SVG output · raster · brand-asset grade",
      envKey: "TH_RECRAFT_API_KEY",
      docsUrl: "https://www.recraft.ai/docs",
      integrated: false,
      testable: false,
    },
    nanobanana: {
      id: "nanobanana",
      label: "Nano Banana (Gemini)",
      hint: "Google · text-to-image via Gemini",
      envKey: "TH_GEMINI_API_KEY",
      docsUrl: "https://aistudio.google.com/apikey",
      integrated: false,
      testable: false,
    },
    leonardo: {
      id: "leonardo",
      label: "Leonardo.ai",
      hint: "Phoenix · Kino XL · FLUX (async)",
      envKey: "TH_LEONARDO_API_KEY",
      docsUrl: "https://app.leonardo.ai/api-access",
      integrated: false,
      testable: false,
    },
    meshy: {
      id: "meshy",
      label: "Meshy",
      hint: "3D mesh (.glb) generation",
      envKey: "TH_MESHY_API_KEY",
      docsUrl: "https://docs.meshy.ai/",
      integrated: false,
      testable: false,
    },
    elevenlabs: {
      id: "elevenlabs",
      label: "ElevenLabs",
      hint: "TTS · voice clone · SFX",
      envKey: "TH_ELEVENLABS_API_KEY",
      docsUrl: "https://elevenlabs.io/app/settings/api-keys",
      integrated: false,
      testable: false,
    },
    imagerouter: {
      id: "imagerouter",
      label: "ImageRouter",
      hint: "Proxy — one key, dozens of backends",
      envKey: "TH_IMAGEROUTER_API_KEY",
      docsUrl: "https://docs.imagerouter.io/",
      integrated: false,
      testable: false,
    },
    quiver: {
      id: "quiver",
      label: "Quiver AI",
      hint: "Vector-native SVG generation (arrow-1.1) — used by `svg-gen` when this key is configured",
      envKey: "TH_QUIVER_API_KEY",
      docsUrl: "https://docs.quiver.ai/getting-started/quickstart",
      integrated: true,
      testable: false,
    },
  };

  // Image-generation models. provider points into PROVIDERS; integrated:true
  // models can be selected on a skill node. Non-integrated rows are reserved
  // for the future and don't appear in the dropdown.
  const IMAGE_MODELS = [
    // OpenAI
    { id: "gpt-image-1",       provider: "openai", label: "gpt-image-1",       hint: "OpenAI · current",       caps: ["t2i", "i2i", "inpaint"], integrated: true, default: true },
    { id: "gpt-image-1-mini",  provider: "openai", label: "gpt-image-1-mini",  hint: "OpenAI · low-cost",      caps: ["t2i", "i2i"],            integrated: true },
    { id: "dall-e-3",          provider: "openai", label: "dall-e-3",          hint: "OpenAI · classic",       caps: ["t2i"],                   integrated: true },
    { id: "dall-e-2",          provider: "openai", label: "dall-e-2",          hint: "OpenAI · legacy",        caps: ["t2i"],                   integrated: true },

    // fal.ai — sync endpoints at fal.run/<model-id>
    { id: "fal-ai/flux/schnell",      provider: "fal", label: "flux/schnell",      hint: "fal · FLUX fast (4-step)", caps: ["t2i"], integrated: true },
    { id: "fal-ai/flux/dev",          provider: "fal", label: "flux/dev",          hint: "fal · FLUX dev",           caps: ["t2i"], integrated: true },
    { id: "fal-ai/flux-pro/v1.1",     provider: "fal", label: "flux-pro/v1.1",     hint: "fal · FLUX 1.1 Pro",       caps: ["t2i"], integrated: true },
    { id: "fal-ai/flux-pro/v1.1-ultra", provider: "fal", label: "flux-pro/ultra",  hint: "fal · FLUX 1.1 Ultra (high-res)", caps: ["t2i"], integrated: true },
    { id: "fal-ai/recraft-v3",        provider: "fal", label: "recraft-v3",        hint: "fal · Recraft (vector-friendly)", caps: ["t2i"], integrated: true },
    { id: "fal-ai/ideogram/v2",       provider: "fal", label: "ideogram/v2",       hint: "fal · Ideogram (typography)", caps: ["t2i"], integrated: true },
    { id: "fal-ai/stable-diffusion-v35-large", provider: "fal", label: "sd-3.5-large", hint: "fal · SD 3.5", caps: ["t2i"], integrated: true },

    // xAI Grok — not integrated yet (listed for the UI)
    { id: "grok-imagine-image", provider: "xai", label: "grok-imagine-image", hint: "xAI · 2K t2i", caps: ["t2i"], integrated: false },

    // Volcengine — not integrated yet
    { id: "doubao-seedream-3-0-t2i-250415", provider: "volcengine", label: "seedream-3.0", hint: "ByteDance · Doubao", caps: ["t2i"], integrated: false },

    // BFL — not integrated yet (BFL needs polling)
    { id: "flux-pro-1.1", provider: "bfl", label: "flux-1.1-pro", hint: "BFL direct (async)", caps: ["t2i"], integrated: false },

    // Nano Banana / Gemini — not integrated yet
    { id: "gemini-3.1-flash-image-preview", provider: "nanobanana", label: "nano-banana", hint: "Google · t2i", caps: ["t2i"], integrated: false },
  ];

  // Phase 4c — text models for the LLM / describe skills. Phase-4 finisher
  // adds Anthropic Claude (Sonnet 4.5 / Haiku 4.5) as a second integrated
  // text provider. Both providers use the same `/__llm_run` dispatch; the
  // daemon picks the renderer by `provider`.
  const TEXT_MODELS = [
    { id: "gpt-4o-mini",     provider: "openai",    label: "gpt-4o-mini",       hint: "OpenAI · fast + cheap",       caps: ["text", "vision"], integrated: true, default: true },
    { id: "gpt-4o",          provider: "openai",    label: "gpt-4o",            hint: "OpenAI · vision-capable",     caps: ["text", "vision"], integrated: true },
    { id: "gpt-4.1-mini",    provider: "openai",    label: "gpt-4.1-mini",      hint: "OpenAI · current generation", caps: ["text"],           integrated: true },
    { id: "gpt-4.1",         provider: "openai",    label: "gpt-4.1",           hint: "OpenAI · flagship text",      caps: ["text"],           integrated: true },
    { id: "claude-sonnet-4-5-20250929", provider: "anthropic", label: "claude-sonnet-4.5", hint: "Anthropic · flagship",     caps: ["text", "vision"], integrated: true },
    { id: "claude-haiku-4-5-20251001",  provider: "anthropic", label: "claude-haiku-4.5",  hint: "Anthropic · fast + cheap", caps: ["text", "vision"], integrated: true },
  ];

  // Skill catalog — each entry is a draggable in the Library's Skills section
  // and a node-type once dropped. The skill node renders config controls
  // appropriate to `inputs` / `output` / model dropdown availability.
  const SKILLS = [
    {
      id: "generate-image",
      label: "Generate image",
      hint: "prompt → image",
      glyph: "◇",
      pathway: "A",
      inputs: ["prompt"],
      output: "image",
      hasModelDropdown: true,
      modelsFilter: (m) => m.caps && m.caps.includes("t2i") && m.integrated,
      defaultModel: "gpt-image-1",
      hasAspect: true,
    },
    {
      id: "rembg",
      label: "Remove background",
      hint: "asset → image (local · pip install rembg · no API key)",
      glyph: "✂",
      pathway: "Local",
      provider: "local",
      model: "u2net",
      inputs: ["asset"],
      output: "image",
      hasModelDropdown: false,
      hasAspect: false,
    },
    {
      id: "upscale",
      label: "Upscale image",
      hint: "asset → image (4× by default)",
      glyph: "↑",
      pathway: "A",
      provider: "fal",
      model: "fal-ai/clarity-upscaler",
      inputs: ["asset"],
      output: "image",
      hasModelDropdown: false,
      hasAspect: false,
      defaultOptions: { upscale_factor: 2 },
    },
    {
      id: "llm",
      label: "LLM call",
      hint: "prompt → text · use for rewriting / expanding prompts before generation",
      glyph: "Σ",
      pathway: "A",
      inputs: ["prompt"],
      output: "text",
      hasModelDropdown: true,
      modelsFilter: (m) => m.caps && m.caps.includes("text") && m.integrated,
      defaultModel: "gpt-4o-mini",
      modelKind: "text",
    },
    {
      id: "describe",
      label: "Describe image",
      hint: "asset → text · GPT-4o-mini vision",
      glyph: "👁",
      pathway: "A",
      inputs: ["asset"],
      output: "text",
      hasModelDropdown: true,
      modelsFilter: (m) => m.caps && m.caps.includes("vision") && m.integrated,
      defaultModel: "gpt-4o-mini",
      modelKind: "text",
    },
    // ── Pathway B — agent-written single-file HTML visuals. Run spawns Claude
    // Code (no external image API) with a curated system prompt; the agent
    // writes one .html file under source/<branch>/ that the iframe can load.
    // No API key needed beyond Claude itself. Aspect / model dropdown hidden
    // because the output is browser-rendered HTML, not a raster image.
    {
      id: "shader",
      label: "Shader scene",
      hint: "prompt → inline WebGL shader page (Claude writes .html)",
      glyph: "✦",
      pathway: "B",
      inputs: ["prompt"],
      output: "image",
      hasModelDropdown: false,
      hasAspect: false,
      pathwayBExt: "html",
      pathwayBSystem:
        "You are a creative coder producing a single, self-contained HTML page with an inline WebGL or WebGL2 shader. Constraints:\n" +
        "1. ONE .html file — no external dependencies beyond what the prompt says is OK.\n" +
        "2. A full-window <canvas> with a fragment shader doing the heavy lifting (raymarched / SDF / noise / particles / generative).\n" +
        "3. Use standard browser APIs only. No bundlers. No frameworks unless explicitly requested.\n" +
        "4. Make it VISUALLY STRIKING. Default to bold color, depth, motion. Animate via requestAnimationFrame.\n" +
        "5. Default canvas to 1280×720 and full viewport with resize handling. Cap pixel ratio at 2.\n" +
        "6. Add a tiny title bar (top-left, 12px, low-opacity, no chrome) showing what the scene is.\n" +
        "7. The file must work when opened directly in a browser — no server-side preprocessing.\n" +
        "Output the file with Write to the path the user specifies. Do not print code in chat; just write the file.",
    },
    {
      id: "viz",
      label: "Data viz",
      hint: "prompt → inline data visualization page (Claude writes .html)",
      glyph: "📈",
      pathway: "B",
      inputs: ["prompt"],
      output: "image",
      hasModelDropdown: false,
      hasAspect: false,
      pathwayBExt: "html",
      pathwayBSystem:
        "You are a data-visualization specialist producing a single self-contained HTML page. Constraints:\n" +
        "1. ONE .html file. D3 v7, Observable Plot, or vanilla SVG — pick what fits the request best. CDN imports are fine.\n" +
        "2. If the user didn't provide data, INVENT plausible data inline (a tiny dataset matching the request — e.g. 12 rows for a bar chart, 50 points for a scatter) and add a one-line comment saying it's synthetic.\n" +
        "3. Strong typography (system-ui or Inter), restrained axis chrome, accessible color (avoid red/green-only encoding).\n" +
        "4. Responsive: use viewBox + 100% width on the SVG. Default frame ≈ 1200×750.\n" +
        "5. Caption + small note at the bottom-right ('synthetic data — illustrative').\n" +
        "6. No interactive frameworks (no React/Vue). Tooltips via inline JS are fine.\n" +
        "Output the file with Write to the path the user specifies. Do not print code in chat; just write the file.",
    },
    {
      id: "html-page",
      label: "HTML page mockup",
      hint: "prompt → single .html page mockup of a UI screen (Claude writes the page)",
      glyph: "▣",
      pathway: "B",
      inputs: ["prompt"],
      output: "image",
      hasModelDropdown: false,
      hasAspect: false,
      pathwayBExt: "html",
      pathwayBSystem:
        "You are a senior product designer producing a single self-contained HTML page mockup of a UI screen. Constraints:\n" +
        "1. ONE .html file. No external dependencies beyond a CDN font and (optionally) a single Google Fonts link. NO React/Vue/build step, NO charting libraries unless the brief is explicitly a dashboard.\n" +
        "2. Realistic, populated mockup — NOT an empty shell. Named entities, specific numbers, voiced microcopy. Never 'User 1' or 'Lorem'.\n" +
        "3. Inline <style> in the <head> using CSS custom properties for tokens (--bg, --surface, --text, --accent, etc.). Tokens cascade from the brief's genre + audience + emotion.\n" +
        "4. Page layout should fit a 1280×800 viewport without horizontal scroll. Use semantic HTML5 (<header>, <main>, <nav>, <article>, etc.).\n" +
        "5. Commit to the requested screen type. If the brief says 'dashboard', show real panels with realistic data; if 'listing', show 8-15 items with varied content; if 'browse', use a grid/masonry with image placeholders + captions.\n" +
        "6. Use <div class=\"img-placeholder\" data-aspect=\"4:3\">PHOTO · café interior</div> for image regions you don't have — DO NOT inline base64 images or hotlink to random URLs.\n" +
        "7. Add ONE small interaction if it adds to the mockup (a tab strip switching content, a hover state on rows, a dropdown opening). Use vanilla JS in a single inline <script>.\n" +
        "8. End with a tiny footer line (12px, low-opacity): 'mockup · <screen-type> · <genre>'.\n" +
        "Output the file with Write to the path the user specifies. Do not print code in chat; just write the file.",
    },
    {
      id: "svg-gen",
      label: "SVG illustration",
      hint: "prompt → standalone .svg (Quiver AI if `quiver` key is set, else Claude writes vector markup)",
      glyph: "▲",
      pathway: "B",
      // Pathway-A fallback. When `runSkill` runs an svg-gen node, it tries
      // POSTing to /__asset_generate with this provider/model first. If the
      // user has a Quiver key configured, Quiver returns the SVG directly
      // and we skip the slow Claude-writes-SVG dispatch. If the daemon
      // returns 502 "no api key configured", we silently fall through to
      // Pathway B so the node still works without a key.
      pathwayAFallback: { provider: "quiver", model: "arrow-1.1", ext: "svg" },
      inputs: ["prompt"],
      output: "image",
      hasModelDropdown: false,
      hasAspect: false,
      pathwayBExt: "svg",
      pathwayBSystem:
        "You are a vector illustration specialist producing a single, self-contained .svg file. Constraints:\n" +
        "1. ONE valid <svg> document. No external resources, no <image href=...> to bitmaps, no JS unless explicitly requested.\n" +
        "2. Set `viewBox` and `width`/`height` (or just `viewBox` if responsive). Default frame matches the brief; pick 24/48/256/512 for icon-scale, 800–1600 for illustrations.\n" +
        "3. STRUCTURE the SVG cleanly — meaningful <g> groups, layered (background → midground → foreground → highlights), descriptive `id`/`data-name` on each top-level group so the user can later edit one part.\n" +
        "4. Visual quality: respect the genre. UI icons → geometric, ≤20 primitives, 1.5–2px stroke, `stroke=\"currentColor\"`. Illustrations / brand marks → layered shapes, varied stroke widths, gradients / radial fills OK, no flat single-shape drawings. Multi-figure compositions are fine.\n" +
        "5. Color: prefer CSS custom-properties (`var(--accent)`, `var(--surface)`) referencing the active DS's tokens when possible. Otherwise use named tokens / hex with intent (warm/cool/accent).\n" +
        "6. Animation: SMIL (<animate>, <animateTransform>) OK if the brief asks for motion. Otherwise static.\n" +
        "7. NO `<foreignObject>` unless explicitly required. NO inline `style=\"...\"` on every shape — set fills/strokes via attributes or a single <style> block at the top.\n" +
        "Output the SVG with Write to the path the user specifies (.svg extension). The first line of the file should be `<?xml version=\"1.0\" encoding=\"UTF-8\"?>` or directly `<svg ...>`. Do not print code in chat; just write the file.",
    },
    {
      id: "threejs",
      label: "3D scene",
      hint: "prompt → inline three.js scene (Claude writes .html)",
      glyph: "▦",
      pathway: "B",
      inputs: ["prompt"],
      output: "image",
      hasModelDropdown: false,
      hasAspect: false,
      pathwayBExt: "html",
      pathwayBSystem:
        "You are a 3D scene developer producing a single self-contained HTML page with three.js. Constraints:\n" +
        "1. ONE .html file. Import three.js + OrbitControls from a CDN (esm.sh or unpkg). Use a recent three.js (r155+).\n" +
        "2. PerspectiveCamera, AmbientLight + DirectionalLight (with shadow if it adds to the scene), OrbitControls.\n" +
        "3. Make the scene visually rich: meaningful materials, at least one animated element, considered composition.\n" +
        "4. Full-window <canvas>, resize handling, pixelRatio capped at 2.\n" +
        "5. A tiny help line bottom-center: 'drag to orbit · scroll to zoom'.\n" +
        "6. No bundlers, no TypeScript. Plain ES modules via <script type=\"module\">.\n" +
        "Output the file with Write to the path the user specifies. Do not print code in chat; just write the file.",
    },
    {
      id: "lottie-gen",
      label: "Lottie animation",
      hint: "prompt → standalone .json (Lottie JSON, plays in lottie-web / dotlottie)",
      glyph: "◉",
      pathway: "B",
      inputs: ["prompt"],
      output: "image",
      hasModelDropdown: false,
      hasAspect: false,
      pathwayBExt: "json",
      pathwayBSystem:
        "You are a Lottie animation author producing a single self-contained Bodymovin JSON file. Constraints:\n" +
        "1. ONE .json file conforming to the Lottie schema (the version that lottie-web / dotLottie players accept — `v` 5.7+).\n" +
        "2. Required top-level keys: `v`, `fr` (frames per second, default 30), `ip` (in-point, default 0), `op` (out-point in frames), `w`, `h` (canvas size in px), `layers` (array of layer objects with `ty` for type, `ks` transforms, `shapes` for shape layers).\n" +
        "3. Author keyframe-driven path morphs / transforms — Lottie's strengths are smooth motion, layered timing, easing. Use Bézier handles in keyframes for natural motion.\n" +
        "4. NO references to external assets (no images, no fonts) unless explicitly requested. Stick to shape layers and gradients.\n" +
        "5. Loop the animation by default (set `op` so the timeline reads cleanly looped), unless the prompt asks for a one-shot.\n" +
        "6. Pick reasonable defaults: 600×600 canvas for icons, 1080×1080 for hero loops, 30 fps.\n" +
        "7. Use the active design system's palette tokens by name when the prompt references brand color (write a comment at the top of the JSON if you can't fit a comment, just stay close to those values).\n" +
        "Output the file with Write to the path the user specifies (.json extension). Validate that your JSON parses — Lottie is strict. If the animation is complex enough that you can't hand-author it cleanly, simplify to a single hero motion (one path morph + one transform) rather than producing invalid JSON.",
    },
    {
      id: "video-gen",
      label: "Video / motion",
      hint: "prompt → .html (inline <video> with motion graphics / CSS animation fallback)",
      glyph: "🎬",
      pathway: "B",
      inputs: ["prompt"],
      output: "image",
      hasModelDropdown: false,
      hasAspect: false,
      pathwayBExt: "html",
      pathwayBSystem:
        "You are a motion-graphics author producing a single self-contained HTML page that plays a short looping motion piece. We DON'T have a generative video API wired in; instead you compose motion using web primitives. Constraints:\n" +
        "1. ONE .html file with a full-window stage. Pick the right tool for the brief:\n" +
        "   - CSS keyframes + transforms / clip-paths for typography & layout motion (text reveals, banner loops, marquees).\n" +
        "   - Inline SVG with SMIL or CSS animation for vector motion (icons that animate, illustrated loops).\n" +
        "   - <canvas> + requestAnimationFrame for procedural / particle / generative motion.\n" +
        "2. The piece must LOOP cleanly. Match the start and end frames so playback is seamless.\n" +
        "3. Default duration ≈ 4–8 s. Cap at 12 s unless the brief asks for longer.\n" +
        "4. NO external assets unless explicitly requested. NO video files (we can't generate them) — author everything inline.\n" +
        "5. Performance: respect `prefers-reduced-motion` (pause / freeze when set), cap pixelRatio at 2, throttle rAF below 60fps if heavy.\n" +
        "6. Render full-window with `position: fixed; inset: 0` on the stage. Black or DS-palette background. No chrome.\n" +
        "If the brief explicitly asks for a real video (mp4/webm), say in a small inline comment that no video-API is integrated and produce a CSS/SVG/canvas fallback that approximates the intent — the user can swap to a real .mp4 later.\n" +
        "Output the file with Write to the path the user specifies. Do not print code in chat; just write the file.",
    },
    {
      id: "canvas-gen",
      label: "Canvas motion / particles",
      hint: "prompt → inline canvas2D / WebGL motion page (Claude writes .html)",
      glyph: "❋",
      pathway: "B",
      inputs: ["prompt"],
      output: "image",
      hasModelDropdown: false,
      hasAspect: false,
      pathwayBExt: "html",
      pathwayBSystem:
        "You are a creative-coding author producing a single self-contained HTML page driven by canvas2D or WebGL. Use this when the brief calls for ambient motion, particle systems, dust / snow / confetti / sparks, fluid simulation lite, flow fields, generative pattern motion, or anything where the IDIOM is a real-time CPU/GPU loop rather than baked keyframes. Constraints:\n" +
        "1. ONE .html file. Full-window <canvas>. No external dependencies beyond what the prompt allows.\n" +
        "2. Pick canvas2D for ≤500 particles / simple alpha-blended shapes; WebGL (or WebGL2) with instanced draw for ≥500 particles, custom blending, or per-particle shaders.\n" +
        "3. requestAnimationFrame loop. Object-pool particles in canvas2D mode to avoid GC churn. Use transform-feedback or instanced uniforms for WebGL state updates.\n" +
        "4. Respect `prefers-reduced-motion` — pause / freeze the loop when the user has that preference set.\n" +
        "5. Cap `window.devicePixelRatio` at 2. Handle resize.\n" +
        "6. Make it VISUALLY STRIKING — bold motion, layered depth, considered color palette (prefer the active DS's accent tokens).\n" +
        "7. A tiny title bar (top-left, 11px, low-opacity) describing what the scene is. No other chrome.\n" +
        "Output the file with Write to the path the user specifies. Do not print code in chat; just write the file.",
    },
  ];

  // Aspect labels for the dropdown — compact so they fit the skill node
  // alongside a model dropdown without wrapping.
  const ASPECTS = [
    { value: "1:1",  label: "1:1" },
    { value: "3:2",  label: "3:2" },
    { value: "16:9", label: "16:9" },
    { value: "2:3",  label: "2:3" },
    { value: "9:16", label: "9:16" },
  ];

  window.TH_MEDIA = { providers: PROVIDERS, imageModels: IMAGE_MODELS, textModels: TEXT_MODELS, skills: SKILLS, aspects: ASPECTS };
})();
