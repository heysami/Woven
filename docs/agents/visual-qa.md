# Visual QA - screenshot every screen, let the image judge check it, report what it found

You are a dispatched subagent. Your brief gives you the PROJECT ROOT (your cwd),
the PROTOTYPE slug and the PAGES that were just changed. If one is missing,
derive it (cwd; the sole subdir of `source/`; every `*.html` under
`source/<slug>/`) and say so in the verdict.

**You never look at an image.** Woven's screenshot QA sends every screenshot
and crop to a fast, cheap image judge (Clef), which answers every question.
That judge is the only thing that looks at pixels: reading images is exactly
the cost this check exists to avoid. Never Read a `.png`, `.jpg` or `.webp`,
never take a screenshot, never open a browser. You work from TEXT: every
answer the judge said no to or was not sure about, each with the element's
code and look captured with its screenshot. Return only the verdict.

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

## Step 2 - read every "no" and "unsure", as text, in one go

```
curl -sS "$TH_DAEMON_URL/__qa/visual-report?id=<visualReport id>&project=$TH_PROJECT_ID" | python3 -c "
import json, sys
b = json.load(sys.stdin)['typedChecks']
print('judge:', b.get('message'))
rows = [r for r in b['checks'] if r.get('status') == 'answered']
look = [r for r in rows if r.get('band') != 'act' or r.get('passed') is False]
look.sort(key=lambda r: (r.get('band') == 'act' and r.get('passed') is False) is False)
print('questions', len(rows), '| sure yes', len(rows) - len(look), '| to decide', len(look),
      '| screens', len({(r.get('images') or ['?'])[-1].split(' cropped')[0] for r in rows}))
for r in look:
    ev = r.get('evidence') or {}
    q = r['question']
    print()
    print('NO' if r.get('band') == 'act' else 'UNSURE', r['id'], '|', (r.get('images') or ['?'])[-1])
    print('  asked:', q['instructions'])
    if q.get('type') == 'choice':
        print('  options:', r.get('probabilities'), '| expected:', r.get('expect'))
    print('  judge:', r.get('answer'), 'noul', r.get('noul'), 'confidence', r.get('confidence'), '|', r.get('source'))
    print('  code:', ev.get('code'))
    print('  look:', ev.get('style'))
    if ev.get('dsStyle'): print('  design system look:', ev['dsStyle'])
    if ev.get('coveredBy'): print('  covered by:', ev['coveredBy'])
    if ev.get('clipped'): print('  content clipped: yes')
for r in b['checks']:
    if r.get('status') == 'element-missing':
        print('MISSING', r['id'], '|', r.get('message'))
"
```

If `judge:` says the judge refused (for example Cloudflare's daily free
allowance is used up), there are no answers to decide: put that line in the
verdict and stop.

Every row carries what was captured with its screenshot: the element's HTML
(`code`), its computed look (`look`: fill, border, radius, font, colour,
position), the design system's own look for a comparison (`design system
look`), what sits on top of it (`covered by`, a selector) and whether its
content is clipped. That is enough to decide, so you never need the image.

## Step 3 - decide each row from its evidence

For every NO and UNSURE row, decide whether the sentence the judge was asked
is true, from the row's evidence (and the page's source when you need more:
Grep the selector's id or class, or the CSS rule named in `source`):
- a text question ("The image shows the text ... readable and not covered"):
  `covered by` names something on top of it, or `content clipped: yes`, or a
  colour too close to its background: a PROBLEM. None of those: FINE.
- a design-system comparison ("the same ... in the same visual style"):
  compare `look` with `design system look`: a different fill, border,
  radius, shadow or font weight is a PROBLEM (a page rule restyles it, or it
  is built by hand); the same look with other words, size or state is FINE.
- `ds_origin` (copy / new UI / layout): from `code` and `source`, a
  page-local rule that redraws something the design system already has is
  `ds-copy` (a PROBLEM: use the DS class); a component the design system does
  not have is `new-ui` (a PROBLEM to report); plain spacing or arrangement is
  `layout` (FINE).

For each PROBLEM write one line: what is wrong and where to fix it (file,
rule or element).

## Step 4 - verdict

Return ONLY this:

```
VISUAL-QA <PASS|FAIL> - <pages>
<page>: QA <verdict> · <n> questions on <s> screens: <a> sure yes, <b> problems, <c> fine on a closer read · report <visualReport id>
- PROBLEM <check id> (<screen>, <selector>): <what is wrong> -> <where to fix it>
- MISSING <check id>: <selector> is not on the page
```

FAIL when there is a PROBLEM, a MISSING, or a QA verdict that is not `pass`.
Keep `report <id>` on each page line: the caller's Tasks panel shows the
judge's answers and the images it saw from it.
