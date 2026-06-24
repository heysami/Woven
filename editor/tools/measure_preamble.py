#!/usr/bin/env python3
"""One-off instrumentation: measure the agent-run preamble section-by-section.

Splits the ASSEMBLED capabilities_preamble() output (the real string an agent
receives) into top-level `## ` sections and reports char + estimated-token
cost per section, for both the `full` tier (orchestrators + main chat) and the
`slim` tier (leaf drawers / lenses). This is the "measure before we trim" pass:
it tells us where the bytes actually are, so any cut is data-driven.

Token estimate: chars / 4.0 (Anthropic-ish rough heuristic; char count is the
ground truth, tokens are an approximation for intuition). Run:

    python3 editor/tools/measure_preamble.py [project_root]
"""
import os, re, sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_EDITOR = os.path.dirname(_HERE)
if _EDITOR not in sys.path:
    sys.path.insert(0, _EDITOR)

from kinds.capabilities import capabilities_preamble  # noqa: E402

EST_DIVISOR = 4.0  # chars -> approx tokens


def split_sections(text):
    """Split into (header, body_including_header) by top-level `## ` markers.
    Anything before the first `## ` is bucketed as '(preamble head)'.
    """
    # Keep the delimiter by splitting on the line boundary before `## `.
    parts = re.split(r'(?m)^(?=## )', text)
    out = []
    for p in parts:
        if not p.strip():
            continue
        m = re.match(r'## (.+)', p)
        header = m.group(1).strip() if m else '(preamble head, pre-first-##)'
        # Trim long headers for the table.
        header = header[:72]
        out.append((header, p))
    return out


def est_tokens(n_chars):
    return round(n_chars / EST_DIVISOR)


def report(label, text):
    total = len(text)
    secs = split_sections(text)
    secs_sized = sorted(((len(b), h) for h, b in secs), reverse=True)
    print(f"\n{'='*86}")
    print(f"  {label}")
    print(f"  total: {total:,} chars  ≈ {est_tokens(total):,} tokens   ({len(secs)} top-level sections)")
    print(f"{'='*86}")
    print(f"  {'chars':>7} {'≈tok':>6} {'%':>5}  section")
    print(f"  {'-'*7} {'-'*6} {'-'*5}  {'-'*60}")
    cum = 0
    for n, h in secs_sized:
        cum += n
        pct = 100.0 * n / total if total else 0
        print(f"  {n:>7,} {est_tokens(n):>6,} {pct:>4.1f}%  {h}")
    return total, secs


def main():
    project_root = sys.argv[1] if len(sys.argv) > 1 else None
    print(f"project_root = {project_root!r}")

    full = capabilities_preamble(project_root, tier="full")
    slim = capabilities_preamble(project_root, tier="slim")

    full_total, full_secs = report("FULL tier (orchestrators + main chat loop)", full)
    slim_total, slim_secs = report("SLIM tier (leaf drawers / lenses)", slim)

    full_headers = {h for h, _ in full_secs}
    slim_headers = {h for h, _ in slim_secs}
    print(f"\n{'='*86}")
    print("  FULL vs SLIM")
    print(f"{'='*86}")
    print(f"  full: {full_total:,} chars ≈ {est_tokens(full_total):,} tok")
    print(f"  slim: {slim_total:,} chars ≈ {est_tokens(slim_total):,} tok")
    drop = full_total - slim_total
    print(f"  slim saves: {drop:,} chars ≈ {est_tokens(drop):,} tok  ({100.0*drop/full_total:.0f}% of full)")
    only_full = full_headers - slim_headers
    if only_full:
        print("\n  sections present in FULL but stripped in SLIM:")
        for h in sorted(only_full):
            print(f"    - {h}")
    only_slim = slim_headers - full_headers
    if only_slim:
        print("\n  sections present in SLIM but not FULL (the leaf stub):")
        for h in sorted(only_slim):
            print(f"    + {h}")


if __name__ == "__main__":
    main()
