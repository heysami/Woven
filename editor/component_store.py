"""Project component library. DS definitions remain owned by the DS library."""
import json
from pathlib import Path
import edit_store


def read(root):
    path = Path(root) / "editor" / "components.json"
    with edit_store.lock(path):
        raw = path.read_bytes() if path.exists() else b'{"definitions":[]}'
        value = json.loads(raw)
        return {"definitions": value.get("definitions", []), "version": edit_store.revision(raw)}


def put(root, definition, expected):
    if not isinstance(definition, dict) or not all(isinstance(definition.get(k), str) and definition[k] for k in ("id", "name", "html")):
        raise ValueError("Component id, name, and HTML are required")
    if not definition["id"].startswith("local:"):
        raise ValueError("Design-system components must be changed through their design-system library")
    path = Path(root) / "editor" / "components.json"
    with edit_store.lock(path):
        current = read(root)
        if expected != current["version"]:
            raise edit_store.Conflict("The component library changed. Reload the library before publishing.")
        rows = [r for r in current["definitions"] if r["id"] != definition["id"]]
        rows.append(definition)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_bytes(b'{"definitions":[]}')
        edit_store.write(path, json.dumps({"schemaVersion": 1, "definitions": rows}, ensure_ascii=False, indent=2), current["version"])
        return read(root)
