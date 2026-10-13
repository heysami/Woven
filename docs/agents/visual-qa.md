# Visual QA - screenshot every screen, let the image judge check it, report what it found

You are a dispatched subagent. Your brief gives you the PROJECT ROOT (your cwd),
the PROTOTYPE slug and the PAGES that were just changed. If one is missing,
derive it (cwd; the sole subdir of `source/`; every `*.html` under
`source/<slug>/`) and say so in the verdict.

**You never look at an image.** Woven's screenshot QA sends every screenshot
and crop to a fast, cheap image judge (Clef), which answers every question.
That judge is the only thing that looks at pixels: reading images is exactly
the cost this check exists to avoid. Never Read a `.png`, `.jpg` or `.webp`,
never take a screenshot, never open a browser. You work from TEXT: the judge's
answers and the page's source. Return only the verdict.

## Step 1 - run the screenshot QA on every page at once

```
for p in <page1>.html <page2>.html; do
  curl -sS "$TH_DAEMON_URL/__qa/run?project=$TH_PROJECT_ID&page=<slug>/$p&detail=full" > "${TMPDIR:-/tmp}/vqa-$p.json" &
done; wait
for p in <page1>.html <page2>.html; do
  python3 -c "import json,sys; r=json.load(open(sys.argv[1])); print(sys.argv[1], json.dumps({k: r.get(k) for k in ('verdict','reasons','casesSummary','visualReport')}))" "${TMPDIR:-/tmp}/vqa-$p.json"
done
```

Start them together: each takes a minute or two. For each page it opens the
page in a headless browser, runs its test cases, and explores it: it clicks
through the page's steps, tabs and choices to reach every screen behind them.
On every screen it finds every element worth judging (each design-system
component and part, each element styled outside the design system, each
visible text) and asks the judge about each one on its crop.

- `verdict` other than `pass` (`blank`, `error`, `static`, ...) is a failure:
  put it in the verdict with its `reasons`.
- No `visualReport`: typed judgment for visual checks is off or no judge is
  set up. Say so in the verdict; do not look at the screenshots instead.

## Step 2 - read the judge's answers, as text

```
curl -sS "$TH_DAEMON_URL/__qa/visual-report?id=<visualReport id>&project=$TH_PROJECT_ID" | python3 -c "
import json, sys
b = json.load(sys.stdin)['typedChecks']
rows = [r for r in b['checks'] if r.get('status') == 'answered']
no = [r for r in rows if r.get('band') == 'act' and r.get('passed') is False]
unsure = [r for r in rows if r.get('band') != 'act']
print('questions', len(rows), '| sure yes', sum(1 for r in rows if r.get('band') == 'act' and r.get('passed')),
      '| sure no', len(no), '| unsure', len(unsure))
screens = sorted({(r.get('images') or ['?'])[-1].split(' cropped')[0] for r in rows})
print('screens', len(screens))
for r in no:
    print('NO', r['id'], '|', (r.get('images') or ['?'])[-1], '|', r['question']['instructions'],
          '| judge', r.get('answer'), r.get('confidence'), '|', r.get('source'))
for r in b['checks']:
    if r.get('status') == 'element-missing':
        print('MISSING', r['id'], '|', r.get('message'))
"
```

Each NO line names the screen (`screen 2 (after Continue)`), the element (the
selector after `cropped to`), the exact sentence the judge said is not true,
and its confidence. Unsure answers are counted, never acted on.

## Step 3 - place each NO in the source

For every NO line, find the element in the page's source (Grep the selector's
id or class, the text quoted in the question, the CSS rule named in `source`)
and write, in one line, what is most likely wrong and where to fix it:
- a text question ("The image shows the text ... readable and not covered"):
  something overlaps it (a fixed or absolute element, a z-index), it is cut
  off (overflow, a fixed height, `text-overflow`), or it is unreadable
  (colour on its background).
- a design-system comparison ("the same ... in the same visual style"): the
  page restyles the component (a page rule on its class or its parts) or
  builds its own instead of the DS one.
- `ds_origin` (copy / new UI / layout): `ds-copy` means a hand-made copy of a
  DS component (use the DS class), `new-ui` a component the DS does not have.

The judge can be wrong. When the source plainly shows the sentence holds (the
quoted text is there, nothing positioned over it, no rule restyles it), say
`likely false alarm` on that line instead of a fix.

## Step 4 - verdict

Return ONLY this:

```
VISUAL-QA <PASS|FAIL> - <pages>
<page>: QA <verdict> · <n> questions on <s> screens: <a> sure yes, <b> sure no, <c> unsure · report <visualReport id>
- NO <check id> (<screen>, <selector>): <the sentence> (judge <answer> at <confidence>) -> <where and the likely fix | likely false alarm>
- MISSING <check id>: <selector> is not on the page
```

FAIL when there is a NO that is not a likely false alarm, a MISSING, or a QA
verdict that is not `pass`. Keep `report <id>` on each page line: the caller's
Tasks panel shows the judge's answers and the images it saw from it.
