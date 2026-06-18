"""Static integrity test for the KIND_IO edge contract.

The repo rule this enforces: **every `editTarget` node kind must declare a
non-empty `authoring` schema string.** `editTarget` tells an agent to rewrite a
node's canonical JSON, but the canonical path alone leaks no schema — without
`authoring` the agent guesses the file shape and ships something the node can't
render (the composer "blank hero" + spline "2D-instead-of-3D" failure class).
`authoring` is the slot io_resolve.resolve_downstream emits verbatim so the
agent produces VALID content. See NODE_IO_FRAMEWORK.md §"How to add a new node
kind" (step 4).

This is ALSO enforced at registry import time (registry.io_contract_violations
is called on load and raises), so check-compat.sh catches a regression before a
sync. This file is the explicit, runnable form of the same rule.

Run: python kinds/test_io_contract.py
"""
from __future__ import annotations

import sys

from .registry import (KIND_IO, KINDS, ASSET_KIND_AUTHORING,
                       MEDIA_MODEL_AUTHORING, io_contract_violations)


def test_every_edit_target_has_authoring():
    """The core rule — no editTarget accept may lack a non-empty authoring."""
    problems = io_contract_violations()
    assert not problems, "editTarget kinds missing authoring schema:\n  - " + \
        "\n  - ".join(problems)


def test_known_edit_target_kinds_covered():
    """Belt-and-suspenders: the three editTarget kinds we know about all carry
    authoring. Guards against someone deleting an authoring block AND the
    violations helper at once."""
    edit_kinds = {
        kind
        for kind, io in KIND_IO.items()
        for a in (io.get("accepts") or [])
        if a.get("ingest") == "editTarget"
    }
    expected = {"composer", "vector-editor", "spline-3d"}
    assert expected <= edit_kinds, \
        f"expected editTarget kinds {expected} present; found {sorted(edit_kinds)}"
    for kind in edit_kinds:
        io = KIND_IO[kind]
        auth = [
            a.get("authoring")
            for a in io["accepts"]
            if a.get("ingest") == "editTarget"
        ]
        assert all(isinstance(s, str) and s.strip() for s in auth), \
            f"{kind}: an editTarget accept has empty authoring"


def test_section_write_has_authoring():
    """sectionWrite carries the container/grid placement protocol (not a medium
    schema — children delegate to their own assetKind authoring)."""
    sec = next((a for a in KIND_IO["section"]["accepts"]
                if a.get("ingest") == "sectionWrite"), None)
    assert sec is not None, "section has no sectionWrite accept"
    assert isinstance(sec.get("authoring"), str) and sec["authoring"].strip(), \
        "section's sectionWrite accept is missing a non-empty authoring protocol"


def test_every_asset_kind_has_authoring():
    """The assetWrite analogue — every assetKind enum value an agent can be told
    to produce must carry a per-medium authoring string, else the dispatch is
    medium-blind (the shader→backdrop-filter failure)."""
    values = KINDS.get("asset", {}).get("inputs", {}).get("assetKind", {}).get("values", [])
    assert values, "asset.assetKind enum not found — registry shape changed?"
    missing = [ak for ak in values
               if not (isinstance(ASSET_KIND_AUTHORING.get(ak), str)
                       and ASSET_KIND_AUTHORING[ak].strip())]
    assert not missing, f"assetKinds with no ASSET_KIND_AUTHORING entry: {missing}"


def test_specific_pathway_b_media_models_have_authoring():
    """Pathway-B media models that all store as html (or another generic kind)
    but expect a SPECIFIC result must each carry a media-model authoring, so an
    agent wired to one gets the right contract — not the generic-HTML one. This
    list mirrors prompts/media-models.js (not daemon-readable), so keep in sync."""
    expected = {"shader", "viz", "threejs", "motion-gen", "canvas-gen",
                "html-page", "svg-gen", "lottie-gen"}
    missing = [m for m in expected
               if not (isinstance(MEDIA_MODEL_AUTHORING.get(m), str)
                       and MEDIA_MODEL_AUTHORING[m].strip())]
    assert not missing, f"media models with no MEDIA_MODEL_AUTHORING entry: {missing}"


def test_layer_specs_flow_through_layer_except_no_layer_position_hosts():
    """Position/effect/trigger specs describe a layer by default.

    Direct position ports are allowed only on editors that lack a layer model and
    therefore need placement as host-level context. Effects and triggers should
    not bypass the layer node.
    """
    direct_position_hosts = {"layer", "pixel-editor", "spline-3d", "voxel-3d"}
    direct_effect_hosts = {"layer"}
    direct_trigger_hosts = {"layer"}

    offenders = []
    for kind, io in KIND_IO.items():
        for accept in io.get("accepts") or []:
            tags = set(accept.get("tags") or [])
            port = accept.get("port")
            if "position" in tags and kind not in direct_position_hosts:
                offenders.append(f"{kind}.{port} accepts position")
            if "effect" in tags and kind not in direct_effect_hosts:
                offenders.append(f"{kind}.{port} accepts effect")
            if "trigger" in tags and kind not in direct_trigger_hosts:
                offenders.append(f"{kind}.{port} accepts trigger")

    assert not offenders, "spec nodes must flow through layer:\n  - " + "\n  - ".join(offenders)


def main():
    tests = [test_every_edit_target_has_authoring, test_known_edit_target_kinds_covered,
             test_section_write_has_authoring, test_every_asset_kind_has_authoring,
             test_specific_pathway_b_media_models_have_authoring,
             test_layer_specs_flow_through_layer_except_no_layer_position_hosts]
    for t in tests:
        try:
            t()
        except AssertionError as e:
            print(f"FAIL {t.__name__}: {e}", file=sys.stderr); return 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {t.__name__}: {type(e).__name__}: {e}", file=sys.stderr); return 1
        print(f"OK   {t.__name__}")
    print(f"\n{len(tests)}/{len(tests)} io-contract tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
