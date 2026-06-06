"""Regression test for the v3.4 planner/builder split.

Background — before v3.4, each `*-planner` agent was scoped as "top-level
orchestrator": research → scaffold → DRIVE THE WHOLE BUILD (dispatch
drawers, run lens trios, commit container). The build phase ran inside
the planner subagent's context, which meant Bash/curl/Write calls hit the
per-tool approval wall the moment they crossed Claude Code's subagent
permission boundary. In hubu the research phase ran fine and then every
drawer dispatch + every file write started getting auto-denied — the
"unknown runId after daemon restart" + "build phase blocked by session
permissions" incidents were both symptoms of this scope mistake.

v3.4 splits the planners: research + scaffold ONLY in the planner; build
phase (drawer dispatch + lens trios + multi-draft cruxes + container
commit) in the CALLER (`bp_*_build` node OR the workflow-mode chat that
dispatched the planner). The caller already has the user's permissions;
the cold subagent does not.

This test pins the contract in five places:

  1. Each planner's frontmatter `description:` advertises scaffold-only.
  2. Each planner's body has a "Phase D — Commit the scaffold + hand off"
     section + a hand-off envelope spec + an explicit "you do NOT dispatch
     drawers / run lens trios / commit container" list.
  3. Each `bp_*_build` preamble in node_agent_preambles.py owns the build
     phase (Phase 2 harness + lens-trio loop + container commit).
  4. The workflow-mode chat preamble in app.js teaches the chat that
     planners are scaffold-only and the chat itself drives the build.
  5. Specific anti-patterns from the legacy design DO NOT appear in the
     planner files (they would re-enable the permission-wall bug).

If any of these drifts, a future planner could quietly re-acquire
build-phase scope and the permission-wall regression returns. Run via
`python3 editor/tests/test_planner_builder_split.py`. Exit 0 on pass.
"""

import os
import re
import sys
import traceback

_HERE = os.path.dirname(os.path.abspath(__file__))
_EDITOR = os.path.dirname(_HERE)
_ROOT = os.path.dirname(_EDITOR)
_AGENTS_DIR = os.path.join(_ROOT, ".claude", "agents")

PLANNERS = ["simulation-planner", "interactive-media-planner", "narrative-experience-planner"]
BUILDERS = ["bp_simulation_build", "bp_interactive_build", "bp_narrative_build"]

FAILURES = []


def _check(cond, label):
    if cond:
        print(f"  ✓ {label}")
    else:
        FAILURES.append(label)
        print(f"  ✗ {label}")


def _read(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _planner_frontmatter(planner_name):
    """Return the YAML frontmatter block (between the two `---` lines) as a string."""
    body = _read(os.path.join(_AGENTS_DIR, planner_name + ".md"))
    m = re.match(r"---\n(.*?)\n---\n", body, re.DOTALL)
    return m.group(1) if m else ""


def test_planner_frontmatter_advertises_scaffold_only():
    print("test: each planner's frontmatter description advertises scaffold-only")
    for planner in PLANNERS:
        fm = _planner_frontmatter(planner)
        desc_match = re.search(r"^description:\s*(.+?)(?=^\w+:|\Z)", fm, re.MULTILINE | re.DOTALL)
        desc = (desc_match.group(1) if desc_match else "").lower()

        _check("research + scaffold" in desc,
               f"[{planner}] description claims 'research + scaffold' scope")
        _check("returns a hand-off envelope" in desc or "return a hand-off envelope" in desc
               or "returns a hand-off" in desc,
               f"[{planner}] description mentions returning a hand-off envelope")
        _check("does not" in desc and ("dispatch drawers" in desc or "dispatch the drawers" in desc),
               f"[{planner}] description explicitly says 'does NOT dispatch drawers'")
        _check(not re.search(r"\btop-level orchestrator\b", desc),
               f"[{planner}] description no longer claims 'top-level orchestrator' "
               f"(legacy scope marker that caused the permission-wall bug)")


def test_planner_body_has_handoff_section():
    print("test: each planner body has a Phase D hand-off section + envelope")
    for planner in PLANNERS:
        body = _read(os.path.join(_AGENTS_DIR, planner + ".md"))

        _check(re.search(r"^## 5\. Phase D.*hand.?off", body, re.MULTILINE | re.IGNORECASE) is not None,
               f"[{planner}] has '## 5. Phase D — ... hand off' section header")
        _check("Hand-off envelope" in body or "hand-off envelope" in body,
               f"[{planner}] body references the 'hand-off envelope'")
        _check('"planner":' in body and '"scaffold":' in body and '"drawerNodes":' in body,
               f"[{planner}] body contains a JSON envelope spec with planner/scaffold/drawerNodes")
        _check('"containerNode":' in body,
               f"[{planner}] envelope spec includes containerNode (so caller knows what to commit)")
        _check("nextStep" in body,
               f"[{planner}] envelope spec includes nextStep instructions for the caller")


def test_planner_body_lists_anti_responsibilities():
    print("test: each planner's 'What you do NOT do' explicitly forbids build-phase ops")
    forbidden_phrases_per_planner = {
        "simulation-planner": [
            "do not dispatch drawers",
            "do not run lens trios",
            "do not commit the `sim_<simId>` container",
        ],
        "interactive-media-planner": [
            "do not dispatch drawers",
            "do not run lens trios",
            "do not commit the `im_<imId>` container",
            "do not run the §8.5 cross-drawer coherence review",
        ],
        "narrative-experience-planner": [
            "do not dispatch drawers",
            "do not run lens trios",
            "do not commit the `nx_<nxId>` container",
            "do not run the §8.5 cross-drawer coherence review",
        ],
    }
    for planner, phrases in forbidden_phrases_per_planner.items():
        body = _read(os.path.join(_AGENTS_DIR, planner + ".md")).lower()
        for phrase in phrases:
            _check(phrase.lower() in body,
                   f"[{planner}] explicitly forbids: \"{phrase}\"")


def test_planner_body_does_not_contain_legacy_harness():
    print("test: planners do NOT contain the legacy build-harness pseudocode")
    # The exact strings that, if they reappear, mean a future edit re-added
    # the build harness inside the planner subagent's context. Keep these
    # specific (don't just grep 'curl') so the architectural-note blockquote
    # that DESCRIBES what was moved doesn't trigger false positives.
    forbidden_patterns = [
        r"for outer_iter in 1 2 3 4 5",            # the §8.3 loop signature
        r"poll_until_done <drawer-id>",            # the drawer-dispatch waiter
        r"# Scaffold \+ dispatch the 3 lenses",    # the lens trio fanout comment
        r"craft_lens_<id>_\$outer_iter",           # the per-iteration lens scaffold
    ]
    for planner in PLANNERS:
        body = _read(os.path.join(_AGENTS_DIR, planner + ".md"))
        for pattern in forbidden_patterns:
            hits = re.findall(pattern, body)
            _check(len(hits) == 0,
                   f"[{planner}] does not contain legacy harness pattern: r\"{pattern}\" "
                   f"(found {len(hits)} occurrences)")


def test_builder_preamble_owns_phase_2():
    print("test: each bp_*_build preamble owns Phase 2 (the build phase)")
    preamble_path = os.path.join(_EDITOR, "prompts", "node_agent_preambles.py")
    src = _read(preamble_path)

    for builder in BUILDERS:
        # Find this builder's preamble block — the literal NODE_AGENT_PREAMBLES["..."] = ( ... )
        m = re.search(
            r'NODE_AGENT_PREAMBLES\["' + re.escape(builder) + r'"\]\s*=\s*\(\s*"[^"]*",\s*"""(.*?)"""',
            src, re.DOTALL,
        )
        _check(m is not None, f"[{builder}] preamble block exists in node_agent_preambles.py")
        if m is None:
            continue
        block = m.group(1)

        _check("v3.4 planner/builder split" in block,
               f"[{builder}] preamble explicitly cites the v3.4 split")
        _check("Phase 1" in block and "Phase 2" in block,
               f"[{builder}] preamble has Phase 1 (delegated) + Phase 2 (YOU drive) structure")
        _check(re.search(r"Phase 2.*build|build.*YOU drive|YOU driving", block, re.IGNORECASE) is not None,
               f"[{builder}] preamble names YOU as the build-phase driver")
        _check("hand-off envelope" in block.lower(),
               f"[{builder}] preamble reads the planner's hand-off envelope")
        _check("DO NOT dispatch drawers" in block or "DO NOT dispatch the drawers" in block
               or "DO NOT" in block and "drawers" in block,
               f"[{builder}] preamble instructs the planner NOT to dispatch drawers")
        _check("loop-until-bar" in block.lower() or "lens trio" in block.lower(),
               f"[{builder}] preamble owns the lens-trio / loop-until-bar harness")


def test_workflow_mode_chat_preamble_teaches_split():
    print("test: workflow-mode chat preamble in app.js teaches the planner/builder split")
    app_js = _read(os.path.join(_EDITOR, "app.js"))

    # Find the workflow-mode branch inside composeModeAwarePrompt
    m = re.search(
        r"if \(mode === \"workflow\"\) \{(.*?)if \(mode === \"editor\"\)",
        app_js, re.DOTALL,
    )
    _check(m is not None, "found the workflow-mode branch of composeModeAwarePrompt")
    if m is None:
        return
    block = m.group(1)

    _check("Planner family" in block or "planner" in block.lower(),
           "workflow-mode preamble names the planner family")
    _check("RESEARCH + SCAFFOLD ONLY" in block.upper() or "research + scaffold only" in block.lower(),
           "workflow-mode preamble says planners do RESEARCH + SCAFFOLD ONLY")
    _check("YOU drive the build" in block or "you drive the build" in block.lower(),
           "workflow-mode preamble says YOU (the chat) drive the build phase")
    _check("subagent permission gates compound" in block.lower()
           or "permission gates compound" in block.lower(),
           "workflow-mode preamble explains the reason (permission-gate compounding)")
    _check("simulation-planner" in block and "interactive-media-planner" in block
           and "narrative-experience-planner" in block,
           "workflow-mode preamble lists all three planner subagent types")


def test_workflow_mode_chat_preamble_warns_against_task_override():
    print("test: workflow-mode chat preamble warns against telling planners to use Task or avoid daemon")
    # This is the contract that mosimosi violated: the chat wrote 'dispatch
    # researchers via the Task tool' inside the planner's prompt body, and the
    # planner (a subagent) hit `Task is not available inside subagents`. Same
    # prompt also said 'don't depend on daemon curl, fall back to direct Write',
    # which would break the cold-isolation contract even if Task had worked.
    app_js = _read(os.path.join(_EDITOR, "app.js"))
    m = re.search(
        r"if \(mode === \"workflow\"\) \{(.*?)if \(mode === \"editor\"\)",
        app_js, re.DOTALL,
    )
    _check(m is not None, "found the workflow-mode branch of composeModeAwarePrompt")
    if m is None:
        return
    block = m.group(1).lower()

    _check("task tool" in block and "not available inside subagents" in block,
           "workflow-mode preamble says Task is NOT available inside subagents")
    _check("brief the what" in block or "brief the planner" in block,
           "workflow-mode preamble tells the chat to brief the WHAT, not the HOW")
    _check("do not tell the planner which tool" in block or "don't tell the planner which tool" in block
           or "do not tell it to avoid the daemon" in block,
           "workflow-mode preamble explicitly forbids telling the planner which tool to use / to avoid the daemon")
    _check("daemon is reachable from inside subagents" in block
           or "daemon is reachable" in block,
           "workflow-mode preamble explicitly says the daemon IS reachable from inside subagents")
    _check("no such tool available: task" in block or "task is not available inside subagents" in block,
           "workflow-mode preamble names the exact error string the chat will see if it gets this wrong")


def test_planner_dispatch_mechanism_warning_is_strong():
    print("test: each planner's DISPATCH MECHANISM warning instructs ignoring caller's 'use Task' brief")
    for planner in PLANNERS:
        body = _read(os.path.join(_AGENTS_DIR, planner + ".md")).lower()
        _check("dispatch mechanism" in body,
               f"[{planner}] has a DISPATCH MECHANISM section")
        _check("task is not available inside subagents" in body
               or "task` tool is not available" in body
               or "task tool is not available" in body,
               f"[{planner}] explicitly states Task is not available inside subagents")
        _check("ignore" in body and ("use task" in body or "via task" in body or "use the task tool" in body),
               f"[{planner}] instructs ignoring caller's 'use Task' instructions")
        _check("ignore" in body and ("avoid the daemon" in body or "don't depend on daemon" in body
                                       or "fall back to direct write" in body),
               f"[{planner}] instructs ignoring caller's 'avoid daemon / use Write' instructions")


def main():
    tests = [
        test_planner_frontmatter_advertises_scaffold_only,
        test_planner_body_has_handoff_section,
        test_planner_body_lists_anti_responsibilities,
        test_planner_body_does_not_contain_legacy_harness,
        test_builder_preamble_owns_phase_2,
        test_workflow_mode_chat_preamble_teaches_split,
        test_workflow_mode_chat_preamble_warns_against_task_override,
        test_planner_dispatch_mechanism_warning_is_strong,
    ]
    for t in tests:
        try:
            t()
        except Exception:
            FAILURES.append(f"{t.__name__} raised")
            traceback.print_exc()
        print()

    if FAILURES:
        print(f"FAIL — {len(FAILURES)} assertion(s) failed:")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    print("PASS — planner/builder split contract upheld")


if __name__ == "__main__":
    main()
