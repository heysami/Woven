# Shared visual editing

Workflow element editing and the preview edit overlay use the same selection
commands, clipboard, sizing rules, component controls, variables, and per-file
editing session. Normal prototype playback continues to use the authored code.

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

## Components and variables

The component browser reads the bound design system's rendered gallery, with
runtime mirror data as a fallback. Project definitions live in
`editor/components.json` and have their own revision checks. Design-system
definitions remain owned by the existing DS update flow.

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
Cross-design-system pastes can inherit a different class or variable vocabulary.
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
node editor/tests/test-edit-ui.cjs
python3 -B -m unittest discover -s editor/tests -p 'test_edit_*.py'
```

The UI test mounts the production preview overlay and workflow inspector, using
the repository's Playwright installation and the same React/htm CDN scripts as
the editor. Fixtures use temporary servers and do not mutate user projects or
start the production daemon. Restart the daemon and reload the editor to load
the new server endpoints and client modules.
