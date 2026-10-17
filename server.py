"""Small, dependency-free HTTP server for the NEON DRIFT browser game.

Render injects PORT at runtime. The server listens on 0.0.0.0 so Render's
reverse proxy can reach it. All vehicle physics and rendering run in-browser.
"""
from __future__ import annotations

import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent


class GameRequestHandler(SimpleHTTPRequestHandler):
    server_version = "NeonDrift/1.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _send_health(self, include_body: bool = True) -> None:
        payload = b"ok\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if include_body:
            self.wfile.write(payload)

    def do_GET(self) -> None:
        if urlsplit(self.path).path == "/healthz":
            self._send_health()
            return
        super().do_GET()

    def do_HEAD(self) -> None:
        if urlsplit(self.path).path == "/healthz":
            self._send_health(include_body=False)
            return
        super().do_HEAD()

    def end_headers(self) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Permissions-Policy", "fullscreen=(self), autoplay=(self)")
        # Always revalidate the entry page so a deployment's latest game version loads.
        if urlsplit(self.path).path in ("/", "/index.html"):
            self.send_header("Cache-Control", "no-cache, must-revalidate")
        super().end_headers()


def main() -> None:
    raw_port = os.environ.get("PORT", "8000")
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise SystemExit(f"Invalid PORT value: {raw_port!r}") from exc
    if not 1 <= port <= 65535:
        raise SystemExit(f"PORT must be between 1 and 65535, got {port}")

    class Server(ThreadingHTTPServer):
        allow_reuse_address = True
        daemon_threads = True

    address = ("0.0.0.0", port)
    with Server(address, GameRequestHandler) as httpd:
        print(f"NEON DRIFT serving {ROOT} on http://{address[0]}:{port}", flush=True)
        try:
            httpd.serve_forever(poll_interval=0.4)
        except KeyboardInterrupt:
            print("\nNEON DRIFT server stopped.", flush=True)


if __name__ == "__main__":
    main()
