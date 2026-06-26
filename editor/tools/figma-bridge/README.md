# Woven Bridge (Figma plugin)

Send a Woven prototype into Figma as real, editable layers. This is the "Send to
Figma" counterpart to Export: instead of writing a folder to disk, the editor
converts the rendered prototype DOM into a scene and hands it to this plugin,
which rebuilds it in Figma Desktop.

## Why a plugin (and not the Figma API)

Figma's REST API is read-only for design content: you cannot create frames or
text through it. The only way to write editable nodes into Figma is from inside
a plugin running in Figma Desktop (via `figma.createFrame`, etc.). So this is a
small local plugin that long-polls the Woven daemon for hand-offs. No Figma
token, no cloud round-trip, nothing leaves your machine.

## Architecture

```
Woven editor (browser)                Woven daemon                 Figma Desktop
  walk prototype DOM   --POST-->   /__figma_send  (queue)
  (figma-bridge.js)                       |
                                          | long-poll
                                  /__figma_poll   <--POST--  Woven Bridge ui.html
                                          |                        | postMessage
                                          |                  code.js builds nodes
  poll job status      --POST-->   /__figma_job          <--POST-- /__figma_status
```

- `editor/figma-bridge.js` - browser-side DOM-to-scene walker.
- `editor/serve.py` - `/__figma_send`, `/__figma_poll`, `/__figma_status`,
  `/__figma_job` (an in-memory per-project relay; clears on daemon restart).
- `ui.html` - the plugin's UI iframe; does all networking (the plugin sandbox
  has no `fetch`) and relays scenes to `code.js` + status back to the daemon.
- `code.js` - the plugin sandbox; rebuilds the scene as Figma nodes.

See `SCENE.md` for the scene JSON contract.

## One-time setup

1. In Figma Desktop: `Menu -> Plugins -> Development -> Import plugin from
   manifest...` and pick this folder's `manifest.json`.
2. Run it: `Menu -> Plugins -> Development -> Woven Bridge`.
3. The plugin auto-scans localhost for running Woven daemons on open. Pick your
   daemon from the **Woven daemon** dropdown and your project from the
   **Project** dropdown (both populate from `GET /__projects`), then click
   **Connect**. The dot turns green. Hit **Rescan** if you started Woven after
   opening the plugin; use **Advanced** to enter a URL by hand for a port the
   scan misses.
4. Leave the plugin window open while you work.

The manifest uses `"allowedDomains": ["*"]`. Figma rejects a port in
`allowedDomains` entries (e.g. `http://127.0.0.1:5731` fails validation as "not a
valid URL"), so the wildcard is what lets the plugin reach the daemon on any
local port. Just set the URL in the plugin window to match your editor; all
traffic stays on your machine.

## Use

In the Woven editor, click **Send to Figma** on any prototype or HTML asset node.
The plugin builds it on the current Figma page and zooms to it.

## Using your Figma design system (component mapping)

By default everything is rebuilt from primitives (frames/text/images). To have
Woven components come in as instances of YOUR Figma library components, set up a
two-part mapping (joined by a component name):

1. **Identity - editor:** Settings -> Send to Figma -> "Component mapping". Add
   rules like `.btn.is-primary -> Button` (variants `Variant=primary`). These are
   stored with the project's design system. Elements that already carry a
   `data-component` attribute are detected automatically, no rule needed.
2. **Binding - this plugin:** after a Send, each tagged component name appears in
   the plugin's "Component mapping" list. Enable your design-system library in the
   file, select the matching component (or component set, or an instance) on the
   canvas, and click **Bind**. The binding is saved per design system in the
   plugin's storage.
3. **Re-send** from Woven. Bound components now build as library instances (with
   variants applied best-effort); unbound ones still fall back to frames.
