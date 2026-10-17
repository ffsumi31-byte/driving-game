# NEON DRIFT — City Run

A playable browser-based 3D drift/driving game with a dense procedural city, physically shaded facade and road textures, a metallic sports coupe, a driver-eye cockpit camera, drifting tire smoke, garage UI, six paint finishes, handling presets, graphics/audio/atmosphere settings, drift scoring, synthesized engine/tire audio, ACES color grading, atmospheric sky, shadows, fog, bloom and keyboard/touch controls.

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

## In-game garage and settings

After starting the engine, use the **Garage**, **Settings**, and **1st Person** buttons at the upper-left HUD. The garage changes the actual car paint across six finishes and switches Street/Sport/Drift handling modes. Settings apply graphics presets (FPS/Balanced/Ultra), bloom, atmospheric depth, camera movement and audio volume without reloading. Use **C** or **V** to switch the chase and driver-eye cockpit cameras; **Esc** or **M** pauses and opens the menu. The cockpit camera sits on the driver side and looks through the windshield at the road, with the dashboard, steering wheel, gauges and cabin geometry in view.

## Controls

- **W / Up Arrow** — accelerate
- **S / Down Arrow** — brake / reverse
- **A / Left Arrow**, **D / Right Arrow** — steer
- **Space** — handbrake / drift
- **Shift** — boost while accelerating
- **C / V** — switch between chase and first-person cockpit cameras
- **R** — reset the car
- **F** — toggle fullscreen
- **Esc / M** — pause and open the garage/settings menu

Touchscreen devices have on-screen driving controls.

## Graphics and simulation notes

- 1024px procedural asphalt and 512px facade/story textures include reflective windows, occupied warm office lights, concrete joints, micro-grain, height/bump detail and variable roughness.
- Neon storefront signs, lobby glazing, canopies, taller downtown blocks, varied roof equipment, trees, street lamps and parking cars break up the street grid. Repeated road markings, lamps and foliage are instanced where practical.
- Metallic/clear-coated car paint, hood stripes, side blades, vents, modeled wheels/rims/brakes, cabin, dashboard, gauges and a driver-eye camera.
- Twilight sky scattering, warm low-angle sun, cool fill lighting, environment reflections, moving directional shadows, distance haze, ACES filmic tone mapping and adjustable bloom.
- GPU-friendly point-sprite tire smoke emits while the rear tyres slide; quality presets adjust render resolution, shadows and bloom.
- The driving model uses longitudinal/lateral velocity components, progressive acceleration, braking before reverse, drag, handbrake-reduced rear grip, speed-limited yaw response, collision response, body roll/pitch, wheel spin and visible suspension movement. It is tuned for an enjoyable drift game and is not a professional vehicle dynamics model.

The visuals are procedural real-time 3D graphics rather than pre-rendered photorealistic assets. The generated shaders and textures are designed to look detailed rather than pixel-art, but they are not scanned commercial texture assets. Render serves the website; the player's browser performs the GPU rendering, so appearance and frame rate depend on the device.
