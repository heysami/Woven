#!/usr/bin/env python3
"""office_text.py - print an Office file (.xlsx, .docx, .pptx) as plain text.

For agents reading a project reference they downloaded through the signed-in
agent browser (docs/agents/signed-in-references.md): a SharePoint or OneDrive
viewer page holds no readable text, so the agent saves the file itself and
reads it here. Woven ships with no pip step, so this is stdlib only (the
.xlsx side is editor/xlsx_io.py).

  python3 office_text.py FILE               the whole file
  python3 office_text.py FILE --sheets      .xlsx: sheet names and sizes only
  python3 office_text.py FILE --sheet NAME  .xlsx: one sheet (repeatable)
  python3 office_text.py FILE --max-rows N  .xlsx: at most N rows per sheet

Sheets print as tab-separated rows, empty rows and trailing empty columns
dropped. Documents print paragraph by paragraph, tables as tab-separated rows.
Slides print in order. Python 3.9-safe. No em dashes anywhere.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import xlsx_io  # noqa: E402  (editor/xlsx_io.py)

_W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def _trim(rows):
    """Drop empty rows and the empty columns at the right edge."""
    rows = [[(c or "").replace("\t", " ").replace("\n", " ").strip() for c in r] for r in rows]
    rows = [r for r in rows if any(r)]
    width = max([max([i + 1 for i, c in enumerate(r) if c] or [0]) for r in rows] or [0])
    return [r[:width] for r in rows], width


def xlsx_text(path, only=None, max_rows=None, names_only=False):
    out = []
    for sheet in xlsx_io.read_xlsx(path):
        if only and sheet["name"] not in only:
            continue
        rows, width = _trim(sheet["rows"])
        out.append("## Sheet: %s (%d rows x %d columns)" % (sheet["name"], len(rows), width))
        if names_only:
            continue
        shown = rows if not max_rows else rows[:max_rows]
        out.extend("\t".join(r) for r in shown)
        if len(shown) < len(rows):
            out.append("[%d more rows not shown]" % (len(rows) - len(shown)))
        out.append("")
    return "\n".join(out)


def _para_text(p):
    parts = []
    for node in p.iter():
        if node.tag == _W + "t" and node.text:
            parts.append(node.text)
        elif node.tag == _W + "tab":
            parts.append("\t")
        elif node.tag in (_W + "br", _W + "cr"):
            parts.append("\n")
    return "".join(parts)


def docx_text(path):
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read("word/document.xml"))
    body = root.find(_W + "body")
    out = []
    for child in (list(body) if body is not None else []):
        if child.tag == _W + "p":
            text = _para_text(child).strip()
            if not text:
                continue
            style = child.find(_W + "pPr/" + _W + "pStyle")
            level = re.match(r"(?i)heading\s*(\d)", style.get(_W + "val") or "") if style is not None else None
            out.append(("#" * int(level.group(1)) + " " + text) if level else text)
        elif child.tag == _W + "tbl":
            rows = [[" ".join(_para_text(p).strip() for p in tc.iter(_W + "p")).strip()
                     for tc in tr.findall(_W + "tc")] for tr in child.findall(_W + "tr")]
            rows, _ = _trim(rows)
            out.append("\n".join("\t".join(r) for r in rows))
    return "\n\n".join(out)


def pptx_text(path):
    with zipfile.ZipFile(path) as zf:
        slides = sorted((n for n in zf.namelist() if re.match(r"ppt/slides/slide\d+\.xml$", n)),
                        key=lambda n: int(re.search(r"(\d+)\.xml$", n).group(1)))
        out = []
        for i, name in enumerate(slides, 1):
            root = ET.fromstring(zf.read(name))
            paras = []
            for p in root.iter(_A + "p"):
                text = "".join(t.text or "" for t in p.iter(_A + "t")).strip()
                if text:
                    paras.append(text)
            out.append("## Slide %d\n%s" % (i, "\n".join(paras)))
    return "\n\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Print an .xlsx, .docx or .pptx file as plain text.")
    ap.add_argument("file")
    ap.add_argument("--sheets", action="store_true", help=".xlsx: sheet names and sizes only")
    ap.add_argument("--sheet", action="append", help=".xlsx: only this sheet (repeatable)")
    ap.add_argument("--max-rows", type=int, help=".xlsx: at most this many rows per sheet")
    args = ap.parse_args(argv)
    ext = os.path.splitext(args.file)[1].lower()
    try:
        if ext in (".xlsx", ".xlsm"):
            text = xlsx_text(args.file, args.sheet, args.max_rows, args.sheets)
        elif ext in (".docx", ".docm"):
            text = docx_text(args.file)
        elif ext in (".pptx", ".pptm"):
            text = pptx_text(args.file)
        else:
            print("office_text: %s files are not handled here (only .xlsx, .docx, .pptx)" % (ext or "extensionless"),
                  file=sys.stderr)
            return 2
    except (OSError, zipfile.BadZipFile, KeyError, ET.ParseError) as e:
        print("office_text: could not read %s: %s" % (args.file, e), file=sys.stderr)
        return 1
    sys.stdout.write(text.rstrip("\n") + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
