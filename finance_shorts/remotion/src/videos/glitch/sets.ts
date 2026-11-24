// "Infinite Money Glitch" world (our own designs, made-up brands):
//  - BAR (origin): "THE NIGHT OWL" bar at 2 a.m.: back-bar shelves of glowing bottles, neon sign, wall clock, long counter,
//    stools, pendant lamps, a night-city window, and Dan's phone with the (made-up) GOLDLEAF BANK app on its screen
//  - RUNWAY (x = +400): tarmac, hangar, a white private jet with airstairs at golden hour
//  - STREET (x = -400): night street with the GOLDLEAF BANK facade for the final vote
import * as THREE from "three";
import { lam, quad, boxGeo, Batch, V } from "../bridge/build";
import { ctex } from "../bridge/paint";
import { woodFloor, slabs, signTex, wallPaint } from "../pepsi/tex";
import { DynTex } from "../silver/places";

export type V3 = [number, number, number];
export const RUNWAY: V3 = [400, 0, 0];
export const STREET: V3 = [-400, 0, 0];
/** the phone standing on the counter (screen faces +z) */
export const PHONE: V3 = [0.55, 1.07, -1.55];

const mesh = (g: THREE.BufferGeometry, m: THREE.Material, cast = true) => { const o = new THREE.Mesh(g, m); o.castShadow = cast; o.receiveShadow = true; return o; };
const col = (key: string, c: string) => lam("gl_" + key, () => ({ color: c }));
const at = <T extends THREE.Object3D>(o: T, x: number, y: number, z: number, ry = 0) => { o.position.set(x, y, z); o.rotation.y = ry; return o; };
const box = (w: number, h: number, d: number, m: THREE.Material) => mesh(new THREE.BoxGeometry(w, h, d), m);
const cyl = (r0: number, r1: number, h: number, m: THREE.Material, seg = 16) => mesh(new THREE.CylinderGeometry(r0, r1, h, seg), m);
const glow = (c: string) => new THREE.MeshBasicMaterial({ color: c });
const pic = (t: THREE.Texture) => new THREE.MeshBasicMaterial({ map: t, side: THREE.DoubleSide });
const hh = (i: number, s = 0) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };

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

export class Sets {
  root = new THREE.Group();
  phoneTex = new DynTex(540, 1080);
  clockTex = new DynTex(256, 256);
  jet = new THREE.Group();

  constructor() { this.bar(); this.runway(); this.street(); }

  // ================= BAR =================
  private bar() {
    const g = new THREE.Group(), b = new Batch(); this.root.add(g);
    const W = 14, H = 4.6, D = 10;
    b.add(boxGeo(V(-W / 2, -0.3, -D), V(W / 2, 0, 5), 2), lam("gl_floor", () => ({ map: woodFloor("gl_floorW", "#5a3a26") })));
    const wall = lam("gl_brickM", () => ({ map: brickDark() }));
    b.add(boxGeo(V(-W / 2, 0, -D - 0.3), V(W / 2, H, -D), 2), wall);
    for (const s of [-1, 1]) b.add(boxGeo(V(s < 0 ? -W / 2 - 0.3 : W / 2, 0, -D), V(s < 0 ? -W / 2 : W / 2 + 0.3, H, 5), 2), wall);
    const ceil = box(W + 0.6, 0.2, D + 5, col("ceil", "#1b1620")); ceil.castShadow = false; at(ceil, 0, H + 0.1, -D / 2 + 2.5); g.add(ceil);
    // back bar: shelves with glowing bottles + a mirror strip
    b.add(boxGeo(V(-5.5, 0, -D + 0.05), V(5.5, 0.9, -D + 0.7), 0), col("backbar", "#2a1c16"));
    b.add(boxGeo(V(-5.5, 1.2, -D + 0.02), V(5.5, 3.2, -D + 0.06), 0), col("mirror", "#3b4a66"));
    for (let row = 0; row < 3; row++) {
      b.add(boxGeo(V(-5.5, 1.15 + row * 0.7, -D + 0.05), V(5.5, 1.2 + row * 0.7, -D + 0.45), 0), col("shelf", "#8a5a34"));
      for (let k = 0; k < 26; k++) {
        const c = ["#3fae8a", "#e8b33a", "#c0353a", "#7fb6ea", "#f4f1ea", "#8a5a34"][(k + row) % 6], x = -5.2 + k * 0.41 + 0.06 * hh(k, row);
        const bt = cyl(0.06, 0.07, 0.36 + 0.1 * hh(k, row + 3), new THREE.MeshPhongMaterial({ color: c, emissive: c, emissiveIntensity: 0.25, transparent: true, opacity: 0.92, shininess: 90 }), 10);
        at(bt, x, 1.4 + row * 0.7, -D + 0.25); bt.castShadow = false; g.add(bt);
      }
    }
    // neon sign (made-up name)
    const neon = new THREE.Mesh(new THREE.PlaneGeometry(4.6, 1.0), pic(signTex("gl_neon", ["THE NIGHT OWL"], { bg: "#140c18", fg: "#ff4fd8", w: 1400, h: 300, sizes: [150], shadow: false, border: "#3ef0ff" })));
    at(neon, 0, 3.75, -D + 0.08); g.add(neon);
    // wall clock (right)
    const clk = new THREE.Mesh(new THREE.CircleGeometry(0.42, 40), pic(this.clockTex.tex)); at(clk, 4.4, 3.5, -D + 0.08); g.add(clk);
    // night window (left wall)
    const win = new THREE.Mesh(new THREE.PlaneGeometry(4, 2.2), pic(nightCity())); win.rotation.y = Math.PI / 2; at(win, -W / 2 + 0.02, 2.3, -4); win.rotation.y = Math.PI / 2; g.add(win);
    // counter: long wooden bar at z -2.4 .. -1.3, brass foot rail, stools in front
    b.add(boxGeo(V(-5.2, 0, -2.4), V(5.2, 1.0, -1.3), 1), lam("gl_counter", () => ({ map: woodFloor("gl_counterW", "#6a3a22") })));
    b.add(boxGeo(V(-5.3, 1.0, -2.5), V(5.3, 1.07, -1.2), 0), col("top", "#3a2416"));
    const brass = col("brass", "#d9b25a"); const rail = cyl(0.04, 0.04, 10.4, brass, 8); rail.rotation.z = Math.PI / 2; at(rail, 0, 0.25, -1.15); g.add(rail);
    for (let i = 0; i < 6; i++) { const x = -4 + i * 1.6; g.add(at(cyl(0.05, 0.05, 0.75, col("stoolLeg", "#2a2a30"), 8), x, 0.37, -0.6)); g.add(at(cyl(0.28, 0.28, 0.1, col("stool", "#c0353a"), 18), x, 0.78, -0.6)); }
    // pendant lamps
    for (const x of [-3.5, 0, 3.5]) { g.add(at(cyl(0.01, 0.01, 1.2, col("cord", "#14101a"), 4), x, H - 0.6, -1.9)); g.add(at(mesh(new THREE.ConeGeometry(0.32, 0.3, 18, 1, true), col("shade", "#2f4a3a"), false), x, H - 1.25, -1.9)); g.add(at(mesh(new THREE.SphereGeometry(0.12, 10, 8), glow("#ffe3a8"), false), x, H - 1.35, -1.9)); }
    // glasses + tip jar on the counter
    for (let i = 0; i < 5; i++) g.add(at(cyl(0.05, 0.04, 0.14, new THREE.MeshPhongMaterial({ color: "#cfe6ff", transparent: true, opacity: 0.6, shininess: 100 }), 10), -3.2 + i * 0.7, 1.14, -1.75));
    // Dan's phone on a little stand (screen = bank app)
    const ph = new THREE.Group();
    ph.add(at(box(0.19, 0.38, 0.02, col("phone", "#14101a")), 0, 0.19, 0));
    const scr = new THREE.Mesh(new THREE.PlaneGeometry(0.17, 0.35), pic(this.phoneTex.tex)); at(scr, 0, 0.19, 0.011); ph.add(scr);
    ph.add(at(box(0.12, 0.03, 0.1, col("stand", "#3a3d47")), 0, 0.0, -0.03));
    ph.rotation.x = -0.12; at(ph, ...PHONE); g.add(ph);
    b.build(g);
  }

  // ================= RUNWAY + PRIVATE JET =================
  private runway() {
    const [X] = RUNWAY, g = new THREE.Group(), b = new Batch(); this.root.add(g);
    b.add(quad(V(X - 200, 0.01, 60), V(X + 200, 0.01, 60), V(X + 200, 0.01, -120), V(X - 200, 0.01, -120), 400 / 8, 180 / 8), lam("gl_tarmacM", () => ({ map: tarmac() })));
    for (let k = -10; k < 10; k++) b.add(boxGeo(V(X + k * 14, 0.02, -8.2), V(X + k * 14 + 7, 0.03, -7.8), 0), col("tmark", "#f4f1ea"));
    b.add(boxGeo(V(X - 40, 0, -60), V(X + 10, 16, -35), 4), lam("gl_hangar", () => ({ map: wallPaint("gl_hangarW", "#c9ced8", "#8a8f9a") })));
    b.build(g);
    // private jet (nose +x): slim fuselage, swept wings, rear engines, T-tail, airstair
    const J = this.jet, white = lam("gl_jetW", () => ({ color: "#f4f6fa" })), dark = col("jetD", "#2b2e3a"), gold = col("jetG", "#d9b25a"), glass = col("jetGlass", "#1f2a3a");
    const prof: THREE.Vector2[] = [];
    for (let k = 0; k <= 40; k++) { const x = -9 + 18 * (k / 40); const r = x > 5 ? 1.25 * Math.sqrt(Math.max(0, 1 - ((x - 5) / 4) ** 2)) : x < -4 ? 1.25 * (0.3 + 0.7 * ((x + 9) / 5)) : 1.25; prof.push(new THREE.Vector2(Math.max(0.05, r), x)); }
    const fus = mesh(new THREE.LatheGeometry(prof, 28), white); fus.rotation.z = -Math.PI / 2; J.add(fus);
    for (const z of [1.22, -1.22]) { J.add(at(box(13, 0.12, 0.05, gold), -0.5, -0.1, z)); for (let i = 0; i < 6; i++) J.add(at(mesh(new THREE.SphereGeometry(0.17, 12, 8), glass), 3 - i * 1.25, 0.35, z * 0.98)); }
    J.add(at(box(0.8, 0.35, 1.6, glass), 6.6, 0.55, 0));
    const ws = new THREE.Shape(); ws.moveTo(1.4, 0); ws.lineTo(-1.2, 7); ws.lineTo(-2.4, 7); ws.lineTo(-1.6, 0); ws.lineTo(-2.4, -7); ws.lineTo(-1.2, -7); ws.closePath();
    const wing = mesh(new THREE.ExtrudeGeometry(ws, { depth: 0.18, bevelEnabled: false }), white); wing.rotation.x = Math.PI / 2; wing.position.set(0.5, -0.55, 0); J.add(wing);
    for (const z of [0.95, -0.95]) { const e = mesh(new THREE.CylinderGeometry(0.42, 0.48, 2.2, 16), white); e.rotation.z = Math.PI / 2; e.position.set(-5.6, 0.75, z * 1.55); J.add(e); J.add(at(box(0.6, 0.15, 0.5, white), -5.6, 0.75, z * 1.1)); }
    const fin = new THREE.Shape(); fin.moveTo(0, 0); fin.lineTo(2.6, 0); fin.lineTo(1.0, 3.2); fin.lineTo(-0.4, 3.2); fin.closePath();
    const fm = mesh(new THREE.ExtrudeGeometry(fin, { depth: 0.18, bevelEnabled: false }), white); fm.position.set(-8.6, 0.6, -0.09); J.add(fm);
    J.add(at(box(1.4, 0.12, 4.2, white), -8.2, 3.75, 0));
    for (const [x, z] of [[4.5, 0], [-0.5, 0.9], [-0.5, -0.9]] as [number, number][]) { J.add(at(box(0.12, 1.1, 0.12, dark), x, -1.55, z)); const w = cyl(0.28, 0.28, 0.2, dark, 12); w.rotation.x = Math.PI / 2; w.position.set(x, -2.05, z); J.add(w); }
    // airstair down from the front door (+z side)
    for (let i = 0; i < 6; i++) J.add(at(box(0.9, 0.08, 0.35, col("stair", "#d7d9de")), 4.6, -0.3 - i * 0.3, 1.5 + i * 0.32));
    const nm = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 0.45), pic(signTex("gl_jetName", ["DAN AIR"], { bg: "#f4f6fa", fg: "#d9b25a", w: 700, h: 100, sizes: [80], shadow: false }))); at(nm, -2.5, 0.05, 1.26); J.add(nm);
    at(J, X, 2.3, -6); g.add(J);
  }

  // ================= STREET + BANK =================
  private street() {
    const [X] = STREET, g = new THREE.Group(), b = new Batch(); this.root.add(g);
    b.add(quad(V(X - 80, 0.01, 30), V(X + 80, 0.01, 30), V(X + 80, 0.01, 6), V(X - 80, 0.01, 6), 160 / 8, 3), lam("gl_tarmacM", () => ({ map: tarmac() })));
    b.add(boxGeo(V(X - 80, 0, -30), V(X + 80, 0.15, 6), 3), lam("slabs", () => ({ map: slabs() })));
    // bank facade (made-up GOLDLEAF BANK), lit windows
    const stone = col("bankStone", "#d8ccb4");
    b.add(boxGeo(V(X + 2, 0, -18), V(X + 22, 14, -4), 3), stone);
    for (let i = 0; i < 5; i++) g.add(at(cyl(0.45, 0.5, 8, col("col", "#efe6d2"), 16), X + 4 + i * 4, 4.15, -3.3));
    b.add(boxGeo(V(X + 2, 8.1, -4.2), V(X + 22, 9.4, -2.6), 0), stone);
    b.add(boxGeo(V(X + 2, 0, -4), V(X + 22, 0.3, -2.4), 0), stone);
    const sg = new THREE.Mesh(new THREE.PlaneGeometry(6.8, 1.0), pic(signTex("gl_bank2", ["GOLDLEAF BANK"], { bg: "#22304f", fg: "#e8c45a", w: 1200, h: 176, sizes: [104], shadow: false })));
    at(sg, X + 7, 8.75, -2.58); g.add(sg);
    for (const dx of [6, 12, 18]) { const w = new THREE.Mesh(new THREE.PlaneGeometry(2.4, 4), glow("#ffd98a")); at(w, X + dx, 3.2, -3.98); g.add(w); }
    // other buildings with lit windows + streetlamps
    for (let k = 0; k < 6; k++) { const x0 = X - 70 + k * 12; if (x0 + 10 > X + 1) continue; b.add(boxGeo(V(x0, 0, -20), V(x0 + 10, 10 + (k % 3) * 4, -6), 3), col("bld" + (k % 3), ["#3a3550", "#4a3a3a", "#35485a"][k % 3]));
      for (let y = 1.5; y < 9; y += 2.2) for (let wx = x0 + 1; wx < x0 + 9; wx += 2.2) if (hh(k * 31 + wx + y) < 0.55) { const w = new THREE.Mesh(new THREE.PlaneGeometry(1, 1.2), glow("#ffd98a")); at(w, wx + 0.5, y, -5.98); g.add(w); } }
    for (const dx of [-14, -2, 10, 22]) { g.add(at(cyl(0.1, 0.14, 5, col("lampP", "#2a2a34"), 8), X + dx, 2.5, 5)); g.add(at(mesh(new THREE.SphereGeometry(0.4, 12, 8), glow("#fff2c4"), false), X + dx, 5.1, 5)); }
    b.build(g);
  }
}
