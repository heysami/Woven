#!/usr/bin/env python3
"""xlsx_io.py - minimal, dependency-free .xlsx read/write for the Woven daemon.

An .xlsx is a zip of XML parts. Woven ships as a downloaded zip with no pip
step, so openpyxl is not available on a fresh install; this module covers the
narrow slice we actually need for the user-stories sheet:

  read_xlsx(path)  -> list of sheets: {"name": str, "rows": [[cell, ...], ...]}
  write_xlsx(path, sheet_name, rows)  -> one sheet, all cells written as
                                         inline strings (no sharedStrings part)

Cells come back as TEXT. Numbers are rendered with their stored digits, dates
are left as the underlying serial (the stories sheet has no date columns), and
formulas resolve to their cached value when the file carries one.

Python 3.9-safe, stdlib only. No em dashes anywhere.
"""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

_NS_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_NS_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_NS_PKGREL = "{http://schemas.openxmlformats.org/package/2006/relationships}"


# ---------------------------------------------------------------------------
# cell references
# ---------------------------------------------------------------------------

def col_to_index(ref):
    # type: (str) -> int
    """'A' -> 0, 'B' -> 1, 'AA' -> 26. Accepts a full ref ('C7') too."""
    letters = re.match(r"([A-Za-z]+)", ref or "")
    if not letters:
        return 0
    n = 0
    for ch in letters.group(1).upper():
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def index_to_col(idx):
    # type: (int) -> str
    """0 -> 'A', 26 -> 'AA'."""
    idx = max(0, int(idx))
    out = ""
    n = idx + 1
    while n > 0:
        n, rem = divmod(n - 1, 26)
        out = chr(65 + rem) + out
    return out


# ---------------------------------------------------------------------------
# read
# ---------------------------------------------------------------------------

def _text_of(node):
    # type: (Any) -> str
    """Concatenate every <t> under a rich-text node, skipping ruby/phonetic."""
    if node is None:
        return ""
    parts = []
    for t in node.iter(_NS_MAIN + "t"):
        parts.append(t.text or "")
    return "".join(parts)


def _shared_strings(zf):
    # type: (zipfile.ZipFile) -> List[str]
    try:
        raw = zf.read("xl/sharedStrings.xml")
    except KeyError:
        return []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []
    return [_text_of(si) for si in root.findall(_NS_MAIN + "si")]


def _sheet_parts(zf):
    # type: (zipfile.ZipFile) -> List[Tuple[str, str]]
    """[(sheet name, zip path)] in workbook order."""
    try:
        wb = ET.fromstring(zf.read("xl/workbook.xml"))
    except (KeyError, ET.ParseError):
        return []
    rel_target = {}  # type: Dict[str, str]
    try:
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        for r in rels.findall(_NS_PKGREL + "Relationship"):
            target = r.get("Target") or ""
            if target.startswith("/"):
                target = target[1:]
            elif not target.startswith("xl/"):
                target = "xl/" + target.lstrip("./")
            rel_target[r.get("Id") or ""] = target
    except (KeyError, ET.ParseError):
        pass

    out = []
    sheets = wb.find(_NS_MAIN + "sheets")
    for i, sh in enumerate(sheets.findall(_NS_MAIN + "sheet") if sheets is not None else []):
        rid = sh.get(_NS_REL + "id") or ""
        path = rel_target.get(rid) or ("xl/worksheets/sheet%d.xml" % (i + 1))
        if path not in zf.namelist():
            continue
        out.append((sh.get("name") or ("Sheet%d" % (i + 1)), path))
    return out


def _cell_value(cell, shared):
    # type: (Any, List[str]) -> str
    ctype = cell.get("t") or "n"
    if ctype == "inlineStr":
        return _text_of(cell.find(_NS_MAIN + "is"))
    v = cell.find(_NS_MAIN + "v")
    raw = (v.text or "") if v is not None else ""
    if ctype == "s":
        try:
            return shared[int(raw)]
        except (ValueError, IndexError):
            return ""
    if ctype == "b":
        return "TRUE" if raw not in ("0", "", None) else "FALSE"
    if ctype in ("str", "e"):
        return raw
    # numeric: drop the trailing .0 that Excel writes for whole numbers
    if raw.endswith(".0"):
        return raw[:-2]
    return raw


def read_xlsx(path):
    # type: (str) -> List[Dict[str, Any]]
    """Read every sheet. Rows are ragged-padded to the widest cell seen."""
    sheets = []
    with zipfile.ZipFile(path, "r") as zf:
        shared = _shared_strings(zf)
        for name, part in _sheet_parts(zf):
            try:
                root = ET.fromstring(zf.read(part))
            except (KeyError, ET.ParseError):
                continue
            rows = []  # type: List[List[str]]
            data = root.find(_NS_MAIN + "sheetData")
            for row in (data.findall(_NS_MAIN + "row") if data is not None else []):
                # Honour r= so a sheet with skipped rows keeps its alignment.
                try:
                    r_idx = int(row.get("r") or (len(rows) + 1)) - 1
                except ValueError:
                    r_idx = len(rows)
                while len(rows) <= r_idx:
                    rows.append([])
                cells = rows[r_idx]
                for i, cell in enumerate(row.findall(_NS_MAIN + "c")):
                    c_idx = col_to_index(cell.get("r") or index_to_col(i))
                    while len(cells) <= c_idx:
                        cells.append("")
                    cells[c_idx] = _cell_value(cell, shared)
            width = max([len(r) for r in rows] or [0])
            for r in rows:
                while len(r) < width:
                    r.append("")
            sheets.append({"name": name, "rows": rows})
    return sheets


# ---------------------------------------------------------------------------
# write
# ---------------------------------------------------------------------------

def _xml_escape(s):
    # type: (str) -> str
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


# Characters XML 1.0 forbids outright. Excel refuses to open a file carrying
# them, so scrub rather than escape.
_ILLEGAL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
    '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
    '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
    "</Types>"
)

_ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
    "</Relationships>"
)

_WB_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>'
    "</Relationships>"
)

# Two cell formats: 0 = plain wrapped text, 1 = bold header.
_STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<fonts count="2">'
    '<font><sz val="11"/><name val="Calibri"/></font>'
    '<font><b/><sz val="11"/><name val="Calibri"/></font>'
    "</fonts>"
    '<fills count="2"><fill><patternFill patternType="none"/></fill>'
    '<fill><patternFill patternType="gray125"/></fill></fills>'
    '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
    '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    '<cellXfs count="2">'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1">'
    '<alignment vertical="top" wrapText="1"/></xf>'
    '<xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyFont="1" applyAlignment="1">'
    '<alignment vertical="top" wrapText="1"/></xf>'
    "</cellXfs>"
    '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>'
    "</styleSheet>"
)


def _sheet_xml(rows, widths=None, header=True, freeze_header=True):
    # type: (List[List[Any]], Optional[List[int]], bool, bool) -> str
    ncols = max([len(r) for r in rows] or [1])
    out = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">',
    ]
    if widths:
        out.append("<cols>")
        for i in range(ncols):
            w = widths[i] if i < len(widths) else 18
            out.append('<col min="%d" max="%d" width="%d" customWidth="1"/>' % (i + 1, i + 1, w))
        out.append("</cols>")
    if freeze_header and header and len(rows) > 1:
        out.append('<sheetViews><sheetView workbookViewId="0">'
                   '<pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
                   "</sheetView></sheetViews>")
    out.append("<sheetData>")
    for r_idx, row in enumerate(rows):
        style = ' s="1"' if (header and r_idx == 0) else ' s="0"'
        out.append('<row r="%d">' % (r_idx + 1))
        for c_idx in range(ncols):
            val = row[c_idx] if c_idx < len(row) else ""
            if val is None:
                val = ""
            text = _ILLEGAL.sub("", str(val))
            ref = "%s%d" % (index_to_col(c_idx), r_idx + 1)
            if text == "":
                out.append('<c r="%s"%s/>' % (ref, style))
            else:
                out.append('<c r="%s"%s t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>'
                           % (ref, style, _xml_escape(text)))
        out.append("</row>")
    out.append("</sheetData></worksheet>")
    return "".join(out)


def write_xlsx(path, sheet_name, rows, widths=None):
    # type: (str, str, List[List[Any]], Optional[List[int]]) -> None
    """Write ONE sheet. Row 0 is styled as a bold, frozen header."""
    safe_name = re.sub(r"[\[\]:*?/\\]", "-", str(sheet_name or "Sheet1"))[:31] or "Sheet1"
    wb = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
        ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheets><sheet name="%s" sheetId="1" r:id="rId1"/></sheets>'
        "</workbook>" % _xml_escape(safe_name)
    )
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES)
        zf.writestr("_rels/.rels", _ROOT_RELS)
        zf.writestr("xl/workbook.xml", wb)
        zf.writestr("xl/_rels/workbook.xml.rels", _WB_RELS)
        zf.writestr("xl/styles.xml", _STYLES)
        zf.writestr("xl/worksheets/sheet1.xml", _sheet_xml(rows, widths=widths))
