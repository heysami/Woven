# Shared visual editing

Workflow element editing and the preview edit overlay use the same selection
commands, clipboard, sizing rules, component controls, variables, and per-file
editing session. Normal prototype playback continues to use the authored code.

## Property panels

Both editing surfaces put Layers on the left and Design properties on the right.
Layers supports search, expandable groups, canvas selection, and arrow-key
navigation. Preview reserves space for both panes so they do not cover the page.
Workflow docks them on opposite sides of the selected prototype node.

The Design panel uses compact controls for dimensions, resizing, layout flow,
alignment, spacing, appearance, fills, and strokes. Auto layout has a nine-point
alignment control. Size limits, effects, and inherited container typography are
expandable. Plain numbers in spacing fields use pixels. Variables can be bound
beside each property; Add opens the component browser. These controls share the
same commands and sessions in both modes.

If an older daemon returns an HTML error page for an editing endpoint, the UI
explains that the daemon must be restarted. Retry keeps pending edits intact.
Component-library errors stay within the component controls.

Arrow keys use the same movement command in both surfaces. In-flow children of
flex and grid containers move past a neighbor in the pressed direction, using
visual positions (including reversed rows, RTL, and wrapping). Ordinary flow
and absolutely positioned layers nudge by 1 CSS pixel; Shift nudges by 10.
Nudging preserves the original layout footprint, transforms, and anchors.
Focused text fields retain cursor movement, and Layers retains tree navigation.
Blocked moves explain the cause, such as the end of a row, the wrong axis,
explicit CSS ordering, hidden content, or a stylesheet preventing movement.

## Editing and saving

Entering edit mode captures the rendered document into an authoring iframe.
Application scripts and animations pause there, so React, timers, and saved
patch observers cannot overwrite text while it is being edited. Navigate the
prototype in playback before entering edit mode to edit another runtime state.

Edits are recorded as commands against persistent `data-woven-id` identities.
Existing pages keep their selector and fingerprint fallbacks. Save merges the
commands into the original source HTML; it does not replace React source with
rendered DOM. Saved patches run before paint and replay after application
rerenders, including text-node changes.
Reorders run once per live target/anchor pair, so replaying earlier movements
cannot shuffle components inserted later. Remounted elements receive the
command again. Runtime code that rearranges the same live nodes retains its
own ordering until those nodes remount; the authoring view remains frozen.

Undo and redo share the per-file session between the two surfaces. Undo after
Save can be saved again to restore the previous source result. Closing the edit
overlay keeps pending edits. Browser draft storage recovers pending edits after
reopening; recovery groups the previous session into one undo entry. Save or
Discard clears the browser draft. Browser storage limits are surfaced visibly.

Saves include the source revision and use atomic replacement. An external edit
causes a conflict rather than an overwrite. Pending work stays available, with
Download pending edits and Reload latest source in the inspector. Edits arriving
during a save remain dirty. Imported source documents have separate sessions
and save results; a failed imported save stays pending.

## Clipboard

Copy captures an immutable element snapshot. Paste and Duplicate assign fresh
identities to every descendant, remap HTML IDs and their references, and retain
component links and variable bindings. Each pasted descendant remains editable.
Pasting again does not change the clipboard. Removing an earlier pasted sibling
reconnects the anchors of later copies when commands are saved.

Add supports Text, Frame, design-system components, and project components.
Insert position is explicit: before, after, or inside the selection. Invalid
HTML nesting is rejected or moved to a valid sibling anchor. Typing fields retain
native text copy/paste; element copy/paste uses the editor's shared clipboard.
Relative media paths are rooted at the source page when copied. Class-based
styling and variable bindings resolve against the destination stylesheet.

## Sizing

| Mode | Behavior |
| --- | --- |
| From stylesheet | No width/height override from the inspector; the page's CSS determines sizing. |
| Fixed | CSS pixels independent of canvas zoom. Stops flex growth and shrinkage on the main axis. |
| Hug | Fits content within available space using `fit-content`. |
| Fill in flex | Shares remaining main-axis space, or stretches on the cross axis. |
| Fill in grid | Stretches in the grid cell. |
| Fill in block | Uses 100 percent of the parent; height requires a defined parent height. |

Fill is unavailable on an axis where the parent explicitly hugs its content.
Minimum and maximum constraints still apply. Auto layout exposes direction,
wrapping, packing, child alignment, gap, and padding. Grid and block behavior
retain CSS semantics. Drag resizing converts dimensions to Fixed using local
CSS pixels, accounting for canvas zoom.
Inline text uses its actual layout dimensions when computed CSS says `auto`.
Inherited sizing is labeled From stylesheet, rather than incorrectly appearing
as Hug. True zero-sized boxes show an explanation, including positioned
children that do not contribute to the parent's intrinsic size.

## Components and variables

The component browser reads the bound design system's rendered gallery, with
runtime mirror data as a fallback. Project definitions live in
`editor/components.json` and have their own revision checks. Design-system
definitions remain owned by the existing DS update flow.
The picker supports explicit `.ds-sample` galleries and the default library's
`.comp` sections and class vocabulary. It shows Design system and Project
sources separately. Gallery components carry their DS ID, version, stable
variant reference, and canonical stylesheet dependencies. Insert, paste, and
swap attach missing stylesheets, which also persist through Save and reload.
Update fetches the latest canonical definition even when Add is closed. The
instance links back to its gallery. Creating a component from a page selection
creates a project definition; it does not silently change the canonical DS.

Instances store a definition reference, definition snapshot, stable part keys,
and per-part overrides. Supported actions are Create, Insert, Update, Swap,
Reset overrides, Detach, and Publish selection as main for project components.
Project definition updates are resolved when source pages load through the
daemon. Text, form-value, placeholder, and style overrides survive updates.
Updates that remove an overridden part retain the instance and flag a conflict.
Exported pages retain their last embedded instance snapshot. Creating a new
definition captures nested components as part of that definition.

Variables show names, aliases, resolved values, bindings, and local overrides.
Bindings preserve `var(...)`. Reset removes a local property; Unbind replaces a
binding with its resolved value. New variables are page-scoped and reject alias
cycles. Theme and persona selectors use existing `data-theme` and `data-mode`
rules, including rules attached to the body. Canonical DS variables continue to
be edited through the DS library.

## Boundaries

This is a DOM/CSS editor. It does not translate arbitrary application logic into
a Figma scene graph or rewrite a data model when a rendered label changes.
Cross-origin embeds and canvas/WebGL internals are not editable DOM components.
Copied script event closures are not synthesized into new application logic.
Plain HTML pastes resolve against the destination CSS. Linked DS instances
require the same bound design system, so importing a library cannot silently
replace the destination page's global styles.
Structural DS changes require Update; live CSS changes follow linked stylesheets.

Saved edit commands remain embedded in source, and the existing daemon history
records source saves. Regeneration that replaces a complete file must preserve
its edit script and component metadata, or use history to recover the edits.
The new component registry is separate from generated prototype markup.

## Implementation and checks

- `editor/edit-engine.js`: identities, clipboard, layout, sessions, recovery, save.
- `editor/edit-components.js`: definitions, instances, overrides, runtime updates.
- `editor/edit-controls.js`: shared inspector controls.
- `editor/edit_store.py` and `editor/component_store.py`: revision-aware storage.
- `GET /__edit_source`, `GET/POST /__edit_components`, `POST /__html_save`:
  project-scoped read and save endpoints.

Run the focused regression checks from the repository root:

```sh
node editor/tests/test-edit-engine.cjs
node editor/tests/test-edit-session.cjs
node editor/tests/test-edit-components.cjs
node editor/tests/test-edit-movement.cjs
node editor/tests/test-edit-ui.cjs
python3 -B -m unittest discover -s editor/tests -p 'test_edit_*.py'
```

The UI test mounts the production preview overlay and workflow inspector, using
the repository's Playwright installation and the same React/htm CDN scripts as
the editor. Fixtures use temporary servers and do not mutate user projects or
start the production daemon. Restart the daemon and reload the editor to load
the new server endpoints and client modules.
