"""Canvas audit authoring contracts and actual handler regressions, without a daemon."""
import ast
import contextlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import threading
import time
import unittest
import urllib.parse

EDITOR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDITOR))
from kinds.registry import KINDS, KIND_IO, LOGIC_NODE_DEFS, io_contract_violations
from kinds.validate import validate_node
from kinds.io_resolve import resolve_downstream
from prompts.logic_authoring import get_section


class ContractTests(unittest.TestCase):
    def test_all_visible_logic_kinds_have_server_contracts_and_edit_destinations(self):
        self.assertEqual(len(LOGIC_NODE_DEFS), 51)
        self.assertIn('kinds/logic_nodes.js', (EDITOR / 'index.html').read_text())
        self.assertIn('const LOGIC_NODE_DEFS = globalThis.TH_LOGIC_NODE_DEFS;', (EDITOR / 'app.js').read_text())
        self.assertFalse(io_contract_violations())
        for kind, definition in LOGIC_NODE_DEFS.items():
            with self.subTest(kind=kind):
                node = {'id': 'target', 'kind': kind, 'x': 0, 'y': 0}
                self.assertFalse(validate_node(node, 'commit'))
                self.assertEqual(KINDS[kind]['controls'], definition['controls'])
                self.assertEqual({p['port'] for p in KIND_IO[kind]['provides']}, set(definition['provides']))
                producer = {'id': 'agent', 'kind': 'agent'}
                wf = {'nodes': [producer, node], 'edges': [{'from': 'agent.out', 'to': 'target.edit'}]}
                text = resolve_downstream(wf, 'agent', producer, {'proto_slug': 'main', 'nodes_by_id': {'agent': producer, 'target': node}})
                self.assertIn('logic-target.js', text)
                self.assertIn('buildSpec', text)

    def test_catalogue_is_generated_and_covers_declared_ports(self):
        catalogue = get_section('catalogue')
        for kind, definition in LOGIC_NODE_DEFS.items():
            self.assertIn('`' + kind + '`', catalogue)
            for port in definition['provides']:
                self.assertIn(port + '(', catalogue)
        self.assertIn('scale v/t -> v', catalogue)


class HandlerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tree = ast.parse((EDITOR / 'serve.py').read_text())
        handler = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'H')
        wanted = {'_workflow_nodes_add_body', '_workflow_node_commit', '_workflow_node_status', '_qa_resolve_url'}
        methods = [n for n in handler.body if isinstance(n, ast.FunctionDef) and n.name in wanted]
        error = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == '_QAResolveError')
        cls.ns = {'os': os, 'json': json, 'time': time, 're': re, 'urllib': urllib,
                  '_history_bracket': lambda *a, **k: contextlib.nullcontext(),
                  '_request_semaphore': lambda *a: threading.Semaphore(1),
                  '_workflow_lock': lambda *a: threading.Lock(),
                  '_autoplace_new_nodes': lambda *a: (0, 0), '_sidecar_layout': lambda *a: {},
                  '_broadcast_workflow_change': lambda *a: None, 'PORT': 5747,
                  '_qs_get': lambda q, k: q.get(k, [''])[0],
                  '_write_json_atomic': lambda p, v: Path(p).write_text(json.dumps(v))}
        exec(compile(ast.Module(body=[error, *methods], type_ignores=[]), str(EDITOR / 'serve.py'), 'exec'), cls.ns)
        cls.Handler = type('HandlerFixture', (), {name: cls.ns[name] for name in wanted})

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.wf = self.root / 'workflow' / 'workflow.json'
        self.wf.parent.mkdir()
        self.wf.write_text('{"nodes":[],"edges":[]}')
        self.ns['resolve_project_root'] = lambda *a, **kw: str(self.root)
        def load(root):
            data = json.loads(self.wf.read_text())
            return data, {n['id']: n for n in data['nodes']}, str(self.wf), None
        self.ns['_load_workflow_nodes'] = load
        self.handler = self.Handler()
        self.handler._reply = lambda status, data: (status, data)
        self.handler._read_json_body = lambda: self.body
        self.handler.headers = {}
        self.body = {}
        self.qs = {'project': ['fixture']}

    def test_documented_scaffold_append_and_slot_commit(self):
        doc = (EDITOR.parent / '.claude/agents/app-node-orchestrator.md').read_text()
        payload = json.loads(re.search(r'```json\n(.*?)\n```', doc, re.S)[1])
        status, reply = self.handler._workflow_nodes_add_body(str(self.root), payload)
        self.assertEqual(status, 200, reply)
        graph = json.loads(self.wf.read_text())
        self.assertEqual(len(graph['nodes']), 5)
        self.assertEqual(len(graph['edges']), 4)
        by_id = {n['id']: n for n in graph['nodes']}
        for edge in graph['edges']:
            for side, ports in [('from', 'provides'), ('to', 'accepts')]:
                nid, port = edge[side].rsplit('.', 1)
                self.assertIn(port, {p['port'] for p in KINDS[by_id[nid]['kind']]['io'][ports]})
        self.body = {}
        status, reply = self.handler._workflow_node_commit(self.qs, 'an_demo_pointer')
        self.assertEqual(status, 200, reply)
        self.assertEqual(reply['runStatus'], 'done')
        # Append is explicitly idempotent and never silently changes an existing node.
        payload['addNodes'][0]['spec']['params']['button'] = 'right'
        status, reply = self.handler._workflow_nodes_add_body(str(self.root), payload)
        self.assertEqual(reply['addedNodes'], [])
        self.assertEqual(json.loads(self.wf.read_text())['nodes'][0]['spec']['params']['button'], 'any')

    def test_invalid_graph_operations_fail_before_commit(self):
        self.wf.write_text(json.dumps({'nodes': [{'id': 'c', 'kind': 'mm-composer'}], 'edges': []}))
        for body in [{'edges': []}, {'addNodes': ['invalid']}, {'addEdges': [{'from': 'x.out', 'to': 'c.in'}]}]:
            self.body = body
            status, reply = self.handler._workflow_node_commit(self.qs, 'c')
            self.assertEqual(status, 400, reply)
        self.assertNotIn('runStatus', json.loads(self.wf.read_text())['nodes'][0])
        self.assertEqual(self.handler._workflow_nodes_add_body(str(self.root), {'edges': []})[0], 400)

    def test_existing_spec_update_and_commit(self):
        self.wf.write_text(json.dumps({'nodes': [{'id': 'p', 'kind': 'input-pointer', 'spec': {'v': 1, 'kind': 'input-pointer', 'params': {'button': 'any'}}}], 'edges': []}))
        body = json.dumps({'spec': {'params': {'button': 'right'}}}).encode()
        self.handler.headers = {'Content-Length': str(len(body))}
        self.handler.rfile = io.BytesIO(body)
        status, reply = self.handler._workflow_node_status(self.qs, 'p')
        self.assertEqual(status, 200, reply)
        self.assertEqual(json.loads(self.wf.read_text())['nodes'][0]['spec']['params']['button'], 'right')
        self.body = {}
        self.assertEqual(self.handler._workflow_node_commit(self.qs, 'p')[0], 200)

    def test_qa_rejects_missing_or_failed_bake(self):
        node = {'id': 'c', 'kind': 'mm-composer', 'bakedPath': 'source/mm-c.html'}
        self.wf.write_text(json.dumps({'nodes': [node], 'edges': []}))
        with self.assertRaises(self.ns['_QAResolveError']):
            self.handler._qa_resolve_url({**self.qs, 'node': ['c']})
        (self.root / 'source').mkdir()
        (self.root / node['bakedPath']).write_text('<html>fixture</html>')
        self.assertTrue(self.handler._qa_resolve_url({**self.qs, 'node': ['c']})['baked'])
        node['runStatus'] = 'error'
        self.wf.write_text(json.dumps({'nodes': [node], 'edges': []}))
        with self.assertRaises(self.ns['_QAResolveError']):
            self.handler._qa_resolve_url({**self.qs, 'node': ['c']})


if __name__ == '__main__':
    unittest.main()
