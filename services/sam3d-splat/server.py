"""SAM 3D Objects → Gaussian-splat HTTP service.

Wraps facebookresearch/sam-3d-objects behind ONE endpoint the Woven daemon
calls (editor/serve.py `_sam3d_convert`):

    POST /convert
      body: {"image": "<data-uri or base64 PNG/JPG>", "seed": 42,
             "mask": "<optional data-uri grayscale mask>"}
      ->   raw .ply bytes  (Content-Type: model/ply)

This MUST run on a CUDA GPU (kaolin + gsplat). It is NOT part of the Woven
daemon — deploy it to Modal / RunPod / Replicate / your own box, then point
Woven at it via media-config.json {"sam3d": {"endpoint": "https://…/convert"}}
or env TH_SAM3D_ENDPOINT.

Pipeline context: the Woven side sends a *background-removed* PNG (raster-gen →
rembg). SAM 3D needs an object mask; if the PNG carries an alpha channel we
derive the mask from it, otherwise the whole frame is used. Pass an explicit
`mask` to override.
"""
from __future__ import annotations

import base64
import io
import os
import sys
import tempfile
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from PIL import Image
from pydantic import BaseModel

# ── SAM 3D Objects repo wiring ──────────────────────────────────────────────
# Point SAM3D_REPO at the cloned facebookresearch/sam-3d-objects checkout and
# SAM3D_CONFIG at its pipeline.yaml (the README uses checkpoints/hf/pipeline.yaml).
SAM3D_REPO = os.environ.get("SAM3D_REPO", "/opt/sam-3d-objects")
SAM3D_CONFIG = os.environ.get("SAM3D_CONFIG", os.path.join(SAM3D_REPO, "checkpoints/hf/pipeline.yaml"))
SAM3D_TOKEN = os.environ.get("SAM3D_TOKEN", "")  # optional shared-secret bearer

for p in (SAM3D_REPO, os.path.join(SAM3D_REPO, "notebook")):
    if p and p not in sys.path:
        sys.path.insert(0, p)

_inference = None


def _get_inference():
    """Lazily build the SAM3D Inference pipeline once (weights load is slow)."""
    global _inference
    if _inference is None:
        # Provided by the repo's notebook/ dir — see its README "Inference" block.
        from inference import Inference  # type: ignore
        _inference = Inference(SAM3D_CONFIG, compile=False)
    return _inference


def _decode_image(data_uri_or_b64: str) -> Image.Image:
    s = data_uri_or_b64
    if s.startswith("data:"):
        s = s.split(",", 1)[1]
    return Image.open(io.BytesIO(base64.b64decode(s)))


def _mask_for(img: Image.Image, mask_field: Optional[str]) -> np.ndarray:
    """Return an HxW uint8 {0,1} object mask.

    Priority: explicit mask -> alpha channel of a background-removed PNG ->
    full frame. NOTE: if your checkpoint expects a different mask dtype/shape
    than a uint8 HxW array, adapt this to match the repo's load_single_mask()
    output — this is the single SAM3D-specific spot most likely to need tuning.
    """
    if mask_field:
        m = _decode_image(mask_field).convert("L")
        return (np.array(m) > 127).astype(np.uint8)
    if img.mode in ("RGBA", "LA"):
        alpha = np.array(img.convert("RGBA").split()[-1])
        if alpha.max() > 0:
            return (alpha > 10).astype(np.uint8)
    w, h = img.size
    return np.ones((h, w), dtype=np.uint8)


class ConvertReq(BaseModel):
    image: str
    mask: Optional[str] = None
    seed: int = 42
    # "splat" -> Gaussian splat .ply (default, for Splat Lab);
    # "mesh"  -> textured polygon .glb (for Spline 3D / Voxel / model-viewer).
    format: str = "splat"


app = FastAPI(title="sam3d-splat")


@app.get("/health")
def health():
    return {"ok": True, "config": SAM3D_CONFIG, "repo": SAM3D_REPO}


def _export_mesh(output, glb_path: str) -> None:
    """Best-effort GLB export of the mesh the pipeline produced.

    ADAPT SPOT: the README documents only output['gs'].save_ply(); the mesh
    object's exact key + export method are not documented, so we try the
    common ones. Tighten to your checkpoint's real API once you see what
    with_mesh_postprocess returns (see sam3d_objects.pipeline + render_utils).
    """
    mesh = None
    if isinstance(output, dict):
        for k in ("mesh", "textured_mesh", "glb", "trimesh"):
            if output.get(k) is not None:
                mesh = output[k]
                break
    if mesh is None:
        raise RuntimeError(
            "no mesh in pipeline output — keys were: "
            + (", ".join(map(str, output.keys())) if isinstance(output, dict) else type(output).__name__))
    for fn in (
        lambda: mesh.save_glb(glb_path),       # custom helpers
        lambda: mesh.export(glb_path),         # trimesh.Trimesh.export (infers .glb)
        lambda: mesh.save(glb_path),
        lambda: mesh.write_glb(glb_path),
    ):
        try:
            fn()
            return
        except (AttributeError, TypeError):
            continue
    raise RuntimeError(f"could not export mesh of type {type(mesh).__name__} to .glb")


@app.post("/convert")
def convert(req: ConvertReq, authorization: str = ""):
    if SAM3D_TOKEN:
        if authorization != f"Bearer {SAM3D_TOKEN}":
            raise HTTPException(status_code=401, detail="bad or missing bearer token")
    want_mesh = (req.format or "splat").lower() in ("mesh", "glb", "3d", "object")
    try:
        img = _decode_image(req.image).convert("RGBA")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"bad image: {e}")

    try:
        from inference import load_image  # type: ignore
        inf = _get_inference()
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            img.save(tf, "PNG")
            img_path = tf.name
        image = load_image(img_path)
        mask = _mask_for(img, req.mask)
        seed = int(req.seed)

        if not want_mesh:
            output = inf(image, mask, seed=seed)
            with tempfile.NamedTemporaryFile(suffix=".ply", delete=False) as pf:
                out_path = pf.name
            output["gs"].save_ply(out_path)
            media = "model/ply"
        else:
            # Same call __call__ makes, but with mesh post-process + texture
            # baking enabled (they are hardcoded False in the splat wrapper).
            rgba = inf.merge_mask_to_rgba(image, mask)
            output = inf._pipeline.run(
                rgba, None, seed,
                stage1_only=False,
                with_mesh_postprocess=True,
                with_texture_baking=True,
                with_layout_postprocess=False,
                use_vertex_color=True,
                stage1_inference_steps=None,
                pointmap=None,
            )
            with tempfile.NamedTemporaryFile(suffix=".glb", delete=False) as pf:
                out_path = pf.name
            _export_mesh(output, out_path)
            media = "model/gltf-binary"

        with open(out_path, "rb") as f:
            data = f.read()
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")

    return Response(content=data, media_type=media)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
