/* ===========================================================================
   SOURCES — shared parametric value-source evaluator.

   A value source (number-generator / timeline) DRIVES a numeric param of a
   position / effect / trigger block. The editor bakes the binding onto the
   target spec:

     spec._bindings[param] = { kind, spec:{ kind:'number', sub, params, vector } }
                           | { kind:'timeline', spec:{ duration, loop, _track } }
     spec._overrides[index] = { rotation, scale, x, y, ... }   (per-cell/instance)

   `evalSource(src, ctx) → number`, ctx = { index, count, time, u, v, cols, rows }.
   Scalar sources broadcast one value; VECTOR sources (algorithmic / random /
   pixel-map / per-instance timeline) are evaluated PER INSTANCE so each grid
   cell / instance gets its own value.

   Self-contained (own hash/mulberry/finiteNumber) so any tool iframe can
   `import { Sources } from '../_shared/sources.js'`. Time is passed in by the
   caller (each tool owns its own clock / playhead).
   =========================================================================== */

function finiteNumber(v, fallback) { const n = Number(v); return Number.isFinite(n) ? n : fallback; }
function hash(s) { s = String(s); let h = 2166136261; for (let i = 0; i < s.length; i++) { h ^= s.charCodeAt(i); h = Math.imul(h, 16777619); } return h >>> 0; }
function mulberry(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

export const Sources = {
  _fnCache: new Map(),
  _imgCache: new Map(),

  isVector(src) {
    const s = (src && src.spec) || src || {};
    if (s.vector) return true;
    if (s.kind === 'timeline') return !!(s._track && s._track.perInstance);  // scalar unless per-instance
    return s.sub === 'algorithmic' || s.sub === 'random' || s.sub === 'pixel-map';
  },

  eval(src, ctx) {
    const s = (src && src.spec) || src || {}; const p = s.params || {}; ctx = ctx || {};
    const i = ctx.index || 0, t = ctx.time || 0, n = ctx.count || 1, u = ctx.u || 0, v = ctx.v || 0, cols = ctx.cols || 1, rows = ctx.rows || 1;
    if (s.kind === 'timeline') {
      const tr = s._track; if (!tr || !tr.keys || !tr.keys.length) return 0;
      const dur = finiteNumber(s.duration, 4) || 4; let tt = t;
      if (tr.perInstance) tt += i * finiteNumber(tr.stagger, 0);
      if (s.loop !== false) { tt = tt % dur; if (tt < 0) tt += dur; } else tt = Math.max(0, Math.min(dur, tt));
      const keys = tr.keys.slice().sort((a, b) => (a.t || 0) - (b.t || 0));
      return this._interp(keys, tt);
    }
    if (s.sub === 'constant') return finiteNumber(p.value, 0);
    if (s.sub === 'algorithmic') { const fn = this._fn(p.expr); try { return finiteNumber(fn(i, t, n, u, v, cols, rows), 0); } catch (e) { return 0; } }
    if (s.sub === 'random') { const min = finiteNumber(p.min, 0), max = finiteNumber(p.max, 1); const r = mulberry(hash(String(p.seed || 'r') + ':' + i)); return min + (max - min) * r(); }
    if (s.sub === 'pixel-map') return this._pixel(s, ctx);
    return 0;
  },

  _interp(keys, t) {
    if (!keys.length) return 0;
    if (t <= keys[0].t) return finiteNumber(keys[0].value, 0);
    const last = keys[keys.length - 1]; if (t >= last.t) return finiteNumber(last.value, 0);
    for (let i = 0; i < keys.length - 1; i++) {
      const a = keys[i], b = keys[i + 1];
      if (t >= a.t && t <= b.t) {
        const span = (b.t - a.t) || 1; let f = (t - a.t) / span; const ease = a.ease || b.ease;
        if (ease === 'in') f = f * f; else if (ease === 'out') f = 1 - (1 - f) * (1 - f); else if (ease === 'inout') f = f < 0.5 ? 2 * f * f : 1 - Math.pow(-2 * f + 2, 2) / 2;
        return finiteNumber(a.value, 0) + (finiteNumber(b.value, 0) - finiteNumber(a.value, 0)) * f;
      }
    }
    return finiteNumber(last.value, 0);
  },

  _fn(expr) {
    let f = this._fnCache.get(expr);
    if (!f) { try { f = new Function('i', 't', 'n', 'u', 'v', 'cols', 'rows', 'return (' + String(expr || '0') + ');'); } catch (e) { f = function () { return 0; }; } this._fnCache.set(expr, f); }
    return f;
  },

  _pixel(s, ctx) {
    const p = s.params || {}; const url = p.assetUrl; const min = finiteNumber(p.min, 0), max = finiteNumber(p.max, 1);
    if (!url) return min;
    let rec = this._imgCache.get(url);
    if (!rec) {
      rec = { ready: false, data: null, w: 0, h: 0 }; this._imgCache.set(url, rec);
      const im = new Image(); try { im.crossOrigin = 'anonymous'; } catch (e) {}
      im.onload = () => { try {
        const w = Math.min(im.naturalWidth || 1, 128), h = Math.min(im.naturalHeight || 1, 128);
        const cv = document.createElement('canvas'); cv.width = w; cv.height = h; const cx = cv.getContext('2d');
        cx.drawImage(im, 0, 0, w, h); rec.data = cx.getImageData(0, 0, w, h).data; rec.w = w; rec.h = h; rec.ready = true;
      } catch (e) { rec.ready = false; } };
      im.src = url;
    }
    if (!rec.ready || !rec.data) return min;
    let px, py;
    if (ctx.u != null || ctx.v != null) { px = Math.max(0, Math.min(rec.w - 1, Math.floor((ctx.u || 0) * (rec.w - 1)))); py = Math.max(0, Math.min(rec.h - 1, Math.floor((ctx.v || 0) * (rec.h - 1)))); }
    else { const idx = (ctx.index || 0) % Math.max(1, rec.w * rec.h); px = idx % rec.w; py = Math.floor(idx / rec.w); }
    const o = (py * rec.w + px) * 4, d = rec.data, ch = p.channel || 'luma';
    let val; if (ch === 'r') val = d[o] / 255; else if (ch === 'g') val = d[o + 1] / 255; else if (ch === 'b') val = d[o + 2] / 255; else if (ch === 'a') val = d[o + 3] / 255;
    else val = (0.299 * d[o] + 0.587 * d[o + 1] + 0.114 * d[o + 2]) / 255;
    return min + (max - min) * val;
  },

  // True if a spec carries any binding/override whose value changes over time
  // (so a static consumer knows it must update each frame).
  isDynamic(p) {
    const b = p && p._bindings; if (!b) return false;
    for (const k in b) { const s = (b[k] && b[k].spec) || b[k] || {};
      if (s.kind === 'timeline') return true;
      if (s.sub === 'algorithmic' && /\bt\b/.test(String((s.params && s.params.expr) || ''))) return true;
    }
    return false;
  },

  // SCALAR bindings (vector=false) overlaid onto a 2D params object before resolve.
  applyScalar(p, time) {
    const b = p && p._bindings; if (!b) return p;
    for (const k in b) { const src = b[k]; if (!src || this.isVector(src)) continue;
      p[k] = this.eval(src, { index: 0, time: time || 0, count: 1 });
      if (k === 'rotation' || k === 'rotateZ') p.rot = (finiteNumber(p.rotation, 0) + finiteNumber(p.rotateZ, 0)) * Math.PI / 180;
    }
    return p;
  },

  // VECTOR bindings overlaid PER INSTANCE onto resolved 2D transforms {x,y,scale,rot}.
  applyVector(p, out, time) {
    const b = p && p._bindings; if (!b || !Array.isArray(out)) return out;
    const keys = Object.keys(b).filter(k => b[k] && this.isVector(b[k])); if (!keys.length) return out;
    const n = out.length;
    for (let i = 0; i < n; i++) { const inst = out[i]; if (!inst) continue;
      const ctx = { index: i, count: n, time: time || 0, u: inst.x, v: inst.y };
      for (const k of keys) { const val = this.eval(b[k], ctx);
        if (k === 'rotation' || k === 'rotateZ') inst.rot = val * Math.PI / 180;
        else if (k === 'scale' || k === 'size') inst.scale = val;
        else if (k === 'x') inst.x = val;
        else if (k === 'y') inst.y = val;
        else inst[k] = val;
      }
    }
    return out;
  },

  // PER-CELL/INSTANCE 2D overrides applied LAST (override > source > base).
  applyOverrides(p, out) {
    const ov = p && p._overrides; if (!ov || !Array.isArray(out)) return out;
    for (const key in ov) { const idx = parseInt(key, 10); if (!(idx >= 0) || idx >= out.length) continue;
      const o = ov[key] || {}, inst = out[idx]; if (!inst) continue;
      for (const k in o) { const val = o[k];
        if (k === 'rotation' || k === 'rotateZ') inst.rot = finiteNumber(val, 0) * Math.PI / 180;
        else if (k === 'scale' || k === 'size') inst.scale = finiteNumber(val, inst.scale);
        else if (k === 'x') inst.x = finiteNumber(val, inst.x);
        else if (k === 'y') inst.y = finiteNumber(val, inst.y);
        else inst[k] = val;
      }
    }
    return out;
  },

  // ── 3D helper ─────────────────────────────────────────────────────────────
  // Resolve the per-instance transform deltas for a 3D clone at index `i`.
  // Returns { rx,ry,rz (radians), scale|null, x,y,z (abs override|null) } from
  // bindings (vector) + overrides. cols/rows/layers let expressions use grid
  // coords. Scalar bindings should be folded into `params` by the caller first.
  resolve3D(p, i, count, time, dims) {
    const r = { rx: null, ry: null, rz: null, scale: null, x: null, y: null, z: null, has: false };
    const deg = Math.PI / 180;
    const ctx = { index: i, count: count, time: time || 0, u: 0, v: 0,
      cols: (dims && dims.cols) || 1, rows: (dims && dims.rows) || 1 };
    const put = (k, val) => {
      if (k === 'rotateX') { r.rx = val * deg; r.has = true; }
      else if (k === 'rotateY') { r.ry = val * deg; r.has = true; }
      else if (k === 'rotateZ' || k === 'rotation') { r.rz = val * deg; r.has = true; }
      else if (k === 'scale' || k === 'size') { r.scale = val; r.has = true; }
      else if (k === 'x') { r.x = val; r.has = true; }
      else if (k === 'y') { r.y = val; r.has = true; }
      else if (k === 'z') { r.z = val; r.has = true; }
    };
    const b = p && p._bindings;
    if (b) for (const k in b) { if (b[k] && this.isVector(b[k])) put(k, this.eval(b[k], ctx)); }
    const ov = p && p._overrides && p._overrides[String(i)];
    if (ov) for (const k in ov) put(k, finiteNumber(ov[k], 0));
    return r;
  },
};
