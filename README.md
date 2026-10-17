# NEON DRIFT — City Run

A playable browser-based 3D drift/driving game with a procedural city, metallic sports coupe, detailed cockpit, chase camera, drift scoring, synthesized engine/tire audio, ACES color grading, shadows, fog, bloom and keyboard/touch controls.

## Deploy to Render (Python web service)

1. Extract this project and push the **contents** of `neon_drift_city/` to the root of a GitHub/GitLab repository. Keep `render.yaml`, `server.py`, `validate_project.py`, and `index.html` together.
2. In Render, choose **New + → Blueprint**, connect that repository, and deploy the blueprint.
3. Render reads `render.yaml`, runs the offline project checks, starts `python server.py`, and checks `https://YOUR-SERVICE.onrender.com/healthz`.
4. Open the service's public `onrender.com` URL. The Three.js engine loads from jsDelivr, so the visitor's browser needs internet access.

The Python server reads Render's assigned `PORT` environment variable and binds to `0.0.0.0`. No Python packages are required. All 3D rendering, controls, sound, and driving physics run in the user's browser; this is a single-player web game, not a multiplayer/server-authoritative simulator.

## Run locally

From this directory:

```bash
python3 server.py
```

Then open <http://localhost:8000>. To test Render-style port binding locally:

```bash
PORT=10000 python3 server.py
```

The health endpoint is <http://localhost:8000/healthz>. The same project audit that Render runs can be executed with:

```bash
python3 validate_project.py
```

Run the HTTP server integration tests and, with Node.js installed, the physics/collision smoke test against the actual game update code:

```bash
python3 -m unittest discover -s tests
node tests/physics_smoke.cjs
```

## Controls

- **W / Up Arrow** — accelerate
- **S / Down Arrow** — brake / reverse
- **A / Left Arrow**, **D / Right Arrow** — steer
- **Space** — handbrake / drift
- **Shift** — boost while accelerating
- **C** — switch between chase and cockpit cameras
- **R** — reset the car
- **F** — toggle fullscreen

Touchscreen devices have on-screen driving controls.

## Graphics and simulation notes

- High-resolution generated asphalt/concrete/facade canvas textures; metallic/clear-coated car paint; modeled wheels, rims, brake detail, cabin, dashboard, gauges and steering wheel.
- Instanced road markings, trees and street lights help keep the city renderable in a browser.
- ACES filmic tone mapping, environment reflections, a moving directional shadow camera, atmospheric fog and restrained bloom.
- The driving model uses longitudinal/lateral velocity components, progressive acceleration, braking before reverse, drag, handbrake-reduced rear grip, speed-limited yaw response, collision response, body roll/pitch, wheel spin and visible suspension movement. It is tuned for an enjoyable drift game and is not a professional vehicle dynamics model.

The visuals are procedural real-time 3D graphics rather than pre-rendered photorealistic assets. Appearance and frame rate depend on the GPU/browser. Render serves the game; it does not provide GPU rendering—the player's browser performs the graphics work.
