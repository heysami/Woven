# Workflow 5 — Apply `MERGES.md` (cherry-pick frame into Main)

**Trigger:** `MERGES.md` appears at repo root.

Append-only log of frame-promotion directives from the editor's "↑ Main" button. The exploration branch stays untouched.

For each `## Promote frame …` section:

1. **Resolve the frame** — read `editor/branches/<from>.js`, note `setupScript` and `parent`.
2. **Identify components** — read `source/<from>/index.html`. List component functions, CSS classes, `window.DEMO` paths used.
3. **Diff vs Main:**
   - New → copy verbatim.
   - Modified → copy branch version; prefer Main's existing token values unless the diff is intentional. When in doubt, log alternatives under `## merge · <slug> · <frameId>` in `NOTES.md`.
   - Unchanged → leave Main alone.
4. **Token discipline:** don't import branch-specific token names if Main has one serving the same role. New tokens → add to `source/main/styles.css :root` with branch's value; cite the branch in a comment.
5. **DEMO data:** only entries the new components need. Don't blanket-overwrite.
6. **Refresh `editor/branches/main.js`** via Workflow 1 if frames/entities/primitives/tokens shifted. **Don't touch `editor/branches/<from>.js`.**
7. **Refresh `DESIGN.md`** via Workflow 3 if `styles.css` or primitives shifted.
8. **Resolve, don't delete.** Replace the section body with `_Applied <ISO>. See commit / NOTES.md._` Don't delete `MERGES.md` itself.

"Promote whole branch → Main" goes through `serve.py` directly — no `MERGES.md`. Run Workflows 1 + 3 against the new Main.
