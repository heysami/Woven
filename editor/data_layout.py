"""Patch literal EDITOR_DATA objects without reformatting unrelated source.

This is a token walker, not a JavaScript evaluator. Strings and comments are
opaque, and only direct properties of the data, meta and frame objects change.
Unsupported object syntax fails before the caller writes anything.
"""
import ast
import json
import re


_TOKEN = re.compile(
    r'''\s+|//[^\r\n]*|/\*[\s\S]*?\*/|"(?:\\[\s\S]|[^"\\])*"'''
    r"|'(?:\\[\s\S]|[^'\\])*'|`(?:\\[\s\S]|[^`\\])*`"
    r"|[A-Za-z_$][\w$]*|-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|[^\s]"
)


def _string(raw):
    if raw.startswith('"'):
        return json.loads(raw)
    if raw.startswith("'"):
        return ast.literal_eval(raw)
    return raw


def patch(text, positions, meta=None, sections=None):
    tokens = [m for m in _TOKEN.finditer(text)
              if not m.group().isspace() and not m.group().startswith(("//", "/*"))]
    values = [t.group() for t in tokens]
    pairs, stack = {}, []
    for i, value in enumerate(values):
        if value in ("{", "[", "("):
            stack.append(i)
        elif value in ("}", "]", ")"):
            if not stack or values[stack[-1]] != {"}": "{", "]": "[", ")": "("}[value]:
                raise ValueError("unbalanced data file")
            pairs[stack.pop()] = i
        elif value in ('"', "'", "`"):
            raise ValueError("unterminated string in data file")
    if stack:
        raise ValueError("unbalanced data file")

    def properties(start):
        if values[start] != "{":
            raise ValueError("expected a literal data object")
        result, i, end = [], start + 1, pairs[start]
        while i < end:
            if i + 1 >= end or values[i + 1] != ":":
                raise ValueError("expected a literal object property")
            key = _string(values[i])
            begin = i + 2
            i = begin
            while i < end and values[i] != ",":
                i = pairs[i] + 1 if i in pairs else i + 1
            if i == begin:
                raise ValueError("missing property value")
            result.append((key, begin, i))
            i += 1
        return result

    roots = [i + 4 for i in range(len(values) - 4)
             if values[i:i + 5] == ["window", ".", "EDITOR_DATA", "=", "{"]]
    if len(roots) != 1:
        raise ValueError("expected one window.EDITOR_DATA object assignment")
    root = roots[0]
    root_fields = {key: (begin, end) for key, begin, end in properties(root)}
    changes, additions = [], {}

    def set_field(start, key, value):
        fields = properties(start)
        matches = [(begin, end) for name, begin, end in fields if name == key]
        encoded = json.dumps(value, ensure_ascii=False)
        if matches:
            # Repair all occurrences of keys duplicated by the old line-based
            # writer, so a later occurrence cannot override the requested value.
            for begin, end in matches:
                lo, hi = tokens[begin].start(), tokens[end - 1].end()
                if text[lo:hi] != encoded:
                    changes.append((lo, hi, encoded))
        else:
            additions.setdefault(start, {})[key] = value

    if positions:
        frame_field = root_fields.get("frames")
        if not frame_field or values[frame_field[0]] != "[":
            raise ValueError("cannot locate frames array")
        i, end = frame_field[0] + 1, pairs[frame_field[0]]
        while i < end:
            if values[i] != "{":
                raise ValueError("expected a literal frame object")
            fields = {key: (begin, stop) for key, begin, stop in properties(i)}
            ident = fields.get("id")
            if not ident or ident[1] != ident[0] + 1:
                raise ValueError("frame is missing a literal id")
            fid = _string(values[ident[0]])
            pos = positions.get(fid, {})
            for key in ("col", "row", "w", "h"):
                if type(pos.get(key)) is int:
                    set_field(i, key, pos[key])
            i = pairs[i] + 1
            if i < end:
                if values[i] != ",":
                    raise ValueError("expected a comma between frames")
                i += 1

    if isinstance(meta, dict):
        updates = {}
        df = meta.get("defaultFrame")
        if isinstance(df, dict) and all(type(df.get(k)) is int for k in ("w", "h")):
            updates["defaultFrame"] = {k: df[k] for k in ("w", "h")}
        if type(meta.get("canvasGap")) is int:
            updates["canvasGap"] = meta["canvasGap"]
        if updates:
            meta_field = root_fields.get("meta")
            if meta_field:
                for key, value in updates.items():
                    set_field(meta_field[0], key, value)
            else:
                set_field(root, "meta", updates)

    if isinstance(sections, list):
        keys = ("id", "label", "col", "row", "col2", "row2", "tone", "members")
        live = [{k: s[k] for k in keys if k in s}
                for s in sections if isinstance(s, dict) and not s.get("deleted")]
        if live or "sections" in root_fields:
            set_field(root, "sections", live)

    for start, fields in additions.items():
        insert = ", ".join(json.dumps(k) + ": " + json.dumps(v, ensure_ascii=False)
                           for k, v in fields.items())
        if properties(start):
            insert += ","
        at = tokens[start].end()
        changes.append((at, at, " " + insert + " "))
    for lo, hi, replacement in sorted(changes, reverse=True):
        text = text[:lo] + replacement + text[hi:]
    return text, len(changes)
