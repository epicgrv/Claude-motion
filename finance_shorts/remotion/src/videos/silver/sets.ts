// "Silver Thursday" world: one three.js scene with three places far apart so no shot sees another.
//  - MOUNT (origin): Texas desert, red mesas, cacti and the brothers' mountain of silver bars (instanced, shiny)
//  - EXCH (x = -400): the made-up "SILVERMART EXCHANGE": marble steps, columns, pediment, glass towers behind
//  - RANCH (x = +400): ranch house, rail fence, nodding pumpjacks, an oil derrick (gusher), "BIG STATE OIL" arch
import * as THREE from "three";
import { lam, quad, boxGeo, Batch, V } from "../bridge/build";
import { twoTone } from "../bridge/shade";
import { ctex } from "../bridge/paint";
import { marble, slabs, glassTower, signTex } from "../pepsi/tex";

export type V3 = [number, number, number];
export const MOUNT: V3 = [0, 0, 0];
export const EXCH: V3 = [-400, 0, 0];
export const RANCH: V3 = [400, 0, 0];
/** bar size and mountain shape */
const BW = 0.9, BH = 0.3, BD = 0.45, LAYERS = 20, R0 = 10.5;
export const TOP_Y = LAYERS * BH;               // the brothers stand here (top plateau radius ~1.9)
/** exchange: top step height / front edge z of the top step */
export const EX_STEP_Y = 1.6, EX_STEP_Z = 6.2;

const mesh = (g: THREE.BufferGeometry, m: THREE.Material, cast = true) => { const o = new THREE.Mesh(g, m); o.castShadow = cast; o.receiveShadow = true; return o; };
const col = (key: string, c: string) => lam("sv_" + key, () => ({ color: c }));
const at = <T extends THREE.Object3D>(o: T, x: number, y: number, z: number, ry = 0) => { o.position.set(x, y, z); o.rotation.y = ry; return o; };
const box = (w: number, h: number, d: number, m: THREE.Material) => mesh(new THREE.BoxGeometry(w, h, d), m);
const cyl = (r0: number, r1: number, h: number, m: THREE.Material, seg = 16) => mesh(new THREE.CylinderGeometry(r0, r1, h, seg), m);
const picMat = (t: THREE.Texture) => new THREE.MeshBasicMaterial({ map: t, side: THREE.DoubleSide });
const board = (w: number, h: number, d: number, face: THREE.Material, frame = "#3a2a2a") => {
  const g = new THREE.Group(); g.add(box(w, h, d, col("frame" + frame, frame)));
  const p = new THREE.Mesh(new THREE.PlaneGeometry(w * 0.95, h * 0.9), face); p.position.z = d / 2 + 0.005; g.add(p); return g;
};
const hh = (i: number, s = 0) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };

// ---------- painted textures ----------
const U = (r: () => number, a: number, b: number) => a + (b - a) * r();
const sand = () => ctex("sv_sand", 1024, 1024, (g, r) => {
  g.fillStyle = "#e2b77c"; g.fillRect(0, 0, 1024, 1024);
  for (let i = 0; i < 50; i++) {
    const x = U(r, 0, 1024), y = U(r, 0, 1024), rad = U(r, 60, 220), gr = g.createRadialGradient(x, y, 0, x, y, rad);
    const c = r() < 0.5 ? "196,140,86" : "244,206,150"; gr.addColorStop(0, `rgba(${c},0.35)`); gr.addColorStop(1, `rgba(${c},0)`);
    g.fillStyle = gr; g.fillRect(x - rad, y - rad, rad * 2, rad * 2);
  }
  for (let i = 0; i < 5000; i++) { g.fillStyle = r() < 0.5 ? "rgba(150,100,60,.35)" : "rgba(255,235,200,.4)"; g.fillRect(U(r, 0, 1024), U(r, 0, 1024), 2.5, 2.5); }
  g.strokeStyle = "rgba(170,120,70,.25)"; g.lineWidth = 4;   // wind ripples
  for (let i = 0; i < 40; i++) { const y = U(r, 0, 1024), x = U(r, 0, 1024); g.beginPath(); g.moveTo(x, y); g.bezierCurveTo(x + 60, y - 14, x + 120, y + 14, x + 190, y); g.stroke(); }
});
const rock = () => ctex("sv_rock", 512, 512, (g, r) => {
  const bands = ["#c8693f", "#d9824f", "#b85a38", "#e19a62", "#c46a42"];
  for (let y = 0, i = 0; y < 512; i++) { const h = U(r, 30, 80); g.fillStyle = bands[i % bands.length]; g.fillRect(0, y, 512, h + 2); y += h; }
  g.strokeStyle = "rgba(90,40,25,.35)"; g.lineWidth = 3;
  for (let i = 0; i < 24; i++) { let x = U(r, 0, 512), y = U(r, 0, 512); g.beginPath(); g.moveTo(x, y); for (let k = 0; k < 4; k++) { y += U(r, 20, 60); x += U(r, -10, 10); g.lineTo(x, y); } g.stroke(); }
});
const barTex = () => ctex("sv_bar", 256, 128, (g) => {
  const gr = g.createLinearGradient(0, 0, 0, 128); gr.addColorStop(0, "#f4f7fb"); gr.addColorStop(0.5, "#c9d1dc"); gr.addColorStop(1, "#9aa5b5");
  g.fillStyle = gr; g.fillRect(0, 0, 256, 128);
  g.strokeStyle = "rgba(60,70,90,.55)"; g.lineWidth = 8; g.strokeRect(4, 4, 248, 120);
  g.fillStyle = "rgba(255,255,255,.55)"; g.fillRect(14, 14, 228, 10);
  g.fillStyle = "rgba(70,80,100,.5)"; g.font = "900 34px Arial"; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("999.9", 128, 72);
});
const wood = () => ctex("sv_wood", 512, 512, (g, r) => {
  g.fillStyle = "#b9824f"; g.fillRect(0, 0, 512, 512);
  for (let y = 0; y < 512; y += 64) { g.fillStyle = r() < 0.5 ? "#c48c58" : "#a97443"; g.fillRect(0, y + 2, 512, 60); g.fillStyle = "rgba(60,35,20,.5)"; g.fillRect(0, y, 512, 3); }
  g.strokeStyle = "rgba(90,55,30,.35)"; g.lineWidth = 2; for (let i = 0; i < 60; i++) { const y = U(r, 0, 512), x = U(r, 0, 512); g.beginPath(); g.moveTo(x, y); g.lineTo(x + U(r, 40, 140), y + U(r, -3, 3)); g.stroke(); }
});

export class Sets {
  root = new THREE.Group();
  /** a few loose bars on the mountain's front flank that slide off when the rules change */
  slide: THREE.Mesh[] = [];
  slideHome: V3[] = [];
  pumps: { beam: THREE.Group; head: THREE.Group }[] = [];
  gusher = new THREE.Group();
  book = new THREE.Group();

  constructor() {
    this.desert();
    this.mountain();
    this.exchange();
    this.ranch();
  }

  // ================= DESERT (shared ground, mesas, cacti) =================
  private desert() {
    const b = new Batch();
    const sm = lam("sv_sandM", () => ({ map: sand() }));
    b.add(quad(V(-1200, 0, 1200), V(1200, 0, 1200), V(1200, 0, -1200), V(-1200, 0, -1200), 2400 / 14, 2400 / 14), sm);
    b.build(this.root);
    // mesas on the horizon around both desert places
    const rm = lam("sv_rockM", () => ({ map: rock() }));
    for (const [cx, n0] of [[0, 0], [400, 7]] as [number, number][]) {
      for (let i = 0; i < 7; i++) {
        const a = -Math.PI / 2 + (i - 3) * 0.3 + 0.1 * hh(i + n0, 1), d = 170 + 60 * hh(i + n0, 2), w = 40 + 50 * hh(i + n0, 3), h = 22 + 28 * hh(i + n0, 4);
        const pts: THREE.Vector2[] = [];
        for (let k = 0; k < 9; k++) { const th = (k / 9) * Math.PI * 2; pts.push(new THREE.Vector2(Math.cos(th) * w * (0.8 + 0.3 * hh(k + i * 9 + n0, 5)), Math.sin(th) * w * 0.55 * (0.8 + 0.3 * hh(k + i * 9 + n0, 6)))); }
        const geo = new THREE.ExtrudeGeometry(new THREE.Shape(pts), { depth: h, bevelEnabled: true, bevelThickness: 4, bevelSize: 6, bevelSegments: 1, steps: 1 });
        geo.rotateX(-Math.PI / 2);
        const uv = geo.attributes.uv as THREE.BufferAttribute, pos = geo.attributes.position as THREE.BufferAttribute;
        for (let k = 0; k < uv.count; k++) uv.setXY(k, (pos.getX(k) + pos.getZ(k)) / 40, pos.getY(k) / 30);
        const m = mesh(geo, rm, false); at(m, cx + Math.cos(a) * d * 1.1, -2, Math.sin(a) * d); this.root.add(m);
      }
    }
    // cacti + scrub near both desert places
    const cm = col("cactus", "#4f9a4a"), sc = col("scrub", "#8a9a4a");
    const cactus = (x: number, z: number, s: number) => {
      const g = new THREE.Group();
      g.add(at(cyl(0.32 * s, 0.36 * s, 3.2 * s, cm, 10), 0, 1.6 * s, 0));
      g.add(at(mesh(new THREE.SphereGeometry(0.32 * s, 10, 6, 0, Math.PI * 2, 0, Math.PI / 2), cm), 0, 3.2 * s, 0));
      for (const sd of [-1, 1]) {
        const h = (1.0 + 0.4 * hh(x + sd, 7)) * s;
        g.add(at(cyl(0.2 * s, 0.22 * s, 0.7 * s, cm, 8), sd * 0.45 * s, 1.4 * s + sd * 0.2 * s, 0).rotateZ(sd * Math.PI / 2) as THREE.Object3D);
        g.add(at(cyl(0.2 * s, 0.2 * s, h, cm, 8), sd * 0.8 * s, 1.4 * s + sd * 0.2 * s + h / 2, 0));
        g.add(at(mesh(new THREE.SphereGeometry(0.2 * s, 8, 5, 0, Math.PI * 2, 0, Math.PI / 2), cm), sd * 0.8 * s, 1.4 * s + sd * 0.2 * s + h, 0));
      }
      at(g, x, 0, z, hh(x, 3) * 6); this.root.add(g);
    };
    for (const cx of [0, 400]) for (let i = 0; i < 18; i++) {
      const a = (i / 18) * Math.PI * 2 + hh(i + cx, 1), d = 18 + 40 * hh(i + cx, 2);
      const x = cx + Math.cos(a) * d, z = Math.sin(a) * d - 6;
      if (cx === 400 && Math.abs(z) < 14 && Math.abs(x - 400) < 26) continue;
      if (i % 3 === 0) cactus(x, z, 0.8 + 0.5 * hh(i, 4));
      else this.root.add(at(mesh(new THREE.IcosahedronGeometry(0.6 + 0.5 * hh(i, 5), 0), sc), x, 0.3, z));
    }
  }

  // ================= MOUNTAIN OF SILVER =================
  private mountain() {
    const mat = twoTone(new THREE.MeshPhongMaterial({ map: barTex(), color: "#ffffff", specular: "#ffffff", shininess: 70 }));
    const geo = new THREE.BoxGeometry(BW, BH, BD);
    // trapezoid ingot: pull the top face in a little
    const p = geo.attributes.position as THREE.BufferAttribute;
    for (let i = 0; i < p.count; i++) if (p.getY(i) > 0) { p.setX(i, p.getX(i) * 0.86); p.setZ(i, p.getZ(i) * 0.8); }
    geo.computeVertexNormals();
    const spots: THREE.Matrix4[] = [], m4 = new THREE.Matrix4(), q = new THREE.Quaternion(), e = new THREE.Euler(), s1 = new THREE.Vector3(1, 1, 1);
    let n = 0;
    for (let L = 0; L < LAYERS; L++) {
      const r = R0 * Math.pow(1 - L / LAYERS, 0.85) + 1.6 * (L / LAYERS), y = L * BH + BH / 2;
      const rot = L % 2 ? Math.PI / 2 : 0;
      for (let gx = -r; gx <= r; gx += BW * 1.02) for (let gz = -r; gz <= r; gz += BD * 1.04) {
        const [x, z] = rot ? [gz, gx] : [gx, gz];
        const rr = Math.hypot(x, z) + 0.6 * hh(n, 3);
        if (rr > r) continue;
        if (rr < r - 2.2 && L < LAYERS - 2) { n++; continue; } // hollow inside (never seen)
        e.set((hh(n, 4) - 0.5) * 0.06, rot + (hh(n, 5) - 0.5) * 0.25, (hh(n, 6) - 0.5) * 0.06);
        m4.compose(new THREE.Vector3(x, y, z), q.setFromEuler(e), s1);
        spots.push(m4.clone()); n++;
      }
    }
    const im = new THREE.InstancedMesh(geo, mat, spots.length);
    spots.forEach((m, i) => { im.setMatrixAt(i, m); im.setColorAt(i, new THREE.Color().setHSL(0.6, 0.06 + 0.06 * hh(i, 8), 0.86 + 0.1 * hh(i, 9))); });
    im.castShadow = true; im.receiveShadow = true;
    this.root.add(im);
    // loose bars at the front-right top (they slide down the slope in the "rules" shot)
    for (let i = 0; i < 14; i++) {
      const L = LAYERS - 3 + (i % 3), r = R0 * Math.pow(1 - L / LAYERS, 0.85) + 1.6 * (L / LAYERS);
      const a = 0.25 + (i / 14) * 1.3, x = Math.sin(a) * (r - 0.1), z = Math.cos(a) * (r - 0.1), y = L * BH + BH * 1.5;
      const bm = mesh(geo, mat); at(bm, x, y, z, a + Math.PI / 2); this.root.add(bm);
      this.slide.push(bm); this.slideHome.push([x, y, z]);
    }
  }

  // ================= SILVERMART EXCHANGE =================
  private exchange() {
    const [X] = EXCH, b = new Batch(), T = new THREE.Group(); this.root.add(T);
    const mm = lam("marble", () => ({ map: marble() })), wk = lam("slabs", () => ({ map: slabs() }));
    // plaza + street
    b.add(boxGeo(V(X - 70, 0, -30), V(X + 70, 0.08, 60), 3), wk);
    b.add(quad(V(X - 70, 0.09, 30), V(X + 70, 0.09, 30), V(X + 70, 0.09, 20), V(X - 70, 0.09, 20), 140 / 8, 1), col("road", "#5d5f6e"));
    // building body + steps (front face at z = 0 .. steps out to EX_STEP_Z + 3)
    b.add(boxGeo(V(X - 16, 0, -22), V(X + 16, 13, -2), 4), mm);
    for (let i = 0; i < 5; i++) b.add(boxGeo(V(X - 17, 0, -2), V(X + 17, (i + 1) * 0.32, EX_STEP_Z + 3 - i * 0.7), 3), mm);
    for (let i = 0; i < 8; i++) T.add(at(cyl(0.55, 0.62, 10.2, col("column", "#f4f1ea"), 18), X - 13.3 + i * 3.8, EX_STEP_Y + 5.1, 0.8));
    b.add(boxGeo(V(X - 17, 11.8, -2), V(X + 17, 13.2, 1.6), 0), mm);
    const ped = new THREE.Shape([new THREE.Vector2(-17, 0), new THREE.Vector2(17, 0), new THREE.Vector2(0, 4.6)]);
    T.add(at(mesh(new THREE.ExtrudeGeometry(ped, { depth: 3.6, bevelEnabled: false }), mm), X, 13.2, -2));
    const sg = new THREE.Mesh(new THREE.PlaneGeometry(17, 1.25), picMat(signTex("sv_exSign", ["SILVERMART EXCHANGE"], { bg: "#ece6da", fg: "#2a2438", w: 2048, h: 150, sizes: [104], shadow: false })));
    at(sg, X, 12.5, 1.62); T.add(sg);
    // dark doorways behind the columns
    for (const dx of [-6, 0, 6]) b.add(boxGeo(V(X + dx - 1.4, EX_STEP_Y, -2.05), V(X + dx + 1.4, EX_STEP_Y + 5, -1.95), 0), col("door", "#2b2433"));
    // banners between columns
    for (const dx of [-9.5, 9.5]) {
      const bn = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 6.2), picMat(signTex("sv_banner", ["Ag", "SILVER"], { bg: "#1d3f8a", fg: "#e8edf5", w: 300, h: 840, sizes: [150, 56] })));
      at(bn, X + dx, EX_STEP_Y + 6.2, -1.9); T.add(bn);
    }
    // glass towers behind + either side
    const gt = lam("glassTower", () => ({ map: glassTower() }));
    for (const [ox, oz, w, h] of [[-34, -26, 16, 46], [-14, -48, 18, 70], [12, -44, 16, 60], [34, -24, 18, 40], [-52, -6, 14, 28], [52, -8, 14, 32]] as [number, number, number, number][])
      b.add(boxGeo(V(X + ox - w / 2, 0, oz - w / 2), V(X + ox + w / 2, h, oz + w / 2), 12), gt);
    // lamps + a couple of trees in planters
    for (const dx of [-20, 20]) { T.add(at(cyl(0.12, 0.15, 5, col("lamp", "#3a3d4a"), 8), X + dx, 2.5, 12)); T.add(at(mesh(new THREE.SphereGeometry(0.4, 12, 8), col("bulb", "#fff2c4")), X + dx, 5.2, 12)); }
    for (const dx of [-26, 26]) {
      b.add(boxGeo(V(X + dx - 1.2, 0, 10), V(X + dx + 1.2, 0.8, 12.4), 0), col("planter", "#8a8f9a"));
      T.add(at(mesh(new THREE.IcosahedronGeometry(2.0, 1), col("leaf", "#4f9a4a")), X + dx, 3.6, 11.2));
      T.add(at(cyl(0.18, 0.22, 2.6, col("trunk", "#7a4f33"), 8), X + dx, 1.8, 11.2));
    }
    b.build(T);
  }

  // ================= RANCH + OIL =================
  private ranch() {
    const [X] = RANCH, b = new Batch(), T = new THREE.Group(); this.root.add(T);
    const wd = lam("sv_woodM", () => ({ map: wood() }));
    // ranch house (behind the brothers, left)
    const HX = 15; // house centre x offset (right, behind)
    b.add(boxGeo(V(X + HX - 9, 0, -34), V(X + HX + 9, 4.2, -24), 2), wd);
    const roof = new THREE.Shape([new THREE.Vector2(-10, 0), new THREE.Vector2(10, 0), new THREE.Vector2(0, 3.4)]);
    T.add(at(mesh(new THREE.ExtrudeGeometry(roof, { depth: 11.4, bevelEnabled: false }), col("roofR", "#a8473a")), X + HX, 4.2, -34.7));
    b.add(boxGeo(V(X + HX - 8, 0, -24), V(X + HX + 8, 0.4, -21.5), 0), wd);                // porch deck
    b.add(boxGeo(V(X + HX - 8.2, 3.4, -24.2), V(X + HX + 8.2, 3.6, -21.3), 0), col("porchRoof", "#7a4f33"));
    for (const x of [-7.6, -2.6, 2.6, 7.6]) T.add(at(box(0.25, 3.0, 0.25, col("post", "#6a4a2c")), X + HX + x, 1.9, -21.6));
    for (const x of [-5, 5]) b.add(boxGeo(V(X + HX + x - 1, 1.4, -23.98), V(X + HX + x + 1, 3.0, -23.9), 0), col("win", "#2c4a7a"));
    b.add(boxGeo(V(X + HX - 0.8, 0.4, -23.98), V(X + HX + 0.8, 3.2, -23.9), 0), col("doorR", "#6a3a22"));
    // rail fence along the front
    for (let x = -40; x <= 40; x += 4) {
      if (Math.abs(x) < 6) continue;
      T.add(at(box(0.22, 1.5, 0.22, col("post", "#6a4a2c")), X + x, 0.75, 6));
    }
    for (const y of [0.6, 1.2]) for (const s of [-1, 1]) b.add(boxGeo(V(X + (s < 0 ? -40 : 6), y, 5.95), V(X + (s < 0 ? -6 : 40), y + 0.14, 6.05), 0), col("rail", "#8a5a3c"));
    // "BIG STATE OIL" roadside sign (left of the gate)
    for (const sx of [-2.6, 2.6]) T.add(at(box(0.3, 3.6, 0.3, col("post", "#6a4a2c")), X - 7 + sx, 1.8, 4.2));
    const sgn = board(6.4, 1.9, 0.25, picMat(signTex("sv_oil", ["BIG STATE OIL"], { bg: "#f2c94c", fg: "#241726", w: 1400, h: 400, sizes: [170], stripe: "#2a2a34" })));
    at(sgn, X - 7, 3.2, 4.2, 0.18); T.add(sgn);
    // pumpjacks (beam + horse head nod) on the right
    for (const [ox, oz, s] of [[13, -10, 1.15], [27, -16, 1.0], [-24, -30, 0.9], [32, -40, 0.85]] as [number, number, number][]) this.pump(T, X + ox, oz, s);
    // derrick tower (lattice) at back right + gusher
    const dx = X - 7.5, dz = -8, dh = 13, steel = col("steel", "#3d4150");
    for (let k = 0; k < 4; k++) {
      const sx = k % 2 ? 1 : -1, sz = k < 2 ? 1 : -1;
      const leg = mesh(new THREE.CylinderGeometry(0.16, 0.22, dh * 1.01, 6), steel);
      leg.position.set(dx + sx * 2.1, dh / 2, dz + sz * 2.1); leg.rotation.set(-sz * 0.075, 0, sx * 0.075); T.add(leg);
    }
    for (let y = 2; y < dh; y += 3) {
      const w = 4.2 * (1 - y / dh) + 0.6;
      for (const [w0, d0, ry] of [[w, 0, 0], [w, 0, Math.PI / 2]] as [number, number, number][]) {
        for (const s of [-1, 1]) { const r = box(w0 * 1.02, 0.12, 0.12, steel); at(r, dx + (ry ? s * w / 2 : 0), y, dz + (ry ? 0 : s * w / 2), ry); T.add(r); void d0; }
      }
    }
    T.add(at(box(1.4, 0.6, 1.4, steel), dx, dh, dz));
    b.add(boxGeo(V(dx - 3.5, 0, dz - 3.5), V(dx + 3.5, 0.6, dz + 3.5), 0), col("pad", "#8a8478"));
    at(this.gusher, dx, dh + 0.3, dz); T.add(this.gusher);
    // barrels
    for (let i = 0; i < 6; i++) T.add(at(cyl(0.45, 0.45, 1.3, col(i % 2 ? "barrelR" : "barrelB", i % 2 ? "#c0353a" : "#2f5f9e"), 14), X + 7 + (i % 3) * 1.0, 0.65, -3 - Math.floor(i / 3) * 1.0));
    b.build(T);
  }

  private pump(T: THREE.Group, x: number, z: number, s: number) {
    const g = new THREE.Group(); at(g, x, 0, z, -0.5); g.scale.setScalar(s); T.add(g);
    const dark = col("pumpD", "#2b2e3a"), yel = col("pumpY", "#e8b33a");
    g.add(at(box(6, 0.4, 1.4, dark), 0, 0.2, 0));
    for (const sz of [-1, 1]) { const l = box(0.25, 4.4, 0.25, dark); l.position.set(0, 2.2, sz * 0.5); l.rotation.x = -sz * 0.12; g.add(l); }
    const beam = new THREE.Group(); beam.position.set(0, 4.3, 0); g.add(beam);
    beam.add(at(box(6.4, 0.45, 0.45, yel), 0.4, 0, 0));
    const head = new THREE.Group(); head.position.set(3.6, 0, 0); beam.add(head);
    const hs = new THREE.Shape(); hs.moveTo(0, 0.9); hs.quadraticCurveTo(1.3, 0.2, 0.2, -1.6); hs.lineTo(-0.3, -1.4); hs.quadraticCurveTo(0.6, 0, -0.3, 0.7); hs.closePath();
    head.add(at(mesh(new THREE.ExtrudeGeometry(hs, { depth: 0.6, bevelEnabled: false }).translate(0, 0, -0.3), yel), 0, 0, 0));
    beam.add(at(box(1.0, 1.0, 0.9, dark), -2.6, -0.6, 0));                  // counterweight
    g.add(at(cyl(0.12, 0.12, 2.6, dark, 6), 3.9, 1.6, 0));                    // polished rod
    this.pumps.push({ beam, head });
  }
}
