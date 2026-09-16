"""End-to-end seams for context settings, reference reuse, contracts, and QA."""
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import context_artifacts as artifacts
import serve


def handler(body):
    raw = json.dumps(body).encode()
    return SimpleNamespace(_read_json_body=lambda **kw: body,
                           headers={"Content-Length": str(len(raw))}, rfile=io.BytesIO(raw),
                           _reply=lambda status, value: (status, value))


def draft():
    return {
        "platePath": "workflow/plate.png",
        "extracted": {"moodWords": ["quiet", "irregular"],
                      "palette": [{"hex": "#92806a", "role": "ground", "ratio": .67}],
                      "valueStructure": "low-key", "contrastRegister": "localized",
                      "lightModel": {"direction": "left"}, "materialRead": {"uiSurfaces": "paper"},
                      "composition": {"density": "sparse"}, "typeConstruction": {"display": "condensed"}},
        "authored": {"typography": {"familyResolution": "Archivo @ wdth 75, wght 800"},
                     "componentStyle": {"cornerRadius": "var(--radius-s)"},
                     "motionCharacter": {"durationBand": "150-250ms"}, "spacing": {"baseUnit": 8}},
        "crossSurfaceContract": {"sharedPaletteHexes": ["#92806a"], "colorUsePrinciple": "sparse",
                                 "imageryRegister": "cut paper", "materialDirective": "matte",
                                 "antiPatterns": ["No neon except the approved chart indicator."]},
        "voice": {"audience": "artists", "toneWords": ["plainspoken"]},
        "buildRegister": {"deriveFrom": "paper, folded planes", "cadence": "one action per sentence"},
        "itemReferences": [], "surfaceContracts": {},
        "formatCommitments": [{"id": "hero3d", "format": "3d", "promise": "Real 3D", "source": "decision:a"}],
        "approvedExceptions": {"caption": "Free-form prose " * 400},
    }


class ContextArtifactsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.defaults = json.loads((Path(serve.EDITOR_DIR) / "art-direction-defaults.json").read_text())

    def call(self, route, body):
        with patch.object(serve, "resolve_project_root", return_value=str(self.root)), \
             patch.object(serve, "_compact_config", return_value=serve.COMPACT_DEFAULTS):
            return serve.H._context_artifact(handler(body), route, {"project": ["fixture"]})

    def test_assembly_is_lossless_and_fills_shared_fields(self):
        original = draft()
        actual = artifacts.assemble_contract(original, self.defaults)
        self.assertEqual(actual["extracted"], original["extracted"])
        self.assertEqual(actual["approvedExceptions"], original["approvedExceptions"])
        self.assertEqual(actual["formatCommitments"], original["formatCommitments"])
        self.assertEqual(actual["voice"]["audience"], "artists")
        self.assertEqual(actual["bindingRules"], self.defaults["bindingRules"])
        self.assertNotIn("bindingRules", original)

    def test_incomplete_contract_is_not_invented(self):
        for mutate in (lambda d: d.pop("authored"), lambda d: d["extracted"].pop("typeConstruction"),
                       lambda d: d["itemReferences"].append("invalid")):
            value = draft(); mutate(value)
            with self.assertRaises(ValueError):
                artifacts.assemble_contract(value, self.defaults)

    def test_publish_requires_plate_and_preserves_concurrent_revision(self):
        body = {"draft": draft()}
        self.assertEqual(self.call("/__context/contract", body)[0], 400)
        plate = self.root / "workflow/plate.png"; plate.parent.mkdir(); plate.write_bytes(b"fixture")
        code, receipt = self.call("/__context/contract", body)
        self.assertEqual(code, 200)
        self.assertEqual(self.call("/__context/contract", body)[0], 200)  # idempotent
        body["draft"]["contractVersion"] = 2
        self.assertEqual(self.call("/__context/contract", body)[0], 409)
        self.assertEqual(json.loads((self.root / receipt["contractPath"]).read_text())["contractVersion"], 1)
        body["previousHash"] = receipt["sha256"]
        self.assertEqual(self.call("/__context/contract", body)[0], 200)
        body["draft"]["platePath"] = "../outside.png"
        self.assertEqual(self.call("/__context/contract", body)[0], 400)

    def test_reference_reuse_rejects_changed_revision_request_and_project(self):
        body = {"source": "figma:file:node", "revision": "verified-v1", "request": "Extract spacing"}
        self.assertFalse(self.call("/__context/reference", body)[1]["hit"])
        self.assertEqual(self.call("/__context/reference", {**body, "action": "put", "value": {"gap": 24}})[0], 200)
        self.assertEqual(self.call("/__context/reference", body)[1]["value"], {"gap": 24})
        for field in ("revision", "source", "request"):
            self.assertFalse(self.call("/__context/reference", {**body, field: "changed"})[1]["hit"])
        self.assertEqual(self.call("/__context/reference", {**body, "revision": ""})[0], 400)
        key = artifacts.reference_key(**body)
        with tempfile.TemporaryDirectory() as other:
            self.assertIsNone(artifacts.reference_get(other, key))
        path = self.root / "workflow/context-cache" / (key + ".json")
        path.write_text('{"key":"corrupt"}')
        self.assertIsNone(artifacts.reference_get(self.root, key))

    def test_file_references_hash_content_and_honor_off(self):
        (self.root / "image.png").write_bytes(b"one")
        body = {"inputPath": "image.png", "request": "Extract shape"}
        self.call("/__context/reference", {**body, "action": "put", "value": "triangle"})
        self.assertTrue(self.call("/__context/reference", body)[1]["hit"])
        (self.root / "image.png").write_bytes(b"two")
        self.assertFalse(self.call("/__context/reference", body)[1]["hit"])
        with patch.object(serve, "resolve_project_root", return_value=str(self.root)), \
             patch.object(serve, "_compact_config", return_value={"referenceReuse": False}):
            status, result = serve.H._context_artifact(handler(body), "/__context/reference", {})
        self.assertEqual(status, 200)
        self.assertFalse(result["enabled"])

    def test_description_endpoint_cache_and_refresh(self):
        body = {"skill": "describe", "input_data_uri": "data:image/png;base64,b25l", "prompt": "Layout"}
        with patch.object(serve, "resolve_project_root", return_value=str(self.root)), \
             patch.object(serve, "_compact_config", return_value=serve.COMPACT_DEFAULTS), \
             patch.object(serve, "_resolve_provider_key", return_value="fake"), \
             patch.object(serve, "detect_agent_bin", return_value=None), \
             patch.object(serve, "_openai_chat", return_value="A centered column") as model:
            first = serve.H._llm_run(handler(body), {})
            second = serve.H._llm_run(handler(body), {})
            self.assertEqual(first[0], 200)
            self.assertTrue(second[1]["cacheHit"])
            self.assertEqual(model.call_count, 1)
            for change in ({"refresh": True}, {"model": "different"}, {"prompt": "Colors"},
                           {"input_data_uri": "data:image/png;base64,dHdv"}, {"options": {"temperature": .4}}):
                self.assertEqual(serve.H._llm_run(handler({**body, **change}), {})[0], 200)
            self.assertEqual(model.call_count, 6)

    def test_qa_keeps_failures_unknowns_and_visual_evidence(self):
        report = {"verdict": "fail", "cases": [
            {"id": "pass", "verdict": "pass", "steps": "detail " * 1000, "frames": {"after": "frame.png"}, "elapsedMs": 123},
            {"id": "bad", "verdict": "fail", "error": "clipped", "steps": ["all details"]},
            {"id": "skip", "verdict": "skipped", "reason": "camera denied"},
            {"id": "mixed", "verdict": "pass", "pageErrors": ["broken"], "steps": "retain"}],
            "metrics": {"fps": 54}, "idleFrames": [{"path": "idle.png"}]}
        packet = artifacts.qa_packet(report)
        self.assertEqual(packet["cases"][1:], report["cases"][1:])
        self.assertEqual(packet["cases"][0]["frames"], {"after": "frame.png"})
        self.assertEqual(packet["cases"][0]["elapsedMs"], 123)
        self.assertEqual(packet["metrics"], report["metrics"])
        self.assertEqual(packet["idleFrames"], report["idleFrames"])
        self.assertLess(len(json.dumps(packet)), len(json.dumps(report)) / 5)

    def test_qa_endpoint_writes_full_report_and_honors_full_response(self):
        report = {"verdict": "pass", "cases": [{"id": "a", "verdict": "pass", "steps": "detail"}]}
        h = SimpleNamespace(_qa_resolve_url=lambda qs: {"baked": True, "url": "http://fixture/", "defaultMode": "render"},
                            _reply=lambda code, value: (code, value))
        with patch.object(serve, "_compact_config", return_value=serve.COMPACT_DEFAULTS), \
             patch.object(serve.tempfile, "mkdtemp", return_value=str(self.root)), \
             patch.object(serve.subprocess, "run", return_value=SimpleNamespace(stdout=json.dumps(report), stderr="", returncode=0)) as run:
            status, packet = serve.H._qa_run(h, {})
            self.assertEqual(status, 200)
            full = json.loads(Path(packet["evidence"]["path"]).read_text())
            self.assertEqual(full["cases"], report["cases"])
            self.assertEqual(artifacts.digest(full), packet["evidence"]["sha256"])
            _, response = serve.H._qa_run(h, {"detail": ["full"]})
            self.assertEqual(response["cases"], report["cases"])
            self.assertEqual(run.call_count, 2)  # No test execution is cached.

    def test_settings_patch_preserves_existing_fields_and_validates(self):
        with patch.object(serve, "COMPACT_CONFIG_PATH", str(self.root / "settings.json")):
            code, value = serve.H._compact_config_set(handler({"summaryModel": "inherit", "compactQa": False}))
            self.assertEqual(code, 200)
            self.assertTrue(value["referenceReuse"])
            _, value = serve.H._compact_config_set(handler({"autoCompact": True, "thresholdTokens": 200000}))
            self.assertEqual(value["summaryModel"], "inherit")
            self.assertFalse(value["compactQa"])
            self.assertEqual(serve.H._compact_config_set(handler({"referenceReuse": "false"}))[0], 400)
            self.assertTrue(serve._compact_config()["referenceReuse"])

    def test_phase_files_preserve_gates_and_load_schema_only_when_finalizing(self):
        root = Path(serve.INSTALL_ROOT)
        common = (root / ".claude/agents/art-director-orchestrator.md").read_text()
        plate = (root / "docs/agents/art-direction-plate.md").read_text()
        finalize = (root / "docs/agents/art-direction-finalize.md").read_text()
        self.assertIn("Load only the current phase", common)
        self.assertNotIn('"bindingRules":', common + plate)
        self.assertIn("<direction-options", plate)
        self.assertIn("motionGateBlock", plate)
        self.assertIn("art-direction-contract.md", finalize)
        self.assertIn("/__context/contract", finalize)
        self.assertLess(len(common + plate), 77448 * .5)


if __name__ == "__main__":
    unittest.main()
