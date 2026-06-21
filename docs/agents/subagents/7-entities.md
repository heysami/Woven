# Subagent 7 - Entities (lens: data shapes)

You own the **data-shapes lens**. Enumerate what *you* see as an entity from `window.DEMO` and `entities.json`, applying merge / variant / fk reasoning. You also own each entity's **position on the Entities canvas** (`x`, `y`, `w`).

**Read [`../conventions.md`](../conventions.md) before starting** - universal rules + entity-ID naming.

## Input (envelope only)

- `slug`, `sourceRoot`, `intent`

No orchestrator-provided entity list. You enumerate.

## Output

Per [`../data-schema.md`](../data-schema.md): `entities[]` with **`x`, `y`, `w` REQUIRED on every entity** (EntitiesView reads `entity.x` / `.y` / `.w` directly - no fallback; if you omit them every card stacks at `(0,0)`). Plus `demoPatches` for source data seeding and `nameAmbiguities` for similar-named pairs.

```json
{
  "entities": [
    { "id": "Reference",  "tag": "base",
      "x": 60, "y": 60, "w": 280,
      "fields": [
        { "name": "id",      "type": "string", "pk": true },
        { "name": "title",   "type": "string" },
        { "name": "authors", "type": "string[]" },
        { "name": "year",    "type": "number" }
      ]
    },
    { "id": "Collection", "tag": "base",
      "x": 400, "y": 60, "w": 280,
      "fields": [
        { "name": "id",           "type": "string", "pk": true },
        { "name": "label",        "type": "string" },
        { "name": "referenceIds", "type": "string[]", "fk": "Reference" }
      ]
    }
  ],
  "demoPatches": {
    "Reference":  [/* sample records to seed window.DEMO.references */]
  },
  "nameAmbiguities": [
    {
      "a": "Programme",
      "b": "InhouseProgramme",
      "sharedFields": ["id", "code", "title"],
      "edgeFound": null,
      "question": "These share name + fields but no fk or merged records. Should one extend the other, or are they intentionally parallel catalogs?"
    }
  ]
}
```

**`x` / `y` / `w` are mandatory on every entity.** Default `w: 280`. The card's rendered height is `38 + fields.length * 22 + 8` so you don't write it - EntitiesView computes it.

## You must read source

### Files you may read

- `source/entities.json` - preferred path; copy verbatim.
- `source/data.js` - `window.DEMO` shape.
- `source/*.html`, `*.js` - for inferring entity rendering patterns when manifest is absent.
- **Existing `source/prototype.json`** - preserve `x` / `y` / `w` for entity IDs already present. Users drag entity cards manually; positions must be stable across regens.

## Enumerate through your lens

**Manifest path (preferred).** `entities.json` exists → copy `entities[]` verbatim. Don't infer.

**Inferred path.** No manifest → walk `window.DEMO`:

1. Each top-level array key → candidate entity. Key (singular, PascalCase per `conventions.md`) → entity `id`.
2. Inspect 3+ records per array to settle field types. Mixed types → `string`.
3. **Merge check.** Two arrays share ≥80% fields by name → one entity with `tag: "merged"`, `mergedFrom: [array1, array2]`.
4. **Variant check.** One array is a strict superset of another → superset is `tag: "variant"`, `extends: "<Base>"`.
5. **`fk` fields.** Field of type `string` or `string[]` whose values look like another entity's `id` (regex match or co-occurrence) → set `fk: "<EntityId>"`.
6. **PK.** First `id`-named field → `pk: true`.
7. **Similar-name pair check.** After enumeration, look for pairs where one ID contains the other (`Programme` / `InhouseProgramme`) or shares ≥6 consecutive characters. For each pair, check whether they share field structure or have value-level references. If they look related but **don't** trip the merge / variant / fk checks above (parallel catalogs with no edge), include both in `entities[]` AND emit them in `nameAmbiguities[]`. The orchestrator's reconciliation surfaces this to the user - don't auto-merge.

## Position recipe - `x` / `y` / `w`

The Entities canvas is a freeform 2D plane. Lay entities out so the rendered Entities view is readable, not a stack at origin.

1. **Preserve prior positions.** For any entity ID already in `source/prototype.json` with `x` / `y` / `w` set, copy those values verbatim. Don't shift placed cards across regens.
2. **Place new entities in a grid pattern.** For each entity not already positioned, walk a 4-column grid:
   - `w`: default `280` (wider - e.g. `320` - only if the entity has long field names or `string[]` types that overflow the default).
   - `colWidth = w + 60` gap; `rowHeight = 38 + maxFields * 22 + 8 + 60` gap (use a row pitch of ~360 px as a safe default if mixed).
   - Index `i` in placement order → `col = i % 4`, `row = floor(i / 4)`.
   - `x = 60 + col * 340`, `y = 60 + row * 360` (gives ~60 px gaps between cards).
3. **Cluster related entities.** When placing new entities, prefer to keep an entity adjacent (next column or next row) to its `fk` target or `extends` base - short edges render cleaner in the routed-edge layout. If preserving prior positions makes this impossible, the prior position wins.
4. **No overlaps.** Two entities should never occupy the same `(x, y)`. If your placement collides with a preserved position, advance to the next free slot.

## demoPatches

For entities without existing `window.DEMO` rows, seed 3-5 records - named entries, voiced microcopy (per `PROTOTYPE.md`).

## Render-verify your slice

After producing your output, load the editor's **Entities** view (Cmd+5 or click the Entities tab) and verify:

1. Every entity card is visible - no card is stacked at `(0, 0)` underneath another.
2. The canvas is not empty / blank - if it is, your `x` / `y` are probably missing or all zero.
3. Cards don't overlap - pan around to confirm.
4. `fk` arrows route between related cards without crossing through unrelated card bodies.
5. Entity count in the view matches `entities.length` in your output.

If anything's wrong (cards stacked, blank canvas, missing cards), fix `x` / `y` / `w` and re-render before reporting done. **Screenshot required.**

## Self-audit (run before returning)

Each item requires **evidence** - a Read / Bash / Grep / screenshot call. Don't tick implicitly.

- [ ] I read `conventions.md`.
- [ ] I read `entities.json` (preferred) or `data.js`.
- [ ] I applied merge / variant / fk checks with the documented thresholds.
- [ ] **Similar-name pair check.** I scanned every entity pair for ID similarity (substring containment, ≥6 shared chars) and emitted any related-looking-but-no-edge pairs in `nameAmbiguities[]`. (The `Programme` / `InhouseProgramme` bug.)
- [ ] I excluded the storyboard from entity extraction.
- [ ] Entity IDs follow the singular-PascalCase naming convention.
- [ ] `demoPatches` seeded with voiced, named, specific records.
- [ ] **Every entity has `x`, `y`, `w` set** (EntitiesView stacks at (0,0) otherwise).
- [ ] **I read existing `prototype.json` and preserved `x` / `y` / `w` for entities already placed there** - users drag cards manually; positions must be stable.
- [ ] **I rendered the Entities view in the editor and confirmed every card is visible, no stacking at origin, no overlaps.** (Screenshot required.)

## Common blindspots

- **`fk` pointing to a non-existent entity.** You wrote `fk: "User"` but no `User` entity exists in `entities[]` (the array is actually called `members`, entity ID `Member`). Cross-check every `fk` value against the final entity ID list before returning.
- **Multiple fields marked `pk: true`.** Only one PK per entity. Compound keys aren't modeled here - pick the most-id-like field.
- **Type inferred from one record.** If 2 of 3 sample records have `year: 2024` and one has `year: "2024"`, type is `string` (mixed). Don't lock in `number` from the first record.
- **`Array<string>` vs `string`.** `referenceIds: ["a", "b"]` → `string[]` with `fk: "Reference"`. `referenceId: "a"` → `string` with `fk: "Reference"`. The `s` matters.
- **Variant missed because field order differs.** `extends` detection by *strict superset* should compare field names as a set, not as an ordered list.
- **Merge applied too aggressively.** Two arrays sharing 80%+ field *names* might still be intentionally separate (different lifecycles, different write paths). When in doubt, emit both with `nameAmbiguities`, not a forced merge.
- **`demoPatches` voiced like a placeholder.** "John Doe / Jane Smith" defeats the prototype's genre. Seed with named entries matching the prototype's voice.

## Don't

- Don't infer `links[]` from `fk` alone - that's a separate manifest decision.
- Don't invent entities from page filenames. Walk `window.DEMO` or `entities.json`.
- Don't silently emit two confusingly similar parallel catalogs without `nameAmbiguities`.
- Don't write frames / arrows / parent / lanes.
- **Don't omit `x` / `y` / `w` - they're required, not optional.** Missing → every card stacks at (0,0) and the view is unreadable.
- Don't shift positions of entities already placed in `prototype.json`. Positions are stable across regens.
