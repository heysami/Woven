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
3. In the plugin window, confirm the daemon URL (default `http://127.0.0.1:5731`)
   and the project id (the `?project=` of your editor URL; `default` in
   single-project mode), then click **Connect**. The dot turns green.
4. Leave the plugin window open while you work.

If your daemon runs on a non-default port, either change the URL in the plugin
window AND add that origin to `manifest.networkAccess.allowedDomains` (Figma only
permits requests to listed origins), or keep the daemon on 5731.

## Use

In the Woven editor, click **Send to Figma** on any prototype or HTML asset node.
The plugin builds it on the current Figma page and zooms to it.
