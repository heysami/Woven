/* ===========================================================================
   LOGICPERMISSION - custom in-iframe permission overlay (no native dialogs).

   Browser sensor / device APIs (getUserMedia for camera + mic,
   DeviceOrientationEvent.requestPermission on iOS 13+) MUST be requested from a
   real user gesture. The logic-graph runtime lives inside a tool iframe, so we
   cannot lean on the editor chrome's uiAlert/uiConfirm: this module paints its
   OWN minimal overlay (inline styles, no external CSS) and resolves a
   Promise<bool> when the user clicks Allow or Cancel. The Allow handler runs
   synchronously inside the click event, so the caller can chain the real
   permission request (getUserMedia / requestPermission) on the same gesture.

   No native alert/confirm/prompt. No emoji. Self-contained: any tool iframe can
   `import { LogicPermission } from '../_shared/logicpermission.js'`.

     LogicPermission.request({ title, body, allowLabel, cancelLabel, mount })
       -> Promise<bool>          // true = user allowed, false = cancelled
     LogicPermission.requestGesture(opts, fn) -> Promise<any>
       // shows the overlay, runs fn() INSIDE the Allow click (so the browser
       // still treats it as a user gesture), resolves with fn()'s result or
       // null if cancelled / fn threw.

   The two-gate pattern (per LOGICGRAPH_DESIGN.md §6): this overlay is gate 1
   (our explanatory prompt on a user gesture); the browser's own permission
   prompt is gate 2 (fired by fn()). We never bypass the browser gate.
   =========================================================================== */

const Z_BASE = 2147480000;  // sit above tool chrome but below nothing of ours

function el(tag, style, text) {
  const n = document.createElement(tag);
  if (style) n.setAttribute('style', style);
  if (text != null) n.textContent = text;
  return n;
}

export const LogicPermission = {

  // Low-level: show the overlay, resolve true/false on the user's choice.
  request(opts) {
    opts = opts || {};
    return new Promise((resolve) => {
      const mount = opts.mount || document.body || document.documentElement;
      if (!mount) { resolve(false); return; }

      const title = opts.title || 'Permission needed';
      const body = opts.body || 'This piece would like access to a device sensor.';
      const allowLabel = opts.allowLabel || 'Allow';
      const cancelLabel = opts.cancelLabel || 'Not now';

      const back = el('div',
        'position:fixed;inset:0;z-index:' + Z_BASE + ';display:flex;' +
        'align-items:center;justify-content:center;padding:24px;' +
        'background:rgba(8,10,14,0.62);backdrop-filter:blur(2px);' +
        '-webkit-backdrop-filter:blur(2px);' +
        'font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;');

      const card = el('div',
        'box-sizing:border-box;width:min(380px,100%);background:#15181f;' +
        'color:#e7ebf2;border:1px solid rgba(255,255,255,0.10);border-radius:14px;' +
        'box-shadow:0 18px 60px rgba(0,0,0,0.55);padding:22px 22px 18px;');

      const h = el('div', 'font-size:15px;font-weight:600;letter-spacing:0.01em;margin:0 0 8px;', title);
      const p = el('div', 'font-size:13px;line-height:1.5;color:#aeb6c4;margin:0 0 18px;', body);

      const row = el('div', 'display:flex;gap:10px;justify-content:flex-end;');
      const cancelBtn = el('button',
        'cursor:pointer;font:inherit;font-size:13px;padding:8px 14px;border-radius:9px;' +
        'border:1px solid rgba(255,255,255,0.14);background:transparent;color:#c4ccda;', cancelLabel);
      const allowBtn = el('button',
        'cursor:pointer;font:inherit;font-size:13px;font-weight:600;padding:8px 16px;border-radius:9px;' +
        'border:1px solid transparent;background:#4f7cff;color:#fff;', allowLabel);

      let done = false;
      const finish = (val) => {
        if (done) return; done = true;
        try { back.remove(); } catch (e) {}
        document.removeEventListener('keydown', onKey, true);
        resolve(val);
      };
      const onKey = (e) => { if (e.key === 'Escape') { e.stopPropagation(); finish(false); } };

      // NOTE: caller-supplied onAllow runs synchronously here so the browser
      // keeps treating the Allow click as the originating user gesture.
      allowBtn.addEventListener('click', () => {
        if (typeof opts.onAllow === 'function') { try { opts.onAllow(); } catch (e) {} }
        finish(true);
      });
      cancelBtn.addEventListener('click', () => finish(false));
      back.addEventListener('click', (e) => { if (e.target === back) finish(false); });
      document.addEventListener('keydown', onKey, true);

      row.appendChild(cancelBtn); row.appendChild(allowBtn);
      card.appendChild(h); card.appendChild(p); card.appendChild(row);
      back.appendChild(card);
      mount.appendChild(back);
      try { allowBtn.focus(); } catch (e) {}
    });
  },

  // High-level: show overlay, run `fn` INSIDE the Allow click (preserving the
  // gesture), resolve with fn()'s result (awaited) or null if cancelled / failed.
  requestGesture(opts, fn) {
    opts = opts || {};
    return new Promise((resolve) => {
      let gesturePromise = null;
      const wrapped = Object.assign({}, opts, {
        onAllow() {
          // Kick off the real (gesture-requiring) API call on the click itself.
          try { gesturePromise = Promise.resolve(typeof fn === 'function' ? fn() : null); }
          catch (e) { gesturePromise = Promise.reject(e); }
        },
      });
      this.request(wrapped).then((allowed) => {
        if (!allowed || !gesturePromise) { resolve(null); return; }
        gesturePromise.then((v) => resolve(v == null ? true : v)).catch(() => resolve(null));
      });
    });
  },
};
