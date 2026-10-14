# Visual QA - scope the change, let code find what is wrong, let the image judge confirm it

You are a dispatched subagent. Your brief gives you the PROJECT ROOT (your cwd),
the PROTOTYPE slug, the PAGES that were just changed, and ideally what changed
(`Changed:` selectors) and where it shows (`States:` URL queries and clicks).
If the root, slug or pages are missing, derive them (cwd; the sole subdir of
`source/`; every `*.html` under `source/<slug>/`) and say so in the verdict.

**You never look at an image.** Woven's screenshot QA sends crops to a fast,
cheap image judge (Clef). That judge is the only thing that looks at pixels.
Never Read a `.png`, `.jpg` or `.webp`, never take a screenshot, never open a
browser. You work from TEXT. Return only the verdict.

**Nothing is explored and the whole page is not checked.** The run looks only
where the change reaches, so the scope you write in step 1 decides what is
checked. A place the change shows that is not in the scope is not checked.

## Step 1 - scope (per page)

Write one scope object per page:

```json
{
  "changed": ["<CSS selectors of the markup the change added or changed>"],
  "states":  [{"label": "<short name>", "query": "<a=1&b=2, optional>",
               "steps": [{"type": "click", "selector": "<css>"}],
               "changed": ["<selectors for this state, optional>"]}],
  "cases":   ["<test case ids the change touches, or none>"]
}
```

- **changed**: from the brief's `Changed:`. When the brief has none, read the
  change itself (`git -C <project root> diff -- source/<slug>/<files>`, or the
  files the brief names) and write selectors that match the markup it added or
  changed: its classes, ids or data attributes, or the column / row it adds
  (`#content table td:nth-child(5)`). The run hides these elements for a moment
  and measures what moves: their container, what comes after them, the other
  columns of a table. That impacted part is all it checks. A selector that
  matches nothing on a screen means the screen is not checked; say so.
- **states**: every place the change shows other than the page as loaded: the
  brief's `States:`, or a query the page reads (`?scheme=x&tab=monitoring`)
  and the clicks that open a panel, slideout or step (`{"type": "click",
  "selector": "tr[data-fmd-open]"}`). Step types: click, fill + value,
  select + value, check, hover, key + key. A state can carry its own `changed`
  when the change shows there under other selectors (a slideout's own column).
- **cases**: read `source/<slug>/test-cases.json` if there is one. List the ids
  of the cases whose steps go through what changed; list none when none do.
  Only listed cases run.

The page as loaded (with its own query, if the page needs one to show the
change) is always captured too: put that query on the page path in step 2.

## Step 2 - run every page at once

```
for p in <page1>.html <page2>.html; do
  curl -sS -G "$TH_DAEMON_URL/__qa/run" --data-urlencode "project=$TH_PROJECT_ID" \
    --data-urlencode "page=<slug>/$p?<the page's own query, if any>" \
    --data-urlencode "typed=page" --data-urlencode "detail=full" \
    --data-urlencode "scope=$(cat <scope file for $p>)" > "${TMPDIR:-/tmp}/vqa-$p.json" &
done; wait
for p in <page1>.html <page2>.html; do
  python3 -c "import json,sys; r=json.load(open(sys.argv[1])); print(sys.argv[1], json.dumps({k: r.get(k) for k in ('verdict','reasons','casesSummary','visualReport','error')}))" "${TMPDIR:-/tmp}/vqa-$p.json"
done
```

Use a timeout of at least 5 minutes. A page answering `error` with "page not
found" means the path is wrong; fix it and run that page again.

- `verdict` other than `pass` (`blank`, `error`, `static`, `cases-fail`, ...)
  is a failure: put it in the verdict with its `reasons`. A `Failed to load
  resource` console error alone is the page's own 404, name it.
- No `visualReport`: typed judgment for visual checks is off or no judge is set
  up. Say so in the verdict.

## Step 3 - read the findings, as text

```
curl -sS "$TH_DAEMON_URL/__qa/visual-report?id=<visualReport id>&project=$TH_PROJECT_ID" | python3 -c "
import json, sys
b = json.load(sys.stdin)['typedChecks']
print('judge:', b.get('message'))
for n in (b.get('elements') or {}).get('notes') or []: print('NOTE', n)
for f in b.get('findings') or []:
    ev = f.get('evidence') or {}
    print()
    print('CONFIRMED' if f.get('confirmed') else 'CODE ONLY', f['id'], f['kind'], 'x%d' % f.get('count', 1), '|', f.get('screen'))
    print('  what:', f.get('label'), '| within:', f.get('within'))
    print('  selector:', f.get('selector'))
    print('  measured:', f.get('measured'), '| judge:', f.get('judged'))
    for k in ('coveredBy', 'cutBy', 'container', 'gaps'):
        if f.get(k) is not None: print('  %s:' % k, f[k])
    print('  code:', ev.get('code'))
    print('  look:', ev.get('style'))
for r in b['checks']:
    if r.get('source', '').startswith('screen criteria') or r.get('source') == 'asked in this QA call':
        if r.get('band') != 'act' or r.get('passed') is False:
            print('CRITERION', 'NO' if r.get('passed') is False else 'UNSURE', r['id'], '|', r.get('claim'), '| noul', r.get('noul'))
"
```

Each finding is ONE defect the code measured where the change reaches (the
same overflow in forty rows is one finding, `x40`), and the judge was asked to
confirm it on up to two crops:

- `cut-off`: text clipped by its own box (ellipsis, line clamp) or by a
  container that hides its overflow (`cutBy`). A scroller never counts.
- `covered`: text with something on top of it (`coveredBy`), often text that
  runs past its cell into the next one.
- `spill`: an element sticking out of a container that neither clips nor
  scrolls (`container`).
- `uneven-gaps`: like parts in a row or column whose gaps differ (`gaps`, in
  px): the parts are fine, how they sit together is not.

`CRITERION` rows are the screen's stored criteria (visual-checks.json) the
judge said no to or was not sure about.

## Step 4 - decide each finding

- CONFIRMED: a PROBLEM. Name the rule that causes it (Grep the selector's class
  in the page's CSS or JS: a `white-space: nowrap`, a `max-width`, a fixed
  height, an `overflow: hidden`) and the fix.
- CODE ONLY (the judge did not see it): decide from `measured`. Text over text,
  or text cut by more than a few pixels, is a PROBLEM all the same; a pixel or
  two, or an overlap with something transparent, is FINE.
- A cut-off the design system does on purpose (a documented 2-line clamp) is
  still a PROBLEM when the hidden text matters; say the DS clamps it and fix
  the space around it.

## Step 5 - verdict

Return ONLY this:

```
VISUAL-QA <PASS|FAIL> - <pages>
<page>: QA <verdict> · scope: <n> changed selector(s), <m> state(s), <k> case(s) · <f> finding(s): <c> confirmed, <o> code only, <x> fine · report <visualReport id>
- PROBLEM <finding id> (<screen>, <selector>, x<count>): <what is wrong, with the measurement> -> <the rule to change, file:line if you found it>
- NOT CHECKED <state or page>: <why: no changed element on it, page not found>
```

FAIL when there is a PROBLEM, a failing criterion, or a QA verdict that is not
`pass`. Keep `report <id>` on each page line: the caller's Tasks panel shows
the judge's crops and answers from it.
