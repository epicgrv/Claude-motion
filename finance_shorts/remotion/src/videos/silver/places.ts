// Silver Thursday, the rest of the world (story shots 8-35). Every place is our own design, no real logos.
//  - TOWN (z = 400): a 1970s Texas main street: grocery (rising price board), "WE BUY SILVER" shop, bank, diner, retro cars
//  - OFFICE (x = 1000): the brothers' wood-panelled office: desk, phone, gold bar, big globe, window onto the oil field
//  - FLOOR (x = 1100): the exchange trading floor: giant price board, wall calendar, trader desks with screens, BUY/SELL console
//  - COURT (x = 1200): courtroom with judge's bench and jury box
//  - VAULT (x = 1300): a steel vault with its round door open, shelves empty
//  - ALPS (x = -1000, z = -900): snowy peaks + pines; the cargo plane flies over them
// Interiors are open-front rooms with a ceiling that casts no shadow (so the sun still lights the room).
import * as THREE from "three";
import { lam, quad, boxGeo, Batch, V } from "../bridge/build";
import { ctex } from "../bridge/paint";
import { marble, slabs, woodFloor, woodPanel, signTex, asphalt, wallPaint, carpet } from "../pepsi/tex";
import { V3 } from "./sets";

export const TOWN: V3 = [0, 0, 400];
export const OFFICE = 1000, FLOOR = 1100, COURT = 1200, VAULT = 1300;
export const ALPS: V3 = [-1000, 0, -900];

const mesh = (g: THREE.BufferGeometry, m: THREE.Material, cast = true) => { const o = new THREE.Mesh(g, m); o.castShadow = cast; o.receiveShadow = true; return o; };
const col = (key: string, c: string) => lam("pl_" + key, () => ({ color: c }));
const at = <T extends THREE.Object3D>(o: T, x: number, y: number, z: number, ry = 0) => { o.position.set(x, y, z); o.rotation.y = ry; return o; };
const box = (w: number, h: number, d: number, m: THREE.Material) => mesh(new THREE.BoxGeometry(w, h, d), m);
const cyl = (r0: number, r1: number, h: number, m: THREE.Material, seg = 16) => mesh(new THREE.CylinderGeometry(r0, r1, h, seg), m);
const picMat = (t: THREE.Texture) => new THREE.MeshBasicMaterial({ map: t, side: THREE.DoubleSide });
const plane = (w: number, h: number, m: THREE.Material) => new THREE.Mesh(new THREE.PlaneGeometry(w, h), m);
const hh = (i: number, s = 0) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };
const sign = (key: string, text: string[], o: { bg: string; fg: string; w?: number; h?: number; sizes?: number[]; stripe?: string }) => picMat(signTex("pl_" + key, text, { shadow: false, ...o }));

/** canvas texture we redraw when its content key changes */
export class DynTex {
  cv: HTMLCanvasElement; tex: THREE.CanvasTexture; key = "";
  constructor(w: number, h: number) {
    this.cv = document.createElement("canvas"); this.cv.width = w; this.cv.height = h;
    this.tex = new THREE.CanvasTexture(this.cv); this.tex.colorSpace = THREE.SRGBColorSpace; this.tex.anisotropy = 8;
  }
  set(key: string, draw: (g: CanvasRenderingContext2D, w: number, h: number) => void) {
    if (key === this.key) return;
    this.key = key;
    const g = this.cv.getContext("2d")!; g.setTransform(1, 0, 0, 1, 0, 0); g.clearRect(0, 0, this.cv.width, this.cv.height);
    draw(g, this.cv.width, this.cv.height); this.tex.needsUpdate = true;
  }
}

// ---------- painted textures ----------
const steel = () => ctex("pl_steel", 512, 512, (g, r) => {
  g.fillStyle = "#9aa3b0"; g.fillRect(0, 0, 512, 512);
  for (let y = 0; y < 512; y += 128) for (let x = 0; x < 512; x += 128) {
    g.fillStyle = r() < 0.5 ? "#a3acb9" : "#939cab"; g.fillRect(x + 2, y + 2, 124, 124);
    g.fillStyle = "#6c7584"; for (const [a, b] of [[10, 10], [116, 10], [10, 116], [116, 116]]) { g.beginPath(); g.arc(x + a, y + b, 5, 0, 7); g.fill(); }
  }
  g.strokeStyle = "rgba(255,255,255,.2)"; g.lineWidth = 2; for (let i = 0; i < 40; i++) { const x = r() * 512, y = r() * 512; g.beginPath(); g.moveTo(x, y); g.lineTo(x + 60, y + 4); g.stroke(); }
});
const windowView = () => ctex("pl_winView2", 1024, 512, (g, r) => {
  const sky = g.createLinearGradient(0, 0, 0, 300); sky.addColorStop(0, "#5f9fe0"); sky.addColorStop(1, "#cfe4f6");
  g.fillStyle = sky; g.fillRect(0, 0, 1024, 320);
  const cloud = (x: number, y: number, s2: number) => { g.fillStyle = "rgba(255,255,255,.92)"; for (const [dx, dy, rr] of [[0, 0, 28], [30, -10, 34], [64, 0, 26], [32, 8, 30]]) { g.beginPath(); g.arc(x + dx * s2, y + dy * s2, rr * s2, 0, 7); g.fill(); } };
  cloud(140, 80, 1.1); cloud(620, 60, 0.9); cloud(860, 120, 0.7);
  // far mesas (hazy violet), near mesas (warm, lit tops)
  const mesa = (pts: number[][], fill: string, top: string) => { g.fillStyle = fill; g.beginPath(); pts.forEach(([x, y], k) => (k ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); g.fill();
    g.fillStyle = top; g.fillRect(pts[1][0], pts[1][1], pts[2][0] - pts[1][0], 6); };
  mesa([[0, 300], [60, 238], [300, 238], [360, 300]], "#b79ab0", "#cdb3c4"); mesa([[520, 300], [600, 226], [880, 226], [960, 300]], "#b79ab0", "#cdb3c4");
  mesa([[180, 330], [250, 262], [470, 262], [540, 330]], "#c9784e", "#e29a68"); mesa([[700, 330], [760, 276], [1000, 276], [1024, 300], [1024, 330]], "#c9784e", "#e29a68");
  const sand = g.createLinearGradient(0, 300, 0, 512); sand.addColorStop(0, "#e8c48e"); sand.addColorStop(1, "#d6a468");
  g.fillStyle = sand; g.fillRect(0, 312, 1024, 200);
  g.fillStyle = "rgba(190,140,90,.35)"; for (let k = 0; k < 5; k++) { g.beginPath(); g.ellipse(100 + k * 220, 420 + (k % 2) * 30, 160, 16, 0, 0, 7); g.fill(); }
  // pumpjacks (proper silhouettes) + a derrick
  const pj = (x: number, y: number, s2: number) => { g.strokeStyle = "#2b2e3a"; g.fillStyle = "#2b2e3a"; g.lineWidth = 5 * s2;
    g.beginPath(); g.moveTo(x - 30 * s2, y); g.lineTo(x, y - 46 * s2); g.lineTo(x + 30 * s2, y); g.stroke();
    g.beginPath(); g.moveTo(x - 50 * s2, y - 44 * s2); g.lineTo(x + 52 * s2, y - 52 * s2); g.stroke();
    g.beginPath(); g.moveTo(x + 52 * s2, y - 60 * s2); g.quadraticCurveTo(x + 66 * s2, y - 50 * s2, x + 54 * s2, y - 34 * s2); g.lineTo(x + 50 * s2, y - 44 * s2); g.fill();
    g.fillRect(x - 58 * s2, y - 46 * s2, 14 * s2, 14 * s2); g.fillRect(x - 40 * s2, y - 3 * s2, 80 * s2, 4 * s2); };
  pj(160, 420, 1.0); pj(430, 380, 0.7); pj(860, 440, 1.1);
  g.strokeStyle = "#2b2e3a"; g.lineWidth = 4; const dx = 640, dy = 400;
  g.beginPath(); g.moveTo(dx - 26, dy); g.lineTo(dx - 4, dy - 170); g.lineTo(dx + 4, dy - 170); g.lineTo(dx + 26, dy); g.stroke();
  for (let k = 1; k < 6; k++) { const y = dy - k * 28, w2 = 26 - k * 4; g.beginPath(); g.moveTo(dx - w2, y); g.lineTo(dx + w2, y); g.moveTo(dx - w2 - 3, y + 28); g.lineTo(dx + w2, y); g.stroke(); }
  g.fillStyle = "#5c7a3a"; for (let k = 0; k < 14; k++) { g.beginPath(); g.arc(40 + r() * 950, 470 + r() * 30, 6 + r() * 8, 0, 7); g.fill(); }
});
const globeTex = (lit: number) => ctex("pl_globe2_" + Math.round(lit * 8), 1024, 512, (g, r) => {
  g.fillStyle = "#3f86d6"; g.fillRect(0, 0, 1024, 512);
  g.strokeStyle = "rgba(255,255,255,.25)"; g.lineWidth = 2;
  for (let x = 0; x < 1024; x += 64) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, 512); g.stroke(); }
  for (let y = 0; y < 512; y += 64) { g.beginPath(); g.moveTo(0, y); g.lineTo(1024, y); g.stroke(); }
  const land = (pts: number[][], c: string) => { g.fillStyle = c; g.strokeStyle = "#241726"; g.lineWidth = 5; g.beginPath(); pts.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); g.fill(); g.stroke(); };
  const green = "#6fb24f";
  land([[120, 90], [250, 70], [330, 120], [300, 200], [250, 230], [230, 270], [190, 230], [140, 180], [100, 140]], green);       // N. America
  land([[250, 280], [310, 290], [330, 350], [290, 440], [260, 450], [240, 370]], green);                                          // S. America
  land([[470, 90], [560, 80], [580, 140], [520, 170], [480, 150]], green);                                                          // Europe
  land([[480, 190], [580, 190], [610, 260], [580, 360], [540, 400], [510, 330], [470, 260]], green);                              // Africa
  land([[590, 70], [820, 60], [900, 130], [860, 220], [760, 240], [700, 200], [620, 160]], green);                                // Asia
  land([[800, 330], [890, 320], [910, 380], [840, 400], [790, 370]], green);                                                        // Australia
  if (lit > 0) { // one third of the world turns silver (hatched), with a bold outline
    g.save(); g.globalAlpha = 0.5 * lit; g.beginPath(); g.rect(100, 0, 341, 512); g.clip();
    const gr = g.createLinearGradient(100, 0, 441, 512); gr.addColorStop(0, "#ffffff"); gr.addColorStop(0.5, "#c9d3e0"); gr.addColorStop(1, "#f4f7fb");
    g.fillStyle = gr; g.fillRect(100, 0, 341, 512);
    g.globalAlpha = 0.35 * lit; g.strokeStyle = "#ffffff"; g.lineWidth = 8; for (let k = -512; k < 512; k += 40) { g.beginPath(); g.moveTo(100 + k, 0); g.lineTo(100 + k + 512, 512); g.stroke(); }
    g.restore(); g.globalAlpha = lit; g.strokeStyle = "#e8c45a"; g.lineWidth = 10; g.setLineDash([26, 16]); g.strokeRect(100, 6, 341, 500); g.setLineDash([]); g.globalAlpha = 1;
  }
  void r;
});

export class Places {
  root = new THREE.Group();
  priceTex = new DynTex(512, 512);         // grocery window price board
  boardTex = new DynTex(1600, 720);        // trading floor price board
  calTex = new DynTex(512, 640);           // wall calendar
  consoleTex = new DynTex(1024, 512);      // BUY / SELL console
  screenTex = new DynTex(256, 192);        // trader CRT screens (shared)
  globe: THREE.Mesh; globeMat: THREE.MeshLambertMaterial;
  phone = new THREE.Group(); handset = new THREE.Group();
  goldBar!: THREE.Group;
  carts: THREE.Group[] = [];
  plane = new THREE.Group(); props: THREE.Group[] = []; propsSpin: THREE.Group[] = [];
  cars: { g: THREE.Group; x0: number; v: number; z: number }[] = [];
  vaultDoor = new THREE.Group();

  constructor() {
    this.town(); this.office(); this.floor(); this.court(); this.vault(); this.alps(); this.makeCarts();
  }

  /** open-front room: floor, back + side walls, a no-shadow ceiling */
  private room(x0: number, w: number, h: number, d: number, floor: THREE.Material, wall: THREE.Material, ceil = "#3a3140") {
    const g = new THREE.Group(), b = new Batch(); this.root.add(g);
    b.add(boxGeo(V(x0 - w / 2 - 0.3, -0.3, -d), V(x0 + w / 2 + 0.3, 0, 4), 2), floor);
    b.add(boxGeo(V(x0 - w / 2, 0, -d - 0.3), V(x0 + w / 2, h, -d), 2), wall);
    for (const s of [-1, 1]) b.add(boxGeo(V(x0 + s * w / 2 - (s > 0 ? 0 : 0.3), 0, -d), V(x0 + s * w / 2 + (s > 0 ? 0.3 : 0), h, 4), 2), wall);
    b.build(g);
    const c = mesh(new THREE.BoxGeometry(w + 0.6, 0.2, d + 4), col("ceil" + ceil, ceil), false); at(c, x0, h + 0.1, (4 - d) / 2); g.add(c);
    return g;
  }

  // ================= TOWN =================
  private town() {
    const [X, , Z] = TOWN, b = new Batch(), T = new THREE.Group(); this.root.add(T);
    b.add(quad(V(X - 90, 0.02, Z + 5), V(X + 90, 0.02, Z + 5), V(X + 90, 0.02, Z - 5), V(X - 90, 0.02, Z - 5), 180 / 8, 1), lam("asphalt", () => ({ map: asphalt() })));
    const wk = lam("slabs", () => ({ map: slabs() }));
    b.add(boxGeo(V(X - 90, 0, Z + 5), V(X + 90, 0.15, Z + 11), 3), wk);
    b.add(boxGeo(V(X - 90, 0, Z - 11), V(X + 90, 0.15, Z - 5), 3), wk);
    // north storefronts (facade at z = Z + 11, facing -z toward the street)
    const shop = (x0: number, x1: number, h: number, wall: string, sg: THREE.Material, awn?: string) => {
      b.add(boxGeo(V(X + x0, 0, Z + 11), V(X + x1, h, Z + 24), 3), col("w" + wall, wall));
      b.add(boxGeo(V(X + x0 + 0.8, 0.6, Z + 10.96), V(X + x1 - 0.8, 3.4, Z + 11.0), 0), col("glass", "#2f5f9e"));
      b.add(boxGeo(V(X + x0, h, Z + 10.8), V(X + x1, h + 0.5, Z + 11.2), 0), col("cornice", "#f4f1ea"));
      if (awn) b.add(boxGeo(V(X + x0 + 0.4, 3.6, Z + 9.4), V(X + x1 - 0.4, 3.9, Z + 11), 0), col("awn" + awn, awn));
      const s = plane(x1 - x0 - 1.6, 1.3, sg); s.rotation.y = Math.PI; at(s, X + (x0 + x1) / 2, h - 1.1, Z + 10.94); s.rotation.y = Math.PI; T.add(s);
    };
    shop(-44, -30, 6.5, "#d9824f", sign("diner", ["DINER"], { bg: "#e2453c", fg: "#fff6d6", w: 800, h: 160, sizes: [110] }), "#f2c94c");
    shop(-28, -12, 6.0, "#7fb6a0", sign("grocery", ["GROCERY"], { bg: "#f4f1ea", fg: "#2f7a3a", w: 1000, h: 140, sizes: [104] }), "#3fae8a");
    shop(-10, 6, 6.8, "#c8b48a", sign("webuy", ["WE BUY SILVER"], { bg: "#241726", fg: "#e8edf5", w: 1200, h: 160, sizes: [100], stripe: "#9aa6b5" }), "#5a6478");
    shop(8, 28, 8.5, "#ece6da", sign("bank", ["FIRST TEXAS BANK"], { bg: "#ece6da", fg: "#1d3f8a", w: 1400, h: 140, sizes: [96] }));
    shop(30, 44, 6.2, "#a27ac9", sign("records", ["RECORDS"], { bg: "#f08a2c", fg: "#241726", w: 900, h: 160, sizes: [110] }), "#e2453c");
    for (const x of [10.5, 14.5, 21.5, 25.5]) T.add(at(cyl(0.35, 0.4, 5.6, col("column", "#f4f1ea"), 14), X + x, 2.95, Z + 10.4));
    // grocery window price board
    const pb = plane(4.6, 2.4, picMat(this.priceTex.tex)); pb.rotation.y = Math.PI; at(pb, X - 20, 2.1, Z + 10.9); pb.rotation.y = Math.PI; T.add(pb);
    // "WE BUY SILVER" window: forks + candlesticks painted
    const wb = plane(5.2, 2.0, sign("wbwin", ["CASH 4 SILVER", "FORKS • SPOONS • TROPHIES"], { bg: "#fff36b", fg: "#241726", w: 1000, h: 380, sizes: [100, 46] }));
    wb.rotation.y = Math.PI; at(wb, X - 4.5, 2.1, Z + 10.9); wb.rotation.y = Math.PI; T.add(wb);
    b.add(boxGeo(V(X + 1, 0.15, Z + 10.95), V(X + 3, 3.2, Z + 11.0), 0), col("door", "#5a3b2a"));
    // far side (south) facades, simple
    for (let x = -88, k = 0; x < 88; x += 16, k++) {
      const h = 6 + (k % 3) * 1.5, c = ["#d9a441", "#c25a7a", "#5a8fc2", "#9ab86a", "#e8b33a"][k % 5];
      b.add(boxGeo(V(X + x, 0, Z - 24), V(X + x + 15, h, Z - 11), 3), col("s" + c, c));
      for (let wx = x + 1.5; wx < x + 14; wx += 3.4) b.add(boxGeo(V(X + wx, 1.2, Z - 11.04), V(X + wx + 2, 3.2, Z - 11.0), 0), col("glass", "#2f5f9e"));
    }
    // lamp posts
    for (let x = -70; x <= 70; x += 20) for (const s of [-1, 1]) { T.add(at(cyl(0.1, 0.12, 5, col("lamp", "#3a3d4a"), 8), X + x, 2.5, Z + s * 5.6)); T.add(at(mesh(new THREE.SphereGeometry(0.32, 10, 8), col("bulb", "#fff2c4")), X + x, 5.1, Z + s * 5.6)); }
    b.build(T);
    // 70s cars (boxy sedans, two-tone)
    const carCols = ["#d9823a", "#5d7a3a", "#c0353a", "#e8c45a", "#3f6fb5", "#8a5a34"];
    for (let i = 0; i < 6; i++) {
      const g = this.car(carCols[i]); T.add(g);
      const parked = i >= 3, z = parked ? Z + 3.9 : i % 2 ? Z - 2 : Z + 2;
      this.cars.push({ g, x0: parked ? X - 36 + i * 22 : X - 70 + i * 50, v: parked ? 0 : i % 2 ? -9 : 11, z });
    }
  }
  private car(c: string) {
    const g = new THREE.Group(), body = col("car" + c, c), dark = col("tyre", "#24222a"), chrome = col("chrome", "#d7d9de"), glass = col("cglass", "#2c4a7a");
    g.add(at(box(5.0, 0.8, 2.0, body), 0, 0.75, 0));
    g.add(at(box(2.8, 0.75, 1.8, col("roof" + c, "#f4f1ea")), -0.2, 1.5, 0));
    g.add(at(box(2.85, 0.55, 1.82, glass), -0.2, 1.45, 0));
    for (const sx of [-2.52, 2.52]) g.add(at(box(0.08, 0.3, 2.0, chrome), sx, 0.6, 0));
    for (const [x, z] of [[-1.7, 1], [1.6, 1], [-1.7, -1], [1.6, -1]]) { const w = cyl(0.42, 0.42, 0.3, dark, 14); w.rotation.x = Math.PI / 2; w.position.set(x, 0.42, z * 0.95); g.add(w); }
    for (const z of [-0.65, 0.65]) g.add(at(mesh(new THREE.SphereGeometry(0.16, 10, 8), col("hl", "#fff2c4")), 2.5, 0.85, z));
    return g;
  }

  // ================= OFFICE =================
  private office() {
    const X = OFFICE, g = this.room(X, 12, 5, 9, lam("pl_offFloor2", () => ({ map: carpet("pl_offCarpet2", "#2f5a46") })), lam("pl_offWall", () => ({ map: wallPaint("pl_offWallT", "#ece3cf", "#7a5236", true) })));
    const b = new Batch();
    const wd = lam("pl_desk", () => ({ map: woodFloor("pl_deskW", "#7a4a2c") }));
    // desk
    b.add(boxGeo(V(X - 2.2, 0, -2.4), V(X + 2.2, 0.85, -1.5), 1), wd);
    b.add(boxGeo(V(X - 2.3, 0.85, -2.5), V(X + 2.3, 0.95, -1.4), 1), wd);
    // window onto the oil field
    const win = plane(5.6, 2.6, picMat(windowView())); at(win, X - 1, 2.6, -8.98); g.add(win);
    for (const [x0, y0, x1, y1] of [[-3.9, 1.2, 1.9, 1.35], [-3.9, 3.85, 1.9, 4.0], [-3.9, 1.2, -3.75, 4.0], [1.75, 1.2, 1.9, 4.0], [-1.08, 1.2, -0.92, 4.0]])
      b.add(boxGeo(V(X + x0, y0, -8.97), V(X + x1, y1, -8.85), 0), col("frame", "#f4f1ea"));
    // bookshelf left
    b.add(boxGeo(V(X - 5.9, 0, -8.5), V(X - 4.3, 3.4, -6.8), 0), col("shelf", "#5a3b2a"));
    for (let i = 0; i < 4; i++) for (let k = 0; k < 6; k++) b.add(boxGeo(V(X - 5.8 + k * 0.24, 0.4 + i * 0.8, -6.85), V(X - 5.62 + k * 0.24, 0.95 + i * 0.8 - 0.1 * (k % 2), -6.8), 0), col("book" + ((i + k) % 4), ["#c0353a", "#3f6fb5", "#e8b33a", "#3fae8a"][(i + k) % 4]));
    // lone-star state flag on the wall (state flag, not a brand)
    const fl = plane(1.8, 1.2, picMat(ctex("pl_txflag", 360, 240, (gg) => {
      gg.fillStyle = "#1d3f8a"; gg.fillRect(0, 0, 120, 240); gg.fillStyle = "#f4f1ea"; gg.fillRect(120, 0, 240, 120); gg.fillStyle = "#c0262f"; gg.fillRect(120, 120, 240, 120);
      gg.fillStyle = "#f4f1ea"; gg.beginPath(); for (let i = 0; i < 10; i++) { const r = i % 2 ? 18 : 44, a = -Math.PI / 2 + (i * Math.PI) / 5; gg.lineTo(60 + r * Math.cos(a), 120 + r * Math.sin(a)); } gg.fill();
    })));
    at(fl, X + 3.6, 3.2, -8.97); g.add(fl);
    b.build(g);
    // phone (body + handset) on the desk, right
    this.phone.add(at(box(0.36, 0.14, 0.3, col("phone", "#c0262f")), 0, 0.07, 0));
    this.handset.add(at(box(0.42, 0.09, 0.1, col("phone", "#c0262f")), 0, 0, 0));
    for (const s of [-1, 1]) this.handset.add(at(box(0.1, 0.1, 0.12, col("phone", "#c0262f")), s * 0.18, -0.03, 0));
    at(this.handset, 0, 0.19, 0); this.phone.add(this.handset);
    at(this.phone, X + 1.5, 0.95, -1.95, -0.3); g.add(this.phone);
    // gold bar (S10)
    const gb = new THREE.Group(); gb.add(at(box(0.5, 0.16, 0.24, col("gold", "#e8b33a")), 0, 0.08, 0));
    at(gb, X - 0.4, 0.95, -1.9, 0.2); g.add(gb); this.goldBar = gb; this.props.push(gb);
    // big globe on a stand (right, front of the flag)
    this.globeMat = lam("pl_globeM", () => ({ map: globeTex(0) })) as THREE.MeshLambertMaterial;
    this.globe = mesh(new THREE.SphereGeometry(1.05, 48, 24), this.globeMat); at(this.globe, X + 3.6, 2.0, -4.6); this.globe.rotation.z = 0.41; g.add(this.globe);
    g.add(at(cyl(0.08, 0.1, 0.95, col("brass", "#c9a24a"), 10), X + 3.6, 0.47, -4.6));  // stand below the globe only
    g.add(at(cyl(0.5, 0.6, 0.12, col("brass", "#c9a24a"), 18), X + 3.6, 0.06, -4.6));
  }
  setGlobe(lit: number) { const m = globeTex(lit); if (this.globeMat.map !== m) { this.globeMat.map = m; this.globeMat.needsUpdate = true; } }

  // ================= TRADING FLOOR =================
  private floor() {
    const X = FLOOR, g = this.room(X, 24, 9, 16, lam("pl_floorM", () => ({ map: woodFloor("pl_floorW", "#a07a52") })), lam("pl_floorWall", () => ({ map: wallPaint("pl_fwall", "#d8d2c4", "#5a6478") })), "#2b2433");
    const b = new Batch();
    // big board on the back wall
    const brd = plane(15, 6.75, picMat(this.boardTex.tex)); at(brd, X, 5.3, -15.95); g.add(brd);
    b.add(boxGeo(V(X - 7.8, 1.75, -16), V(X + 7.8, 8.9, -15.98), 0), col("bframe", "#241726"));
    // wall calendar (left of the board)
    const cal = plane(2.2, 2.75, picMat(this.calTex.tex)); at(cal, X - 10, 4.6, -15.95); g.add(cal);
    // podium in front of the board
    b.add(boxGeo(V(X - 0.8, 0, -12.6), V(X + 0.8, 1.15, -11.8), 0), col("podium", "#5a3b2a"));
    // trader desks with CRT screens (3 rows)
    const scr = picMat(this.screenTex.tex);
    for (let r = 0; r < 3; r++) for (let k = 0; k < 4; k++) {
      const x = X - 8.4 + k * 5.6, z = -9 + r * 4.2;
      b.add(boxGeo(V(x - 2.0, 0, z - 0.55), V(x + 2.0, 0.85, z + 0.55), 0), col("deskF", "#e6e0d4"));
      for (const sx of [-1, 1]) {
        const mx = x + sx * 0.9;
        b.add(boxGeo(V(mx - 0.12, 0.85, z - 0.3), V(mx + 0.12, 0.93, z - 0.1), 0), col("crtStand", "#9a9384"));
        b.add(boxGeo(V(mx - 0.28, 0.98, z - 0.5), V(mx + 0.28, 1.42, z - 0.2), 0), col("crtBack", "#bdb6a6"));   // tube housing
        b.add(boxGeo(V(mx - 0.4, 0.93, z - 0.2), V(mx + 0.4, 1.52, z + 0.02), 0), col("crt", "#d9d2c2"));        // front case
        b.add(boxGeo(V(mx - 0.36, 0.97, z + 0.02), V(mx + 0.36, 1.48, z + 0.04), 0), col("bezel", "#3a3d47"));    // dark bezel
        const s = plane(0.6, 0.43, scr); at(s, mx, 1.225, z + 0.045); g.add(s);
        b.add(boxGeo(V(mx - 0.32, 0.85, z + 0.18), V(mx + 0.32, 0.89, z + 0.42), 0), col("kbd", "#cfc8b8"));       // keyboard
        for (let k = 0; k < 4; k++) b.add(boxGeo(V(mx - 0.29, 0.89, z + 0.2 + k * 0.055), V(mx + 0.29, 0.9, z + 0.24 + k * 0.055), 0), col("keys", "#8f8a7e"));
      }
    }
    // BUY / SELL console (close-up desk at front right)
    b.add(boxGeo(V(X + 3.0, 0, 1.0), V(X + 6.0, 0.9, 2.4), 0), col("deskF", "#e6e0d4"));
    const cons = plane(2.8, 1.4, picMat(this.consoleTex.tex)); cons.rotation.x = -Math.PI / 2 + 0.35; at(cons, X + 4.5, 0.95, 1.7); cons.rotation.x = -Math.PI / 2 + 0.35; g.add(cons);
    // ticker banner along the top of the side walls
    for (const s of [-1, 1]) { const tk = plane(14, 0.7, sign("ticker", ["Ag ▲  Au ▼  Cu ▲  Ag ▲  Au ▼"], { bg: "#14101a", fg: "#5cf5a6", w: 2048, h: 102, sizes: [70] })); tk.rotation.y = -s * Math.PI / 2; at(tk, X + s * 11.95, 7.6, -7); tk.rotation.y = -s * Math.PI / 2; g.add(tk); }
    b.build(g);
  }

  // ================= COURT =================
  private court() {
    const X = COURT, g = this.room(X, 12, 6, 9, lam("pl_courtF", () => ({ map: woodFloor("pl_courtFW", "#8a5a3c") })), lam("woodPanel", () => ({ map: woodPanel() })), "#2b2433");
    const b = new Batch(), mm = lam("marble", () => ({ map: marble() })), wd = col("bench", "#6a3f26");
    b.add(boxGeo(V(X - 2.4, 0, -7.6), V(X + 2.4, 1.6, -6.4), 0), wd);                 // judge's bench
    b.add(boxGeo(V(X - 2.5, 1.6, -7.7), V(X + 2.5, 1.7, -6.3), 0), col("benchTop", "#4a2c1a"));
    b.add(boxGeo(V(X - 1.2, 0, -8.9), V(X + 1.2, 4.2, -8.7), 0), mm);
    const seal = plane(1.5, 1.5, picMat(ctex("pl_seal", 256, 256, (gg) => { gg.fillStyle = "#e8c45a"; gg.beginPath(); gg.arc(128, 128, 120, 0, 7); gg.fill(); gg.strokeStyle = "#241726"; gg.lineWidth = 10; gg.stroke(); gg.fillStyle = "#241726"; gg.font = "900 60px Arial"; gg.textAlign = "center"; gg.textBaseline = "middle"; gg.fillText("⚖", 128, 132); })));
    at(seal, X, 3.4, -8.65); g.add(seal);
    // jury box (right): low wall + two tiers
    b.add(boxGeo(V(X + 2.6, 0, -1.6), V(X + 5.9, 0.85, -1.4), 0), wd);
    b.add(boxGeo(V(X + 2.6, 0, -4.2), V(X + 5.9, 0.3, -1.6), 0), wd);
    b.add(boxGeo(V(X + 2.6, 0.3, -4.2), V(X + 5.9, 0.6, -2.9), 0), wd);
    // defendants' table (left front)
    b.add(boxGeo(V(X - 4.6, 0, -1.4), V(X - 1.4, 0.8, -0.6), 0), wd);
    b.build(g);
  }

  // ================= VAULT =================
  private vault() {
    const X = VAULT, st = lam("pl_steelM", () => ({ map: steel() }));
    const g = this.room(X, 8, 4.4, 8, st, st, "#5a6170");
    const b = new Batch();
    for (const s of [-1, 1]) for (let i = 0; i < 4; i++) b.add(boxGeo(V(X + s * 3.95 - (s > 0 ? 1.2 : 0), 0.4 + i * 0.95, -7.6), V(X + s * 3.95 + (s < 0 ? 1.2 : 0), 0.48 + i * 0.95, -1.0), 0), col("shelfS", "#6c7584"));
    b.build(g);
    // round door, open, on the back wall left; dark opening behind
    const hole = new THREE.Mesh(new THREE.CircleGeometry(1.6, 48), picMat(ctex("pl_vaultIn", 512, 512, (gg) => {
      const bg = gg.createRadialGradient(256, 230, 30, 256, 256, 300); bg.addColorStop(0, "#f2efe6"); bg.addColorStop(1, "#8d96a6"); gg.fillStyle = bg; gg.fillRect(0, 0, 512, 512);
      gg.fillStyle = "#6c7584"; gg.beginPath(); gg.moveTo(0, 512); gg.lineTo(160, 340); gg.lineTo(352, 340); gg.lineTo(512, 512); gg.fill();           // floor
      gg.strokeStyle = "#5a6170"; gg.lineWidth = 10;
      for (const s2 of [-1, 1]) for (let k = 0; k < 4; k++) { const y = 150 + k * 55; gg.beginPath(); gg.moveTo(256 + s2 * 250, y + 40 + k * 10); gg.lineTo(256 + s2 * 100, y); gg.stroke(); }   // empty shelves
      gg.fillStyle = "#4a5160"; gg.fillRect(170, 120, 172, 220); gg.fillStyle = "#e9e3d4"; gg.fillRect(180, 130, 152, 200);                                       // back wall + lit niche
      gg.fillStyle = "#c9ced8"; gg.font = '900 42px "Arial Black", Arial'; gg.textAlign = "center"; gg.fillText("EMPTY", 256, 245);
      gg.strokeStyle = "#241726"; gg.lineWidth = 18; gg.beginPath(); gg.arc(256, 256, 247, 0, 7); gg.stroke();
    })));
    at(hole, X - 0.8, 2.0, -7.97); g.add(hole);
    const door = mesh(new THREE.CylinderGeometry(1.7, 1.7, 0.5, 40), col("vdoor", "#b9c0cc")); door.rotation.x = Math.PI / 2; this.vaultDoor.add(door);
    for (let i = 0; i < 6; i++) { const sp = box(0.12, 2.4, 0.08, col("spoke", "#6c7584")); sp.rotation.z = (i * Math.PI) / 6; sp.position.z = 0.29; this.vaultDoor.add(sp); }
    this.vaultDoor.add(at(cyl(0.3, 0.3, 0.2, col("hub", "#6c7584")), 0, 0, 0.35).rotateX(Math.PI / 2) as THREE.Object3D);
    at(this.vaultDoor, X + 2.0, 2.0, -6.6, -1.2); g.add(this.vaultDoor);
    // a single spotlight pool on the floor
    const pool = mesh(new THREE.CircleGeometry(1.6, 32), new THREE.MeshBasicMaterial({ color: "#ffffff", transparent: true, opacity: 0.12, depthWrite: false }), false);
    pool.rotation.x = -Math.PI / 2; at(pool, X, 0.01, -3.2); g.add(pool);
  }

  /** shopping carts full of silver bars (posed per shot on the exchange plaza) */
  private makeCarts() {
    const wire = col("cartW", "#b9c0cc"), red = col("cartR", "#d8323c"), bar = col("cartBar", "#dfe5ee"), tyre = col("tyre", "#24222a");
    for (let i = 0; i < 10; i++) {
      const g = new THREE.Group(); g.visible = false; this.root.add(g);
      for (const [w, h, d, x, y, z] of [[1.1, 0.05, 0.7, 0, 0.45, 0], [1.1, 0.6, 0.04, 0, 0.75, 0.35], [1.1, 0.6, 0.04, 0, 0.75, -0.35], [0.04, 0.6, 0.7, 0.55, 0.75, 0], [0.04, 0.6, 0.7, -0.55, 0.75, 0]] as number[][])
        g.add(at(box(w, h, d, wire), x, y, z));
      g.add(at(box(0.05, 0.05, 0.8, red), -0.75, 1.15, 0)); g.add(at(box(0.25, 0.04, 0.04, wire), -0.65, 1.12, 0.35)); g.add(at(box(0.25, 0.04, 0.04, wire), -0.65, 1.12, -0.35));
      for (const [x, z] of [[0.45, 0.3], [0.45, -0.3], [-0.45, 0.3], [-0.45, -0.3]]) { const w = cyl(0.1, 0.1, 0.06, tyre, 10); w.rotation.x = Math.PI / 2; w.position.set(x, 0.1, z); g.add(w); }
      g.add(at(box(0.05, 0.4, 0.05, wire), 0.45, 0.25, 0.3)); g.add(at(box(0.05, 0.4, 0.05, wire), -0.45, 0.25, 0.3)); g.add(at(box(0.05, 0.4, 0.05, wire), 0.45, 0.25, -0.3)); g.add(at(box(0.05, 0.4, 0.05, wire), -0.45, 0.25, -0.3));
      for (let k = 0; k < 14; k++) { const L = Math.floor(k / 5); g.add(at(box(0.36, 0.12, 0.18, bar), -0.36 + (k % 5) * 0.18 + L * 0.05, 0.54 + L * 0.13 + (k % 2) * 0.02, -0.18 + (k % 3) * 0.18, (k % 2) * 0.3)); }
      this.carts.push(g);
    }
  }

  // ================= ALPS + CARGO PLANE =================
  private alps() {
    const [X, , Z] = ALPS, g = new THREE.Group(); this.root.add(g);
    const snow = col("snow", "#f4f7fb"), rock = col("rockA", "#8a8f9a"), pine = col("pine", "#2f6a4a");
    const gp = mesh(new THREE.PlaneGeometry(1400, 1400), snow, false); gp.rotation.x = -Math.PI / 2; at(gp, X, 0.05, Z); g.add(gp);
    for (let i = 0; i < 40; i++) {
      const a = hh(i, 1) * Math.PI * 2, d = 40 + 380 * hh(i, 2), r = 50 + 70 * hh(i, 3), h = 90 + 140 * hh(i, 4);
      const x = X + Math.cos(a) * d, z = Z + Math.sin(a) * d;
      const m = mesh(new THREE.ConeGeometry(r, h, 7 + (i % 4)), rock); at(m, x, h / 2, z, hh(i, 5) * 3); g.add(m);
      const c = mesh(new THREE.ConeGeometry(r * 0.42, h * 0.42, 7 + (i % 4)), snow); at(c, x, h - h * 0.21 + 0.5, z, hh(i, 5) * 3); g.add(c);
    }
    for (let i = 0; i < 120; i++) {
      const x = X + (hh(i, 6) - 0.5) * 700, z = Z + (hh(i, 7) - 0.5) * 700, s = 4 + 6 * hh(i, 8);
      g.add(at(mesh(new THREE.ConeGeometry(s * 0.45, s * 1.6, 7), pine), x, s * 0.8, z));
    }
    // cargo plane (nose = +x): lathe fuselage with an upswept tail, tapered high wing, 4 turboprops, swept fin
    const P = this.plane, body = lam("pl_planeB", () => ({ color: "#c3c9d3" })), dark = col("planeD", "#4a505c"), stripe = col("planeS", "#1d3f8a"), glass = col("pglass", "#1f2a3a");
    const prof: THREE.Vector2[] = [];
    for (let k = 0; k <= 40; k++) { const x = -15 + 30 * (k / 40); const r = x > 10 ? 2.25 * Math.sqrt(Math.max(0, 1 - ((x - 10) / 5) ** 2)) : x < -6 ? 2.25 * (0.35 + 0.65 * ((x + 15) / 9)) : 2.25; prof.push(new THREE.Vector2(Math.max(0.05, r), x)); }
    const fus = mesh(new THREE.LatheGeometry(prof, 28), body); fus.rotation.z = -Math.PI / 2; fus.scale.set(1, 1, 0.95); P.add(fus);
    const tailUp = mesh(new THREE.BoxGeometry(9, 1.2, 1.6), body); tailUp.position.set(-11, 1.3, 0); tailUp.rotation.z = 0.12; P.add(tailUp);
    // cockpit windows + cabin windows + stripe
    for (const z of [-0.9, 0.9]) P.add(at(box(1.4, 0.5, 0.5, glass), 12.2, 1.1, z));
    P.add(at(box(1.0, 0.45, 1.5, glass), 12.6, 1.25, 0));
    for (let i = 0; i < 9; i++) for (const z of [2.17, -2.17]) P.add(at(box(0.5, 0.45, 0.06, glass), 8 - i * 1.9, 0.7, z));
    for (const z of [2.2, -2.2]) P.add(at(box(22, 0.28, 0.06, stripe), -1, 0.05, z));
    // wing: tapered planform, extruded thin, mounted high
    const wsh = new THREE.Shape(); wsh.moveTo(2.6, 0); wsh.lineTo(1.6, 21); wsh.lineTo(-0.6, 21); wsh.lineTo(-2.8, 0); wsh.lineTo(-0.6, -21); wsh.lineTo(1.6, -21); wsh.closePath();
    const wing = mesh(new THREE.ExtrudeGeometry(wsh, { depth: 0.45, bevelEnabled: true, bevelThickness: 0.12, bevelSize: 0.12, bevelSegments: 1 }), body); wing.rotation.x = Math.PI / 2; wing.position.set(1.5, 2.55, 0); P.add(wing);
    // engines + spinning props
    this.propsSpin = [];
    for (const z of [-12.5, -6.5, 6.5, 12.5]) {
      const nac = mesh(new THREE.CylinderGeometry(0.7, 0.85, 4.2, 16), body); nac.rotation.z = Math.PI / 2; nac.position.set(3.2, 1.95, z); P.add(nac);
      const sp = mesh(new THREE.ConeGeometry(0.45, 0.9, 14), dark); sp.rotation.z = -Math.PI / 2; sp.position.set(5.75, 1.95, z); P.add(sp);
      const rot = new THREE.Group(); rot.position.set(5.5, 1.95, z); P.add(rot);
      for (let k = 0; k < 4; k++) { const bl = box(0.12, 2.1, 0.32, dark); bl.position.y = 1.05; const arm = new THREE.Group(); arm.rotation.x = (k * Math.PI) / 2; arm.add(bl); rot.add(arm); }
      const disc = new THREE.Mesh(new THREE.CircleGeometry(2.15, 32), new THREE.MeshBasicMaterial({ color: "#3a404c", transparent: true, opacity: 0.18, depthWrite: false })); disc.rotation.y = Math.PI / 2; rot.add(disc);
      this.propsSpin.push(rot);
    }
    // swept vertical fin + tapered stabilisers
    const fin = new THREE.Shape(); fin.moveTo(0, 0); fin.lineTo(5, 0); fin.lineTo(2.2, 7.5); fin.lineTo(-0.6, 7.5); fin.closePath();
    const finM = mesh(new THREE.ExtrudeGeometry(fin, { depth: 0.35, bevelEnabled: false }), body); finM.position.set(-16.6, 1.6, -0.17); P.add(finM);
    const finBand = mesh(new THREE.ExtrudeGeometry(new THREE.Shape([new THREE.Vector2(1.7, 4.6), new THREE.Vector2(3.9, 4.6), new THREE.Vector2(3.1, 6.3), new THREE.Vector2(0.9, 6.3)]), { depth: 0.37, bevelEnabled: false }), stripe);
    finBand.position.set(-16.6, 1.6, -0.18); P.add(finBand);
    const hs = new THREE.Shape(); hs.moveTo(1.2, 0); hs.lineTo(0.2, 7); hs.lineTo(-1.2, 7); hs.lineTo(-2.4, 0); hs.lineTo(-1.2, -7); hs.lineTo(0.2, -7); hs.closePath();
    const hsm = mesh(new THREE.ExtrudeGeometry(hs, { depth: 0.25, bevelEnabled: false }), body); hsm.rotation.x = Math.PI / 2; hsm.position.set(-14.6, 2.3, 0); P.add(hsm);
    // landing-gear sponsons + name
    for (const z of [2.1, -2.1]) P.add(at(box(6, 1.0, 0.6, body), 0.5, -1.4, z));
    const nm = plane(8, 1.0, sign("cargo2", ["SILVER AIR CARGO"], { bg: "#c3c9d3", fg: "#1d3f8a", w: 1200, h: 150, sizes: [110] })); at(nm, 1, 1.2, 2.24); P.add(nm);
    g.add(P);
  }
}
