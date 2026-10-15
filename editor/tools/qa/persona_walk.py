#!/usr/bin/env python3
"""Persona critique browser walk - the eyes of a simulated research session.

Two subcommands, both driven by editor/personas.py:

  survey --plan pages.json --out DIR [--device desktop]
      Open every page, screenshot it (survey-P<n>.jpg) and list what a user
      can SEE on it: headings, buttons, links, fields, choices, by their
      on-screen labels. Writes DIR/survey.json. The fast planner reads this
      to write steps that target real labels.

  walk --plan plan.json --out DIR --device desktop|mobile
      Carry out the planner's task table the way a user would - by visible
      label, never by selector - and screenshot the screen after every step
      (<device>-<n>.jpg). A step that cannot be done is recorded (that is a
      finding in itself) and the walk goes on. Writes DIR/walk-<device>.json.

Python 3.9-safe. No em/en dashes. Fails soft with a clear message when
Playwright or a browser is missing.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

VIEWPORTS = {
    "desktop": {"viewport": {"width": 1280, "height": 800}, "device_scale_factor": 1},
    "mobile": {"viewport": {"width": 390, "height": 844}, "device_scale_factor": 2,
               "is_mobile": True, "has_touch": True},
}

_INVENTORY_JS = r"""() => {
  const vis = (el) => {
    const r = el.getBoundingClientRect();
    if (r.width < 2 || r.height < 2) return false;
    const s = getComputedStyle(el);
    return s.visibility !== 'hidden' && s.display !== 'none' && parseFloat(s.opacity || '1') > 0.05;
  };
  const clean = (t) => (t || '').replace(/\s+/g, ' ').trim().slice(0, 80);
  const name = (el) => clean(el.getAttribute('aria-label') || el.innerText || el.value
    || el.getAttribute('title') || el.getAttribute('alt'));
  const labelFor = (el) => clean((el.labels && el.labels[0] && el.labels[0].innerText)
    || el.getAttribute('aria-label') || el.getAttribute('placeholder') || el.getAttribute('title'));
  // Controls that exist but are not on screen yet (a form revealed by a
  // button, a later step) are listed too, marked `later`, so the planner can
  // write the steps after the reveal with real labels instead of guesses.
  // Text an off-screen element would SHOW (innerText) is empty while hidden,
  // so those fall back to textContent.
  const out = [], seen = new Set();
  const push = (role, nm, extra) => {
    nm = clean(nm);
    if (!nm) return;
    const k = role + '|' + nm;
    if (seen.has(k)) return;
    seen.add(k);
    out.push(Object.assign({ role, name: nm }, extra || {}));
  };
  const each = (sel, role, nameOf, extraOf) => document.querySelectorAll(sel).forEach(el => {
    const on = vis(el);
    const nm = nameOf(el) || (!on ? clean(el.textContent) : '');
    push(role, nm, Object.assign(on ? {} : { later: true }, extraOf ? extraOf(el) : {}));
  });
  document.querySelectorAll('h1,h2,h3,[role=heading]').forEach(el => vis(el) && push('heading', el.innerText));
  each('button,[role=button],input[type=submit],input[type=button]', 'button', name);
  each('[role=tab]', 'tab', name);
  document.querySelectorAll('a[href]').forEach(el => vis(el) && push('link', name(el)));
  document.querySelectorAll('[role=menuitem],[role=option]').forEach(el => vis(el) && push('choice', name(el)));
  document.querySelectorAll('input:not([type=hidden]):not([type=submit]):not([type=button]),textarea').forEach(el => {
    const t = (el.getAttribute('type') || '').toLowerCase();
    push(t === 'checkbox' ? 'checkbox' : t === 'radio' ? 'radio' : 'field', labelFor(el) || clean(el.getAttribute('name')),
      vis(el) ? {} : { later: true });
  });
  each('select', 'select', labelFor, el => ({ options: Array.from(el.options).slice(0, 10).map(o => clean(o.text)).filter(Boolean) }));
  return out.slice(0, 90);
}"""

_MOTION_JS = r"""() => {
  let running = 0;
  try { running = document.getAnimations().filter(a => a.playState === 'running' && a.effect && a.effect.getComputedTiming().iterations !== Infinity).length; } catch (e) {}
  return running + ',' + Math.round(window.scrollY);
}"""


def log(msg: str) -> None:
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


def launch(pw: Any) -> Any:
    try:
        return pw.chromium.launch(channel="chrome", headless=True)
    except Exception as exc:
        log("channel=chrome launch failed (%s); trying bundled chromium" % exc)
    return pw.chromium.launch(headless=True)


def settle(page: Any, timeout_ms: int = 2500) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=timeout_ms)
    except Exception:
        pass
    last, t0 = None, time.time()
    while (time.time() - t0) * 1000 < 1500:
        try:
            now = str(page.evaluate(_MOTION_JS))
        except Exception:
            return
        if now == last and now.startswith("0,"):
            return
        last = now
        page.wait_for_timeout(150)


def shoot(page: Any, path: str) -> bool:
    try:
        page.screenshot(path=path, type="jpeg", quality=70, full_page=False)
        return True
    except Exception as exc:
        log("screenshot failed: %s" % exc)
        return False


def _first_visible(cands: List[Any]) -> Optional[Any]:
    for loc in cands:
        try:
            n = loc.count()
        except Exception:
            continue
        for i in range(min(n, 6)):
            el = loc.nth(i)
            try:
                if el.is_visible():
                    return el
            except Exception:
                continue
    return None


def find(page: Any, do: str, target: str) -> Optional[Any]:
    if not target:
        return None
    if do == "click":
        cands = [page.get_by_role(r, name=target, exact=True)
                 for r in ("button", "link", "tab", "menuitem", "checkbox", "radio", "switch", "option")]
        cands += [page.get_by_label(target, exact=True), page.get_by_text(target, exact=True)]
        cands += [page.get_by_role(r, name=target) for r in ("button", "link", "tab", "menuitem")]
        cands += [page.get_by_text(target)]
    elif do == "fill":
        cands = [page.get_by_label(target, exact=True), page.get_by_placeholder(target, exact=True),
                 page.get_by_role("textbox", name=target, exact=True), page.get_by_role("spinbutton", name=target),
                 page.get_by_label(target), page.get_by_placeholder(target), page.get_by_role("textbox", name=target)]
    elif do == "select":
        cands = [page.get_by_label(target, exact=True), page.get_by_role("combobox", name=target),
                 page.get_by_label(target)]
    else:
        cands = [page.get_by_text(target, exact=True), page.get_by_text(target),
                 page.get_by_role("heading", name=target)]
    return _first_visible(cands)


def do_step(context: Any, page: Any, task: Dict[str, Any], urls: Dict[str, str]) -> Any:
    """Carry out one task. Returns the page now in front (a link may open a
    new tab). Raises with a user-facing reason when it cannot be done."""
    do = task.get("do")
    target = (task.get("target") or "").strip()
    value = task.get("value") or ""
    if do == "open":
        url = urls.get(task.get("page") or "") or next(iter(urls.values()), None)
        if not url:
            raise RuntimeError("no screen to open")
        page.goto(url, wait_until="load", timeout=20000)
        return page
    if do == "look":
        return page
    if do == "scroll":
        el = find(page, "scroll", target) if target else None
        if el is not None:
            el.scroll_into_view_if_needed(timeout=3000)
        else:
            page.mouse.wheel(0, 600)
        return page
    if do == "press":
        # A key pressed ON something (Enter on "Submit") goes to that element.
        el = find(page, "click", target) if target else None
        if el is not None:
            el.press(value or "Enter", timeout=4000)
            page.wait_for_timeout(350)
        else:
            page.keyboard.press(value or "Enter")
        return page
    el = find(page, do, target)
    if el is None:
        raise RuntimeError('could not find "%s" on the screen' % target)
    before = len(context.pages)
    if do == "click":
        el.click(timeout=4000)
    elif do == "fill":
        el.fill(str(value), timeout=4000)
    elif do == "select":
        # The planner's choice by its words: exact, then either containing the
        # other. Not among the choices is a finding, named with the choices.
        want = str(value).strip().lower()
        try:
            opts = [o.strip() for o in el.evaluate("s => Array.from(s.options || []).map(o => o.text)")]
        except Exception:
            opts = []
        pick = next((o for o in opts if o.lower() == want), None) \
            or next((o for o in opts if want and (want in o.lower() or o.lower() in want) and o), None)
        if opts and pick is None:
            raise RuntimeError('"%s" is not a choice in "%s" (choices: %s)' % (value, target, ", ".join(opts[:8])))
        el.select_option(label=pick or str(value), timeout=4000)
    else:
        raise RuntimeError("unknown action %r" % do)
    page.wait_for_timeout(350)
    if len(context.pages) > before:
        page = context.pages[-1]
        try:
            page.wait_for_load_state("load", timeout=10000)
        except Exception:
            pass
    return page


def survey(pw: Any, pages: List[Dict[str, str]], out: str, device: str) -> Dict[str, Any]:
    browser = launch(pw)
    try:
        ctx = browser.new_context(**VIEWPORTS[device])
        result = []
        for p in pages:
            page = ctx.new_page()
            entry: Dict[str, Any] = {"key": p["key"]}
            try:
                page.goto(p["url"], wait_until="load", timeout=20000)
                settle(page)
                entry["title"] = (page.title() or "")[:120]
                entry["inventory"] = page.evaluate(_INVENTORY_JS)
                name = "survey-%s.jpg" % p["key"]
                if shoot(page, os.path.join(out, name)):
                    entry["shot"] = name
            except Exception as exc:
                entry["error"] = str(exc)[:300]
            finally:
                page.close()
            result.append(entry)
        return {"pages": result}
    finally:
        browser.close()


def walk(pw: Any, pages: List[Dict[str, str]], tasks: List[Dict[str, Any]], out: str, device: str) -> Dict[str, Any]:
    urls = {p["key"]: p["url"] for p in pages}
    browser = launch(pw)
    steps = []
    try:
        ctx = browser.new_context(**VIEWPORTS[device])
        page = ctx.new_page()
        for i, task in enumerate(tasks):
            n = i + 1
            step: Dict[str, Any] = {"n": n, "ok": True}
            try:
                page = do_step(ctx, page, task, urls)
            except Exception as exc:
                step["ok"] = False
                msg = str(exc).splitlines()[0] if str(exc) else exc.__class__.__name__
                if "Timeout" in msg and "could not" not in msg:
                    msg = 'nothing responded to "%s"' % (task.get("target") or task.get("do"))
                step["error"] = msg[:240]
            settle(page)
            try:
                step["title"] = (page.title() or "")[:120]
            except Exception:
                pass
            name = "%s-%d.jpg" % (device, n)
            if shoot(page, os.path.join(out, name)):
                step["shot"] = name
            steps.append(step)
    finally:
        browser.close()
    return {"device": device, "steps": steps}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("cmd", choices=("survey", "walk"))
    ap.add_argument("--plan", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="desktop", choices=tuple(VIEWPORTS))
    args = ap.parse_args()
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except Exception:
        log("Playwright is not installed for %s (pip install playwright && playwright install chromium)" % sys.executable)
        return 2
    with open(args.plan, "r", encoding="utf-8") as f:
        plan = json.load(f)
    pages = [p for p in (plan.get("pages") or []) if isinstance(p, dict) and p.get("url")]
    os.makedirs(args.out, exist_ok=True)
    with sync_playwright() as pw:
        if args.cmd == "survey":
            res = survey(pw, pages, args.out, args.device)
            dest = os.path.join(args.out, "survey.json")
        else:
            res = walk(pw, pages, plan.get("tasks") or [], args.out, args.device)
            dest = os.path.join(args.out, "walk-%s.json" % args.device)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
