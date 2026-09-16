## 4.7 Phase C.7 - (mode: finalize) MOTION PLATE - animate the chosen plate for motion-bearing owns-surfaces

A still plate locks composition, palette, and material - it cannot lock **pacing, energy, juice, or transition feel**, which is exactly the register the motion-bearing families commit in their research step and the user currently approves blind. This phase closes that gap: per qualifying approved owns-surface, animate the CHOSEN plate into one short clip (i2v), read what the clip actually does, and write it into that surface's `surfaceContracts` entry as the binding temporal register.

**Gating - all three, else skip the phase silently (motion plates are an enhancement, never fail-closed like §1):**

1. `GET /__capabilities` → `videoModels` is non-empty (a video provider is wired).
2. `approvedOwnsSurface` contains at least one **motion-benefiting family**. The roster, and what the clip must demonstrate for each:
   - `narrative-experience` - the emotional + pacing register: camera drifting through the place, light shifting, ambient breathing. What being there FEELS like over time.
   - `game-experience` - the juice register: ONE action landing (impact, particle burst, screen energy) at the committed energy level - the Vlambeer-juicy vs contemplative-restraint axis in pixels.
   - `interactive-media` - the response feel: an implied input (hand, pointer, pulse) and the visual answering it - the mapping energy (direct snap vs accumulative drift).
   - `motion-studio` - the transition register: one scene beat moving at the intended cinematic pacing; this clip is ALSO a legal i2v reference for its concept plates downstream.
   - `scene-3d` - the ambient idle: material under motion (glass refracting, cloth swaying) + the idle energy band.
   Simulation and scrapbook are deliberately OFF this roster (sim registers are paradigm-driven, scrapbook motion is subtle drift a still implies fine) - do not generate clips for them.
3. **The envelope carries `motionPlates: true`** - the user explicitly opted in at the §4 `motionGateBlock` card (this phase runs only in `mode: "finalize"`). `motionPlates: false` (user chose stills-only) or `null` (question was never eligible) → skip this phase entirely, no clips, no `motionPlate` blocks; downstream falls back to the prose `motionBound` alone. Never generate video the user did not opt into.

**Generate - one clip per qualifying surface, i2v-conditioned on the chosen plate:**

```bash
curl -fsS -m 900 -X POST "$TH_DAEMON_URL/__asset_generate?project=$TH_PROJECT_ID" -H "Content-Type: application/json" -d '{
  "skill":"video-gen",
  "prompt":"<five-clause motion prompt - see below>",
  "output":"source/<branch>/_artdir/motion-<surfaceId>.mp4",
  "aspect":"16:9",
  "options":{"duration":4},
  "input_path":"source/<branch>/_artdir/north-star-<chosen>.png"}'
# then copy to the canonical served planning path + commit a video asset node (race-safe append):
cp "$TH_PROJECT_ROOT/source/<branch>/_artdir/motion-<surfaceId>.mp4" "$TH_PROJECT_ROOT/workflow/artdirection/motion-<surfaceId>.mp4"
curl -fsS -X POST "$TH_DAEMON_URL/__workflow/nodes/add?project=$TH_PROJECT_ID" -H "Content-Type: application/json" -d '{
  "addNodes":[{"id":"ad_motion_<projectId>_<surfaceId>","kind":"asset","assetKind":"video",
    "title":"Motion plate - <surface label>","path":"workflow/artdirection/motion-<surfaceId>.mp4",
    "projectId":"<project>","runStatus":"done"}],
  "addEdges":[{"from":"ad_plate_<projectId>_<chosen>","to":"ad_motion_<projectId>_<surfaceId>"},
              {"from":"ad_motion_<projectId>_<surfaceId>","to":"ad_contract_<projectId>"}]}'
```

- `input_path` is the i2v lever: the daemon converts it to the provider's `image_url` and auto-promotes a text-only model to its image-to-video sibling, so the clip's world IS the approved plate's world. OMIT `model` - the daemon default applies (1V-video.md rules).
- The **prompt** follows 1V-video.md's five clauses (subject / composition / MOTION / lighting / palette), where clause 3 carries the surface's intended feel translated from the plate's DNA + the surface's `motionBound` draft: name a specific motion at a specific energy ("one soft impact ripple, slow settle, nothing snaps" / "camera slow-drifts left through the space, dust motes rise"). Generic motion phrases produce generic clips.
- `duration: 4` always - this is a register sample, not content. Do NOT re-fire on silence (video renders take 30s-10min; re-firing double-bills). One retry on a hard error; after that, drop `motionPlate` for that surface and note it in the hand-off - never block finalize on a clip.

**Convert the clip into the contract: still plate → clip → 12 frames → analysis + keyframes.** The agent never "watches" video; the clip becomes frames and numbers:

1. **Extract 12 evenly spaced FULL-RES frames**: `ffmpeg -y -i motion-<surfaceId>.mp4 -vf fps=3 <framesDir>/frame-%02d.png` (3 fps over a 4s clip ≈ 12; adjust to the real clip length; ffmpeg availability is reported in `/__capabilities`). Individual full frames - NEVER a tiled contact sheet (tiling shrinks every frame and destroys detail).
2. **Measure the motion mechanically** (PIL: consecutive-frame mean-abs-diff over ALL frames of the clip, not just the 12) → `observed.energyBand`, `settleMs`, `loopPeriodS`, `peakToRestRatio`. Quantities are always measured, never eyeballed.
3. **Read EACH of the 12 frames in order** and analyze how the motion progresses: what moved between frame N and N+1, camera behaviour (closed vocabulary only), where the peak lands, what the end state is → `observed.frameByFrame` + `whatMoves` + `cameraBehaviour`. Where the eyeball read contradicts the numbers (frames look static, measured energy high), re-read; still contradicting → write "uncertain" for that field - the numbers win.
4. **Pick 2-4 KEYFRAMES as references** → `keyframes[]` with `t` + `why`: the frames capturing states the still plate does NOT contain (the impulse peak, the settled end state, a mid-motion view worth matching). These become downstream visual references, so they answer the "video changes things the still never captured" gap. SKIP any frame where generation artefacts (melted UI text, warped chrome) would poison a reference - prefer frames whose UI regions are clean or out of frame; if no clean frame exists for a state, leave it out and say so in `frameByFrame`.
5. **Conformance**: if the measured register contradicts the briefed one (asked calm, measured punchy) → regenerate ONCE with a corrected motion clause; still wrong → keep the better clip and record the miss in `frameByFrame`.

**This phase runs BEFORE §4.6 writes the contract file** (generate clips right after the §4.5 crops, while the contract is still in memory), so `workflow/art-direction-contract.json` is still written ONCE, fully populated - the §4.6 "no later patch step" rule holds. Motion plates are planning artefacts under `bindingRules.plateIsNotAnAsset` exactly like the stills: the runtime never loads them; a surface that wants shipped video commissions it through its own family pipeline, i2v-conditioned on the plate.
