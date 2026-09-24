"""Layout saves must survive parsing and leave unrelated source intact."""
import ast
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch as mock_patch

EDITOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDITOR))
import data_layout


def parse_js(text):
    script = "const vm=require('node:vm'),fs=require('node:fs'),c={window:{}};vm.runInNewContext(fs.readFileSync(0,'utf8'),c);process.stdout.write(JSON.stringify(c.window.EDITOR_DATA));"
    return json.loads(subprocess.check_output(["node", "-e", script], input=text, text=True))


class DataLayoutTests(unittest.TestCase):
    def test_multiline_move_and_resize_through_production_handler(self):
        data = {"meta": {"project": "Fixture"}, "frames": [
            {"id": "screen", "col": 0, "row": 0, "w": 1440, "h": 900}], "arrows": []}
        source = "window.EDITOR_DATA = " + json.dumps(data, indent=2) + ";"
        tree = ast.parse((EDITOR / "serve.py").read_text())
        handler = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "H")
        method = next(n for n in handler.body if isinstance(n, ast.FunctionDef) and n.name == "_patch_data_layout")
        method.decorator_list = []
        namespace = {}
        exec(compile(ast.Module(body=[method], type_ignores=[]), "layout_handler", "exec"), namespace)
        with mock_patch("builtins.open", return_value=io.StringIO(source)):
            result, count = namespace["_patch_data_layout"]("fixture", {"screen": {
                "col": 5, "row": 2, "w": 800, "h": 600}}, None, None)
        self.assertEqual(count, 4)
        self.assertEqual(parse_js(result)["frames"][0], {
            "id": "screen", "col": 5, "row": 2, "w": 800, "h": 600})
        self.assertEqual(result.count('"col"'), 1)

    def test_compact_frames_and_nested_fields_are_not_confused(self):
        source = '''window.EDITOR_DATA = {meta: {id: "second"}, frames: [
          {id: "first", col: 0, row: 0}, {id: "second", nested: {col: 77, w: 88}, col: 1, row: 0}
        ]};'''
        result, _ = data_layout.patch(source, {"second": {"col": 4, "w": 800}})
        data = parse_js(result)
        self.assertEqual(data["frames"][0]["col"], 0)
        self.assertEqual(data["frames"][1]["col"], 4)
        self.assertEqual(data["frames"][1]["w"], 800)
        self.assertEqual(data["frames"][1]["nested"], {"col": 77, "w": 88})
        self.assertEqual(data["meta"], {"id": "second"})

    def test_comments_strings_and_single_quoted_ids_are_preserved(self):
        source = '''// A misleading frames: [] and id: "screen"
window.EDITOR_DATA = {
  meta: { project: 'Fixture' },
  frames: [{ id: 'screen', /* } ], col: 123 */ col: 0,
    setupScript: "setTimeout(function(){ const o = {w: 12}; }, 80)",
    note: `braces { }, col: 55`, label: 'User\\'s screen' }],
  arrows: []
};'''
        result, _ = data_layout.patch(source, {"screen": {"col": 2, "row": 3}})
        data = parse_js(result)
        self.assertEqual(data["frames"][0]["col"], 2)
        self.assertEqual(data["frames"][0]["row"], 3)
        self.assertEqual(data["frames"][0]["setupScript"], parse_js(source)["frames"][0]["setupScript"])
        self.assertIn("/* } ], col: 123 */", result)
        self.assertIn("// A misleading frames: []", result)

    def test_existing_duplicate_fields_are_repaired(self):
        source = 'window.EDITOR_DATA = {frames:[{id:"a", col:5, row:2, col:0, row:0}]};'
        result, _ = data_layout.patch(source, {"a": {"col": 8, "row": 4}})
        self.assertEqual(parse_js(result)["frames"][0], {"id": "a", "col": 8, "row": 4})

    def test_meta_sections_and_missing_fields(self):
        source = 'window.EDITOR_DATA = {meta:{dsRef:{id:"suss",w:20}},frames:[{id:"a"}],arrows:[]};'
        section = {"id": "one", "label": "One", "col": 0, "row": 0, "col2": 1, "row2": 0, "members": ["a"]}
        result, _ = data_layout.patch(source, {"a": {"col": 2, "row": 3, "w": 800, "h": 600}},
                                      {"defaultFrame": {"w": 800, "h": 600}, "canvasGap": 40},
                                      [section, {"id": "old", "deleted": True}])
        data = parse_js(result)
        self.assertEqual(data["meta"], {"dsRef": {"id": "suss", "w": 20}, "defaultFrame": {"w": 800, "h": 600}, "canvasGap": 40})
        self.assertEqual(data["frames"][0], {"id": "a", "col": 2, "row": 3, "w": 800, "h": 600})
        self.assertEqual(data["sections"], [section])
        unchanged, count = data_layout.patch(result, {"a": {"col": 2, "row": 3, "w": 800, "h": 600}},
                                             {"defaultFrame": {"w": 800, "h": 600}, "canvasGap": 40}, [section])
        self.assertEqual(unchanged, result)
        self.assertEqual(count, 0)
        partial, _ = data_layout.patch(result, {"a": {"col": 7}})
        self.assertEqual(parse_js(partial)["sections"], [section])
        cleared, _ = data_layout.patch(partial, {}, sections=[])
        self.assertEqual(parse_js(cleared)["sections"], [])

    def test_empty_and_missing_meta(self):
        for source in ('window.EDITOR_DATA = {frames:[],meta:{/* keep */}};',
                       'window.EDITOR_DATA = {frames:[]};'):
            result, _ = data_layout.patch(source, {}, {"defaultFrame": {"w": 400, "h": 700}, "canvasGap": 20})
            self.assertEqual(parse_js(result)["meta"], {"defaultFrame": {"w": 400, "h": 700}, "canvasGap": 20})

    def test_unsupported_or_malformed_data_fails_before_write(self):
        for source in ('window.EDITOR_DATA = {frames: [{id: "a"}];',
                       'window.EDITOR_DATA = {frames: getFrames()};',
                       'window.EDITOR_DATA = {frames: [{id: "a", ...other}]};'):
            with self.assertRaises(ValueError):
                data_layout.patch(source, {"a": {"col": 2}})


if __name__ == "__main__":
    unittest.main()
