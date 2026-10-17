"""Integration tests for the dependency-free Render server."""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class RenderServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.port = free_port()
        env = os.environ.copy()
        env["PORT"] = str(cls.port)
        cls.process = subprocess.Popen(
            [sys.executable, str(ROOT / "server.py")],
            cwd=ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cls.base = f"http://127.0.0.1:{cls.port}"
        deadline = time.monotonic() + 6
        while time.monotonic() < deadline:
            if cls.process.poll() is not None:
                raise RuntimeError("server.py exited before becoming ready")
            try:
                with urllib.request.urlopen(cls.base + "/healthz", timeout=0.3) as response:
                    if response.status == 200:
                        return
            except Exception:
                time.sleep(0.08)
        cls.process.terminate()
        raise RuntimeError("server.py did not become ready")

    @classmethod
    def tearDownClass(cls) -> None:
        cls.process.terminate()
        try:
            cls.process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            cls.process.kill()
            cls.process.wait(timeout=2)

    def test_health_endpoint(self) -> None:
        with urllib.request.urlopen(self.base + "/healthz") as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), b"ok\n")
            self.assertIn("no-store", response.headers.get("Cache-Control", ""))

    def test_head_health_endpoint(self) -> None:
        request = urllib.request.Request(self.base + "/healthz", method="HEAD")
        with urllib.request.urlopen(request) as response:
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), b"")

    def test_game_entrypoint(self) -> None:
        with urllib.request.urlopen(self.base + "/") as response:
            self.assertEqual(response.status, 200)
            self.assertIn(b"NEON DRIFT", response.read())

    def test_index_alias(self) -> None:
        with urllib.request.urlopen(self.base + "/index.html") as response:
            self.assertEqual(response.status, 200)
            self.assertIn("no-cache", response.headers.get("Cache-Control", ""))

    def test_unknown_asset_is_404(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(self.base + "/missing-asset.fake", timeout=2)
        self.assertEqual(caught.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
