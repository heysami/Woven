"""Exercise the production handlers without starting daemon workers or watchers."""
import ast
import contextlib
import os
from pathlib import Path
import sys
import tempfile
import unittest

EDITOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDITOR))
import component_store
import edit_store


class EditEndpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse((EDITOR / "serve.py").read_text())
        handler = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "H")
        wanted = {"_edit_source", "_html_save", "_edit_components"}
        methods = [n for n in handler.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
        safe_join = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_safe_join")
        cls.namespace = {"os": os, "_history_bracket": lambda *a, **k: contextlib.nullcontext()}
        module = ast.Module(body=[safe_join, *methods], type_ignores=[])
        exec(compile(module, str(EDITOR / "serve.py"), "exec"), cls.namespace)
        cls.Handler = type("HandlerFixture", (), {name: cls.namespace[name] for name in wanted})

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "source").mkdir()
        self.file = self.root / "source" / "index.html"
        self.file.write_text("<h1>Original</h1>")
        self.handler = self.Handler()
        self.handler._reply = lambda status, value: (status, value)
        self.handler._read_json_body = lambda **kwargs: self.body
        self.body = {}

        def resolve(qs, require_explicit=False):
            if require_explicit and qs.get("project") != ["fixture"]:
                raise ValueError("Explicit project is required")
            return str(self.root)

        self.namespace["resolve_project_root"] = resolve
        self.qs = {"project": ["fixture"]}

    def test_baseline_and_compare_and_swap(self):
        status, baseline = self.handler._edit_source({**self.qs, "path": ["source/index.html"]})
        self.assertEqual(status, 200)
        self.body = {"path": "source/index.html", "html": "<h1>Changed</h1>", "expectedVersion": baseline["version"]}
        status, saved = self.handler._html_save(self.qs)
        self.assertEqual(status, 200)
        self.assertEqual(saved["version"], edit_store.read(self.file)["version"])
        self.body["html"] = "stale"
        self.assertEqual(self.handler._html_save(self.qs)[0], 409)
        self.assertEqual(self.file.read_text(), "<h1>Changed</h1>")

    def test_invalid_paths_and_missing_project_are_rejected(self):
        for path in ["source/../../outside.html", "source/../editor/index.html", "editor/app.js", "source/index.js"]:
            self.assertEqual(self.handler._edit_source({**self.qs, "path": [path]})[0], 400)
            self.body = {"path": path, "html": "no"}
            self.assertEqual(self.handler._html_save(self.qs)[0], 400)
        self.assertEqual(self.handler._edit_source({"path": ["source/index.html"]})[0], 400)
        self.assertEqual(self.handler._edit_components({})[0], 400)

    def test_symlink_cannot_escape_source(self):
        outside = self.root / "editor.html"
        outside.write_text("untouched")
        (self.root / "source" / "linked.html").symlink_to(outside)
        self.body = {"path": "source/linked.html", "html": "no"}
        self.assertEqual(self.handler._html_save(self.qs)[0], 400)
        self.assertEqual(self.handler._edit_source({**self.qs, "path": ["source/linked.html"]})[0], 400)
        self.assertEqual(outside.read_text(), "untouched")

    def test_components_have_revisions_and_cannot_overwrite_ds(self):
        _, library = self.handler._edit_components(self.qs)
        self.body = {"definition": {"id": "local:button", "name": "Button", "html": "<button>Go</button>"}, "expectedVersion": library["version"]}
        status, saved = self.handler._edit_components(self.qs, True)
        self.assertEqual(status, 200)
        self.assertEqual(len(saved["definitions"]), 1)
        self.assertEqual(self.handler._edit_components(self.qs, True)[0], 409)
        self.body["definition"]["id"] = "ds:button"
        self.body["expectedVersion"] = saved["version"]
        self.assertEqual(self.handler._edit_components(self.qs, True)[0], 400)
        self.assertEqual(component_store.read(self.root)["definitions"][0]["id"], "local:button")


if __name__ == "__main__":
    unittest.main()
