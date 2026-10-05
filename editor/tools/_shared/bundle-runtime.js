// Export local ESM dependencies as data URLs, preserving the import graph.
// A failed dependency aborts the bake instead of producing a partial artifact.
export async function bundleRuntime(entryUrls, fetcher = fetch) {
  const cache = new Map();
  async function module(url) {
    if (cache.has(url)) return cache.get(url);
    const pending = (async () => {
      const response = await fetcher(url);
      if (!response.ok) throw new Error('Runtime dependency HTTP ' + response.status + ': ' + url);
      let source = await response.text();
      const refs = [...source.matchAll(/^\s*(?:import\s+(?:[^'"\n]+?\s+from\s*)?|export\s+[^'"\n]+?\s+from\s*)['"](\.\.?\/[^'"]+)['"]/gm)];
      for (const ref of refs) {
        const target = await module(new URL(ref[1], url).href);
        source = source.replace(ref[0], ref[0].replace(ref[1], target));
      }
      const bytes = new TextEncoder().encode(source);
      let binary = '';
      for (let i = 0; i < bytes.length; i += 8192) binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
      return 'data:text/javascript;base64,' + btoa(binary);
    })();
    cache.set(url, pending);
    return pending;
  }
  return Object.fromEntries(await Promise.all(Object.entries(entryUrls).map(async ([key, url]) => [key, await module(url)])));
}

export async function bundleLocalMedia(value, base, fetcher = fetch) {
  const cache = new Map(), origin = new URL(base).origin;
  async function dataUrl(path, parent = base, ancestors = []) {
    const url = new URL(path, parent);
    if (url.origin !== origin || url.protocol === 'data:' || url.protocol === 'blob:') return path;
    const project = new URL(parent).searchParams.get('project');
    if (project && !url.searchParams.has('project')) url.searchParams.set('project', project);
    if (ancestors.includes(url.href)) throw new Error('Cyclic export asset dependency: ' + url.href);
    if (!cache.has(url.href)) cache.set(url.href, (async () => {
      const response = await fetcher(url.href);
      if (!response.ok) throw new Error('Export asset HTTP ' + response.status + ': ' + path);
      const type = response.headers.get('content-type') || 'application/octet-stream';
      let bytes = new Uint8Array(await response.arrayBuffer());
      const next = [...ancestors, url.href];
      async function css(text) {
        for (const match of [...text.matchAll(/url\(\s*['"]?([^'"\s)]+)['"]?\s*\)/g)]) {
          if (match[1].startsWith('#')) continue;
          const asset = await dataUrl(match[1], url.href, next);
          text = text.replace(match[0], () => 'url("' + asset + '")');
        }
        return text;
      }
      if (type.startsWith('text/html')) {
        const doc = new DOMParser().parseFromString(new TextDecoder().decode(bytes), 'text/html');
        for (const element of doc.querySelectorAll('script[src],img[src],video[src],audio[src],source[src],link[rel="stylesheet"][href]')) {
          const attr = element.tagName === 'LINK' ? 'href' : 'src';
          const src = element.getAttribute(attr);
          if (element.tagName === 'SCRIPT' && element.type === 'module') {
            const modules = await bundleRuntime({entry:new URL(src, url.href).href}, fetcher);
            element.setAttribute(attr, modules.entry);
          } else element.setAttribute(attr, await dataUrl(src, url.href, next));
        }
        for (const style of doc.querySelectorAll('style')) style.textContent = await css(style.textContent);
        for (const element of doc.querySelectorAll('[style]')) element.setAttribute('style', await css(element.getAttribute('style')));
        bytes = new TextEncoder().encode('<!doctype html>' + doc.documentElement.outerHTML);
      } else if (type.startsWith('text/css')) {
        bytes = new TextEncoder().encode(await css(new TextDecoder().decode(bytes)));
      }
      let binary = '';
      for (let i = 0; i < bytes.length; i += 8192) binary += String.fromCharCode(...bytes.subarray(i, i + 8192));
      return 'data:' + type + ';base64,' + btoa(binary);
    })());
    return cache.get(url.href);
  }
  async function walk(v) {
    if (Array.isArray(v)) return Promise.all(v.map(walk));
    if (!v || typeof v !== 'object') return v;
    const out = {};
    for (const [key, item] of Object.entries(v)) {
      out[key] = (['_assetUrl', '_imageUrl'].includes(key) || key === 'url' && typeof v.kind === 'string') && typeof item === 'string' && item
        ? await dataUrl(item) : await walk(item);
    }
    return out;
  }
  return walk(value);
}
