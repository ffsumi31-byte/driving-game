// Smoke-test the actual updateSimulation/collide functions embedded in index.html.
// Uses lightweight mocks for Three.js meshes and UI nodes; no dependencies required.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const html = fs.readFileSync(path.join(__dirname, '..', 'index.html'), 'utf8');
const moduleMatch = html.match(/<script type="module">([\s\S]*?)<\/script>/);
assert(moduleMatch, 'could not find the game module script');
const moduleSource = moduleMatch[1];
const updateStart = moduleSource.indexOf('function updateSimulation(dt){');
const updateEnd = moduleSource.indexOf('function animate(now){', updateStart);
assert(updateStart >= 0 && updateEnd > updateStart, 'could not isolate updateSimulation');
const updateSource = moduleSource.slice(updateStart, updateEnd).trim();
const collisionStart = moduleSource.indexOf('function collide(){');
const collisionEnd = moduleSource.indexOf('// Engine / tire audio synthesized', collisionStart);
assert(collisionStart >= 0 && collisionEnd > collisionStart, 'could not isolate collide');
const collisionSource = moduleSource.slice(collisionStart, collisionEnd).trim();

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const damp = (a, b, lambda, dt) => lerp(a, b, 1 - Math.exp(-lambda * dt));
const keys = new Set();
Object.assign(globalThis, {
  keys, clamp, damp,
  pressed: (...codes) => codes.some(k => keys.has(k)),
  simTime: 0, yaw: 0, velX: 0, velZ: 0, steer: 0,
  throttle: 0, braking: false, handbrake: false, boost: false, started: true,
  bodyRoll: 0, bodyPitch: 0, driftScore: 0, driftCombo: 1, driftTimer: 0,
  totalDistance: 0, topSpeed: 0,
  vehicle: { position: { x: 0, z: 0 }, rotation: { y: 0 } },
  body: { rotation: { x: 0, z: 0 }, position: { y: 0 } },
  wheelGroups: Array.from({ length: 4 }, (_, i) => ({
    pivot: { rotation: { x: 0, y: 0 }, position: { y: 0.39 } },
    front: i < 2, baseY: 0.39, phase: i * 0.7, side: i % 2 ? 1 : -1,
    axle: i < 2 ? -1.36 : 1.36,
  })),
  steeringWheel: { rotation: { z: 0 } },
  gaugeNeedles: [{ rotation: { z: 0 } }, { rotation: { z: 0 } }],
  headlights: [{ intensity: 0 }, { intensity: 0 }],
  tailLights: [{ intensity: 0 }, { intensity: 0 }],
  collidersExpanded: [], updateAudio: () => {}, updateDriftSmoke: () => {},
});
const ids = ['center-alert', 'alert-copy', 'drift-angle', 'drift-points', 'combo', 'traction-status', 'speed', 'gear', 'rpm', 'rpm-fill'];
const elements = Object.fromEntries(ids.map(id => [id, { textContent: '', style: {} }]));
globalThis.$ = id => elements[id] || (elements[id] = { textContent: '', style: {} });
globalThis.collide = () => {};
const updateSimulation = new Function(`${updateSource}\nreturn updateSimulation;`)();

function tick(seconds, heldKeys) {
  keys.clear();
  for (const key of heldKeys) keys.add(key);
  const frames = Math.round(seconds * 60);
  for (let i = 0; i < frames; i++) updateSimulation(1 / 60);
}
function resetDynamics() {
  Object.assign(globalThis, {
    simTime: 0, yaw: 0, velX: 0, velZ: 0, steer: 0, throttle: 0, braking: false,
    handbrake: false, boost: false, bodyRoll: 0, bodyPitch: 0, driftScore: 0,
    driftCombo: 1, driftTimer: 0, totalDistance: 0, topSpeed: 0,
  });
  vehicle.position.x = 0; vehicle.position.z = 0; vehicle.rotation.y = 0;
  body.rotation.x = 0; body.rotation.z = 0; body.position.y = 0;
  for (const key of Object.keys(elements)) { elements[key].textContent = ''; elements[key].style = {}; }
  keys.clear();
}

// Full braking/collision implementation test (rectangular buildings and parked cars).
const actualCollide = new Function(`${collisionSource}\nreturn collide;`)();
globalThis.collidersExpanded = [{ x: 0, z: 0, hw: 2, hd: 2, h: 12 }];
vehicle.position.x = 0; vehicle.position.z = 0; globalThis.velX = 12; globalThis.velZ = -8;
globalThis.driftCombo = 3; globalThis.driftTimer = 2;
actualCollide();
assert(Math.abs(vehicle.position.x) > 3.1 || Math.abs(vehicle.position.z) > 3.7, 'collision must separate overlapping car/building bounds');
assert(Math.abs(velX) < 12 && driftCombo === 1 && driftTimer === 0, 'collision must damp velocity and reset drift combo');
globalThis.collidersExpanded = [];

// Acceleration is progressive and bounded; the car moves along its forward (-Z) axis.
resetDynamics(); tick(4, ['KeyW']);
const normalSpeed = Math.hypot(velX, velZ);
assert(normalSpeed > 15 && normalSpeed < 55.5, `normal acceleration/top speed out of range: ${normalSpeed}`);
assert(vehicle.position.z < 0, 'forward should move towards -Z');

// Boost adds speed, but remains capped.
resetDynamics(); tick(4, ['KeyW', 'ShiftLeft']);
const boostedSpeed = Math.hypot(velX, velZ);
assert(boostedSpeed > normalSpeed + 3 && boostedSpeed <= 61.5, `boost response/cap wrong: ${boostedSpeed} vs ${normalSpeed}`);

// Steering rotates the chassis smoothly instead of causing an immediate spin.
resetDynamics(); tick(4, ['KeyW']);
const yawBefore = yaw; tick(1.2, ['KeyW', 'KeyA']);
const yawDelta = Math.abs(yaw - yawBefore);
assert(yawDelta > 0.03 && yawDelta < 1.5, `steering response out of range: ${yawDelta}`);

// The handbrake must generate a measurable drift angle and score.
let maxDriftAngle = 0;
keys.clear(); keys.add('KeyW'); keys.add('KeyD'); keys.add('Space');
for (let i = 0; i < 180; i++) {
  updateSimulation(1 / 60);
  maxDriftAngle = Math.max(maxDriftAngle, Number(elements['drift-angle'].textContent) || 0);
}
assert(maxDriftAngle > 11, `handbrake drift did not register: ${maxDriftAngle} degrees`);
assert(Number(elements['drift-points'].textContent) > 0, 'drift score should increase during a qualifying slide');
const speedBeforeBrake = Math.hypot(velX, velZ); tick(0.25, ['KeyS']);
const speedAfterBrake = Math.hypot(velX, velZ);
assert(speedAfterBrake < speedBeforeBrake, `braking failed to reduce speed: ${speedBeforeBrake} -> ${speedAfterBrake}`);

console.log('Physics smoke test passed:', JSON.stringify({
  normalSpeedMps: +normalSpeed.toFixed(2),
  boostedSpeedMps: +boostedSpeed.toFixed(2),
  steeringYawDeltaRad: +yawDelta.toFixed(3),
  maxDriftAngleDeg: maxDriftAngle,
  driftScore: Number(elements['drift-points'].textContent),
  brakingReducedSpeed: true,
  collisionResponse: 'passed',
}));
