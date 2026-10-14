# DS compare - check what the design system does not recognise

You are a dispatched subagent. Your brief gives you the PROJECT ROOT (your cwd),
the PROTOTYPE slug, the PAGES that were just changed, and ideally what changed
(`Changed:` selectors) and where it shows (`States:` URL queries and clicks):
the same brief the visual-qa subagent gets.

**Only what the design system does not recognise is checked.** Markup written
with the DS's own classes is correct by construction (ds-guardian lints the
CSS around it). What is left is an element styled by page CSS or an inline
style that carries no DS class: a hand-made copy of a DS component, or a new
pattern. You decide which. The image judge (Clef) only scores how alike two
things look; it decides nothing. You never look at an image: never Read a
`.png`, `.jpg` or `.webp`, never take a screenshot. Return only the verdict.

## Step 1 - scope (per page)

Write the same scope the visual-qa subagent writes (see
`$TH_PROTOCOL_ROOT/docs/agents/visual-qa.md`, step 1), without `cases`:
`{"changed": [...], "states": [...]}`. Only unrecognised elements inside what
the change impacts are listed; with no `changed`, the whole screen is.

## Step 2 - list the unrecognised elements (no judge calls)

```
curl -sS -G "$TH_DAEMON_URL/__qa/run" --data-urlencode "project=$TH_PROJECT_ID" \
  --data-urlencode "page=<slug>/<page>.html?<the page's own query, if any>" \
  --data-urlencode "typed=ds" --data-urlencode "detail=full" \
  --data-urlencode "scope=$(cat <scope file>)" > "${TMPDIR:-/tmp}/dsc-list.json"
python3 -c "
import json, sys
r = json.load(open(sys.argv[1])); b = r.get('typedChecks') or {}
print('verdict:', r.get('verdict'), r.get('error') or '', '|', b.get('message'))
for n in (b.get('elements') or {}).get('notes') or []: print('NOTE', n)
for u in b.get('unrecognised') or []:
    print(); print(u['id'], 'x%d' % u['count'], '|', u['screen'], '|', u['size'], '|', u['source'])
    print('  selector:', u['selector']); print('  code:', u['code']); print('  look:', u['look'])
" "${TMPDIR:-/tmp}/dsc-list.json"
```

None listed: the verdict is PASS for that page (say how many states it saw).

## Step 3 - shortlist, from the code and the catalog

For each element, read its code, the rule that styles it (`source`: grep it in
the page's `<style>` or CSS file) and its look, then the design system's
catalog: every component with its title and what it is for.

```
python3 -c "
import sys; sys.path.insert(0, '$TH_PROTOCOL_ROOT/editor/tools/qa'); import ds_contract
c = ds_contract.load_or_build('design-systems/<ds id>', '<ds id>')
for r in c['components']:
    print('.%s | %s | %s | variants: %s' % (r['id'], r.get('title'), (r.get('description') or '')[:200], ', '.join(r.get('variants') or [])))
"
```

(`<ds id>`: the folder under `design-systems/` the page's stylesheet links.)
Decide per element:
- **layout**: it only frames or arranges other content (a band, a panel
  background, a column, a divider). Not a component; drop it.
- **candidates**: up to 3 components it may be a hand-made copy of, by ROLE
  first (what a user does with it: a button, a status, a filter trigger, a
  card, a field) and look second. Name each as `<class>` or
  `<class>.<modifier>` for a variant (`btn.btn--outline`, `status.status--attention`).
- **new**: no component plays its role. Keep it for the verdict.

## Step 4 - compare the candidates

Run the page again with the shortlist in the scope (`compare`), same `changed`
and `states`:

```json
{"changed": [...], "states": [...],
 "compare": [{"selector": "<the element's selector>", "screen": "<its screen label>",
              "candidates": ["btn", "btn.btn--outline"]}]}
```

```
curl -sS -G "$TH_DAEMON_URL/__qa/run" ... --data-urlencode "typed=ds" \
  --data-urlencode "scope=$(cat <scope file with compare>)" > "${TMPDIR:-/tmp}/dsc-cmp.json"
python3 -c "
import json, sys
r = json.load(open(sys.argv[1])); b = r.get('typedChecks') or {}
print('judge:', b.get('message'), '| report', r.get('visualReport'))
for k, why in ((b.get('elements') or {}).get('unmatched') or {}).items(): print('UNMATCHED', k, '-', why)
for f in b.get('findings') or []:
    print(); print(f['id'], 'x%d' % f['count'], '|', f['source'], '|', f['selector'])
    for c in f['candidates']:
        print('  vs .%s (%s%s): %s | scores %s | after the chain %s | %s' % (c['key'], c.get('title'),
              '' if c.get('exactVariant') else ', base only', c.get('answer'), c.get('scores'),
              c.get('chainScores'), c.get('chain') or 'no chain'))
        print('     measured differences:', c.get('differences'))
" "${TMPDIR:-/tmp}/dsc-cmp.json"
```

For each pair, the judge scored A (the gallery's own component) against B
(the page's element) side by side, per dimension: colour, border, shape, font
(style) and icon, layout, words (content, which never counts). When a style
dimension scored, the chain re-shot A with B's words and icon and on the colour
B sits on, and asked again: `after the chain` is the answer that counts.
`measured differences` are the exact computed values that differ.

## Step 5 - decide each element

- **copy**: it plays the role of a candidate and looks like it (`same style`,
  or only content differs). PROBLEM: replace it with the component (name the
  markup to write) and drop its rule.
- **variant**: it plays the role of a candidate but a style dimension differs
  (`differs in colour`), confirmed by `measured differences`. PROBLEM: use the
  component; if the difference is wanted, it belongs in the design system as a
  variant (styles.css + gallery.html + DESIGN.md), never in the page.
- **new pattern**: no candidate plays its role (step 3), or every candidate
  differs in role and look. STANDARDISE: say what it is and that it is a
  candidate for the design system.

## Step 6 - verdict

Return ONLY this:

```
DS-COMPARE <PASS|FAIL> - <pages>
<page>: <u> unrecognised element(s) in scope, <l> layout, <c> compared · report <visualReport id>
- COPY <id> (<selector>, x<count>, rule <source>): rebuilds .<class> -> use <markup>, drop <rule>
- VARIANT <id> (...): .<class> but <dimension: measured page vs DS> -> use .<class>; add a variant to the DS if wanted
- NEW <id> (...): <what it is> -> standardise: propose it for the design system
```

FAIL when there is a COPY or a VARIANT. A NEW alone is a PASS with its lines:
the caller reports them to the user.
