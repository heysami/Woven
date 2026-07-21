/* Woven share worker.
 *
 * Sits on *.getwoven.design/s/* (and /__global_fonts/*) in FRONT of the
 * per-install Cloudflare tunnels. Serving rules, in order:
 *
 *   /s/<token>/live*        -> ALWAYS the tunnel (live editor / multiplayer -
 *                              inherently dynamic, never snapshotted)
 *   /s/<token>/api/meta     -> snapshot copy when hosted (keeps the viewer
 *                              booting with the daemon offline), else tunnel
 *   /s/<token>/api/*        -> tunnel (comments stay live while the owner's
 *                              daemon is up); graceful JSON fallbacks when the
 *                              tunnel is down so the viewer degrades quietly
 *   /s/<token>/<anything>   -> R2 object s/<token>/<anything> when the share
 *                              is hosted; tunnel passthrough when it is not
 *   /__global_fonts/<name>  -> R2 object fonts/<install>/<name> (install =
 *                              request subdomain), else tunnel
 *
 * "Hosted" is defined by the marker object s/<token>/__hosted.json, written
 * as part of every snapshot upload. When the marker exists, static misses are
 * real 404s (the snapshot is the whole truth); when it doesn't, everything
 * falls through to the tunnel and the worker is invisible.
 */

const TOKEN_RE = /^\/s\/([a-f0-9]{24,64})(\/.*)?$/;
const INSTALL_RE = /^[a-f0-9]{32}$/;
const FONT_NAME_RE = /^[A-Za-z0-9._-]+$/;

const TEXTISH = /\.(html?|css|js|mjs|json|svg|txt|md|xml)$/i;

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname.startsWith("/__global_fonts/")) {
      return serveFont(request, env, url);
    }

    const m = TOKEN_RE.exec(url.pathname);
    if (!m) return passthrough(request);
    const token = m[1];
    let sub = m[2];

    // /s/<token> without the trailing slash -> canonicalise (the gate 301s too).
    if (sub === undefined || sub === "") {
      url.pathname = "/s/" + token + "/";
      return Response.redirect(url.toString(), 301);
    }

    // Live editor / multiplayer session - never static.
    if (sub === "/live" || sub.startsWith("/live/")) return passthrough(request);

    if (sub.startsWith("/api/")) return serveApi(request, env, token, sub);

    // Static snapshot space. Only GET/HEAD can be static; anything else needs
    // the daemon.
    if (request.method !== "GET" && request.method !== "HEAD") {
      return passthrough(request);
    }
    return serveStatic(request, env, token, sub);
  },
};

function passthrough(request) {
  return fetch(request);
}

/* Tunnel-down detection: fetch() to an origin whose tunnel is offline yields
 * a Cloudflare 52x/530 error page (or throws). */
async function tryOrigin(request) {
  try {
    const r = await fetch(request);
    if (r.status >= 520 && r.status <= 530) return null;
    return r;
  } catch {
    return null;
  }
}

function json(status, obj) {
  return new Response(JSON.stringify(obj), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });
}

function objectResponse(request, obj, key) {
  const etag = obj.httpEtag;
  if (etag && request.headers.get("If-None-Match") === etag) {
    return new Response(null, { status: 304, headers: { ETag: etag } });
  }
  const headers = new Headers();
  obj.writeHttpMetadata(headers);
  if (!headers.get("Content-Type")) headers.set("Content-Type", "application/octet-stream");
  if (etag) headers.set("ETag", etag);
  // Snapshots update in place: keep text revalidating, let media cache briefly.
  headers.set("Cache-Control", TEXTISH.test(key) ? "no-cache" : "max-age=3600");
  const body = request.method === "HEAD" ? null : obj.body;
  return new Response(body, { status: 200, headers });
}

async function isHosted(env, token) {
  const marker = await env.SHARES.head("s/" + token + "/__hosted.json");
  return marker !== null;
}

async function serveStatic(request, env, token, sub) {
  const rel = decodeURIComponent(sub).replace(/^\/+/, "");
  if (rel.split("/").includes("..")) return json(404, { error: "not found" });

  let key = "s/" + token + "/" + (rel === "" || rel.endsWith("/") ? rel + "index.html" : rel);
  let obj = await env.SHARES.get(key);
  if (obj === null && !rel.endsWith("/") && !/\.[A-Za-z0-9]+$/.test(rel)) {
    // Extensionless path that is really a directory (gate behavior: dir -> index.html).
    key = "s/" + token + "/" + rel + "/index.html";
    obj = await env.SHARES.get(key);
  }
  if (obj !== null) return objectResponse(request, obj, key);

  // Miss: hosted shares own their URL space (404); unhosted fall through.
  if (await isHosted(env, token)) return json(404, { error: "not found" });
  return passthrough(request);
}

async function serveApi(request, env, token, sub) {
  // Meta boots the viewer - prefer the snapshot copy so a hosted share renders
  // with the owner's machine off, and stays CONSISTENT with the static files
  // being served (the tunnel's live meta may describe newer source).
  if (sub === "/api/meta" && (request.method === "GET" || request.method === "HEAD")) {
    const obj = await env.SHARES.get("s/" + token + "/api/meta");
    if (obj !== null) return objectResponse(request, obj, "api/meta.json");
    return passthrough(request);
  }

  // Everything else under /api/ (comments CRUD, shots, attachments) is live.
  const r = await tryOrigin(request);
  if (r !== null) return r;

  // Owner offline. Only degrade for hosted shares - an unhosted share with a
  // dead tunnel should look dead, exactly as it does today.
  if (!(await isHosted(env, token))) return json(530, { error: "share offline" });
  if ((request.method === "GET" || request.method === "HEAD") && sub === "/api/links") {
    // Sibling-share links (the viewer's prototype/branch hop dropdowns):
    // baked at upload and re-pushed by the owner's daemon on every registry
    // change, so this is current as of the owner's last online moment. A
    // miss (pre-links snapshot) must NOT answer an empty list - an error
    // makes the viewer keep the copy baked into its meta instead.
    const obj = await env.SHARES.get("s/" + token + "/api/links");
    if (obj !== null) return objectResponse(request, obj, "api/links.json");
    return json(503, { error: "links unavailable while the share owner is offline" });
  }
  if (request.method === "GET" && sub === "/api/comments") {
    // The stored copy of the discussion: baked into the snapshot at upload
    // and re-pushed by the daemon on every change, so it is CURRENT as of the
    // last moment the owner was online - not the upload date.
    const obj = await env.SHARES.get("s/" + token + "/api/comments");
    if (obj !== null) return objectResponse(request, obj, "api/comments.json");
    return json(200, { comments: [], hostedOffline: true });
  }
  // Comment screenshots + attachments captured in the snapshot.
  if ((request.method === "GET" || request.method === "HEAD")
      && /^\/api\/comments\/[cr]-[a-f0-9]{8,16}\/(shot|attach\/a-[a-f0-9]{8,16})$/.test(sub)) {
    const obj = await env.SHARES.get("s/" + token + sub);
    if (obj !== null) {
      return objectResponse(request, obj, sub.endsWith("/shot") ? "shot.jpg" : "attach.bin");
    }
    return json(404, { error: "not available while the share owner is offline" });
  }
  // New comments queue at the broker's inbox; the owner's daemon collects
  // them when it comes back online. Everything else under /api/ (replies,
  // status flips, shots, attachments) genuinely needs the daemon.
  if (request.method === "POST" && sub === "/api/comments") {
    return queueComment(request, env, token);
  }
  return json(503, {
    error: "This action is unavailable right now - the share owner is offline. The prototype itself keeps working.",
  });
}

async function queueComment(request, env, token) {
  let comment;
  try {
    comment = await request.json();
  } catch {
    return json(400, { error: "invalid comment body" });
  }
  try {
    const r = await fetch(env.BROKER_URL.replace(/\/+$/, "") + "/shares/inbox", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, comment }),
    });
    const j = await r.json().catch(() => ({}));
    if (r.ok && j.ok) {
      return json(200, { ok: true, queued: true, comment: j.comment });
    }
    return json(r.status === 429 ? 429 : 503, {
      error: j.detail || j.error || "could not save the comment right now - please try again later",
    });
  } catch {
    return json(503, {
      error: "could not save the comment right now - please try again later",
    });
  }
}

async function serveFont(request, env, url) {
  const name = url.pathname.slice("/__global_fonts/".length);
  const install = url.hostname.split(".")[0];
  if (FONT_NAME_RE.test(name) && INSTALL_RE.test(install)) {
    const key = "fonts/" + install + "/" + name;
    const obj = await env.SHARES.get(key);
    if (obj !== null) return objectResponse(request, obj, key);
  }
  return passthrough(request);
}
