// Phase 4b - Single source of truth for media providers, models, and skills.
// Modelled on open-design's catalog (apps/daemon/src/media-models.ts) but
// scoped to what the test-harness daemon actually integrates. Loaded into
// window.TH_MEDIA before app.js so React components can read it synchronously.
//
// Adding a new provider/model/skill:
//   1. Append a row in the matching array below.
//   2. If the provider needs a new HTTP shape, add a renderer in serve.py and
//      register it in the RENDERERS dispatch table.
//   3. The UI (skill node, library, settings dialog) picks it up automatically
//      via window.TH_MEDIA - no app.js change required for catalog-only adds.

(function () {
  const PROVIDERS = {
    openai: {
      id: "openai",
      label: "OpenAI",
      hint: "gpt-image-2 · gpt-image-1.5 · gpt-4.1",
      envKey: "TH_OPENAI_API_KEY",
      docsUrl: "https://platform.openai.com/api-keys",
      integrated: true,
      testable: true,
    },
    anthropic: {
      id: "anthropic",
      label: "Anthropic",
      hint: "Claude Opus 4.8 · Sonnet 4.6 · Haiku 4.5 (text models for `llm` / `describe`)",
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
      integrated: false, // listed but not yet wired - surfaces in Settings as "coming soon"
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
      hint: "text→3D · image→3D · textured .glb (async)",
      envKey: "TH_MESHY_API_KEY",
      docsUrl: "https://docs.meshy.ai/",
      integrated: true,
      testable: false, // Meshy has no free test endpoint; first real Run validates the key
    },
    sam3d: {
      id: "sam3d",
      label: "SAM 3D (splat)",
      hint: "image → 3D Gaussian splat .ply · self-hosted GPU service (Modal/RunPod). Set endpoint in media-config.json sam3d.endpoint; key optional.",
      envKey: "TH_SAM3D_API_KEY",
      docsUrl: "https://github.com/facebookresearch/sam-3d-objects",
      integrated: false,
      testable: false, // no free endpoint; the endpoint URL is user-provided
    },
    elevenlabs: {
      id: "elevenlabs",
      label: "ElevenLabs",
      hint: "TTS · sound effects · music (one key, all three)",
      envKey: "TH_ELEVENLABS_API_KEY",
      docsUrl: "https://elevenlabs.io/app/settings/api-keys",
      integrated: true,
      testable: false, // no free test endpoint; first real Run validates the key
    },
    imagerouter: {
      id: "imagerouter",
      label: "ImageRouter",
      hint: "Proxy - one key, dozens of backends",
      envKey: "TH_IMAGEROUTER_API_KEY",
      docsUrl: "https://docs.imagerouter.io/",
      integrated: false,
      testable: false,
    },
    quiver: {
      id: "quiver",
      label: "Quiver AI",
      hint: "Vector-native SVG generation (arrow-1.1) - used by `svg-gen` when this key is configured",
      envKey: "TH_QUIVER_API_KEY",
      docsUrl: "https://docs.quiver.ai/getting-started/quickstart",
      integrated: true,
      testable: false,
    },
    higgsfield: {
      id: "higgsfield",
      label: "Higgsfield",
      hint: "video (DoP image→video) · paste your key as KEY_ID:KEY_SECRET",
      envKey: "TH_HIGGSFIELD_API_KEY",
      docsUrl: "https://cloud.higgsfield.ai/",
      integrated: true,
      // Higgsfield auths with `Authorization: Key KEY_ID:KEY_SECRET` (compound
      // key+secret), NOT a single bearer token. The stored value is the whole
      // "KEY_ID:KEY_SECRET" string; the renderer sends it after `Key `.
      testable: false, // no free test endpoint; first real Run validates the key
    },
    exa: {
      id: "exa",
      label: "Exa",
      hint: "Web search (exa.ai) for the Research assistant",
      envKey: "TH_EXA_API_KEY",
      docsUrl: "https://dashboard.exa.ai/api-keys",
      integrated: true,
      testable: true, // /search with numResults:1 validates the key
    },
  };

  // v3.4.7 (June 2026) - Catalog refreshed against current provider APIs.
  // DEPRECATIONS applied:
  //   • DALL·E 2 + DALL·E 3 - shut down May 12, 2026 (removed entirely).
  //   • gpt-image-1 - scheduled deprecation Oct 23, 2026 (kept with warning).
  //   • Ideogram v2 → v3 (current flagship; v2 endpoint still works).
  //   • Bare `fal-ai/luma-dream-machine` returns "endpoint deprecated"
  //     errors - replaced by the ray-2 family.
  //   • Kling v1 → v2.5 Turbo Pro (cheaper + sharper).
  //   • MiniMax Hailuo 02 → Hailuo 2.3 Fast Pro (newer, faster).
  //   • Sora 2 - deprecated April 26, 2026, API shutdown Sept 24, 2026 (skipped).
  // Sources: OpenAI deprecation announcement (May 2026), fal.ai model docs
  //   (Luma Ray 2, Veo 3.1, Kling 2.5/2.6, Hailuo 2.3, Ideogram V3,
  //   Seedance 2.0), anthropic.com (Claude 4.6 / 4.7 / 4.8 / Haiku 4.5).
  //
  // Image-generation models. provider points into PROVIDERS; integrated:true
  // models can be selected on a skill node. Non-integrated rows are reserved
  // for the future and don't appear in the dropdown.
  const IMAGE_MODELS = [
    // OpenAI - gpt-image-2 is the current flagship (May 2026). gpt-image-1
    // is on the deprecation list (Oct 23, 2026) but still callable.
    { id: "gpt-image-2",       provider: "openai", label: "gpt-image-2",       hint: "OpenAI · current flagship",     caps: ["t2i", "i2i", "inpaint"], integrated: true, default: true },
    { id: "gpt-image-1.5",     provider: "openai", label: "gpt-image-1.5",     hint: "OpenAI · mid-tier",             caps: ["t2i", "i2i", "inpaint"], integrated: true },
    { id: "gpt-image-1",       provider: "openai", label: "gpt-image-1",       hint: "OpenAI · deprecates Oct 2026",  caps: ["t2i", "i2i", "inpaint"], integrated: true },
    { id: "gpt-image-1-mini",  provider: "openai", label: "gpt-image-1-mini",  hint: "OpenAI · low-cost",             caps: ["t2i", "i2i"],            integrated: true },

    // fal.ai - sync endpoints at fal.run/<model-id>
    { id: "fal-ai/flux/schnell",      provider: "fal", label: "flux/schnell",      hint: "fal · FLUX fast (4-step)", caps: ["t2i"], integrated: true },
    { id: "fal-ai/flux/dev",          provider: "fal", label: "flux/dev",          hint: "fal · FLUX dev",           caps: ["t2i"], integrated: true },
    { id: "fal-ai/flux-pro/v1.1",     provider: "fal", label: "flux-pro/v1.1",     hint: "fal · FLUX 1.1 Pro",       caps: ["t2i"], integrated: true },
    { id: "fal-ai/flux-pro/v1.1-ultra", provider: "fal", label: "flux-pro/ultra",  hint: "fal · FLUX 1.1 Ultra (high-res)", caps: ["t2i"], integrated: true },
    { id: "fal-ai/recraft-v3",        provider: "fal", label: "recraft-v3",        hint: "fal · Recraft (vector-friendly)", caps: ["t2i"], integrated: true },
    { id: "fal-ai/ideogram/v3",       provider: "fal", label: "ideogram/v3",       hint: "fal · Ideogram V3 (typography · current)", caps: ["t2i"], integrated: true },
    { id: "fal-ai/stable-diffusion-v35-large", provider: "fal", label: "sd-3.5-large", hint: "fal · SD 3.5", caps: ["t2i"], integrated: true },

    // xAI Grok - not integrated yet (listed for the UI)
    { id: "grok-imagine-image", provider: "xai", label: "grok-imagine-image", hint: "xAI · 2K t2i", caps: ["t2i"], integrated: false },

    // Volcengine - not integrated yet
    { id: "doubao-seedream-3-0-t2i-250415", provider: "volcengine", label: "seedream-3.0", hint: "ByteDance · Doubao", caps: ["t2i"], integrated: false },

    // BFL - not integrated yet (BFL needs polling)
    { id: "flux-pro-1.1", provider: "bfl", label: "flux-1.1-pro", hint: "BFL direct (async)", caps: ["t2i"], integrated: false },

    // Nano Banana / Gemini - not integrated yet
    { id: "gemini-3.1-flash-image-preview", provider: "nanobanana", label: "nano-banana", hint: "Google · t2i", caps: ["t2i"], integrated: false },
  ];

  // Text models for the LLM / describe skills. Both OpenAI + Anthropic share
  // /__llm_run dispatch; daemon picks renderer by `provider`. Refreshed June
  // 2026 with current Anthropic flagship IDs (Opus 4.8 · Sonnet 4.6 · Haiku 4.5).
  // Sonnet 4.5 + Haiku 4.5 (2025-09 / 2025-10 dated) still respond via the
  // dated alias but show up as legacy.
  const TEXT_MODELS = [
    // v3.5 - CLI default sentinels. When picked, the daemon doesn't pass
    // --model and the CLI uses whatever it's configured for (matches the
    // user's `codex login` / `claude login` settings). Both rows show up
    // at the top of their provider's filter so they're easy to find.
    { id: "codex-default",   provider: "openai",    label: "Codex CLI default", hint: "OpenAI · uses Codex CLI's own default model", caps: ["text"],           integrated: true, cliOnly: true },
    { id: "gpt-5",           provider: "openai",    label: "gpt-5",             hint: "OpenAI · current flagship",   caps: ["text", "vision"], integrated: true, default: true },
    { id: "gpt-5-mini",      provider: "openai",    label: "gpt-5-mini",        hint: "OpenAI · fast + cheap",       caps: ["text", "vision"], integrated: true },
    { id: "gpt-5-nano",      provider: "openai",    label: "gpt-5-nano",        hint: "OpenAI · ultra-light",        caps: ["text"],           integrated: true },
    { id: "o3",              provider: "openai",    label: "o3",                hint: "OpenAI · reasoning flagship", caps: ["text"],           integrated: true },
    { id: "o4-mini",         provider: "openai",    label: "o4-mini",           hint: "OpenAI · reasoning · fast",   caps: ["text"],           integrated: true },
    { id: "gpt-4.1",         provider: "openai",    label: "gpt-4.1",           hint: "OpenAI · prior flagship",     caps: ["text"],           integrated: true },
    { id: "gpt-4.1-mini",    provider: "openai",    label: "gpt-4.1-mini",      hint: "OpenAI · prior generation",   caps: ["text"],           integrated: true },
    { id: "gpt-4o",          provider: "openai",    label: "gpt-4o",            hint: "OpenAI · vision-capable",     caps: ["text", "vision"], integrated: true },
    { id: "gpt-4o-mini",     provider: "openai",    label: "gpt-4o-mini",       hint: "OpenAI · legacy fast + cheap",caps: ["text", "vision"], integrated: true },
    { id: "claude-default",        provider: "anthropic", label: "Claude CLI default", hint: "Anthropic · uses Claude CLI's own default model", caps: ["text"], integrated: true, cliOnly: true },
    { id: "claude-opus-4-8",       provider: "anthropic", label: "claude-opus-4.8",    hint: "Anthropic · top reasoning",   caps: ["text", "vision"], integrated: true },
    { id: "claude-opus-4-7",       provider: "anthropic", label: "claude-opus-4.7",    hint: "Anthropic · prior opus",      caps: ["text", "vision"], integrated: true },
    { id: "claude-opus-4-6",       provider: "anthropic", label: "claude-opus-4.6",    hint: "Anthropic · 1M context",      caps: ["text", "vision"], integrated: true },
    { id: "claude-sonnet-4-6",     provider: "anthropic", label: "claude-sonnet-4.6",  hint: "Anthropic · current sonnet",  caps: ["text", "vision"], integrated: true },
    { id: "claude-haiku-4-5",      provider: "anthropic", label: "claude-haiku-4.5",   hint: "Anthropic · fast + cheap",    caps: ["text", "vision"], integrated: true },
  ];

  // Video models. fal rows dispatch through fal's sync POST endpoint and parse
  // via _fal_extract_video_url ({ video: { url } } / { videos: [{ url }] } /
  // { url }); Higgsfield rows dispatch through the async higgsfield renderer.
  // Caps vocabulary:
  //   t2v      = pure text-to-video (no input frame)
  //   i2v      = accepts a START input image the motion is generated from
  //   endframe = ALSO accepts an END/last frame so motion is pinned at both
  //              ends (start+end interpolation). Read by orchestrators that
  //              want two-ended scene control (e.g. motion-studio).
  // Refreshed June 2026 against fal model docs + the Higgsfield SDK.
  //
  // The bare `fal-ai/luma-dream-machine` endpoint is DEPRECATED (returns
  // {"detail":[{"msg":"This endpoint is deprecated…"}]}). Luma now ships
  // under the `/ray-2/...` namespace. Google Veo 3.1 became the new default
  // in May 2026 (best quality + native audio). Kling, Hailuo, Pika all
  // bumped major versions.
  const VIDEO_MODELS = [
    // Default - Veo 3.1 is the current sota text-to-video (with native audio).
    { id: "fal-ai/veo3.1",                                         provider: "fal", label: "veo-3.1",            hint: "fal · Google Veo 3.1 (t2v · native audio)",     caps: ["t2v"],         integrated: true, default: true },
    { id: "fal-ai/veo3.1/fast/image-to-video",                     provider: "fal", label: "veo-3.1-fast-i2v",   hint: "fal · Veo 3.1 Fast (image → video)",            caps: ["i2v"],         integrated: true },
    // Luma - Ray 2 family (the bare `luma-dream-machine` endpoint is deprecated).
    { id: "fal-ai/luma-dream-machine/ray-2/text-to-video",         provider: "fal", label: "luma-ray-2",         hint: "fal · Luma Ray 2 (t2v)",                        caps: ["t2v"],         integrated: true },
    { id: "fal-ai/luma-dream-machine/ray-2/image-to-video",        provider: "fal", label: "luma-ray-2-i2v",     hint: "fal · Luma Ray 2 (image → video)",              caps: ["i2v"],         integrated: true },
    // Kling - v2.5 Turbo Pro is the current cinematic default; v2.6 i2v is newer.
    { id: "fal-ai/kling-video/v2.5-turbo/pro/text-to-video",       provider: "fal", label: "kling-2.5-pro",      hint: "fal · Kling 2.5 Turbo Pro (cinematic)",         caps: ["t2v"],         integrated: true },
    { id: "fal-ai/kling-video/v2.6/pro/image-to-video",            provider: "fal", label: "kling-2.6-pro-i2v",  hint: "fal · Kling 2.6 Pro (image → video + audio)",   caps: ["i2v"],         integrated: true },
    // MiniMax Hailuo - 2.3 Fast is the current entry.
    { id: "fal-ai/minimax/hailuo-2.3-fast/pro/text-to-video",      provider: "fal", label: "hailuo-2.3-fast",    hint: "fal · MiniMax Hailuo 2.3 Fast (1080p)",         caps: ["t2v"],         integrated: true },
    { id: "fal-ai/minimax/hailuo-2.3-fast/pro/image-to-video",     provider: "fal", label: "hailuo-2.3-fast-i2v", hint: "fal · Hailuo 2.3 Fast (image → video)",        caps: ["i2v"],         integrated: true },
    // ByteDance Seedance 2.0 - launched April 2026.
    { id: "fal-ai/seedance-2.0",                                   provider: "fal", label: "seedance-2.0",       hint: "fal · ByteDance Seedance 2.0",                  caps: ["t2v", "i2v"], integrated: true },
    // Pika - v2 Turbo still current.
    { id: "fal-ai/pika/v2/turbo/text-to-video",                    provider: "fal", label: "pika-v2",            hint: "fal · Pika v2 (animated)",                      caps: ["t2v"],         integrated: true },
    // Higgsfield DoP (platform.higgsfield.ai) - image→video with an optional
    // END frame so motion is pinned at both ends. Async submit+poll via
    // serve.py's _higgsfield_generate_video. The end-frame field is best-effort
    // pending live API confirmation (see the serve.py renderer header note).
    { id: "dop-lite",    provider: "higgsfield", label: "Higgsfield DoP Lite",    hint: "Higgsfield · fast preview (image→video, +end frame)", caps: ["i2v", "endframe"], integrated: true },
    { id: "dop-turbo",   provider: "higgsfield", label: "Higgsfield DoP Turbo",   hint: "Higgsfield · 2x faster (image→video, +end frame)",    caps: ["i2v", "endframe"], integrated: true },
    { id: "dop-preview", provider: "higgsfield", label: "Higgsfield DoP Preview", hint: "Higgsfield · top quality (image→video, +end frame)",  caps: ["i2v", "endframe"], integrated: true },
  ];

  // 3D-model generators. caps: `t23d` = text→3D, `i23d` = image→3D. Bytes are
  // a textured `.glb`. Meshy is async (create task → poll → download) and is
  // handled by serve.py's _meshy_generate_3d; the fal rows go through the sync
  // fal.run pipeline (_fal_generate_3d). Both dispatch under the `3d-gen` skill.
  const MODELS_3D = [
    // Meshy - the dedicated 3D provider. Default. Text/image-to-3D are textured
    // (preview→refine bakes PBR). The "-anim" rows add Meshy's rig+animate pass
    // (character/humanoid meshes; needs a plan tier that exposes rigging) - they
    // fall back to the static textured mesh if rigging isn't available.
    { id: "meshy/text-to-3d",      provider: "meshy", label: "Meshy 5 (text→3D)",        hint: "Meshy · prompt → textured .glb (preview+refine)", caps: ["t23d"],         integrated: true, default: true },
    { id: "meshy/image-to-3d",     provider: "meshy", label: "Meshy 5 (image→3D)",       hint: "Meshy · image → textured .glb",                   caps: ["i23d"],         integrated: true },
    { id: "meshy/text-to-3d-anim", provider: "meshy", label: "Meshy 5 (text→animated)",  hint: "Meshy · prompt → textured + rigged + animated .glb (character)", caps: ["t23d"], integrated: true },
    { id: "meshy/image-to-3d-anim",provider: "meshy", label: "Meshy 5 (image→animated)", hint: "Meshy · image → textured + rigged + animated .glb (character)",  caps: ["i23d"], integrated: true },
    // fal - sync 3D endpoints (already wired in serve.py).
    { id: "fal-ai/hyper3d/rodin", provider: "fal",   label: "Rodin (Hyper3D)",    hint: "fal · text/image → 3D (PBR)",                     caps: ["t23d", "i23d"], integrated: true },
    { id: "fal-ai/hunyuan3d-v2",  provider: "fal",   label: "Hunyuan3D v2",       hint: "fal · Tencent Hunyuan3D v2",                      caps: ["t23d", "i23d"], integrated: true },
    { id: "fal-ai/triposr",       provider: "fal",   label: "TripoSR",            hint: "fal · fast image → 3D",                           caps: ["i23d"],         integrated: true },
  ];

  // Audio generation models - ElevenLabs. The single `audio-gen` skill picks
  // a MODE from this list via the model dropdown: tts (voiceover/narration),
  // sfx (sound effect), music (track). All three return mp3 bytes; the daemon
  // renderer (_elevenlabs_generate_audio) branches on the model id. Per-mode
  // knobs (voice_id, duration_seconds, music_length_ms, ...) ride in the node
  // `options`. Requires TH_ELEVENLABS_API_KEY.
  const AUDIO_MODELS = [
    { id: "elevenlabs/tts",   provider: "elevenlabs", label: "Voiceover (TTS)", hint: "ElevenLabs · text → narration .mp3 (eleven_multilingual_v2; voice via options.voice_id)", caps: ["tts"],   integrated: true, default: true },
    { id: "elevenlabs/sfx",   provider: "elevenlabs", label: "Sound effect",    hint: "ElevenLabs · text → SFX .mp3 (≤22s; options.duration_seconds)",                            caps: ["sfx"],   integrated: true },
    { id: "elevenlabs/music", provider: "elevenlabs", label: "Music (beta)",    hint: "ElevenLabs · prompt → music .mp3 (options.music_length_ms)",                               caps: ["music"], integrated: true },
  ];

  // Skill catalog - each entry is a draggable in the Library's Skills section
  // and a node-type once dropped. The skill node renders config controls
  // appropriate to `inputs` / `output` / model dropdown availability.
  const SKILLS = [
    {
      id: "generate-image",
      label: "Generate image",
      hint: "prompt → image · playbook: docs/research/imagegen-playbook.md",
      glyph: "◇",
      pathway: "A",
      inputs: ["prompt"],
      output: "image",
      hasModelDropdown: true,
      modelsFilter: (m) => m.caps && m.caps.includes("t2i") && m.integrated,
      defaultModel: "gpt-image-2",  // v3.4.7 - gpt-image-1 deprecates Oct 23, 2026
      hasAspect: true,
      playbookPath: "docs/research/imagegen-playbook.md",
    },
    {
      // Identity-preserving image-to-image. Takes a raster of ONE subject
      // (character or object) on its `asset` input and re-renders the SAME
      // subject under structured pose/rotation/expression/clothing changes the
      // node's control panel assembles into the prompt. Always i2i, so the
      // model list is filtered to i2i-capable models (gpt-image family) and the
      // dispatcher feeds the subject image as input_path. No `prompt` input -
      // the instruction is built on-node from the pose controls.
      id: "pose-subject",
      label: "Pose / restyle",
      hint: "subject image → re-posed / re-styled image (keeps identity) · rotate axis, change pose / expression / clothes",
      glyph: "⟳",
      pathway: "A",
      inputs: ["asset"],
      output: "image",
      hasModelDropdown: true,
      modelsFilter: (m) => m.caps && m.caps.includes("i2i") && m.integrated,
      defaultModel: "gpt-image-2",
      hasAspect: true,
      playbookPath: "docs/research/imagegen-playbook.md",
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
      // ONE-SHOT ornate 9-slice frame: prompt in, finished frame out. The
      // daemon appends the geometry contract (hollow frame, transparent
      // center, tileable edges), generates, removes the background, and
      // auto-detects the border-image-slice insets - so the user drives it
      // from a SINGLE node, no chain to wire. For ornate frames (gold filigree,
      // carved stone) that the procedural slice9-gen.py cannot draw.
      id: "slice9-frame",
      label: "Slice-9 frame",
      hint: "prompt → 9-slice game-UI frame (generate + cut + auto-slice in one node)",
      glyph: "▦",
      pathway: "A",
      inputs: ["prompt"],
      output: "image",
      hasModelDropdown: true,
      modelsFilter: (m) => m.caps && m.caps.includes("t2i") && m.integrated,
      defaultModel: "gpt-image-2",
      hasAspect: true,
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
      id: "image-to-ply",
      label: "Image → 3D splat",
      hint: "asset → 3D Gaussian splat .ply (hosted on fal · tripo3d/triposplat · no local GPU · needs a fal key). Pipe a background-removed PNG in; out feeds Splat Lab.",
      glyph: "✦",
      pathway: "A",
      provider: "fal",
      model: "tripo3d/triposplat",   // hosted image→splat; daemon also supports provider "sam3d" (self-hosted GPU)
      inputs: ["asset"],
      output: "3d",
      pathwayBExt: "ply",
      hasModelDropdown: false,
      hasAspect: false,
    },
    {
      id: "image-to-glb",
      label: "Image → 3D mesh",
      hint: "asset → textured 3D mesh .glb (hosted on fal · fal-ai/trellis · no local GPU · needs a fal key). Pipe a background-removed PNG in; out feeds Spline 3D / Voxel / model-viewer.",
      glyph: "◈",
      pathway: "A",
      provider: "fal",
      model: "fal-ai/trellis",       // hosted image→mesh; daemon also supports provider "sam3d" (self-hosted GPU)
      inputs: ["asset"],
      output: "3d",
      pathwayBExt: "glb",
      hasModelDropdown: false,
      hasAspect: false,
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
    // ── Pathway B - agent-written single-file HTML visuals. Run spawns Claude
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
        "1. ONE .html file - no external dependencies beyond what the prompt says is OK.\n" +
        "2. A full-window <canvas> with a fragment shader doing the heavy lifting (raymarched / SDF / noise / particles / generative).\n" +
        "3. Use standard browser APIs only. No bundlers. No frameworks unless explicitly requested.\n" +
        "4. Make it VISUALLY STRIKING. Default to bold color, depth, motion. Animate via requestAnimationFrame.\n" +
        "5. Default canvas to 1280×720 and full viewport with resize handling. Cap pixel ratio at 2.\n" +
        "6. Add a tiny title bar (top-left, 12px, low-opacity, no chrome) showing what the scene is.\n" +
        "7. The file must work when opened directly in a browser - no server-side preprocessing.\n" +
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
        "1. ONE .html file. D3 v7, Observable Plot, or vanilla SVG - pick what fits the request best. CDN imports are fine.\n" +
        "2. If the user didn't provide data, INVENT plausible data inline (a tiny dataset matching the request - e.g. 12 rows for a bar chart, 50 points for a scatter) and add a one-line comment saying it's synthetic.\n" +
        "3. Strong typography (system-ui or Inter), restrained axis chrome, accessible color (avoid red/green-only encoding).\n" +
        "4. Responsive: use viewBox + 100% width on the SVG. Default frame ≈ 1200×750.\n" +
        "5. Caption + small note at the bottom-right ('synthetic data - illustrative').\n" +
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
        "2. Realistic, populated mockup - NOT an empty shell. Named entities, specific numbers, voiced microcopy. Never 'User 1' or 'Lorem'.\n" +
        "3. Inline <style> in the <head> using CSS custom properties for tokens (--bg, --surface, --text, --accent, etc.). Tokens cascade from the brief's genre + audience + emotion.\n" +
        "4. Page layout should fit a 1280×800 viewport without horizontal scroll. Use semantic HTML5 (<header>, <main>, <nav>, <article>, etc.).\n" +
        "5. Commit to the requested screen type. If the brief says 'dashboard', show real panels with realistic data; if 'listing', show 8-15 items with varied content; if 'browse', use a grid/masonry with image placeholders + captions.\n" +
        "6. Use <div class=\"img-placeholder\" data-aspect=\"4:3\">PHOTO · café interior</div> for image regions you don't have - DO NOT inline base64 images or hotlink to random URLs.\n" +
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
        "2. Set `viewBox` and `width`/`height` (or just `viewBox` if responsive). Default frame matches the brief; pick 24/48/256/512 for icon-scale, 800-1600 for illustrations.\n" +
        "3. STRUCTURE the SVG cleanly - meaningful <g> groups, layered (background → midground → foreground → highlights), descriptive `id`/`data-name` on each top-level group so the user can later edit one part.\n" +
        "4. Visual quality: respect the genre. UI icons → geometric, ≤20 primitives, 1.5-2px stroke, `stroke=\"currentColor\"`. Illustrations / brand marks → layered shapes, varied stroke widths, gradients / radial fills OK, no flat single-shape drawings. Multi-figure compositions are fine.\n" +
        "5. Color: prefer CSS custom-properties (`var(--accent)`, `var(--surface)`) referencing the active DS's tokens when possible. Otherwise use named tokens / hex with intent (warm/cool/accent).\n" +
        "6. Animation: SMIL (<animate>, <animateTransform>) OK if the brief asks for motion. Otherwise static.\n" +
        "7. NO `<foreignObject>` unless explicitly required. NO inline `style=\"...\"` on every shape - set fills/strokes via attributes or a single <style> block at the top.\n" +
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
        "7. Textures when the style permits: never ship a default-gray hero. Use a provided texture/model file if the prompt names one, otherwise a procedural CanvasTexture (noise / gradient / stripes) toned to the brief's palette. Pixel/retro briefs: low-res textures + NearestFilter.\n" +
        "8. Advanced effects only when the brief earns them (see editor/kinds/3D_CAPABILITIES.md): GPU particles via THREE.Points + ShaderMaterial (pre-allocated, no rAF allocation), water as a Gerstner vertex-shader plane, cloth/strands via small verlet grids, fog first for atmosphere. Honour prefers-reduced-motion by damping, not freezing.\n" +
        "9. If the prompt provides a Spline scene URL (.splinecode), you may use @splinetool/runtime to load and drive it instead of hand-building geometry - never fabricate a .splinecode URL.\n" +
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
        "1. ONE .json file conforming to the Lottie schema (the version that lottie-web / dotLottie players accept - `v` 5.7+).\n" +
        "2. Required top-level keys: `v`, `fr` (frames per second, default 30), `ip` (in-point, default 0), `op` (out-point in frames), `w`, `h` (canvas size in px), `layers` (array of layer objects with `ty` for type, `ks` transforms, `shapes` for shape layers).\n" +
        "3. Author keyframe-driven path morphs / transforms - Lottie's strengths are smooth motion, layered timing, easing. Use Bézier handles in keyframes for natural motion.\n" +
        "4. NO references to external assets (no images, no fonts) unless explicitly requested. Stick to shape layers and gradients.\n" +
        "5. Loop the animation by default (set `op` so the timeline reads cleanly looped), unless the prompt asks for a one-shot.\n" +
        "6. Pick reasonable defaults: 600×600 canvas for icons, 1080×1080 for hero loops, 30 fps.\n" +
        "7. Use the active design system's palette tokens by name when the prompt references brand color (write a comment at the top of the JSON if you can't fit a comment, just stay close to those values).\n" +
        "Output the file with Write to the path the user specifies (.json extension). Validate that your JSON parses - Lottie is strict. If the animation is complex enough that you can't hand-author it cleanly, simplify to a single hero motion (one path morph + one transform) rather than producing invalid JSON.",
    },
    // v4.0 - the "3D editor (Spline-style)" Tool-pathway skill was removed.
    // It is now a first-class node kind `spline-3d` rendered directly on the
    // canvas (Composition section), not a run-a-skill-to-spawn-an-asset step.
    // See editor/kinds/registry.py + WorkflowSpline3DNode in app.js.
    {
      // 3D-model generation → a textured `.glb` written under
      // source/<branch>/models3d/. Pathway A: dispatches to Meshy (async
      // create+poll, preview→refine) or fal (sync) per the picked model's
      // provider. The iframe renders .glb via the existing 3d/<model-viewer>
      // asset card. defaultModel is REQUIRED (see the video-gen note below for
      // why an empty default silently breaks Run).
      id: "3d-gen",
      label: "3D model",
      hint: "prompt → .glb 3D mesh (requires a 3D-gen API key - Meshy / fal)",
      glyph: "⬢",
      pathway: "A",
      defaultModel: "meshy/text-to-3d",
      provider: "meshy",  // belt-and-suspenders: provider resolves even if MODELS_3D isn't loaded yet
      pathwayAFallback: { provider: "meshy", model: "meshy/text-to-3d", ext: "glb" },
      inputs: ["prompt"],
      output: "3d",
      hasModelDropdown: true,
      modelKind: "3d",
      modelsFilter: (m) => m.caps && (m.caps.includes("t23d") || m.caps.includes("i23d")) && m.integrated,
      hasAspect: false,
    },
    {
      // ElevenLabs audio. ONE skill, three modes selected via the model
      // dropdown (AUDIO_MODELS): elevenlabs/tts (voiceover), elevenlabs/sfx
      // (sound effect), elevenlabs/music (track). Pathway A - the daemon
      // renderer _elevenlabs_generate_audio POSTs to ElevenLabs and writes the
      // returned mp3 bytes to source/<branch>/audio/. Per-mode knobs (voice_id,
      // duration_seconds, music_length_ms, prompt_influence) ride in options.
      id: "audio-gen",
      label: "Audio",
      hint: "prompt → .mp3 voiceover / SFX / music (requires an ElevenLabs API key)",
      glyph: "♪",
      pathway: "A",
      defaultModel: "elevenlabs/tts",
      provider: "elevenlabs",  // belt-and-suspenders: resolves even if AUDIO_MODELS isn't loaded yet
      pathwayAFallback: { provider: "elevenlabs", model: "elevenlabs/tts", ext: "mp3" },
      inputs: ["prompt"],
      output: "audio",
      hasModelDropdown: true,
      modelKind: "audio",
      modelsFilter: (m) => m.caps && (m.caps.includes("tts") || m.caps.includes("sfx") || m.caps.includes("music")) && m.integrated,
      hasAspect: false,
    },
    {
      // v3.4.1 - Real video output. The previous "video-gen" definition
      // silently produced HTML motion pieces because no video API was
      // wired in; that was misleading - picking a skill called "Video"
      // should produce video. Now:
      //   • pathwayAFallback dispatches to fal's image-to-video / text-to-
      //     video endpoints first when the fal key is present. The output
      //     extension is `.mp4`. Other providers (Replicate Veo / Runway
      //     Gen-3 / Pika / Luma) can be slotted in here later - they all
      //     return mp4 bytes.
      //   • If NO video provider key is configured, the agent STOPs and
      //     surfaces the limitation in chat (matching the universal
      //     refinement-constraints contract). It does NOT silently fall
      //     back to HTML - a user who wants the HTML motion-graphics path
      //     should pick the separate `motion-gen` skill below.
      id: "video-gen",
      label: "Video",
      hint: "prompt → .mp4 (requires a video-gen API key - fal / replicate / runway / pika)",
      glyph: "🎬",
      pathway: "A",
      // v3.4.6 - defaultModel is the CRITICAL field that was missing.
      // Without it, freshly-dropped video-gen nodes had empty model + empty
      // provider, so Run failed with "Cannot resolve provider for model "
      // (note the trailing blank). The dropdown also showed the first
      // option visually but never fired onChange unless the user
      // explicitly re-picked → looked saved, wasn't.
      // v3.4.7 (June 2026) - Switched default from the deprecated
      // `fal-ai/luma-dream-machine` bare endpoint to Veo 3.1 (current sota,
      // native audio). The bare luma endpoint returns "deprecated" errors.
      defaultModel: "fal-ai/veo3.1",
      provider:     "fal",  // belt-and-suspenders: provider resolves even if VIDEO_MODELS isn't loaded yet
      pathwayAFallback: { provider: "fal", model: "fal-ai/veo3.1", ext: "mp4" },
      inputs: ["prompt"],
      output: "video",
      hasModelDropdown: true,
      modelsFilter: (m) => m.caps && (m.caps.includes("t2v") || m.caps.includes("i2v")),
      hasAspect: true,
    },
    {
      // Video chain - render a sequence of image→video clips and ffmpeg-stitch
      // them into ONE mp4. Two modes, picked by how many images you wire in:
      //   • AUTO-HANDOFF (1 wired image): each line in the prompt box is one
      //     shot; the LAST frame of each clip seeds the next clip's start frame,
      //     so continuity is derived. Works on any i2v model.
      //   • KEYFRAME-ANCHOR (2+ wired images): lay the images out left→right on
      //     the canvas and wire them all in; each consecutive pair becomes one
      //     clip pinned at BOTH ends (imgA→imgB), so the images ARE the chain
      //     (N images → N-1 clips). Prompt lines are optional per-transition
      //     guidance. Higgsfield-only - it's the one provider that can pin an
      //     end frame (that field is best-effort pending live API confirmation).
      //     Anchor order = source-node x-position (left→right).
      // Every clip is image→video, so the model list is filtered to i2v models.
      // The whole chain runs in ONE server-side request, so it can take minutes.
      id: "video-chain",
      label: "Video chain",
      hint: "1 image = auto-handoff (one shot per prompt line); 2+ images wired left→right = keyframe morph A→B→C (Higgsfield) → one stitched .mp4",
      glyph: "⇉",
      pathway: "A",
      defaultModel: "dop-turbo",
      provider: "higgsfield",
      pathwayAFallback: { provider: "higgsfield", model: "dop-turbo", ext: "mp4" },
      inputs: ["prompt", "asset"],
      output: "video",
      hasModelDropdown: true,
      // image→video each step, so only i2v-capable models qualify.
      modelsFilter: (m) => m.caps && m.caps.includes("i2v"),
      hasAspect: true,
    },
    {
      // v3.4.40 - Hyperframes-flavored motion piece. The OLD "video-gen"
      // → "Motion (HTML)" intent now authors files using the Hyperframes
      // composition model (https://github.com/heygen-com/hyperframes):
      // a single HTML file with a #stage root, clip elements timed via
      // data-start / data-duration, and a paused GSAP timeline exposed
      // on window.__timelines so the file is BOTH a Hyperframes-render
      // target AND plays standalone in the browser. Same constraints
      // (no video API), same single-file output.
      id: "motion-gen",
      label: "Motion (HTML)",
      hint: "prompt → .html (looping motion piece authored as a Hyperframes composition - plays in-browser, renders to video via Hyperframes)",
      glyph: "🎞",
      pathway: "B",
      inputs: ["prompt"],
      output: "image",
      hasModelDropdown: false,
      hasAspect: false,
      pathwayBExt: "html",
      pathwayBSystem:
        "You are a motion-graphics author producing a single self-contained HTML page using the HYPERFRAMES composition model (https://github.com/heygen-com/hyperframes). Hyperframes lets you write a video as HTML: a `#stage` element declares the canvas, child elements are `clip`s timed via data-attributes, and a paused GSAP timeline drives every animatable property. The same file plays standalone in any browser AND can be deterministically rendered to a video file by the Hyperframes runtime.\n\n" +
        "MANDATORY FILE STRUCTURE\n" +
        "1. ONE .html file. No external assets unless the brief explicitly supplies them (inline SVGs, data URIs, and inline canvas are fine).\n" +
        "2. Include GSAP from CDN in <head>: <script src=\"https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js\"></script>. GSAP is Hyperframes' default seekable-animation engine.\n" +
        "3. The body contains exactly one root composition: <div id=\"stage\" data-composition-id=\"<slug>\" data-start=\"0\" data-width=\"<W>\" data-height=\"<H>\"> … </div>. Pick W/H from the brief; default 1920×1080 (16:9), or 1080×1920 for portrait, or 1080×1080 for square. data-composition-id is a kebab-case slug describing the scene.\n" +
        "4. Every animatable child of #stage uses `class=\"clip\"` + `data-start=\"<seconds>\"` + `data-duration=\"<seconds>\"`. Audio/video tracks additionally take `data-track-index=\"<n>\"`. CSS positions clips with `position: absolute` inside the relatively-positioned stage.\n" +
        "5. Build ONE GSAP timeline per composition, paused, and expose it on `window.__timelines[<composition-id>]`. Hyperframes' Puppeteer-based renderer seeks this timeline frame-by-frame; without it the scene can't be rendered to video.\n\n" +
        "MANDATORY STAGE CSS\n" +
        "#stage { position: relative; width: var(--w); height: var(--h); overflow: hidden; background: <DS or scene-appropriate color>; }\n" +
        ".clip { position: absolute; }\n" +
        "Use `--w`/`--h` custom properties matching the data-width / data-height so the stage scales cleanly when previewed.\n\n" +
        "MANDATORY TIMELINE BOOTSTRAP - copy this shape, fill in the tweens:\n" +
        "  const TL = gsap.timeline({ paused: true });\n" +
        "  TL.from('#title', { opacity: 0, y: 40, duration: 0.8 }, 1.0);\n" +
        "  // …more tweens, each anchored to an absolute time so it matches the clip's data-start/duration…\n" +
        "  window.__timelines = window.__timelines || {};\n" +
        "  window.__timelines['<composition-id>'] = TL;\n" +
        "  // Standalone-preview fallback: when no Hyperframes renderer is driving the timeline, play it on a loop in the browser. The renderer sets window.__hyperframesRender = true before seeking; that flag suppresses autoplay so seeking remains deterministic.\n" +
        "  if (!window.__hyperframesRender) {\n" +
        "    TL.repeat(-1).repeatDelay(0).play();\n" +
        "    const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;\n" +
        "    if (reduce) TL.progress(0).pause();\n" +
        "  }\n\n" +
        "ANIMATION CHOICES\n" +
        "- GSAP tweens are the default - use them for typography reveals, transforms, opacity, color, clip-path morphs, SVG attribute animation (GSAP handles SVG natively).\n" +
        "- For procedural / particle / generative motion: drop a <canvas class=\"clip\" data-start=\"...\" data-duration=\"...\"> inside #stage, drive it with requestAnimationFrame. To keep the canvas seekable from the GSAP timeline, advance the canvas state from a `time` proxy that the timeline writes to (e.g. TL.to(canvasState, { t: 1, duration: 6, ease: 'none' }, 0)) so the canvas reads canvasState.t each rAF tick and computes its frame deterministically - never read `performance.now()` directly.\n" +
        "- For inline SVG with SMIL: SMIL is NOT seekable by Hyperframes' renderer. Convert SMIL ideas to GSAP tweens on the same SVG nodes instead.\n" +
        "- Three.js / Lottie / Anime.js / WAAPI are all supported by Hyperframes - only reach for them when the brief calls for it; otherwise GSAP-on-DOM/SVG is the lighter default.\n\n" +
        "TIMING & LOOP RULES\n" +
        "- Default total duration ≈ 4-8 s. Cap at 12 s unless the brief asks for longer.\n" +
        "- Set the timeline's intrinsic duration via the last tween's end time; the standalone bootstrap above wraps it in `repeat(-1)` so the in-browser preview loops seamlessly.\n" +
        "- For a clean loop: match the visual state at TL.progress(1) to TL.progress(0). Use `yoyo: true` on the timeline only when the brief calls for ping-pong.\n" +
        "- Every clip's data-start + data-duration must agree with the GSAP tween it controls (the renderer treats data-* as ground truth for when an element is on-screen).\n\n" +
        "PERFORMANCE & A11Y\n" +
        "- Respect `prefers-reduced-motion`: skip the autoplay (`TL.progress(0).pause()`) when the user has it set.\n" +
        "- Cap `window.devicePixelRatio` at 2 for canvas/WebGL. Handle window resize for full-window playback.\n" +
        "- No external network requests beyond the GSAP CDN and any explicitly-supplied assets.\n\n" +
        "OUTPUT\n" +
        "- Write the file with Write to the path the user specifies. Do not print code in chat; just write the file.\n" +
        "- If the brief asks for a real .mp4/.webm, STOP and tell the user to use the `Video` skill instead. The Hyperframes runtime can later convert this HTML composition to video, but that conversion is out of scope here - your job is the composition file itself.",
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
        "4. Respect `prefers-reduced-motion` - pause / freeze the loop when the user has that preference set.\n" +
        "5. Cap `window.devicePixelRatio` at 2. Handle resize.\n" +
        "6. Make it VISUALLY STRIKING - bold motion, layered depth, considered color palette (prefer the active DS's accent tokens).\n" +
        "7. A tiny title bar (top-left, 11px, low-opacity) describing what the scene is. No other chrome.\n" +
        "Output the file with Write to the path the user specifies. Do not print code in chat; just write the file.",
    },
  ];

  // Aspect labels for the dropdown - compact so they fit the skill node
  // alongside a model dropdown without wrapping.
  const ASPECTS = [
    { value: "1:1",  label: "1:1" },
    { value: "3:2",  label: "3:2" },
    { value: "16:9", label: "16:9" },
    { value: "2:3",  label: "2:3" },
    { value: "9:16", label: "9:16" },
  ];

  window.TH_MEDIA = { providers: PROVIDERS, imageModels: IMAGE_MODELS, textModels: TEXT_MODELS, videoModels: VIDEO_MODELS, models3d: MODELS_3D, audioModels: AUDIO_MODELS, skills: SKILLS, aspects: ASPECTS };
})();
