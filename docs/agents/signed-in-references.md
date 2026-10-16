# Signed-in references - reading SharePoint and OneDrive files through the agent browser

Read this when a project reference (or a link inside one) is on SharePoint,
OneDrive, Teams or office.com. Those links never get past WebFetch: it lands on
the Microsoft sign-in page every time. Open them with the
`mcp__reference_browser__*` tools instead. They drive a browser the user has
signed in to, so a link that looks private usually opens fine there.

The read-only rules from the references block still hold: open only the
project's references and links inside them, only read, never type into, submit,
share, edit, delete, accept or change anything, never sign in or out.

## Why the page itself is not enough

The Excel, Word and PowerPoint viewer pages show the tools the app's toolbar
and sheet tabs, not the content. A snapshot of an open workbook has no cells.
So read the FILE: ask SharePoint what the link points at, save the file, and
read the saved copy.

## Steps

1. **Open the link.** `new_page` with the reference's link, exactly as listed.
   If it lands on a Microsoft sign-in or "Pick an account" page, stop: tell the
   user the agent browser is not signed in to that site, ask them to sign in
   there (Preview > References), and retry after. Otherwise note the new page's
   id from the result.

2. **Ask SharePoint what it is.** `evaluate_script` on that page with this
   function, TARGET set to the link (or, for a sub-folder, to the `item` value
   an earlier answer gave you):

   ```js
   async () => {
     const TARGET = "<the link, or a sub-folder's item>";
     const api = location.origin + "/_api/v2.0/";
     const base = TARGET.startsWith("http")
       ? "shares/u!" + btoa(unescape(encodeURIComponent(TARGET))).replace(/=+$/, "").replace(/\//g, "_").replace(/\+/g, "-") + "/driveItem"
       : TARGET;
     const sel = "?$select=id,name,size,file,folder,lastModifiedDateTime,parentReference";
     const get = async p => (await fetch(api + p, {credentials: "include", headers: {Accept: "application/json"}})).json();
     const row = x => {
       const item = "drives/" + x.parentReference.driveId + "/items/" + x.id;
       return {name: x.name, folder: !!x.folder, size: x.size, modified: x.lastModifiedDateTime,
               item: item, download: x.folder ? undefined : api + item + "/content"};
     };
     const it = await get(base + sel);
     if (it.error) return {error: it.error.code + ": " + it.error.message};
     const out = row(it);
     if (it.folder) out.children = ((await get(base + "/children" + sel + "&$top=200")).value || []).map(row);
     return out;
   }
   ```

   It answers with the item's name, size and last change. For a folder,
   `children` lists what is inside, each with its own `item`, and a `download`
   address for each file. Pick the files that cover what you are working on;
   do not save a whole folder.

3. **Save the file.** `new_page` with the file's `download` address. The tool
   answers `net::ERR_ABORTED`: that is normal for a download and the file IS
   saved. It lands in `~/Downloads` under its own name, and Chrome adds " (1)",
   " (2)" when that name is already taken. Take the newest copy, and never an
   older one already sitting there, because each save is the file as it is
   now:
   `ls -t ~/Downloads | grep -F "<name without its extension>" | head -1`
   (wait a second and look again if only a `.crdownload` is there).

4. **Read it.**
   `python3 "$TH_PROTOCOL_ROOT/editor/tools/office_text.py" "$HOME/Downloads/<file>"`
   prints .xlsx, .docx and .pptx as text. For a workbook, add `--sheets` first
   to see the sheet names and sizes, then `--sheet "<name>"` (repeatable) for
   the sheets you need: a whole workbook can run to a hundred thousand
   characters. Read a PDF with the Read tool.

5. **Close your tabs.** Call `list_pages`, then `close_page` on each tab YOU
   opened, picked by its address (a download leaves its tab as `about:blank`).
   Never close another tab: the user's own tabs are in the same list, and page
   ids are renumbered whenever the browser tools restart, so an id from an
   earlier list can point at the user's tab.

## Saying what you read

Name the reference, the file you read and its last-change date from step 2.
If a step failed, say which step and what it answered (the error text or the
page it showed). "It needs a sign-in" is only true when step 1 showed a
sign-in page.
