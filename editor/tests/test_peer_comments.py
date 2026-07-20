"""Contract test - peer comment sync (comments connect WITHOUT git).

Background: review comments used to reach a teammate only via commit → push →
pull, so the discussion fragmented per machine (and a raw-git branch switch
could roll it back). Peer sync fixes that: each daemon pulls every registered
contributor gate's /api/comments (share/links.json says where they live) and
unions the payload into the local store. Deletions travel as tombstones in
comments.json's `deleted` list, so a removed comment never resurrects from a
stale peer copy.

Pins: peer union (add / reply-union / local-edit-wins / idempotence),
tombstone behaviour on delete + git-merge union, and an end-to-end
peer_pull_comments over a real HTTP server serving a gate-shaped payload.

Run: `python3 editor/tests/test_peer_comments.py` (no pytest required).
Exit 0 on pass, non-zero on any failure.
"""
import http.server
import json
import os
import shutil
import sys
import tempfile
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shares   # noqa: E402


def comment(cid, ts, text="hi", replies=None, status="open"):
    return {"id": cid, "prototype": "main", "page": "index.html", "text": text,
            "createdAt": ts, "status": status, "replies": replies or [],
            "attachments": [], "shot": "", "author": {"name": "t", "email": ""}}


def write_store(root, comments, deleted=None):
    os.makedirs(os.path.join(root, "share"), exist_ok=True)
    with open(os.path.join(root, "share", "comments.json"), "w") as f:
        json.dump({"comments": comments, "deleted": deleted or []}, f)


def ids(root):
    return sorted(c["id"] for c in shares.comments_load(root)["comments"])


def test_union():
    root = tempfile.mkdtemp(prefix="peer-union-")
    try:
        write_store(root, [comment("c-aaaaaaaaaa", "2026-07-01T00:00:00")])

        # a new peer comment appends
        changed, new_ids = shares.comments_peer_union(root, {
            "comments": [comment("c-bbbbbbbbbb", "2026-07-02T00:00:00")]})
        assert changed and new_ids == ["c-bbbbbbbbbb"]
        assert ids(root) == ["c-aaaaaaaaaa", "c-bbbbbbbbbb"]

        # pulling the same payload again is a no-op
        changed, new_ids = shares.comments_peer_union(root, {
            "comments": [comment("c-bbbbbbbbbb", "2026-07-02T00:00:00")]})
        assert not changed and new_ids == [], "idempotent"

        # replies union by id; the local copy's own fields win
        local = shares.comments_load(root)
        local["comments"][0]["text"] = "edited locally"
        local["comments"][0]["replies"] = [{"id": "r-1111111111", "text": "mine",
                                            "createdAt": "2026-07-03T00:00:00"}]
        shares._comments_save(root, local)
        changed, _ = shares.comments_peer_union(root, {
            "comments": [comment("c-aaaaaaaaaa", "2026-07-01T00:00:00", text="peer text",
                                 replies=[{"id": "r-2222222222", "text": "theirs",
                                           "createdAt": "2026-07-04T00:00:00"}])]})
        assert changed
        c = next(c for c in shares.comments_load(root)["comments"]
                 if c["id"] == "c-aaaaaaaaaa")
        assert c["text"] == "edited locally", "local edit wins"
        assert sorted(r["id"] for r in c["replies"]) == ["r-1111111111", "r-2222222222"], \
            "replies union"

        # a peer tombstone removes the local copy and sticks
        changed, _ = shares.comments_peer_union(root, {
            "comments": [], "deleted": [{"id": "c-bbbbbbbbbb", "at": "2026-07-05T00:00:00"}]})
        assert changed and ids(root) == ["c-aaaaaaaaaa"], "peer deletion applies"
        changed, new_ids = shares.comments_peer_union(root, {
            "comments": [comment("c-bbbbbbbbbb", "2026-07-02T00:00:00")]})
        assert not changed and new_ids == [], "tombstoned comment never re-imports"

        # garbage payloads never raise, never change anything
        for bad in (None, [], {"comments": "x"}, {"comments": [{"id": "zzz"}]}):
            changed, new_ids = shares.comments_peer_union(root, bad)
            assert not changed and new_ids == []
    finally:
        shutil.rmtree(root)


def test_tombstones():
    root = tempfile.mkdtemp(prefix="peer-tombs-")
    try:
        write_store(root, [comment("c-aaaaaaaaaa", "2026-07-01T00:00:00"),
                           comment("c-bbbbbbbbbb", "2026-07-02T00:00:00")])
        # deleting records a tombstone
        assert shares.comment_delete(root, "c-bbbbbbbbbb")
        data = shares.comments_load(root)
        assert [t["id"] for t in data["deleted"]] == ["c-bbbbbbbbbb"]

        # the git 3-way merge unions tombstones and applies them: a side that
        # still carries the deleted comment (stale copy) loses it
        merged = shares.comments_merge_texts(
            "", json.dumps(data),
            json.dumps({"comments": [comment("c-bbbbbbbbbb", "2026-07-02T00:00:00"),
                                     comment("c-cccccccccc", "2026-07-03T00:00:00")]}))
        got = sorted(c["id"] for c in merged["comments"])
        assert got == ["c-aaaaaaaaaa", "c-cccccccccc"], \
            "tombstone beats stale copy in git merge, got %r" % got
        assert [t["id"] for t in merged["deleted"]] == ["c-bbbbbbbbbb"]
    finally:
        shutil.rmtree(root)


class _GateStub(http.server.BaseHTTPRequestHandler):
    payload = {}

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.endswith("/api/comments"):
            body = json.dumps(self.payload).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif "/shot" in self.path:
            self.send_response(200)
            self.send_header("Content-Length", "3")
            self.end_headers()
            self.wfile.write(b"JPG")
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.end_headers()


def test_pull_http():
    root = tempfile.mkdtemp(prefix="peer-pull-")
    srv = http.server.HTTPServer(("127.0.0.1", 0), _GateStub)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        write_store(root, [])
        pc = comment("c-dddddddddd", "2026-07-06T00:00:00")
        pc["shot"] = "c-dddddddddd.jpg"
        _GateStub.payload = {"comments": [pc], "deleted": []}
        base = "http://127.0.0.1:%d/s/%s/" % (srv.server_port, "f" * 32)
        assert shares.peer_pull_comments(root, base), "pull imports the comment"
        assert ids(root) == ["c-dddddddddd"]
        shot = shares.comment_shot_abspath(root, "c-dddddddddd")
        assert os.path.isfile(shot), "missing screenshot fetched from the peer"
        assert not shares.peer_pull_comments(root, base), "second pull is a no-op"
        # a non-loopback plain-http URL is refused outright
        assert shares.peer_pull_comments(root, "http://evil.example/s/x/") is False
    finally:
        srv.shutdown()
        shutil.rmtree(root)


def main():
    test_union()
    test_tombstones()
    test_pull_http()
    print("test_peer_comments: ALL PASS")


if __name__ == "__main__":
    main()
