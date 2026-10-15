"""Phone door: a tiny web receiver the iPhone Shortcut talks to.

POST /ask   {"text": "..."}  -> {"reply": "..."}     (same Claude thread as the Mac window)
GET  /health                 -> {"ok": true}
Every request must carry the shared token (header X-Token or JSON field "token").
"""
from __future__ import annotations

import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import settings as S
import tts
from brain import Brain

brain = Brain()


def token() -> str:
    try:
        t = S.RECEIVER_TOKEN_FILE.read_text().strip()
        if t:
            return t
    except OSError:
        pass
    t = secrets.token_urlsafe(18)
    S.RECEIVER_TOKEN_FILE.write_text(t)
    S.RECEIVER_TOKEN_FILE.chmod(0o600)
    return t


TOKEN = token()


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send(200, {"ok": True})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/ask":
            self._send(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
        except ValueError:
            self._send(400, {"error": "bad json"})
            return
        if (self.headers.get("X-Token") or data.get("token")) != TOKEN:
            self._send(403, {"error": "wrong token"})
            return
        text = (data.get("text") or "").strip()
        if not text:
            self._send(400, {"error": "empty"})
            return
        reply = brain.ask(text)
        self._send(200, {"reply": tts.speakable(reply), "full": reply})

    def log_message(self, fmt, *args) -> None:  # quiet
        pass


def main() -> None:
    srv = ThreadingHTTPServer((S.RECEIVER_HOST, S.RECEIVER_PORT), Handler)
    print(f"Claude Voice receiver on {S.RECEIVER_HOST}:{S.RECEIVER_PORT}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
