# sam3d-splat - image → Gaussian-splat (.ply) service

Wraps [facebookresearch/sam-3d-objects](https://github.com/facebookresearch/sam-3d-objects)
behind one HTTP route so Woven's **Image → Splat** node / `image-to-ply` skill can
turn a (background-removed) PNG into a 3D Gaussian-splat `.ply` that **Splat Lab**
loads directly.

> ⚠️ Needs a **CUDA GPU** (`kaolin` + `gsplat`). It does **not** run in the Woven
> daemon. Model weights are under the **SAM License** (Meta) - accept + download
> them yourself. This dir is a deploy starting point, not a turn-key build.

## Contract (what Woven calls)

```
POST <endpoint>/convert
  Authorization: Bearer <token>          # optional (set SAM3D_TOKEN to require)
  { "image": "<data-uri or base64 PNG>", "seed": 42, "mask": "<optional data-uri>" }
  → 200  raw .ply bytes  (Content-Type: model/ply)
```

The daemon also accepts a JSON reply `{"ply_b64": "..."}` or `{"ply_url": "..."}`
if you prefer (see `editor/serve.py` `_sam3d_convert`). `mask` is optional - if the
incoming PNG has alpha (it will, after rembg) the object mask is taken from it.

## Pipeline

```
raster-foreground (image-gen)  →  rembg (transparent PNG)  →  Image → Splat (this service)  →  Splat Lab
```

## Deploy

**Modal (simplest):**
```bash
pip install modal && modal token new
modal deploy modal_app.py          # prints https://<you>--sam3d-splat-web.modal.run
```
Finish the two TODOs in `modal_app.py` (weights + dep pins).

**Own GPU box / RunPod / Replicate:** clone the repo, `pip install -r
requirements.inference.txt` + `requirements.txt`, place the weights, then
`SAM3D_REPO=/path/to/sam-3d-objects python server.py` (serves `:8000`).

Env: `SAM3D_REPO`, `SAM3D_CONFIG` (default `checkpoints/hf/pipeline.yaml`),
`SAM3D_TOKEN` (optional bearer).

## Wire into Woven

Point the daemon at your deployed URL - either:

- env: `export TH_SAM3D_ENDPOINT="https://…/convert"` (+ optional `TH_SAM3D_API_KEY`), or
- `~/.test-harness/media-config.json`:
  ```json
  { "sam3d": { "endpoint": "https://…/convert", "api_key": "<token, optional>" } }
  ```

Then drop a **Splat (from image)** node, wire a background-removed image into it,
and ▶ Run - or wire an Agent into its edit port to drive the whole chain.

## Adapt if needed

`server.py` `_mask_for()` builds a uint8 HxW mask. If your checkpoint expects a
different mask dtype/shape than what `inference()` wants, that's the one spot to
match against the repo's `notebook/inference.py` `load_single_mask()`.
