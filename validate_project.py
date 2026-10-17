"""Offline project sanity checks run by Render during the build step."""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INDEX = ROOT / "index.html"
SERVER = ROOT / "server.py"
RENDER = ROOT / "render.yaml"


class MarkupAudit(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: set[str] = set()
        self.scripts: list[dict[str, str]] = []
        self._current_script: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        if "id" in values:
            self.ids.add(values["id"])
        if tag == "script":
            self._current_script = {"type": values.get("type", "classic"), "text": ""}
            self.scripts.append(self._current_script)

    def handle_data(self, data: str) -> None:
        if self._current_script is not None:
            self._current_script["text"] += data

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self._current_script = None


def fail(message: str) -> None:
    raise SystemExit(f"Project validation failed: {message}")


def main() -> None:
    for required in (INDEX, SERVER, RENDER):
        if not required.is_file():
            fail(f"missing {required.name}")

    html = INDEX.read_text(encoding="utf-8")
    audit = MarkupAudit()
    audit.feed(html)
    audit.close()

    for element_id in ("game", "start-button", "speed", "drift-angle", "minimap", "camera-name"):
        if element_id not in audit.ids:
            fail(f"missing game UI element #{element_id}")

    importmaps = [script for script in audit.scripts if script["type"] == "importmap"]
    if len(importmaps) != 1:
        fail("expected exactly one browser import map")
    try:
        mapping = json.loads(importmaps[0]["text"])
    except json.JSONDecodeError as exc:
        fail(f"invalid import map JSON: {exc}")
    imports = mapping.get("imports", {})
    if "three" not in imports or "three/addons/" not in imports:
        fail("Three.js core and addon aliases must both be mapped")

    for feature in (
        "UnrealBloomPass", "ACESFilmicToneMapping", "FogExp2", "MeshPhysicalMaterial",
        "function updateSimulation(dt)", "lateralGrip", "yawRate", "handbrake",
        "bodyRoll", "wheelGroups", "function collide()",
    ):
        if feature not in html:
            fail(f"expected graphics/physics feature not found: {feature}")

    if re.search(r"from\s+['\"]https://cdn\.jsdelivr\.net/npm/three@0\.180\.0/examples/jsm/", html):
        fail("addon imports should use the import-map alias to resolve Three.js correctly")

    server = SERVER.read_text(encoding="utf-8")
    if 'os.environ.get("PORT", "8000")' not in server or '"0.0.0.0"' not in server:
        fail("server must bind Render's PORT on 0.0.0.0")
    if "/healthz" not in server:
        fail("server must expose /healthz for Render health checks")

    render = RENDER.read_text(encoding="utf-8")
    for marker in ("runtime: python", "startCommand: python server.py", "healthCheckPath: /healthz"):
        if marker not in render:
            fail(f"Render configuration missing {marker!r}")

    module_count = sum(script["type"] == "module" for script in audit.scripts)
    if module_count != 1:
        fail(f"expected exactly one JavaScript module, found {module_count}")

    print("NEON DRIFT project checks passed: Render config, health endpoint, import map, HUD, rendering and physics markers.")


if __name__ == "__main__":
    main()
