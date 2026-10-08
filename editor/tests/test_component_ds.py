"""Component design system tooling: editor/tools/ds/{ds_model,ds_page,ds_check,build_ds}.py.

Runs against the fixture DS in editor/tools/ds/fixtures/mini-project and against
broken temp copies of it. The browser side lives in test-component-ds-runtime.cjs.
"""

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "tools", "ds")
sys.path.insert(0, os.path.abspath(TOOLS))

import build_ds  # noqa: E402
import ds_check  # noqa: E402
import ds_model  # noqa: E402

PROJECT = os.path.join(os.path.abspath(TOOLS), "fixtures", "mini-project")
DS_DIR = os.path.join(PROJECT, "design-systems", "mini")


def codes(findings, level=None):
    return sorted(set(f.code for f in findings if level is None or f.level == level))


class FixtureBuilds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ds, wrote = build_ds.build(DS_DIR)
        assert wrote

    def test_clean(self):
        self.assertEqual([f.fmt() for f in self.ds.findings if f.level != "info"], [])

    def test_outputs(self):
        for f in ("ds.css", "ds-runtime.js", "manifest.json", "CATALOG.md", "gallery.html"):
            self.assertTrue(os.path.isfile(os.path.join(DS_DIR, "build", f)), f)

    def test_css_order(self):
        css = open(os.path.join(DS_DIR, "build", "ds.css")).read()
        self.assertNotIn("@layer", css, "one plain stylesheet: specificity + order like a hand-written file")
        order = [css.index(m) for m in ("tokens/tokens.css", "foundations/base.css", "components/stack/style.css",
                                        "components/button/style.css", "components/card/style.css", "shells/app/style.css", "themes/dark.css")]
        self.assertEqual(order, sorted(order), "tokens, foundations, blocks by layer rank, themes")
        # contains comes first: button (atom) contains icon (atom)
        self.assertLess(css.index("components/icon/style.css"), css.index("components/button/style.css"))
        # a parent's context rule lands after the child it styles: card contains button
        self.assertLess(css.index(".btn--primary {"), css.index(".card__actions .btn {"))

    def test_runtime_payload_is_script_safe(self):
        js = open(os.path.join(DS_DIR, "build", "ds-runtime.js")).read()
        self.assertIn("DS.__load(", js)
        self.assertIn('DS.behavior("filter-chip"', js)
        self.assertIn('DS.service("toast"', js)
        self.assertTrue(js.rstrip().endswith("DS.__boot();"))
        payload = js[js.index("DS.__load(") + len("DS.__load("):]
        self.assertNotIn("</script", payload.lower())

    def test_catalog_signatures(self):
        cat = open(os.path.join(DS_DIR, "build", "CATALOG.md")).read()
        self.assertIn("<ds-filter-chip label! count:number size:m|s=m>", cat)
        self.assertIn("<ds-card title> slots: default(any), actions(button)", cat)
        self.assertIn("Replaces <select>.", cat)
        self.assertIn("`DS.toast` Toast messages.", cat)
        self.assertIn("## Icons (2; styles: filled, outline; default filled)", cat)

    def test_manifest(self):
        man = json.load(open(os.path.join(DS_DIR, "build", "manifest.json")))
        self.assertEqual(man["blocks"]["button"]["rootClass"], "btn")
        self.assertEqual(man["blocks"]["filter-bar"]["kind"], "patterns")
        self.assertIn("edit", man["icons"]["outline"])
        self.assertNotIn("fill=", man["icons"]["filled"]["edit"]["b"], "icon colour comes from currentColor")


class PageChecks(unittest.TestCase):
    def test_class_roots_catch_hand_built_parts(self):
        tmp = tempfile.mkdtemp()
        try:
            proj = os.path.join(tmp, "p")
            shutil.copytree(PROJECT, proj, ignore=shutil.ignore_patterns("build"))
            d = os.path.join(proj, "design-systems", "mini", "components", "select", "component.json")
            spec = json.load(open(d)); spec["classRoots"] = ["select-panel"]; json.dump(spec, open(d, "w"))
            page = os.path.join(proj, "source", "main", "x.html")
            open(page, "w").write('<link rel="stylesheet" href="../../design-systems/mini/build/ds.css">'
                                  '<script src="../../design-systems/mini/build/ds-runtime.js"></script>'
                                  '<div class="select-panel">hand</div>')
            ds, fs = ds_check.run(pages=[page])
            self.assertIn("hand-built-block", codes(fs, "error"))
        finally:
            shutil.rmtree(tmp)


    def test_good_page(self):
        ds, fs = ds_check.run(pages=[os.path.join(PROJECT, "source", "main", "index.html")])
        self.assertIsNotNone(ds)
        self.assertEqual(codes(fs, "error"), [])
        self.assertEqual(codes(fs, "info"), ["ds-custom"])

    def test_bad_page(self):
        ds, fs = ds_check.run(pages=[os.path.join(PROJECT, "source", "main", "bad.html")])
        self.assertEqual(codes(fs, "error"), sorted([
            "bad-enum", "bad-prop-type", "custom-without-reason", "hand-built-block", "inline-style-on-block",
            "missing-required", "missing-runtime", "page-css-touches-ds", "raw-replaced-element",
            "slot-not-allowed", "unknown-block", "unknown-prop"]))
        self.assertEqual(codes(fs, "warn"), ["hand-built-in-js", "raw-replaced-in-js", "unknown-token"])

    def test_features_page_clean(self):
        ds, fs = ds_check.run(pages=[os.path.join(PROJECT, "source", "main", "features.html")])
        self.assertEqual([f.fmt() for f in fs if f.level != "info"], [])

    def test_part_and_template_slot_errors(self):
        tmp = tempfile.mkdtemp()
        try:
            page = os.path.join(PROJECT, "source", "main", "_tmp_parts.html")
            open(page, "w").write('<link rel="stylesheet" href="../../design-systems/mini/build/ds.css">'
                                  '<script src="../../design-systems/mini/build/ds-runtime.js"></script>'
                                  '<ds-input-affix nope:id="x" input:style="color:red" input:onclick="go()"></ds-input-affix>'
                                  '<ds-table columns="A"><template slot="body"><tr><td>x</td></tr></template></ds-table>'
                                  '<ds-select options=\'["a", "b,c"]\'></ds-select><ds-select options="[broken"></ds-select>')
            ds, fs = ds_check.run(pages=[page])
            got = codes(fs, "error")
            self.assertIn("unknown-part", got)
            self.assertIn("slot-not-allowed", got)
            self.assertIn("bad-prop-type", got)
            self.assertIn("bad-part-attr", got, "inline style on a part is an error, like on a block")
            self.assertEqual(sum(1 for f in fs if f.code == "bad-part-attr"), 1, "on* handlers are allowed on a part")
        finally:
            os.remove(page)
            shutil.rmtree(tmp)

    def test_resolution_from_page_link(self):
        self.assertEqual(os.path.normpath(ds_check.resolve_ds_dir(os.path.join(PROJECT, "source", "main", "index.html"))), os.path.normpath(DS_DIR))

    def test_cli_exit_codes(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(ds_check.main(["--page", os.path.join(PROJECT, "source", "main", "index.html")]), 0)
            self.assertEqual(ds_check.main(["--page", os.path.join(PROJECT, "source", "main", "bad.html"), "--json"]), 1)

    def test_document_ds_is_skipped(self):
        tmp = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(tmp, "design-systems", "doc"))
            json.dump({"id": "doc"}, open(os.path.join(tmp, "design-systems", "doc", "meta.json"), "w"))
            os.makedirs(os.path.join(tmp, "source", "main"))
            page = os.path.join(tmp, "source", "main", "a.html")
            open(page, "w").write("<p>hi</p>")
            ds, reason = ds_check.run(pages=[page])
            self.assertIsNone(ds)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(ds_check.main(["--page", page]), 2)
        finally:
            shutil.rmtree(tmp)


class BrokenDS(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.ds_dir = os.path.join(self.tmp, "mini")
        shutil.copytree(DS_DIR, self.ds_dir, ignore=shutil.ignore_patterns("build"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def put(self, rel, text):
        with open(os.path.join(self.ds_dir, rel), "w") as f:
            f.write(text)

    def edit_json(self, rel, fn):
        p = os.path.join(self.ds_dir, rel)
        d = json.load(open(p))
        fn(d)
        json.dump(d, open(p, "w"))

    def found(self):
        return codes(ds_model.load(self.ds_dir).findings, "error")

    def test_template_errors(self):
        self.put("components/stack/template.html", '<div class="stack">{{#if gap}}<ds-slot></ds-slot></div>')
        self.assertIn("template-error", self.found())

    def test_unknown_template_name(self):
        self.put("components/stack/template.html", '<div class="stack stack--{{gapp}}"><ds-slot></ds-slot></div>')
        self.assertIn("template-unknown-name", self.found())

    def test_multi_root(self):
        self.put("components/stack/template.html", '<div class="stack"><ds-slot></ds-slot></div><div></div>')
        self.assertIn("template-not-single-root", self.found())

    def test_schema(self):
        self.edit_json("components/stack/component.json", lambda d: d.update({"colour": "red"}))
        self.assertIn("schema-invalid", self.found())

    def test_duplicate_root_class(self):
        self.edit_json("components/select/component.json", lambda d: d.update({"rootClass": "btn"}))
        self.assertIn("duplicate-root-class", self.found())

    def test_tokens_and_literals(self):
        self.put("components/stack/style.css", ".stack { gap: var(--space-9); color: #ff0000; }\n")
        f = self.found()
        self.assertIn("token-undefined", f)
        self.assertIn("raw-value-in-block-css", f)

    def test_slot_mismatch(self):
        self.put("components/stack/template.html", '<div class="stack stack--{{gap}}"></div>')
        self.assertIn("schema-invalid", self.found())

    def test_behavior_name(self):
        self.put("components/filter-chip/behavior.js", 'DS.behavior("chip", {});\n')
        self.assertIn("behavior-name", self.found())

    def test_template_hand_builds_other_block(self):
        # card does not list filter-chip in `contains`, so it may not write its classes
        self.put("components/card/template.html", '<section class="card"><span class="filter-chip">x</span><ds-stack><ds-slot></ds-slot></ds-stack><ds-slot name="actions"></ds-slot></section>')
        self.assertIn("hand-built-block", self.found())

    def test_template_may_use_raw_replaced_elements(self):
        # filter-chip's root is a raw <button> while ds-button replaces <button>: allowed in DS code
        self.assertNotIn("raw-replaced-element", self.found())

    def test_css_outside_block_warns(self):
        self.put("components/stack/style.css", ".stack--s { gap: var(--space-2); }\n.stack .btn { margin: 0; }\n")
        fs = ds_model.load(self.ds_dir).findings
        self.assertIn("css-outside-block", codes(fs, "warn"))

    def test_contains_allows_composition_in_templates(self):
        # same-element composition (.card on a stat block's root) and part reuse
        os.makedirs(os.path.join(self.ds_dir, "components", "stat"))
        json.dump({"name": "stat", "layer": "molecule", "oneLine": "Number tile.", "rootClass": "stat",
                   "props": {"value": {"type": "string"}}, "contains": ["card"]},
                  open(os.path.join(self.ds_dir, "components", "stat", "component.json"), "w"))
        self.put("components/stat/template.html", '<div class="card stat"><h3 class="card__title">{{value}}</h3></div>')
        json.dump([{"title": "x", "props": {"value": "3"}}], open(os.path.join(self.ds_dir, "components", "stat", "examples.json"), "w"))
        self.assertNotIn("hand-built-block", self.found())
        self.edit_json("components/stat/component.json", lambda d: d.update({"contains": []}))
        self.assertIn("hand-built-block", self.found())

    def test_class_roots(self):
        self.edit_json("components/select/component.json", lambda d: d.update({"classRoots": ["select-panel"]}))
        ds = ds_model.load(self.ds_dir)
        self.assertIs(ds.owner_of_class("select-panel__item"), ds.blocks["select"])
        self.assertEqual(codes(ds.findings, "error"), [])
        self.edit_json("components/card/component.json", lambda d: d.update({"classRoots": ["select-panel"]}))
        self.assertIn("duplicate-root-class", self.found())

    def test_templated_first_class_is_no_root_class(self):
        self.put("components/stack/template.html", '<div class="{{gap}} stack"><ds-slot></ds-slot></div>')
        self.edit_json("components/stack/component.json", lambda d: d.pop("rootClass"))
        ds = ds_model.load(self.ds_dir)
        self.assertIsNone(ds.blocks["stack"].root_class)
        self.assertIn("stack", ds.blocks["stack"].template_classes)

    def test_big_enum_needs_no_full_coverage(self):
        self.edit_json("components/icon/component.json", lambda d: d["props"]["style"].update({"values": ["filled", "outline"] + ["s" + str(i) for i in range(30)]}))
        fs = ds_model.load(self.ds_dir).findings
        self.assertNotIn("missing-example", codes(fs, "warn"))

    def test_parts_declared_and_marked(self):
        self.edit_json("components/input-affix/component.json", lambda d: d["parts"].update({"clear": "clear button"}))
        self.assertIn("schema-invalid", self.found())

    def test_slot_ref_must_exist(self):
        self.put("components/stack/template.html", '<div class="stack stack--{{gap}}">{{#if @slot.nope}}x{{/if}}<ds-slot></ds-slot></div>')
        self.assertIn("template-unknown-name", self.found())

    def test_comment_slot_point_counts(self):
        self.put("components/stack/template.html", '<div class="stack stack--{{gap}}"><!--ds-slot--></div>')
        self.assertEqual(self.found(), [])

    def test_knob_fallback_is_allowed(self):
        self.put("components/stack/style.css", ".stack { display: grid; grid-template-columns: repeat(var(--stack-cols, 1), 1fr); }\n.stack--s { gap: var(--space-2); }\n.stack--m { gap: var(--space-3); }\n")
        self.assertNotIn("token-undefined", self.found())

    def test_strict_build_refuses(self):
        self.put("components/stack/template.html", "<div>")
        ds, wrote = build_ds.build(self.ds_dir, strict=True)
        self.assertFalse(wrote)
        self.assertFalse(os.path.exists(os.path.join(self.ds_dir, "build")))


class WovenIntegration(unittest.TestCase):
    """serve.py endpoints + hook registration, capabilities preamble branch."""

    @classmethod
    def setUpClass(cls):
        build_ds.build(DS_DIR)
        editor = os.path.join(os.path.abspath(TOOLS), "..", "..")
        for p in (editor, os.path.join(editor, "kinds")):
            if p not in sys.path:
                sys.path.insert(0, os.path.abspath(p))
        import serve
        import capabilities
        cls.serve, cls.cap = serve, capabilities

    def test_design_system_endpoints(self):
        h = self.serve.H.__new__(self.serve.H)
        out = {}
        h._reply = lambda code, body: out.update(code=code, body=body)
        orig = self.serve.resolve_project_root
        self.serve.resolve_project_root = lambda qs, **kw: PROJECT
        try:
            h._design_system_get({})
            item = out["body"]["items"][0]
            self.assertEqual((item["kind"], item["hasStyles"], item["hasGallery"]), ("component", True, True))
            h._design_system_get({"id": ["mini"]})
            self.assertEqual(out["code"], 200)
            self.assertEqual(out["body"]["kind"], "component")
            self.assertIn("/* ==== blocks ==== */", out["body"]["trio"]["stylesCss"])
        finally:
            self.serve.resolve_project_root = orig

    def test_hook_registered(self):
        tmp = tempfile.mkdtemp()
        orig = self.serve.INSTALL_ROOT
        try:
            os.makedirs(os.path.join(tmp, ".claude", "hooks"))
            for n in ("require-orchestrator.sh", "ds-check-on-write.py"):
                open(os.path.join(tmp, ".claude", "hooks", n), "w").write("#")
            self.serve.INSTALL_ROOT = tmp
            path = self.serve._ensure_harness_settings()
            post = json.load(open(path))["hooks"]["PostToolUse"]
            self.assertEqual(post[0]["matcher"], "Write|Edit|MultiEdit")
            self.assertTrue(post[0]["hooks"][0]["command"].endswith("ds-check-on-write.py"))
        finally:
            self.serve.INSTALL_ROOT = orig
            shutil.rmtree(tmp)

    def test_guard_toggle_reaches_hook(self):
        self.assertEqual(self.serve._apply_guard_env({}, {"dsGuard": False}).get("TH_DS_GUARD"), "0")
        self.assertNotIn("TH_DS_GUARD", self.serve._apply_guard_env({"TH_DS_GUARD": "0"}, {"dsGuard": True}))

    def test_preamble_branch(self):
        b = self.cap._resolve_ds_binding(PROJECT, "main")
        self.assertEqual(b["kind"], "component")
        self.assertEqual(b["catalog"], "design-systems/mini/build/CATALOG.md")
        cat = self.cap._design_system_catalog(PROJECT, "main")
        self.assertIn("<design-system-catalog>", cat)
        self.assertIn("<ds-filter-chip label!", cat)
        self.assertNotIn("styles.css", cat)
        guard = self.cap._ds_guard_stub(PROJECT, "main")
        self.assertIn("ds_check.py --page", guard)
        self.assertNotIn("ds-guardian", guard)

    def test_document_ds_unchanged(self):
        tmp = tempfile.mkdtemp()
        try:
            d = os.path.join(tmp, "design-systems", "doc")
            os.makedirs(d)
            open(os.path.join(d, "DESIGN.md"), "w").write("# Doc DS")
            json.dump({"id": "doc"}, open(os.path.join(d, "meta.json"), "w"))
            b = self.cap._resolve_ds_binding(tmp, None)
            self.assertEqual(b["kind"], "document")
            self.assertIn("<design-system-index>", self.cap._design_system_catalog(tmp, None))
            self.assertIn("ds-guardian", self.cap._ds_guard_stub(tmp, None))
        finally:
            shutil.rmtree(tmp)


class TemplateGrammar(unittest.TestCase):
    def test_render_matches_runtime_rules(self):
        nodes = ds_model.compile_template('<a class="x x--{{v}}">{{#if n == "2"}}two{{else}}other{{/if}}{{#each items as it}}[{{it.k}}{{@index}}]{{/each}}{{icon}}</a>')
        out = ds_model.render_template(nodes, {"v": "a", "n": 2, "items": [{"k": "p"}, {"k": "q"}], "icon": "<b>"})
        self.assertEqual(out, '<a class="x x--a">two[p0][q1]&lt;b&gt;</a>')

    def test_else_if_compare_json_first_last(self):
        nodes = ds_model.compile_template(
            '{{#each xs as x}}{{#if x == v}}[eq]{{else if @first}}[first]{{else if @last}}[last]{{else}}[mid]{{/if}}{{/each}}|{{json xs}}')
        out = ds_model.render_template(nodes, {"xs": ["a", "b", "c", "d"], "v": "c"})
        self.assertEqual(out, "[first][mid][eq][last]|[&quot;a&quot;,&quot;b&quot;,&quot;c&quot;,&quot;d&quot;]")

    def test_slot_flags(self):
        nodes = ds_model.compile_template('{{#if @slot.actions}}A{{/if}}{{#if @slot}}D{{/if}}')
        self.assertEqual(ds_model.render_template(nodes, {}, ctx={"slots": {"actions": True}}), "A")
        self.assertEqual(ds_model.render_template(nodes, {}, ctx={"slots": {"default": True}}), "D")

    def test_strings_have_no_members(self):
        nodes = ds_model.compile_template('{{#each cs as c}}{{#if c.sub}}S{{/if}}{{c}}{{/each}}')
        self.assertEqual(ds_model.render_template(nodes, {"cs": ["x", {"sub": "y"}]}), "xS")

    def test_double_else_rejected(self):
        with self.assertRaises(ds_model.TemplateError):
            ds_model.compile_template("{{#if a}}1{{else}}2{{else}}3{{/if}}")

    def test_icon_helper_needs_args(self):
        nodes = ds_model.compile_template('{{icon name "outline"}}')
        self.assertEqual(nodes[0]["t"], "icon")
        self.assertEqual(ds_model.compile_template("{{icon}}")[0]["t"], "var")

    def test_no_raw_output(self):
        with self.assertRaises(ds_model.TemplateError):
            ds_model.compile_template("{{{html}}}")


if __name__ == "__main__":
    unittest.main()
