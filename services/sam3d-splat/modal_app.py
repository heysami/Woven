"""Modal deployment for the SAM 3D Objects → splat service.

    pip install modal && modal token new          # one-time
    modal deploy modal_app.py                      # deploy
    # -> prints a URL like https://<you>--sam3d-splat-web.modal.run
    # Point Woven at  <that URL>/convert  (media-config.json sam3d.endpoint).

This is a STARTING TEMPLATE. Two things you must finish, because they depend on
the SAM License weights you have to accept/download yourself:

  1. WEIGHTS. SAM 3D Objects checkpoints are license-gated. Bake them into the
     image (ADD a `run_commands(... download ...)` step with your HF token) or
     mount a Modal Volume containing checkpoints/. Set SAM3D_CONFIG to the
     pipeline.yaml inside it.
  2. DEP PINS. requirements.inference.txt pulls kaolin + gsplat (CUDA-compiled).
     Match the CUDA/torch versions to the `gpu=` you pick below; kaolin wheels
     are CUDA/torch-specific.
"""
import modal

REPO = "https://github.com/facebookresearch/sam-3d-objects"

image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("git", "build-essential", "libgl1", "libglib2.0-0")
    .run_commands(
        f"git clone --depth 1 {REPO} /opt/sam-3d-objects",
        # Install the model's own inference deps (torch, kaolin, gsplat, …).
        "pip install -r /opt/sam-3d-objects/requirements.inference.txt",
        # TODO: download/place license-gated weights into
        #   /opt/sam-3d-objects/checkpoints/hf/  (HF token, your acceptance).
    )
    .pip_install("fastapi[standard]==0.115.*", "pillow", "numpy")
    .add_local_file("server.py", remote_path="/root/server.py")
)

app = modal.App("sam3d-splat")


@app.function(image=image, gpu="A10G", timeout=900, scaledown_window=300)
@modal.concurrent(max_inputs=1)
@modal.asgi_app()
def web():
    import os
    os.environ.setdefault("SAM3D_REPO", "/opt/sam-3d-objects")
    # Optional: protect the endpoint. Set the same value as Woven's
    # media-config sam3d.api_key (or TH_SAM3D_API_KEY).
    # os.environ.setdefault("SAM3D_TOKEN", "<shared-secret>")
    import sys
    sys.path.insert(0, "/root")
    from server import app as fastapi_app
    return fastapi_app
