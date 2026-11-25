// "Infinite Money Glitch" world (our own designs, made-up brands):
//  - BAR (origin): "THE NIGHT OWL" at 2 a.m.: back bar with real-looking labelled bottles, neon, clock, counter, stools,
//    a tip jar, and Dan's phone with the made-up GOLDLEAF BANK app
//  - RUNWAY (x = +400): tarmac, hangar, a white private jet with an open door and a proper airstair
//  - STREET (x = -400): night street: GOLDLEAF BANK (a real multi-storey building), GRAND PALMS HOTEL, CITY POLICE
//  - SERVER (x = 1000), BEDROOM (x = 1100), POLICE interior + jail cell (x = 1200)
import * as THREE from "three";
import { lam, quad, boxGeo, Batch, V } from "../bridge/build";
import { ctex } from "../bridge/paint";
import { woodFloor, slabs, signTex, wallPaint, carpet } from "../pepsi/tex";
import { DynTex } from "../silver/places";

export type V3 = [number, number, number];
export const RUNWAY: V3 = [400, 0, 0];
export const STREET: V3 = [-400, 0, 0];
export const SERVER = 1000, BEDROOM = 1100, POLICE = 1200;
/** the phone standing on the counter (screen faces +z) */
export const PHONE: V3 = [0.55, 1.07, -1.5];
export const HOTEL_X = STREET[0] - 60, COPS_X = STREET[0] + 45;

const mesh = (g: THREE.BufferGeometry, m: THREE.Material, cast = true) => { const o = new THREE.Mesh(g, m); o.castShadow = cast; o.receiveShadow = true; return o; };
const col = (key: string, c: string) => lam("gl_" + key, () => ({ color: c }));
const at = <T extends THREE.Object3D>(o: T, x: number, y: number, z: number, ry = 0) => { o.position.set(x, y, z); o.rotation.y = ry; return o; };
const box = (w: number, h: number, d: number, m: THREE.Material) => mesh(new THREE.BoxGeometry(w, h, d), m);
const cyl = (r0: number, r1: number, h: number, m: THREE.Material, seg = 16) => mesh(new THREE.CylinderGeometry(r0, r1, h, seg), m);
const glow = (c: string) => new THREE.MeshBasicMaterial({ color: c });
const pic = (t: THREE.Texture) => new THREE.MeshBasicMaterial({ map: t, side: THREE.DoubleSide });
const plane = (w: number, h: number, m: THREE.Material) => new THREE.Mesh(new THREE.PlaneGeometry(w, h), m);
const hh = (i: number, s = 0) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };

// ---------- painted textures ----------
const nightCity = () => ctex("gl_nightCity", 1024, 512, (g, r) => {
  const sky = g.createLinearGradient(0, 0, 0, 512); sky.addColorStop(0, "#0e1530"); sky.addColorStop(1, "#33285a"); g.fillStyle = sky; g.fillRect(0, 0, 1024, 512);
  g.fillStyle = "#fff6d6"; g.beginPath(); g.arc(820, 90, 34, 0, 7); g.fill();
  for (let i = 0; i < 60; i++) { g.fillStyle = "rgba(255,255,255,.7)"; g.fillRect(r() * 1024, r() * 200, 2, 2); }
  for (let x = 0; x < 1024;) { const w = 60 + r() * 90, h = 140 + r() * 260; g.fillStyle = r() < 0.5 ? "#1b2140" : "#232a4d"; g.fillRect(x, 512 - h, w, h);
    for (let y = 512 - h + 12; y < 500; y += 22) for (let wx = x + 8; wx < x + w - 10; wx += 16) if (r() < 0.45) { g.fillStyle = r() < 0.8 ? "#ffd98a" : "#9fd4ff"; g.fillRect(wx, y, 8, 10); }
    x += w + 4; }
});
const brickDark = () => ctex("gl_brick", 512, 512, (g, r) => {
  g.fillStyle = "#3a2a2e"; g.fillRect(0, 0, 512, 512);
  for (let y = 0; y < 512; y += 32) for (let x = (y / 32) % 2 ? -32 : 0; x < 512; x += 64) { g.fillStyle = ["#6a3a32", "#5e342e", "#734036"][Math.floor(r() * 3)]; g.fillRect(x + 2, y + 2, 60, 28); }
});
const tarmac = () => ctex("gl_tarmac", 512, 512, (g, r) => { g.fillStyle = "#5a5d68"; g.fillRect(0, 0, 512, 512); for (let i = 0; i < 1500; i++) { g.fillStyle = r() < 0.5 ? "rgba(30,30,40,.25)" : "rgba(170,170,185,.2)"; g.fillRect(r() * 512, r() * 512, 3, 3); } });
const limestone = () => ctex("gl_lime", 512, 512, (g, r) => {
  g.fillStyle = "#e3d6bb"; g.fillRect(0, 0, 512, 512);
  for (let y = 0; y < 512; y += 64) for (let x = (y / 64) % 2 ? -64 : 0; x < 512; x += 128) { g.fillStyle = r() < 0.5 ? "#e8dcc3" : "#dccfb2"; g.fillRect(x + 2, y + 2, 124, 60); }
});
/** a facade with a grid of lit / dark windows (floors x bays) */
const facade = (key: string, wall: string, frame: string, floors: number, bays: number, lit = 0.55) => ctex("gl_fac" + key, 512, 512, (g, r) => {
  g.fillStyle = wall; g.fillRect(0, 0, 512, 512);
  const fh = 512 / floors, bw = 512 / bays;
  for (let f = 0; f < floors; f++) {
    g.fillStyle = "rgba(0,0,0,.12)"; g.fillRect(0, f * fh + fh - 8, 512, 8);
    for (let b = 0; b < bays; b++) {
      const x = b * bw + bw * 0.22, y = f * fh + fh * 0.2, w = bw * 0.56, h = fh * 0.58;
      g.fillStyle = frame; g.fillRect(x - 5, y - 5, w + 10, h + 10);
      g.fillStyle = r() < lit ? "#ffd98a" : "#2b3a5c"; g.fillRect(x, y, w, h);
      g.fillStyle = frame; g.fillRect(x + w / 2 - 2, y, 4, h); g.fillRect(x, y + h * 0.45, w, 4);
    }
  }
});
/** bottle label (made-up brands) */
const LABELS: [string, string, string][] = [["OAK & ASH", "#f4e3b0", "#5a2a16"], ["SILVER FOX", "#e8edf5", "#22304f"], ["BLUE RIDGE", "#cfe6ff", "#1d3f8a"], ["DESERT ROSE", "#ffd9d0", "#9c2b35"],
  ["OLD HARBOR", "#f2c94c", "#241726"], ["NIGHT OWL GIN", "#e6f7ef", "#2f6a4a"]];
const labelTex = (i: number) => ctex("gl_label" + i, 256, 128, (g) => {
  const [n, bg, fg] = LABELS[i % LABELS.length];
  g.fillStyle = bg; g.fillRect(0, 0, 256, 128); g.strokeStyle = fg; g.lineWidth = 6; g.strokeRect(8, 8, 240, 112);
  g.fillStyle = fg; g.font = '900 30px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(n, 128, 56);
  g.font = "700 18px Arial"; g.fillText("EST. 1974", 128, 92);
});

export class Sets {
  root = new THREE.Group();
  phoneTex = new DynTex(540, 1080);
  clockTex = new DynTex(256, 256);
  serverTex = new DynTex(800, 450);
  calTex = new DynTex(512, 512);
  nightPhoneTex = new DynTex(270, 540);
  jet = new THREE.Group();
  leds: THREE.MeshBasicMaterial[] = [];
  copLight!: THREE.MeshBasicMaterial;
  cellDoor = new THREE.Group();

  constructor() { this.bar(); this.runway(); this.street(); this.server(); this.bedroom(); this.police(); }

  /** open-front room: floor, back + side walls, a no-shadow ceiling */
  private room(x0: number, w: number, h: number, d: number, floor: THREE.Material, wall: THREE.Material, ceil = "#1b1620") {
    const g = new THREE.Group(), b = new Batch(); this.root.add(g);
    b.add(boxGeo(V(x0 - w / 2 - 0.3, -0.3, -d), V(x0 + w / 2 + 0.3, 0, 5), 2), floor);
    b.add(boxGeo(V(x0 - w / 2, 0, -d - 0.3), V(x0 + w / 2, h, -d), 2), wall);
    for (const s of [-1, 1]) b.add(boxGeo(V(x0 + s * w / 2 - (s > 0 ? 0 : 0.3), 0, -d), V(x0 + s * w / 2 + (s > 0 ? 0.3 : 0), h, 5), 2), wall);
    b.build(g);
    const c = box(w + 0.6, 0.2, d + 5, col("ceil" + ceil, ceil)); c.castShadow = false; at(c, x0, h + 0.1, (5 - d) / 2); g.add(c);
    return g;
  }

  // ================= BAR =================
  private bar() {
    const g = this.room(0, 14, 4.6, 10, lam("gl_floor", () => ({ map: woodFloor("gl_floorW", "#5a3a26") })), lam("gl_brickM", () => ({ map: brickDark() })));
    const b = new Batch(), D = 10;
    // back bar cabinet, mirror, three shelves of real-looking bottles (lathe shape + label + cap), evenly spaced
    b.add(boxGeo(V(-5.5, 0, -D + 0.05), V(5.5, 0.95, -D + 0.75), 0), col("backbar", "#2a1c16"));
    b.add(boxGeo(V(-5.5, 1.1, -D + 0.02), V(5.5, 3.3, -D + 0.06), 0), col("mirror", "#2f3c58"));
    const profiles = [
      [[0.0, 0], [0.085, 0], [0.09, 0.02], [0.09, 0.22], [0.08, 0.26], [0.03, 0.31], [0.028, 0.4], [0.0, 0.4]],     // round bottle
      [[0.0, 0], [0.075, 0], [0.08, 0.02], [0.08, 0.26], [0.04, 0.29], [0.025, 0.42], [0.0, 0.42]],                  // tall slim
      [[0.0, 0], [0.095, 0], [0.1, 0.02], [0.1, 0.18], [0.06, 0.22], [0.03, 0.26], [0.028, 0.33], [0.0, 0.33]],      // squat
    ].map((p) => new THREE.LatheGeometry(p.map(([x, y]) => new THREE.Vector2(x, y)), 18));
    const glassCols0 = ["#2b3242"]; void glassCols0;
    const glassCols = ["#7a4a1c", "#c9d8e8", "#2f6a4a", "#8a2f35", "#b88a3a", "#cfe6ff"];
    for (let row = 0; row < 3; row++) {
      const y0 = 1.2 + row * 0.72;
      b.add(boxGeo(V(-5.5, y0 - 0.05, -D + 0.05), V(5.5, y0, -D + 0.5), 0), col("shelf", "#8a5a34"));
      for (let k = 0; k < 16; k++) {
        const x = -5.0 + k * 0.665, ty = (k + row * 2) % 3, c = glassCols[(k + row) % glassCols.length];
        const m = new THREE.MeshPhongMaterial({ color: c, emissive: c, emissiveIntensity: 0.18, transparent: true, opacity: 0.9, shininess: 110, specular: "#ffffff" });
        const bt = new THREE.Mesh(profiles[ty], m); at(bt, x, y0, -D + 0.28); g.add(bt);
        const h = ty === 2 ? 0.1 : 0.12, rr = ty === 1 ? 0.082 : ty === 2 ? 0.102 : 0.092;
        const lb = new THREE.Mesh(new THREE.CylinderGeometry(rr, rr, h, 18, 1, true, -Math.PI / 2.2, Math.PI / 1.1), pic(labelTex(k + row * 5)));
        at(lb, x, y0 + (ty === 2 ? 0.1 : 0.13), -D + 0.28); g.add(lb);
        const cap = cyl(0.03, 0.03, 0.035, col("cap" + (k % 3), ["#d9b25a", "#241726", "#c0262f"][k % 3]), 10); cap.castShadow = false;
        g.add(at(cap, x, y0 + (ty === 1 ? 0.43 : ty === 2 ? 0.345 : 0.415), -D + 0.28));
      }
    }
    // neon sign, clock, night window
    const neon = plane(4.6, 1.0, pic(signTex("gl_neon2", ["THE NIGHT OWL"], { bg: "#140c18", fg: "#ff4fd8", w: 1400, h: 300, sizes: [150], shadow: false, border: "#3ef0ff" })));
    at(neon, 0, 3.85, -D + 0.08); g.add(neon);
    const clk = new THREE.Mesh(new THREE.CircleGeometry(0.42, 40), pic(this.clockTex.tex)); at(clk, 4.4, 3.6, -D + 0.08); g.add(clk);
    const win = plane(4, 2.2, pic(nightCity())); win.rotation.y = Math.PI / 2; at(win, -6.98, 2.3, -4); win.rotation.y = Math.PI / 2; g.add(win);
    // bar door (left wall, front) for the friends' entrance
    b.add(boxGeo(V(-7.0, 0, -0.5), V(-6.95, 2.6, 1.0), 0), col("barDoor", "#5a3b2a"));
    // counter (customer side faces +z), brass foot rail, stools in front
    b.add(boxGeo(V(-5.2, 0, -2.4), V(5.2, 1.0, -1.3), 1), lam("gl_counter", () => ({ map: woodFloor("gl_counterW", "#6a3a22") })));
    b.add(boxGeo(V(-5.3, 1.0, -2.5), V(5.3, 1.07, -1.2), 0), col("top", "#3a2416"));
    const rail = cyl(0.04, 0.04, 10.4, col("brass", "#d9b25a"), 8); rail.rotation.z = Math.PI / 2; at(rail, 0, 0.25, -1.15); g.add(rail);
    for (let i = 0; i < 6; i++) { const x = -3.6 + i * 1.6; g.add(at(cyl(0.05, 0.05, 0.75, col("stoolLeg", "#2a2a30"), 8), x, 0.37, -0.75)); g.add(at(cyl(0.28, 0.28, 0.1, col("stool", "#c0353a"), 18), x, 0.78, -0.75)); }
    for (const x of [-3.5, 0, 3.5]) { g.add(at(cyl(0.01, 0.01, 1.2, col("cord", "#14101a"), 4), x, 4.0, -1.9)); g.add(at(mesh(new THREE.ConeGeometry(0.32, 0.3, 18, 1, true), col("shade", "#2f4a3a"), false), x, 3.35, -1.9)); g.add(at(mesh(new THREE.SphereGeometry(0.12, 10, 8), glow("#ffe3a8"), false), x, 3.25, -1.9)); }
    // glasses, a drink by Dan's spot, the tip jar
    for (let i = 0; i < 4; i++) g.add(at(cyl(0.05, 0.04, 0.14, new THREE.MeshPhongMaterial({ color: "#cfe6ff", transparent: true, opacity: 0.55, shininess: 100 }), 10), -3.6 + i * 0.6, 1.14, -1.8));
    g.add(at(cyl(0.055, 0.045, 0.16, new THREE.MeshPhongMaterial({ color: "#c9893a", transparent: true, opacity: 0.85, shininess: 100 }), 12), 0.05, 1.15, -1.5));
    const jar = cyl(0.12, 0.12, 0.26, new THREE.MeshPhongMaterial({ color: "#dff0ff", transparent: true, opacity: 0.45, shininess: 120 }), 18); at(jar, -1.4, 1.2, -1.55); g.add(jar);
    for (let i = 0; i < 3; i++) g.add(at(cyl(0.04, 0.04, 0.012, col("coin", "#c9ced8"), 12), -1.42 + (i - 1) * 0.05, 1.08 + i * 0.013, -1.55));
    const tip = plane(0.24, 0.1, pic(signTex("gl_tips", ["TIPS"], { bg: "#f4f1ea", fg: "#241726", w: 256, h: 100, sizes: [60], shadow: false }))); at(tip, -1.4, 1.22, -1.42); g.add(tip);
    // Dan's phone on a little stand (screen = bank app)
    const ph = new THREE.Group();
    ph.add(at(box(0.19, 0.38, 0.02, col("phone", "#14101a")), 0, 0.19, 0));
    const scr = plane(0.17, 0.35, pic(this.phoneTex.tex)); at(scr, 0, 0.19, 0.011); ph.add(scr);
    ph.add(at(box(0.12, 0.03, 0.1, col("stand", "#3a3d47")), 0, 0.0, -0.03));
    ph.rotation.x = -0.3; at(ph, ...PHONE); g.add(ph);
    b.build(g);
  }

  // ================= RUNWAY + PRIVATE JET =================
  private runway() {
    const [X] = RUNWAY, g = new THREE.Group(), b = new Batch(); this.root.add(g);
    b.add(quad(V(X - 200, 0.01, 60), V(X + 200, 0.01, 60), V(X + 200, 0.01, -120), V(X - 200, 0.01, -120), 400 / 8, 180 / 8), lam("gl_tarmacM", () => ({ map: tarmac() })));
    for (let k = -10; k < 10; k++) b.add(boxGeo(V(X + k * 14, 0.02, 9.8), V(X + k * 14 + 7, 0.03, 10.2), 0), col("tmark", "#f4f1ea"));
    b.add(boxGeo(V(X - 95, 0, -120), V(X - 45, 11, -100), 4), lam("gl_hangar", () => ({ map: wallPaint("gl_hangarW", "#c9ced8", "#8a8f9a") })));
    b.build(g);
    // private jet (nose +x): slim fuselage, swept wings, rear engines, T-tail, tall gear, open door + airstair
    const J = this.jet, white = lam("gl_jetW", () => ({ color: "#f4f6fa" })), dark = col("jetD", "#2b2e3a"), gold = col("jetG", "#d9b25a"), glass = col("jetGlass", "#1f2a3a");
    const prof: THREE.Vector2[] = [];
    for (let k = 0; k <= 40; k++) { const x = -9 + 18 * (k / 40); const r = x > 5 ? 1.25 * Math.sqrt(Math.max(0, 1 - ((x - 5) / 4) ** 2)) : x < -4 ? 1.25 * (0.3 + 0.7 * ((x + 9) / 5)) : 1.25; prof.push(new THREE.Vector2(Math.max(0.05, r), x)); }
    const fus = mesh(new THREE.LatheGeometry(prof, 28), white); fus.rotation.z = -Math.PI / 2; J.add(fus);
    for (const z of [1.23, -1.23]) { J.add(at(box(14, 0.1, 0.05, gold), -0.5, -0.25, z)); for (let i = 0; i < 6; i++) J.add(at(mesh(new THREE.SphereGeometry(0.16, 12, 8), glass), 2.4 - i * 1.15, 0.3, z * 0.98)); }
    J.add(at(box(0.8, 0.35, 1.6, glass), 6.6, 0.55, 0));
    // open door (dark opening) just behind the cockpit on the +z side, with a frame
    J.add(at(box(0.95, 1.5, 0.06, col("doorHole", "#14101a")), 4.3, 0.05, 1.22));
    J.add(at(box(1.05, 0.06, 0.08, white), 4.3, 0.82, 1.24)); J.add(at(box(0.06, 1.55, 0.08, white), 3.78, 0.05, 1.24)); J.add(at(box(0.06, 1.55, 0.08, white), 4.82, 0.05, 1.24));
    // airstair: from the door sill (y -0.7) down to the ground, 7 steps, two handrails
    const H = 2.6 - 0.0, steps = 7, run = 2.4, stair = new THREE.Group();
    for (let i = 0; i < steps; i++) { const u = i / (steps - 1); stair.add(at(box(0.85, 0.07, 0.32, col("step", "#d7d9de")), 0, -0.72 - u * (H - 0.75), 1.45 + u * run)); }
    for (const sx of [-0.45, 0.45]) {
      const a = new THREE.Vector3(sx, -0.72, 1.4), b2 = new THREE.Vector3(sx, -0.72 - (H - 0.75), 1.45 + run);
      const side = box(0.05, 0.22, a.distanceTo(b2), white); side.position.copy(a).add(b2).multiplyScalar(0.5); side.lookAt(b2); stair.add(side);
      const ra = a.clone().add(new THREE.Vector3(0, 0.85, 0)), rb = b2.clone().add(new THREE.Vector3(0, 0.85, 0));
      const rail = box(0.04, 0.04, ra.distanceTo(rb), gold); rail.position.copy(ra).add(rb).multiplyScalar(0.5); rail.lookAt(rb); stair.add(rail);
      for (const k of [0.15, 0.55, 0.9]) { const p = a.clone().lerp(b2, k); stair.add(at(box(0.03, 0.85, 0.03, gold), p.x, p.y + 0.42, p.z)); }
    }
    stair.position.x = 4.3; J.add(stair);
    const ws = new THREE.Shape(); ws.moveTo(1.4, 0); ws.lineTo(-1.2, 7); ws.lineTo(-2.4, 7); ws.lineTo(-1.6, 0); ws.lineTo(-2.4, -7); ws.lineTo(-1.2, -7); ws.closePath();
    const wing = mesh(new THREE.ExtrudeGeometry(ws, { depth: 0.18, bevelEnabled: false }), white); wing.rotation.x = Math.PI / 2; wing.position.set(0.0, -0.6, 0); J.add(wing);
    for (const z of [0.95, -0.95]) { const e = mesh(new THREE.CylinderGeometry(0.42, 0.48, 2.2, 16), white); e.rotation.z = Math.PI / 2; e.position.set(-5.6, 0.75, z * 1.55); J.add(e); J.add(at(box(0.6, 0.15, 0.5, white), -5.6, 0.75, z * 1.1)); J.add(at(mesh(new THREE.CircleGeometry(0.36, 16), dark), -4.49, 0.75, z * 1.55).rotateY(Math.PI / 2) as THREE.Object3D); }
    const fin = new THREE.Shape(); fin.moveTo(0, 0); fin.lineTo(2.6, 0); fin.lineTo(1.0, 3.2); fin.lineTo(-0.4, 3.2); fin.closePath();
    const fm = mesh(new THREE.ExtrudeGeometry(fin, { depth: 0.18, bevelEnabled: false }), white); fm.position.set(-8.6, 0.6, -0.09); J.add(fm);
    const fb = mesh(new THREE.ExtrudeGeometry(new THREE.Shape([new THREE.Vector2(0.9, 1.2), new THREE.Vector2(2.1, 1.2), new THREE.Vector2(1.6, 2.2), new THREE.Vector2(0.5, 2.2)]), { depth: 0.2, bevelEnabled: false }), gold);
    fb.position.set(-8.6, 0.6, -0.1); J.add(fb);
    J.add(at(box(1.4, 0.12, 4.2, white), -8.2, 3.75, 0));
    // tall landing gear (body sits ~2.6 m up, like a real business jet)
    for (const [x, z] of [[5.2, 0], [-0.8, 1.0], [-0.8, -1.0]] as [number, number][]) { J.add(at(box(0.12, 2.0, 0.12, dark), x, -1.6, z)); const w = cyl(0.34, 0.34, 0.24, dark, 14); w.rotation.x = Math.PI / 2; w.position.set(x, -2.6 + 0.34, z); J.add(w); }
    at(J, X, 2.6, -6); g.add(J);
  }

  // ================= STREET: BANK, HOTEL, POLICE =================
  private street() {
    const [X] = STREET, g = new THREE.Group(), b = new Batch(); this.root.add(g);
    b.add(quad(V(X - 120, 0.01, 30), V(X + 120, 0.01, 30), V(X + 120, 0.01, 6), V(X - 120, 0.01, 6), 240 / 8, 3), lam("gl_tarmacM", () => ({ map: tarmac() })));
    b.add(boxGeo(V(X - 120, 0, -40), V(X + 120, 0.15, 6), 3), lam("slabs", () => ({ map: slabs() })));
    const stone = lam("gl_limeM", () => ({ map: limestone() }));
    // ---- GOLDLEAF BANK: 4-storey stone building, rusticated base, portico with 4 columns + pediment, cornice, parapet
    const BX = X + 7;
    b.add(boxGeo(V(BX - 9, 0, -16), V(BX + 9, 15, -4), 0), lam("gl_bankFac", () => ({ map: facade("bank", "#e3d6bb", "#b8a888", 4, 6, 0.6) })));
    b.add(boxGeo(V(BX - 9.3, 0, -4.3), V(BX + 9.3, 3.2, -3.9), 3), stone);                          // rusticated base band
    b.add(boxGeo(V(BX - 9.5, 15, -16.3), V(BX + 9.5, 15.6, -3.6), 0), stone);                       // cornice
    b.add(boxGeo(V(BX - 9.2, 15.6, -16), V(BX + 9.2, 16.4, -3.9), 0), stone);                       // parapet
    b.add(boxGeo(V(BX - 4.6, 0, -3.9), V(BX + 4.6, 0.3, -1.2), 0), stone);                          // steps
    b.add(boxGeo(V(BX - 4.2, 0.3, -3.9), V(BX + 4.2, 0.6, -2.0), 0), stone);
    for (let i = 0; i < 4; i++) { const cx = BX - 3.3 + i * 2.2; g.add(at(cyl(0.4, 0.45, 6.4, col("bcol", "#f1e8d6"), 18), cx, 3.8, -2.6)); g.add(at(box(1.1, 0.35, 1.1, stone), cx, 7.1, -2.6)); g.add(at(box(1.1, 0.3, 1.1, stone), cx, 0.75, -2.6)); }
    b.add(boxGeo(V(BX - 4.6, 7.25, -3.9), V(BX + 4.6, 8.3, -1.9), 0), stone);                      // entablature
    const ped = new THREE.Shape([new THREE.Vector2(-4.8, 0), new THREE.Vector2(4.8, 0), new THREE.Vector2(0, 1.8)]);
    g.add(at(mesh(new THREE.ExtrudeGeometry(ped, { depth: 2.1, bevelEnabled: false }), stone), BX, 8.3, -3.95));
    const sg = plane(7.6, 0.85, pic(signTex("gl_bank3", ["GOLDLEAF BANK"], { bg: "#22304f", fg: "#e8c45a", w: 1300, h: 146, sizes: [100], shadow: false })));
    at(sg, BX, 7.78, -1.88); g.add(sg);
    for (const dx of [-1.1, 1.1]) b.add(boxGeo(V(BX + dx - 0.85, 0.6, -3.95), V(BX + dx + 0.85, 3.6, -3.88), 0), col("bdoor", "#8a6a3a"));
    const dglow = plane(3.6, 0.8, glow("#ffd98a")); at(dglow, BX, 4.1, -3.89); g.add(dglow);
    // ATM + lamps
    b.add(boxGeo(V(BX + 6, 0.15, -3.95), V(BX + 7.2, 2.2, -3.6), 0), col("atm", "#2b2e3a"));
    const atm = plane(0.9, 0.5, glow("#5cf5a6")); at(atm, BX + 6.6, 1.6, -3.59); g.add(atm);
    // ---- neighbours with lit windows
    for (let k = 0; k < 4; k++) { const x0 = X - 46 + k * 11; b.add(boxGeo(V(x0, 0, -18), V(x0 + 10, 9 + (k % 3) * 3, -5), 0), lam("gl_nb" + k, () => ({ map: facade("nb" + k, ["#3a3550", "#5a3a3a", "#35485a", "#4a4a3a"][k], "#1a1a24", 3 + (k % 3), 4, 0.5) }))); }
    // ---- GRAND PALMS HOTEL (left): tall tower, red canopy, red carpet, palms
    const HX = HOTEL_X;
    b.add(boxGeo(V(HX - 8, 0, -22), V(HX + 8, 34, -6), 0), lam("gl_hotelFac", () => ({ map: facade("hotel", "#efe6d2", "#c9a24a", 10, 6, 0.7) })));
    b.add(boxGeo(V(HX - 3.5, 3.4, -6), V(HX + 3.5, 3.7, -2.5), 0), col("canopy", "#9c2b35"));
    for (const dx of [-3.3, 3.3]) g.add(at(cyl(0.06, 0.06, 3.4, col("gold", "#d9b25a"), 8), HX + dx, 1.7, -2.6));
    b.add(boxGeo(V(HX - 1.4, 0.15, -6), V(HX + 1.4, 0.17, 4), 0), col("carpet", "#c0262f"));
    const hs = plane(9, 1.6, pic(signTex("gl_hotel", ["GRAND PALMS HOTEL", "★★★★★"], { bg: "#14101a", fg: "#e8c45a", w: 1400, h: 250, sizes: [96, 70], shadow: false })));
    at(hs, HX, 5.0, -5.95); g.add(hs);
    for (const dx of [-6, 6]) { g.add(at(cyl(0.18, 0.28, 6, col("palmT", "#8a6a3a"), 8), HX + dx, 3, -3)); for (let k = 0; k < 6; k++) { const lf = box(2.4, 0.08, 0.5, col("palmL", "#3f8a3a")); lf.position.set(HX + dx + Math.cos(k) * 0.9, 6.1, -3 + Math.sin(k) * 0.9); lf.rotation.set(0, -k, 0.35); g.add(lf); } }
    // ---- CITY POLICE station (right): brick, blue lamp, sign
    const PX = COPS_X;
    b.add(boxGeo(V(PX - 8, 0, -16), V(PX + 8, 11, -4), 0), lam("gl_copsFac", () => ({ map: facade("cops", "#7a4a3a", "#e6e0d4", 3, 5, 0.6) })));
    b.add(boxGeo(V(PX - 2.4, 0.15, -4.05), V(PX + 2.4, 0.45, -1.5), 0), col("copStep", "#b9b4ac"));
    b.add(boxGeo(V(PX - 1.2, 0.45, -4.02), V(PX + 1.2, 3.2, -3.96), 0), col("copDoor", "#1d3f8a"));
    const ps = plane(6, 1.1, pic(signTex("gl_cops", ["CITY POLICE"], { bg: "#1d3f8a", fg: "#ffffff", w: 1200, h: 220, sizes: [130], shadow: false })));
    at(ps, PX, 4.2, -3.95); g.add(ps);
    for (const dx of [-3.6, 3.6]) { g.add(at(cyl(0.05, 0.05, 1.0, col("lampP", "#2a2a34"), 8), PX + dx, 3.4, -3.7)); g.add(at(mesh(new THREE.BoxGeometry(0.4, 0.5, 0.4), glow("#7fb6ff"), false), PX + dx, 3.95, -3.7)); }
    for (const dx of [-30, -14, 2, 18, 34, 50, 66]) { g.add(at(cyl(0.1, 0.14, 5, col("lampP", "#2a2a34"), 8), X + dx, 2.5, 5)); g.add(at(mesh(new THREE.SphereGeometry(0.4, 12, 8), glow("#fff2c4"), false), X + dx, 5.1, 5)); }
    b.build(g);
  }

  // ================= SERVER ROOM (bank, night) =================
  private server() {
    const X = SERVER, g = this.room(X, 12, 4.5, 10, col("srvFloor", "#3a3d47"), col("srvWall", "#2b3040"), "#1b1f2a"), b = new Batch();
    for (let r = 0; r < 2; r++) for (let k = 0; k < 6; k++) {
      const x = X - 5 + k * 1.15 + (r ? 0 : 0), z = r ? -7.5 : -4.2;
      b.add(boxGeo(V(x - 0.5, 0, z - 0.5), V(x + 0.5, 2.6, z + 0.5), 0), col("rack2", "#3a4256"));
      for (let s = 0; s < 8; s++) {
        b.add(boxGeo(V(x - 0.44, 0.25 + s * 0.29, z + 0.5), V(x + 0.44, 0.48 + s * 0.29, z + 0.52), 0), col("blade2", "#5a6478"));
        const m = new THREE.MeshBasicMaterial({ color: s % 3 ? "#5cf5a6" : "#7fb6ff" }); this.leds.push(m);
        g.add(at(mesh(new THREE.BoxGeometry(0.06, 0.05, 0.02), m, false), x + 0.32, 0.36 + s * 0.29, z + 0.535));
      }
    }
    // big status screen + guard desk with monitor + wall calendar
    const scr = plane(4.0, 2.25, pic(this.serverTex.tex)); at(scr, X + 3.4, 2.6, -9.95); g.add(scr);
    b.add(boxGeo(V(X + 2.2, 0, -2.6), V(X + 4.8, 0.85, -1.6), 0), col("gdesk", "#5a4a3a"));
    b.add(boxGeo(V(X + 3.0, 0.85, -2.5), V(X + 3.9, 1.5, -2.2), 0), col("gmon", "#1f2330"));
    const cal = plane(1.6, 1.6, pic(this.calTex.tex)); cal.rotation.y = Math.PI / 2; at(cal, X - 5.95, 2.4, -2.0); cal.rotation.y = Math.PI / 2; g.add(cal);
    const cal2 = plane(1.6, 1.6, pic(this.calTex.tex)); at(cal2, X + 0.3, 2.9, -9.95); g.add(cal2);
    b.build(g);
  }

  // ================= BEDROOM (4 a.m.) =================
  private bedroom() {
    const X = BEDROOM, g = this.room(X, 8, 4.0, 7, lam("gl_bedFloor", () => ({ map: carpet("gl_bedCarpet", "#3a4a6a") })), lam("gl_bedWall", () => ({ map: wallPaint("gl_bedWallT", "#4a5a7a", "#2f3a52") })), "#20263a"), b = new Batch();
    b.add(boxGeo(V(X - 2.0, 0, -6.8), V(X + 2.0, 0.55, -3.6), 0), col("bedBase", "#5a3b2a"));
    b.add(boxGeo(V(X - 2.0, 0.55, -6.8), V(X + 2.0, 0.8, -3.6), 0), col("mattress", "#e6e0d4"));
    b.add(boxGeo(V(X - 2.05, 0.8, -5.6), V(X + 2.05, 0.95, -3.5), 0), col("blanket", "#2f5f9e"));
    b.add(boxGeo(V(X - 2.1, 0, -7.0), V(X + 2.1, 1.6, -6.8), 0), col("headboard", "#4a2c1a"));
    for (const dx of [-1, 1]) b.add(boxGeo(V(X + dx - 0.6, 0.8, -6.7), V(X + dx + 0.6, 1.05, -6.1), 0), col("pillow", "#f4f1ea"));
    b.add(boxGeo(V(X + 2.3, 0, -6.4), V(X + 3.1, 0.7, -5.6), 0), col("nstand", "#5a3b2a"));
    const nph = plane(0.16, 0.32, pic(this.nightPhoneTex.tex)); nph.rotation.x = -0.25; at(nph, X + 2.7, 0.88, -5.95); nph.rotation.x = -0.25; g.add(nph);
    g.add(at(box(0.18, 0.34, 0.015, col("nphB", "#14101a")), X + 2.7, 0.88, -5.962).rotateX(-0.25) as THREE.Object3D);
    g.add(at(cyl(0.12, 0.18, 0.35, col("lampB", "#c9a24a"), 12), X + 2.6, 0.88, -6.2));
    const win = plane(2.6, 1.8, pic(nightCity())); at(win, X - 0.5, 2.4, -6.98); g.add(win);
    this.copLight = new THREE.MeshBasicMaterial({ color: "#ff3b3b", transparent: true, opacity: 0, depthWrite: false });
    const cl = plane(2.6, 1.8, this.copLight); at(cl, X - 0.5, 2.4, -6.96); g.add(cl);
    const clk = new THREE.Mesh(new THREE.CircleGeometry(0.3, 32), pic(this.clockTex.tex)); at(clk, X + 2.6, 2.6, -6.98); g.add(clk);
    b.build(g);
  }

  // ================= POLICE front desk + jail cell =================
  private police() {
    const X = POLICE, g = this.room(X, 14, 4.6, 10, col("polFloor", "#9aa3b0"), lam("gl_polWall", () => ({ map: wallPaint("gl_polWallT", "#d8dde6", "#1d3f8a", true) })), "#2b3040"), b = new Batch();
    b.add(boxGeo(V(X - 5.5, 0, -4.0), V(X - 1.0, 1.15, -3.0), 0), col("pdesk", "#5a4a3a"));
    b.add(boxGeo(V(X - 5.6, 1.15, -4.1), V(X - 0.9, 1.22, -2.9), 0), col("pdeskTop", "#2b2e3a"));
    const ps = plane(4.4, 0.9, pic(signTex("gl_polDesk", ["POLICE • FRONT DESK"], { bg: "#1d3f8a", fg: "#ffffff", w: 1200, h: 240, sizes: [110], shadow: false }))); at(ps, X - 3.25, 3.4, -9.95); g.add(ps);
    const badge = new THREE.Mesh(new THREE.CircleGeometry(0.6, 6), pic(ctex("gl_badge", 256, 256, (gg) => { gg.fillStyle = "#e8c45a"; gg.beginPath(); for (let i = 0; i < 12; i++) { const r = i % 2 ? 80 : 118, a = -Math.PI / 2 + (i * Math.PI) / 6; gg.lineTo(128 + r * Math.cos(a), 128 + r * Math.sin(a)); } gg.fill(); gg.fillStyle = "#1d3f8a"; gg.beginPath(); gg.arc(128, 128, 56, 0, 7); gg.fill(); })));
    at(badge, X - 3.25, 2.3, -9.95); g.add(badge);
    // jail cell (right): back + side walls, bars in front, sliding barred door
    b.add(boxGeo(V(X + 1.5, 0, -6.2), V(X + 6.8, 0.25, -2.0), 0), col("cellFloor", "#7a7f8c"));
    b.add(boxGeo(V(X + 1.5, 0.25, -6.2), V(X + 6.8, 1.0, -5.6), 0), col("cellBench", "#6c7584"));
    const bar = col("bars", "#3a3d47");
    for (let k = 0; k < 9; k++) g.add(at(cyl(0.045, 0.045, 3.4, bar, 8), X + 1.6 + k * 0.32, 1.95, -2.0));
    for (const y of [0.4, 3.5]) g.add(at(box(2.9, 0.1, 0.1, bar), X + 2.9, y, -2.0));
    for (let k = 0; k < 7; k++) this.cellDoor.add(at(cyl(0.045, 0.045, 3.4, bar, 8), k * 0.32, 1.95, 0));
    for (const y of [0.4, 1.9, 3.5]) this.cellDoor.add(at(box(2.1, 0.1, 0.1, bar), 0.96, y, 0));
    at(this.cellDoor, X + 4.5, 0, -1.9); g.add(this.cellDoor);
    b.add(boxGeo(V(X + 1.5, 3.65, -2.1), V(X + 6.8, 4.6, -1.9), 0), col("cellTop", "#3a3d47"));
    b.build(g);
  }
}
