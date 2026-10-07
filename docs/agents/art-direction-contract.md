# Art-direction contract fields

Read only during finalization, after the chosen plate and crops have been inspected.
Creative descriptions remain free-form. Supply each project-specific decision once.
The assembler fills contractVersion (1 for a first contract), bindingRules,
voice.addressPrinciple, voice.copyAntiPatterns, and buildRegister.antiVoice from
`$TH_PROTOCOL_ROOT/editor/art-direction-defaults.json`. Omit those shared fields
unless an explicitly approved exception needs a different value. It does not
invent missing creative decisions. All supplied values are retained exactly.
For revisions supply the incremented contractVersion and all prior decisions
that still apply. Read the previous contract before making a revision.

```jsonc
{
  "projectId": "<project>",
  "contractVersion": 1,
  "platePath": "workflow/artdirection/north-star-<chosen>.png",
  "candidatesConsidered": ["north-star-1.png", "north-star-2.png"],   // when a set was generated

  "extracted": {
    "moodWords": ["<3-5 words the plate actually evokes>"],
    "palette": [
      { "hex": "#0e1620", "role": "ground",  "usage": "decorative", "ratio": 0.55 },
      { "hex": "#efe7d6", "role": "surface", "usage": "semantic",   "ratio": 0.20 },
      { "hex": "#7ad9c4", "role": "glow",    "usage": "illustration","ratio": 0.15 },
      { "hex": "#241a12", "role": "ink",     "usage": "semantic",   "ratio": 0.10 }
    ],                                       // ratios ~sum to 1.0 - this IS the colour-use ratio the brief asked for
    "valueStructure": "low-key, single luminous focal against deep ground",
    "contrastRegister": "high local contrast at the glow, low everywhere else",
    "lightModel": { "direction": "from the subject outward", "softness": "very soft bloom", "bloom": true },
    "materialRead": {
      "imagery": "iridescent, gradient-rich, soft-render",
      "uiSurfaces": "<HOW this material logic should manifest on chrome - e.g. 'matte warm paper that catches a faint glow at edges near the focal, never glossy'>",
      "reactiveBudget": "subtle | rich | theatrical"
    },
    "composition": {
      "negativeSpaceRatio": "high",
      "focalStrategy": "single hero glow per view",
      "edgeTreatment": "content floats on the ground, rarely boxed",
      "density": "calm"
    },
    "typeConstruction": {                       // §3.1 - OBSERVED from the plate's rendered text, not the brief's words
      "display": "<what the model actually drew for the headline: width (condensed/normal/extended), weight, stroke contrast (mono/high), case, slant, roundness - e.g. 'very heavy, tall + condensed, near-mono stroke, all-caps, upright'>",
      "body": "<same, observed from the plate's body / label text>",
      "note": "the TARGET authored.typography.familyResolution must match - the letterforms in the pixels, not the family the brief named"
    }
  },

  "authored": {
    "typography": {
      "display": "<family + construction, e.g. warm humanist serif>",
      "body": "<family + construction>",
      "mono": "<or null>",
      "modularScale": 1.5,
      "displayToBodyRatio": 4,
      "lineHeight": { "body": 1.6, "display": 1.1 },
      "tracking": "<per role>",
      "caseUsage": "<sentence case body, title display, etc.>",
      "rhythmNote": "<the typographic rhythm the plate implies>",
      "familyResolution": "<the concrete web-available family + variant/axis that REALISES extracted.typeConstruction - e.g. 'Archivo variable @ wght 800 / wdth 75', 'Archivo Narrow', 'Archivo Expanded' - NOT the static Archivo Black when the plate reads condensed (§3.1)>",
      "constructionMatch": "<one line: how familyResolution matches the observed construction; if you could not find an exact web font, say so and name the nearest>"
    },
    "componentStyle": {
      "cornerRadius": "<token>",
      "border": "<hairline / none / heavy>",
      "elevation": "<shadow language - soft long glow-shadow vs hard offset>",
      "fillVsOutline": "<default treatment>",
      "recipeNotes": "<button / chip / card treatment consistent with the plate>"
    },
    "motionCharacter": {
      "easing": "<register - gentle spring / crisp ease>",
      "durationBand": "<ms range>",
      "whatMoves": ["idle drift on the focal", "bloom on action", "..."],
      "reducedMotionAnalogue": "<the still equivalent>"
    },
    "spacing": { "baseUnit": "<px>", "scale": "<ratio or steps>" }
  },

  "crossSurfaceContract": {
    "sharedPaletteHexes": ["#0e1620", "#efe7d6", "#7ad9c4", "#241a12"],   // the palette SYSTEM (with extracted.palette roles+ratios) - NOT a "put all of these in every asset" list
    "colorUsePrinciple": "<how colour is RATIONED across the page - e.g. 'accents are concentrated punches on a quiet neutral ground, never spread evenly; the page-level ratio is satisfied across assets, not within each one'. Each asset draws the SUBSET that fits its role/scale (small→one accent, large→dominant or neutral+sparse accent). The per-slot subset is assigned by visual-orchestrator (step 3.5), which knows each slot's size+position; the contract only sets the system + this principle.>",
    "imageryRegister": "<the single register illustration/photography/visual must all hit so assets match the chrome>",
    "materialDirective": "<the single material logic material-orchestrator applies to UI surfaces>",
    "antiPatterns": ["<verbatim from brief + any the plate review surfaced>"]
  },

  "voice": {
    // The COPY half of the single source of truth - the sibling of the visual halves above.
    // The plate already renders REAL WORDS (composition law §2 #5: "real words not lorem"), so
    // that copy is your sample: OBSERVE the register it implies, then author the binding rule
    // (§3.3). step-content reads this; the final QA gate runs a copywriting pass against it.
    "audience": "<who the shipped copy SPEAKS TO, in their own terms - the real end reader / persona / customer (e.g. 'a touring musician's fans deciding whether to buy a ticket'), NOT 'the development team', 'the client', or 'whoever wrote the brief'>",
    "toneWords": ["<3-5 words for the voice the plate's real copy implies - e.g. 'warm', 'plainspoken', 'a little cocky'>"],
    "addressPrinciple": "Copy is addressed TO the audience and talks about THEIR world. It NEVER answers the build brief, narrates the product to whoever commissioned it, or describes a feature to a 'development team'. Ship the line the reader should see: 'Ship when the data says ship.' - NOT 'This is a landing page for a developer-analytics SaaS.'",
    "copyAntiPatterns": [
      "instruction-echo - restating the brief/prompt back as copy ('A clean, modern dashboard that displays your key metrics')",
      "meta-narration - copy that describes the page to the reader ('This section showcases...', 'Below you will find...', 'Welcome to our website')",
      "spec / dev-team address - talking to the builder or stakeholder instead of the actual user",
      "lorem / placeholder / [BRACKETED TODO] shipped as final copy",
      "feature-listing where a benefit is owed - naming the mechanism, not what it does for the reader"
    ]
  },

  "buildRegister": {
    // prose-lane, not diffed; governs the language of BUILD BRIEFS, NOT shipped copy (that is `voice`).
    // The register in which downstream build briefs are WRITTEN - each slot named in the craft's real
    // vocabulary (the model, not the appearance: "sphere / volume / light / mass" not "ball";
    // "bounce = restitution + squash + settle" not "moves up and down"). DERIVED per project from the
    // committed plate + each slot's actual behaviour, never picked from a catalogue. Example words are
    // illustrative, non-binding - do NOT ship a fixed word list; ship the derivation method.
    "deriveFrom": "<derive the vocabulary from the committed plate + each downstream slot's ACTUAL behaviour: name each thing by its underlying model/craft, never by its surface look (illustrative, non-binding: a physics slot earns 'restitution / squash / settle', a type slot earns 'axis / weight / optical size', a light slot earns 'key / fill / falloff') - never impose these, read what THIS plate and THESE slots actually are>",
    "cadence": "<the brief-writing cadence the plate implies - e.g. terse imperative spec-note, one behaviour per line, no scene-setting (illustrative, non-binding)>",
    "antiVoice": [
      "no 'imagine you are a...'",
      "no adjective-decoration",
      "no reaching for a house vocabulary the project didn't earn"
    ]
  },

  "itemReferences": [
    // LEAVE THIS [] IN PHASE B. It is populated only in the mode=finalize dispatch, AFTER the
    // pick, by the §4.5 crop pass (crop FIRST, then author this contract from the crops in §4.6).
    // PRIORITISE the high-value references the old pass skipped: the human SUBJECT and the UI
    // sample - NOT just discrete text stickers. By role:
    //   subject - the person, rembg'd → i2i identity ref for hero/portrait raster-photo slots
    //   ui      - nav+hero+card+button rectangle, NO rembg → composition/component ground-truth
    //             for the build (layout/components) + the aesthetic-lens; matchesSlots:[] (not an i2i input)
    //   item    - mascot / logo / album object / product, rembg'd → i2i ref for its raster slot
    //   decoration - a sticker/badge that genuinely recurs as its own slot (LAST, sparingly)
    // subject/item/(recurring decoration) need an i2i-capable model (openai gpt-image-*); the ui
    // crop is worth taking regardless. Refs live under source/ (only writable + i2i-readable tree).
    {
      "itemId": "hero-artist",
      "role": "subject",
      "refPath": "source/<branch>/_artdir_refs/hero-artist.png",   // rembg'd figure, AS the plate drew them
      "matchesSlots": ["hero-portrait", "about-portrait"],          // raster-photo slots that should be THIS person
      "bboxNote": "central figure in north-star-1.png"
    },
    {
      "itemId": "ui-sample",
      "role": "ui",
      "refPath": "source/<branch>/_artdir_refs/ui-sample.png",      // nav+hero+card+button rectangle, layout intact
      "matchesSlots": [],                                            // build/lens reference, not an image-gen input
      "bboxNote": "top nav + STREAM NOW pill + LATEST DROP card stack"
    }
    // ... then item / decoration entries; [] when nothing reference-worthy or not i2i-capable
  ],

  "surfaceContracts": {
    // ONE entry per approvedOwnsSurface member, keyed by its containerId. This is the
    // binding brief the owns-surface orchestrator (game / sim / motion / etc.) reads
    // in its research step so its register is a TRANSLATION of the app's DNA, not an
    // independent pick - the reconciliation that stops the "two halves" fork.
    "game-experience": {
      "inheritPaletteHexes": ["#0e1620", "#7ad9c4", "#241a12"],   // subset the surface draws from
      "materialDirective": "<how the surface's material reads, consistent with the chrome>",
      "motionBound": "<the surface MAY be more kinetic than the chrome, but bounded by this - e.g. 'gentle spring, soft bloom; no hard arcade snap'>",
      "registerNote": "<one line: the surface's feel as a translation of the contract, e.g. 'a calm bioluminescent care surface, not a juicy arcade game'>",
      "compositionNote": "<how it sits in the frame: full-bleed | inset panel | behind-chrome>",
      "motionPlate": {
        // OPTIONAL - populated by §4.7 in the finalize dispatch, ONLY when the user opted in at
        // the §4 motionGateBlock card (envelope motionPlates: true) AND a video provider is
        // wired AND this surface's family is motion-benefiting (§4.7 roster). The TEMPORAL half
        // of this surface's brief: a short i2v clip animated FROM the chosen plate, plus what it
        // actually shows. Absent = no video provider / non-motion family; downstream falls back
        // to the prose motionBound alone.
        "path": "workflow/artdirection/motion-<surfaceId>.mp4",
        "framesDir": "workflow/artdirection/motion-<surfaceId>-frames/",   // the 12 extracted full-res frames
        "observed": {
          "energyBand": "calm | gentle | lively | punchy",   // MEASURED (frame-diff over all frames), never eyeballed
          "settleMs": 400,           // decay time after the biggest motion peak - seeds downstream easing constants
          "loopPeriodS": 3.1,        // dominant idle periodicity; null if none
          "peakToRestRatio": 1.2,    // impulse character: low = continuous drift, high = punchy hits
          "cameraBehaviour": "static | drift | dolly | orbit | cut",   // read off the frames, closed vocabulary
          "whatMoves": ["<subject-scale list, read per frame>"],
          "frameByFrame": "<3-6 lines: how the motion progresses across the 12 frames - what changes when, where the peak lands, what the end state is>"
        },
        "keyframes": [
          // 2-4 frames picked as REFERENCES - the states the motion passes through that the STILL
          // plate does not contain (impulse peak, settled end state, mid-turn view). These are the
          // ONLY frames downstream may use as visual references.
          { "path": "workflow/artdirection/motion-<surfaceId>-frames/frame-07.png", "t": 2.3,
            "why": "<one line: which state this captures + what downstream should use it for>" }
        ],
        "promptUsed": "<the five-clause motion prompt the clip was generated from>"
      }
    }
    // ... one per approvedOwnsSurface entry
  },

  "formatCommitments": [
    // FORMAT is not vibe. When the brief, the locked decisions, or an approvedOwnsSurface
    // entry promises the user a MEDIUM - real 3d moments, video heroes, camera input,
    // handlettered headlines, generative shader backgrounds, playable physics - record it
    // here as a boolean deliverable. These are the promises the user can check with one
    // look ("is it actually 3d or not"), so they are the ones that must never silently
    // downgrade. Derive them from what was actually promised (brief wording, the
    // prototype-direction pick, the orchestrator-plan roster) - do NOT invent format
    // ambitions the user never asked for.
    {
      "id": "immersive-3d-moments",
      "promise": "<one line, in the user's terms: what medium was promised, where>",
      "format": "3d",            // 3d | 2d-plate | raster | vector | video | motion | audio
                                 // | shader | particle | interactive-input | handlettering
      "appliesTo": "<surface / slot / 'per downstream research route table'>",
      "source": "brief"          // brief | decision:<id> | plate | approvedOwnsSurface
    }
    // [] ONLY when the brief + decisions genuinely promise no specific medium anywhere.
  ],

  "bindingRules": {
    "inheritFromPlate": ["colour ratios", "value structure", "composition logic", "material logic", "type rhythm", "motion character"],
    "doNotReplicate": ["the plate's literal subject", "its exact layout / coordinates", "its specific copy", "any single-screen framing - the app has many screens"],
    "principleNotPixels": "The build inherits the plate's design DNA. If a build step is reproducing the plate's content rather than its principles, it is wrong.",
    "plateIsNotAnAsset": "The plate + its crops (_artdir/, _artdir_refs/, workflow/artdirection/) are planning artefacts and i2i references - shipped HTML/CSS/JS must never load them (img src, background-image, poster). A shell/title screen that needs keyart commissions a dedicated asset i2i-conditioned on the plate, inheriting the DNA without the baked chrome.",
    "buildRegister": "buildRegister obeys aesthetic-authority - translate the committed vibe into a register, never default to a generic 'creative' voice.",
    "formatCommitmentsAreHard": "Every formatCommitments entry is a boolean deliverable, not direction. Downstream research MUST copy each applicable entry into its slot's deliverables.json (capabilities.py, 'The deliverables ledger'); the runtime/composer marks delivery; the final qa_gate audits it and cannot commit with an unresolved item. Downgrading a committed format (2d standing in for 3d, a still standing in for video) is allowed ONLY through a user-accepted decision-request recorded in the ledger - never through a graceful fallback, a code comment, or a lens pass."
  }
}
```
