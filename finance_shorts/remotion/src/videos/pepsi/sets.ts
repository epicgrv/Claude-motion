// Every place of the story in one three.js scene. Town at the origin (road along x); interiors are open-top,
// open-front rooms far out on +x (X0 = 1000 + 100 k) so the camera never sees one place from another.
import * as THREE from "three";
import { lam, quad, boxGeo, Batch, house, V } from "../bridge/build";
import { twoTone } from "../bridge/shade";
import { brick as brickT, roofHD } from "../bridge/paint";
import { NOINK } from "../bridge/ink";
import {
  asphalt, slabs, lawn, woodFloor, carpet, wallPaint, woodPanel, marble, glassTower, schoolBrick, chalkboard, signTex, canLabel, canTop,
  chequeTex, catalogTex, couponTex, drawSign, SignOpts,
} from "./tex";
import { buildJet, Jet } from "./jet";

export type V3 = [number, number, number];
export const ROOM = { dorm: 1000, class: 1100, board: 1200, office: 1300, court: 1400 } as const;

// ---------- anchors the story and cast use ----------
export const A = {
  mailbox: [3.6, 0.1, -7.2] as V3,
  porch: [0, 0.6, -9.6] as V3,
  jetLawn: [70, 0.1, -15] as V3,
  bus: [96, 0, 2.0] as V3,
  store: [-30, 0.15, 9] as V3,
  court: [-75, 0.15, 12] as V3,
  hq: [-130, 0, -42] as V3,
};

// ---------- small helpers ----------
const mesh = (g: THREE.BufferGeometry, m: THREE.Material, cast = true) => { const o = new THREE.Mesh(g, m); o.castShadow = cast; o.receiveShadow = true; return o; };
const col = (key: string, c: string) => lam("c_" + key, () => ({ color: c }));
const at = (o: THREE.Object3D, x: number, y: number, z: number, ry = 0) => { o.position.set(x, y, z); o.rotation.y = ry; return o; };
const box = (w: number, h: number, d: number, m: THREE.Material) => mesh(new THREE.BoxGeometry(w, h, d), m);
const cyl = (r0: number, r1: number, h: number, m: THREE.Material, seg = 16) => mesh(new THREE.CylinderGeometry(r0, r1, h, seg), m);
/** unlit picture (signs, screens, posters): stays readable whatever the sun does */
export const picMat = (t: THREE.Texture, transparent = false) => {
  const m = new THREE.MeshBasicMaterial({ map: t, transparent, alphaTest: transparent ? 0.3 : 0, side: THREE.DoubleSide });
  return m;
};
/** a framed board: box of the frame colour + an unlit face on its front (+z) */
export const board = (w: number, h: number, d: number, face: THREE.Material, frame = "#3a2a2a") => {
  const g = new THREE.Group();
  g.add(box(w, h, d, col("frame" + frame, frame)));
  const p = new THREE.Mesh(new THREE.PlaneGeometry(w * 0.94, h * 0.9), face); p.position.z = d / 2 + 0.005; g.add(p);
  return g;
};

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
    draw(g, this.cv.width, this.cv.height);
    this.tex.needsUpdate = true;
  }
}

// ---------- props ----------
const tree = (b: THREE.Group, x: number, z: number, s = 1, seed = 0) => {
  const t = cyl(0.16 * s, 0.24 * s, 2.4 * s, col("trunk", "#7a4f33"), 8); at(t, x, 1.2 * s, z); b.add(t);
  const greens = ["#5fae4a", "#4f9a44", "#72b853"];
  for (let i = 0; i < 3; i++) {
    const r = (1.25 - i * 0.18) * s, a = seed * 2.1 + i * 2.2;
    const l = mesh(new THREE.IcosahedronGeometry(r, 1), col("leaf" + i, greens[(i + seed) % 3]));
    at(l, x + Math.cos(a) * 0.45 * s, (2.6 + i * 0.75) * s, z + Math.sin(a) * 0.45 * s); b.add(l);
  }
};
const lamp = (b: THREE.Group, x: number, z: number) => {
  b.add(at(cyl(0.07, 0.09, 5, col("lampPost", "#3a3f4e"), 8), x, 2.5, z));
  b.add(at(box(0.9, 0.08, 0.12, col("lampPost", "#3a3f4e")), x, 4.95, z + (z > 0 ? -0.4 : 0.4)));
  b.add(at(box(0.36, 0.18, 0.5, col("lampHead", "#f4f1ea")), x, 4.85, z + (z > 0 ? -0.8 : 0.8)));
};
const car = (b: THREE.Group, x: number, z: number, ry: number, c: string) => {
  const g = new THREE.Group(), body = twoTone(new THREE.MeshPhongMaterial({ color: c, specular: "#ffffff", shininess: 70 }));
  const glass = twoTone(new THREE.MeshPhongMaterial({ color: "#2c3e64", specular: "#cfe6ff", shininess: 90 }));
  // rounded lower body + cabin
  const lo = mesh(new THREE.CapsuleGeometry(0.45, 3.4, 6, 16).rotateZ(Math.PI / 2), body); lo.scale.set(1, 0.95, 1.95); lo.position.y = 0.72; g.add(lo);
  const cab = mesh(new THREE.CapsuleGeometry(0.42, 1.5, 6, 12).rotateZ(Math.PI / 2), glass); cab.scale.set(1, 1.05, 1.8); cab.position.set(-0.25, 1.28, 0); g.add(cab);
  const roofC = mesh(new THREE.BoxGeometry(1.5, 0.08, 1.4), body); roofC.position.set(-0.25, 1.7, 0); g.add(roofC);
  for (const sx of [-1.35, 1.35]) for (const sz of [-0.86, 0.86]) {
    const w = cyl(0.36, 0.36, 0.26, col("tyre", "#25252c"), 18); w.rotation.x = Math.PI / 2; at(w, sx, 0.36, sz); g.add(w);
    const hub = cyl(0.18, 0.18, 0.28, col("hub", "#d7d9de"), 12); hub.rotation.x = Math.PI / 2; at(hub, sx, 0.36, sz); g.add(hub);
  }
  for (const sz of [-0.55, 0.55]) { g.add(at(box(0.06, 0.16, 0.34, col("headL", "#fff6c9")), 2.33, 0.8, sz)); g.add(at(box(0.06, 0.14, 0.3, col("tailL", "#d8323c")), -2.33, 0.82, sz)); }
  g.add(at(box(0.1, 0.12, 1.7, col("bumper", "#d7d9de")), 2.35, 0.5, 0)); g.add(at(box(0.1, 0.12, 1.7, col("bumper", "#d7d9de")), -2.35, 0.5, 0));
  b.add(at(g, x, 0, z, ry));
};
const hydrant = (b: THREE.Group, x: number, z: number) => {
  const m = col("hydrant", "#d8323c");
  b.add(at(cyl(0.16, 0.19, 0.6, m, 12), x, 0.45, z)); b.add(at(mesh(new THREE.SphereGeometry(0.17, 12, 8, 0, Math.PI * 2, 0, Math.PI / 2), m), x, 0.75, z));
  const n = cyl(0.07, 0.07, 0.42, m, 8); n.rotation.z = Math.PI / 2; at(n, x, 0.55, z); b.add(n);
};
const bin = (b: THREE.Group, x: number, z: number) => { b.add(at(cyl(0.3, 0.26, 0.95, col("bin", "#3f6a4a"), 14), x, 0.62, z)); b.add(at(cyl(0.33, 0.33, 0.06, col("binLid", "#2f4f38"), 14), x, 1.12, z)); };
const bush = (b: THREE.Group, x: number, z: number, s = 1) => { for (let i = 0; i < 3; i++) b.add(at(mesh(new THREE.IcosahedronGeometry(0.5 * s, 1), col("leaf" + i, ["#5fae4a", "#4f9a44", "#72b853"][i])), x + (i - 1) * 0.45 * s, 0.4 * s + 0.1, z + (i % 2) * 0.2)); };
const fence = (b: THREE.Group, x0: number, x1: number, z: number) => {
  const m = col("fence", "#f4f1ea");
  for (let x = x0; x <= x1; x += 0.35) b.add(at(box(0.09, 0.9, 0.05, m), x, 0.55, z));
  b.add(at(box(x1 - x0, 0.08, 0.05, m), (x0 + x1) / 2, 0.75, z + 0.04)); b.add(at(box(x1 - x0, 0.08, 0.05, m), (x0 + x1) / 2, 0.35, z + 0.04));
};
/** our soda can (generic brand), 0.12 m tall at s = 1 */
export const canMesh = (s = 1) => {
  const g = new THREE.Group();
  const side = lam("canSide", () => ({ map: canLabel() }));
  const top = lam("canTopM", () => ({ map: canTop() }));
  const body = mesh(new THREE.CylinderGeometry(0.033 * s, 0.033 * s, 0.11 * s, 20, 1, true), side); body.position.y = 0.06 * s; g.add(body);
  const t = mesh(new THREE.CylinderGeometry(0.029 * s, 0.033 * s, 0.012 * s, 20), top); t.position.y = 0.121 * s; g.add(t);
  const bt = mesh(new THREE.CylinderGeometry(0.033 * s, 0.027 * s, 0.01 * s, 20), col("canAl", "#c9ccd6")); bt.position.y = 0.005 * s; g.add(bt);
  return g;
};
/** pyramid of cans via instancing (side + top), n rows, can scale s */
const canPile = (rows: number, s: number) => {
  const pos: THREE.Vector3[] = [];
  const d = 0.068 * s, h = 0.125 * s;
  for (let r = 0; r < rows; r++) {
    const n = rows - r;
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) pos.push(new THREE.Vector3((i - (n - 1) / 2) * d, r * h, (j - (n - 1) / 2) * d));
  }
  const g = new THREE.Group();
  const side = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.033 * s, 0.033 * s, 0.11 * s, 16, 1, true).translate(0, 0.06 * s, 0), lam("canSide", () => ({ map: canLabel() })), pos.length);
  const top = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.029 * s, 0.033 * s, 0.012 * s, 16).translate(0, 0.121 * s, 0), lam("canTopM", () => ({ map: canTop() })), pos.length);
  const m = new THREE.Matrix4();
  pos.forEach((p, i) => { m.makeRotationY((i * 2.399) % 6.28).setPosition(p); side.setMatrixAt(i, m); top.setMatrixAt(i, m); });
  for (const im of [side, top]) { im.castShadow = true; im.receiveShadow = true; g.add(im); }
  return g;
};

// ---------- the world ----------
export class Sets {
  root = new THREE.Group();
  jet: Jet;
  priceTex = new DynTex(1024, 900);
  price = new THREE.Group();        // the giant price board (posts + board), posed per shot
  tvTex = new DynTex(800, 480);
  calcTex = new DynTex(640, 240);
  mailFlag = new THREE.Group(); mailDoor = new THREE.Group();
  bus = new THREE.Group();
  arrow = new THREE.Group(); arrowBody: THREE.Mesh; arrowHead: THREE.Mesh;
  chequeBig: THREE.Group; chequeB: THREE.Group; letter = new THREE.Group();
  coin = new THREE.Group();
  catalog: THREE.Mesh;
  cansDorm: THREE.Group; cansMega: THREE.Group;
  gavel = new THREE.Group();
  dust: THREE.Mesh;

  constructor() {
    const R = this.root;
    this.town(R);
    this.jet = buildJet(); R.add(this.jet.group);
    // ---- giant price board ----
    const pb = new THREE.Group();
    const face = picMat(this.priceTex.tex);
    const brd = board(5.6, 5.0, 0.35, face, "#c9a24a"); brd.position.y = 5.6; pb.add(brd);
    for (const sx of [-2.0, 2.0]) pb.add(at(cyl(0.14, 0.18, 6.0, col("postY", "#5a5f70"), 10), sx, 3.0, -0.1));
    this.price = pb; R.add(pb);
    // ---- school bus ----
    this.buildBus(); R.add(this.bus);
    // ---- inflation arrow ----
    const am = col("arrowRed", "#e2453c");
    this.arrowBody = mesh(new THREE.BoxGeometry(2.4, 1, 1.4).translate(0, 0.5, 0), am);
    this.arrowHead = mesh(new THREE.ConeGeometry(2.6, 3.4, 4).rotateY(Math.PI / 4), am);
    this.arrow.add(this.arrowBody, this.arrowHead); R.add(this.arrow);
    // ---- big cheque (3D card) ----
    this.chequeBig = this.cheque("$700,000.00", "Seven hundred thousand & 00/100");
    this.chequeB = this.cheque("$700,008.50", "Seven hundred thousand eight & 50/100");
    R.add(this.chequeBig, this.chequeB);
    // envelope / letter
    this.letter.add(box(0.5, 0.32, 0.01, col("env", "#f4ead2")));
    const st = new THREE.Mesh(new THREE.PlaneGeometry(0.08, 0.1), col("stamp", "#d8323c")); st.position.set(0.18, 0.08, 0.006); this.letter.add(st);
    R.add(this.letter);
    // coin
    const cm = twoTone(new THREE.MeshPhongMaterial({ color: "#e8b33a", specular: "#fff2c0", shininess: 60 }));
    const c = mesh(new THREE.CylinderGeometry(1, 1, 0.16, 40), cm); c.rotation.x = Math.PI / 2; this.coin.add(c);
    const cf = new THREE.Mesh(new THREE.CircleGeometry(0.8, 40), picMat(signTex("coin10", ["10¢"], { bg: "#f2c94c", fg: "#7a5212", w: 512, h: 512, radius: 256, sizes: [230] })));
    cf.position.z = 0.085; this.coin.add(cf);
    const cb = cf.clone(); cb.position.z = -0.085; cb.rotation.y = Math.PI; this.coin.add(cb);
    R.add(this.coin);
    // gavel
    const wood = col("gavel", "#7a3f22");
    const head = mesh(new THREE.CylinderGeometry(0.11, 0.11, 0.42, 16), wood); head.rotation.z = Math.PI / 2;
    const handle = mesh(new THREE.CylinderGeometry(0.03, 0.035, 0.7, 10).translate(0, -0.35, 0), wood);
    this.gavel.add(head, handle); R.add(this.gavel);
    // dust ring (landing)
    this.dust = new THREE.Mesh(new THREE.RingGeometry(0.3, 1, 48), new THREE.MeshBasicMaterial({ color: "#efe6cf", transparent: true, opacity: 0.6, depthWrite: false }));
    this.dust.rotation.x = -Math.PI / 2; this.dust.layers.set(NOINK); R.add(this.dust);
    // ---- interiors ----
    this.cansDorm = canPile(9, 2.2); this.cansMega = canPile(10, 2.2);
    this.catalog = new THREE.Mesh(new THREE.PlaneGeometry(0.42, 0.575), lam("catalogM", () => ({ map: catalogTex() })));
    this.catalog.receiveShadow = true;
    this.dorm(); this.classroom(); this.boardroom(); this.office(); this.courtroom();
  }

  private cheque(amount: string, words: string) {
    const g = new THREE.Group();
    g.add(box(1.4, 0.62, 0.03, col("chequeEdge", "#cfe0c9")));
    const f = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 0.62), lam("chq" + amount, () => ({ map: chequeTex(amount, words) }))); f.position.z = 0.016; f.receiveShadow = true; g.add(f);
    return g;
  }

  private buildBus() {
    const B = this.bus, y = col("busY", "#f2b32c"), blk = col("busBlk", "#25252c");
    B.add(at(box(11, 1.35, 2.5, y), 0, 1.22, 0));            // lower body, full length
    B.add(at(box(9.9, 1.05, 2.5, y), 0.55, 2.42, 0));        // upper body behind the driver
    for (const s of [-1, 1]) B.add(at(box(0.9, 1.05, 0.08, y), -5.05, 2.42, s * 1.21)); // cab pillars (open side window)
    B.add(at(box(1.6, 1.3, 2.4, y), -6.2, 1.2, 0)); // hood (front toward -x)
    B.add(at(box(11.02, 0.12, 2.52, blk), 0, 1.45, 0));
    B.add(at(box(11.02, 0.12, 2.52, blk), 0, 2.05, 0));
    const glass = col("busGlass", "#2c3e64");
    for (let i = 0; i < 8; i++) for (const s of [-1, 1]) { const w = box(0.95, 0.75, 0.05, glass); at(w, -3.6 + i * 1.15, 2.42, s * 1.255); B.add(w); }
    // windshield: an open frame so the driver card inside is visible
    B.add(at(box(0.06, 0.12, 2.4, blk), -5.52, 3.0, 0));
    B.add(at(box(0.06, 0.12, 2.4, blk), -5.52, 1.98, 0));
    B.add(at(box(0.06, 1.1, 0.12, blk), -5.52, 2.5, 0));
    B.add(at(box(11, 0.2, 2.5, col("busRoof", "#f4f1ea")), 0, 3.0, 0));
    const sgn = new THREE.Mesh(new THREE.PlaneGeometry(4.2, 0.5), picMat(signTex("busSign", ["SCHOOL BUS"], { bg: "#f2b32c", fg: "#241726", w: 1024, h: 128, sizes: [96], shadow: false })));
    for (const s of [-1, 1]) { const m = sgn.clone(); m.position.set(0, 2.85, s * 1.27); m.rotation.y = s > 0 ? 0 : Math.PI; B.add(m); }
    for (const sx of [-4.2, 3.2]) for (const sz of [-1.15, 1.15]) { const w = cyl(0.5, 0.5, 0.36, col("tyre", "#25252c"), 16); w.rotation.x = Math.PI / 2; at(w, sx, 0.5, sz); B.add(w); }
    // interior: floor + seat back so the driver sits in something
    B.add(at(box(0.6, 0.9, 0.7, col("seat", "#3a5a9a")), -4.2, 1.6, -0.5));
    const wheel = mesh(new THREE.TorusGeometry(0.2, 0.035, 8, 20), blk); wheel.rotation.y = Math.PI / 2; wheel.rotation.x = 0.6; at(wheel, -5.15, 1.98, -0.5); B.add(wheel);
  }

  // ================= TOWN =================
  private town(R: THREE.Group) {
    const b = new Batch(), T = new THREE.Group(); R.add(T);
    const road = lam("asphalt", () => ({ map: asphalt() }));
    b.add(quad(V(-260, 0, 4), V(260, 0, 4), V(260, 0, -4), V(-260, 0, -4), 520 / 8, 1), road);
    const walk = lam("slabs", () => ({ map: slabs() }));
    for (const s of [-1, 1]) {
      b.add(boxGeo(V(-260, 0, s > 0 ? 4 : -6.5), V(260, 0.15, s > 0 ? 6.5 : -4), 3), walk);
      b.add(boxGeo(V(-260, 0, s > 0 ? 4 : -4.25), V(260, 0.17, s > 0 ? 4.25 : -4), 0), col("curb", "#e6e0d4"));
    }
    const grassM = lam("lawnP", () => ({ map: lawn() }));
    b.add(boxGeo(V(-260, 0, -160), V(260, 0.1, -6.5), 12), grassM);
    b.add(boxGeo(V(-260, 0, 6.5), V(260, 0.1, 160), 12), grassM);
    // ---- houses ----
    const north = (x: number) => (x > -8 && x < 8) || (x > 44 && x < 96) || (x > -150 && x < -106);
    const south = (x: number) => (x > -44 && x < -16) || (x > -96 && x < -54);
    let k = 0;
    for (const s of [-1, 1]) {
      for (let x = -240; x < 240; x += 13) {
        const skip = s < 0 ? north(x) || north(x + 10) || north(x - 4) : south(x) || south(x + 10) || south(x - 4);
        if (skip) continue;
        const w = 9 + (k % 3), h = 6.2 + (k % 3) * 1.1;
        house(b, x + 5, s * 15, s < 0 ? 0 : Math.PI, w, 8, h, (k * 5 + 3) % 8, 0.1);
        if (k % 2 === 0) tree(T, x + 11.5, s * 9.5, 0.95 + (k % 3) * 0.1, k);
        k++;
      }
    }
    // John's house (cream, blue shutters) + porch + path + mailbox
    house(b, 0, -15, 0, 10, 8, 7.2, 0, 0.1);
    const porchM = woodFloor("porch", "#c8a070");
    b.add(boxGeo(V(-3.4, 0.1, -11), V(3.4, 0.6, -8.4), 2), lam("porchM", () => ({ map: porchM })));
    for (let i = 0; i < 2; i++) b.add(boxGeo(V(-1.2, 0.1, -8.4 + i * 0.35), V(1.2, 0.45 - i * 0.18, -8.05 + i * 0.35), 1), col("step", "#efe3c8"));
    for (const x of [-3.2, 3.2]) b.add(boxGeo(V(x - 0.12, 0.6, -8.62), V(x + 0.12, 3.2, -8.38), 0), col("trimW", "#f4f1ea"));
    b.add(boxGeo(V(-3.7, 3.2, -11), V(3.7, 3.4, -8.2), 0), col("porchRoof", "#d27a62"));
    for (let x = -3.1; x <= 3.1; x += 0.35) if (Math.abs(x) > 1.3) b.add(boxGeo(V(x - 0.03, 0.6, -8.5), V(x + 0.03, 1.4, -8.44), 0), col("trimW", "#f4f1ea"));
    for (const s of [-1, 1]) b.add(boxGeo(V(s > 0 ? 1.3 : -3.2, 1.36, -8.52), V(s > 0 ? 3.2 : -1.3, 1.46, -8.4), 0), col("trimW", "#f4f1ea"));
    b.add(boxGeo(V(-0.8, 0.1, -8.05), V(0.8, 0.13, -6.5), 1), walk);
    // mailbox
    const [mx, , mz] = A.mailbox;
    T.add(at(box(0.12, 1.1, 0.12, col("mpost", "#6a4a2c")), mx, 0.65, mz));
    const mb = mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.55, 20, 1, false, 0, Math.PI).rotateZ(Math.PI / 2).rotateY(Math.PI / 2), col("mbox", "#2f5fa8"));
    at(mb, mx, 1.2, mz); T.add(mb);
    T.add(at(box(0.4, 0.2, 0.55, col("mbox", "#2f5fa8")), mx, 1.1, mz));
    const fl = new THREE.Group(); fl.add(at(box(0.03, 0.34, 0.04, col("flagR", "#e2453c")), 0, 0.17, 0)); fl.add(at(box(0.03, 0.12, 0.16, col("flagR", "#e2453c")), 0, 0.3, 0.08));
    at(this.mailFlag, mx + 0.21, 1.05, mz - 0.1); this.mailFlag.add(fl); T.add(this.mailFlag);
    // front door hinged at the bottom (opens toward the street) + the dark inside it reveals
    const mouthM = new THREE.Mesh(new THREE.PlaneGeometry(0.36, 0.36), new THREE.MeshBasicMaterial({ color: "#14101a" }));
    at(mouthM, mx, 1.19, mz + 0.276); T.add(mouthM);
    const door = new THREE.Group();
    const plate = mesh(new THREE.CylinderGeometry(0.205, 0.205, 0.03, 24, 1, false, -Math.PI / 2, Math.PI).rotateX(Math.PI / 2).translate(0, 0.0, 0), col("mboxDoor", "#27509a"));
    plate.position.set(0, 0.2, 0.015); door.add(plate);
    door.add(at(box(0.41, 0.2, 0.03, col("mboxDoor", "#27509a")), 0, 0.1, 0.015));
    door.add(at(box(0.1, 0.035, 0.05, col("mboxHandle", "#d7d9de")), 0, 0.33, 0.04));
    at(this.mailDoor, 0, 1.0, 0); this.mailDoor.add(door);
    const doorPivot = new THREE.Group(); at(doorPivot, mx, 0, mz + 0.28); doorPivot.add(this.mailDoor); T.add(doorPivot);
    // lamps, cars
    for (let x = -230; x < 240; x += 26) { lamp(T, x, 5.9); lamp(T, x + 13, -5.9); }
    car(T, -12, 2.2, 0, "#3f6fb5"); car(T, 24, -2.2, Math.PI, "#c0353a"); car(T, -52, -2.2, Math.PI, "#5d7a3a"); car(T, 118, 2.2, 0, "#7b5ac9");
    car(T, 14, 2.4, 0, "#e8b33a"); car(T, -26, 2.4, 0, "#2f5f6a"); car(T, 40, -2.4, Math.PI, "#f4f1ea"); car(T, -88, 2.4, 0, "#e2453c");
    for (const [x, z] of [[-6, 6.0], [30, -6.0], [-44, 6.0], [86, -6.0]] as [number, number][]) hydrant(T, x, z);
    for (const [x, z] of [[8, -6.1], [-18, 6.1], [46, 6.1], [-62, -6.1]] as [number, number][]) bin(T, x, z);
    fence(T, -4.6, -1.4, -8.0); fence(T, 4.2, 5.8, -8.0);
    for (const x of [-5.6, -3, 5.2]) bush(T, x, -11.6, 1.0);
    // ---- school ----
    const sb = lam("schoolBrick", () => ({ map: schoolBrick() }));
    b.add(boxGeo(V(48, 0, -38), V(92, 11, -25), 6), sb);
    const winM = lam("schoolWin", () => ({ color: "#2c4a7a" }));
    for (let fl2 = 0; fl2 < 3; fl2++) for (let x = 51; x < 90; x += 3.2) if (Math.abs(x + 1 - 70) > 4) b.add(boxGeo(V(x, 1.4 + fl2 * 3.3, -25.0), V(x + 2, 3.2 + fl2 * 3.3, -24.9), 0), winM);
    for (let fl2 = 0; fl2 < 3; fl2++) for (let x = 51; x < 90; x += 3.2) if (Math.abs(x + 1 - 70) > 4) b.add(boxGeo(V(x - 0.15, 1.25 + fl2 * 3.3, -24.95), V(x + 2.15, 1.4 + fl2 * 3.3, -24.75), 0), col("trimW", "#f4f1ea"));
    b.add(boxGeo(V(47.6, 11, -38.4), V(92.4, 11.6, -24.6), 0), col("roofTop", "#b9b4ac"));
    for (const [x0, x1, z0, z1] of [[47.6, 92.4, -24.9, -24.6], [47.6, 92.4, -38.4, -38.1], [47.6, 47.9, -38.4, -24.6], [92.1, 92.4, -38.4, -24.6]]) b.add(boxGeo(V(x0, 11.6, z0), V(x1, 12.1, z1), 0), col("trimW", "#f4f1ea"));
    for (const x of [52, 56, 86]) { b.add(boxGeo(V(x, 11.6, -36.8), V(x + 2.2, 12.9, -34.8), 0), col("acUnit", "#cfd3da")); }
    const pad = new THREE.Mesh(new THREE.CircleGeometry(6.2, 48), picMat(signTex("helipad", ["H"], { bg: "#3a3d4a", fg: "#f2c94c", w: 512, h: 512, radius: 256, sizes: [330], border: "#f2c94c", shadow: false })));
    pad.rotation.x = -Math.PI / 2; at(pad, 70, 11.625, -31.5); pad.rotation.z = Math.PI / 2; this.root.add(pad);
    // portico
    b.add(boxGeo(V(64, 0.1, -25), V(76, 0.5, -21.5), 2), col("step", "#efe3c8"));
    for (const x of [64.8, 67.6, 72.4, 75.2]) T.add(at(cyl(0.38, 0.42, 6.5, col("column", "#f4f1ea"), 16), x, 3.75, -22.2));
    b.add(boxGeo(V(63.6, 7, -25), V(76.4, 8.2, -21.6), 0), col("trimW", "#f4f1ea"));
    b.add(boxGeo(V(68, 0.5, -25.05), V(72, 4.5, -24.95), 0), col("schoolDoor", "#7a3f22"));
    const ss = new THREE.Mesh(new THREE.PlaneGeometry(11, 1.1), picMat(signTex("school", ["LINCOLN HIGH SCHOOL"], { bg: "#f4f1ea", fg: "#1c2f7a", w: 1536, h: 160, sizes: [110], shadow: false })));
    at(ss, 70, 7.6, -21.55); T.add(ss);
    T.add(at(cyl(0.08, 0.1, 13, col("pole", "#d7d9de"), 8), 57, 6.5, -21));
    const flag = new THREE.Mesh(new THREE.PlaneGeometry(2.6, 1.6), lam("usFlag", () => ({ map: signTex("usflag", [""], { bg: "#f4f1ea", fg: "#000", w: 512, h: 320, stripe: "#c8323a", radius: 4 }), side: THREE.DoubleSide })));
    at(flag, 58.35, 12, -21); T.add(flag);
    for (const x of [52, 88]) tree(T, x, -18, 1.3, x);
    // ---- store ----
    const store = new THREE.Group();
    b.add(boxGeo(V(-40, 0.15, 10.5), V(-20, 7, 20), 3), lam("storeWall", () => ({ map: brickT() })));
    b.add(boxGeo(V(-39, 0.6, 10.45), V(-21, 4.4, 10.5), 0), col("storeGlass", "#3b5f9e"));
    for (let x = -39; x <= -21; x += 3) b.add(boxGeo(V(x - 0.1, 0.6, 10.4), V(x + 0.1, 4.4, 10.5), 0), col("trimW", "#f4f1ea"));
    b.add(boxGeo(V(-41, 4.5, 9.2), V(-19, 4.8, 10.5), 0), col("awning", "#e2453c"));
    const sTex = signTex("storeSign", ["MEGA MART"], { bg: "#1d4fb8", fg: "#ffffff", w: 1024, h: 200, sizes: [140] });
    const sg = new THREE.Mesh(new THREE.PlaneGeometry(12, 2.2), picMat(sTex)); sg.rotation.y = Math.PI; at(sg, -30, 5.9, 10.4); sg.rotation.y = Math.PI; store.add(sg);
    for (let i = 0; i < 3; i++) {
      const bn = new THREE.Mesh(new THREE.PlaneGeometry(4.6, 2.6), picMat(signTex("off96", ["96%", "OFF!"], { bg: "#fff36b", fg: "#e2453c", w: 768, h: 440, sizes: [190, 120] })));
      bn.position.set(-35 + i * 5, 2.6, 10.35); bn.rotation.y = Math.PI + (i - 1) * 0.06; bn.rotation.z = (i - 1) * 0.07; store.add(bn);
    }
    const bf = new THREE.Mesh(new THREE.PlaneGeometry(5, 1.6), picMat(signTex("bf", ["BLACK FRIDAY: 40% OFF"], { bg: "#241726", fg: "#ffffff", w: 1024, h: 330, sizes: [92] })));
    bf.position.set(-23.5, 6.2, 10.0); bf.rotation.y = Math.PI; bf.rotation.z = 0.25; store.add(bf);
    T.add(store);
    // ---- courthouse ----
    const mm = lam("marble", () => ({ map: marble() }));
    b.add(boxGeo(V(-88, 0.15, 20), V(-62, 12, 34), 4), mm);
    for (let i = 0; i < 4; i++) b.add(boxGeo(V(-89 + i * 0.0, 0.15 + i * 0.35, 13 + i * 1.2), V(-61, 0.5 + i * 0.35, 20), 3), mm);
    for (let i = 0; i < 7; i++) T.add(at(cyl(0.55, 0.62, 9, col("column", "#f4f1ea"), 18), -86 + i * 3.67, 6.1, 18.6));
    b.add(boxGeo(V(-89, 10.6, 17.6), V(-61, 11.8, 20), 0), mm);
    const ped = new THREE.Shape([new THREE.Vector2(-14, 0), new THREE.Vector2(14, 0), new THREE.Vector2(0, 4)]);
    const pm = mesh(new THREE.ExtrudeGeometry(ped, { depth: 2.4, bevelEnabled: false }), mm); at(pm, -75, 11.8, 17.6); T.add(pm);
    const cs = new THREE.Mesh(new THREE.PlaneGeometry(14, 1.0), picMat(signTex("courtSign", ["UNITED STATES DISTRICT COURT"], { bg: "#ece6da", fg: "#3a3040", w: 2048, h: 146, sizes: [100], shadow: false })));
    cs.rotation.y = Math.PI; at(cs, -75, 11.2, 17.55); cs.rotation.y = Math.PI; T.add(cs);
    // ---- HQ tower + downtown ----
    const gt = lam("glassTower", () => ({ map: glassTower() }));
    const [hx, , hz] = A.hq;
    b.add(boxGeo(V(hx - 11, 0, hz - 11), V(hx + 11, 72, hz + 11), 12), gt);
    b.add(boxGeo(V(hx - 11.5, 72, hz - 11.5), V(hx + 11.5, 74, hz + 11.5), 0), col("hqTop", "#e6e0d4"));
    const hs = new THREE.Mesh(new THREE.PlaneGeometry(20, 5), picMat(signTex("hqSign", ["SODA CO."], { bg: "#1d4fb8", fg: "#ffffff", w: 1024, h: 256, sizes: [170], stripe: "#d8323c" })));
    at(hs, hx, 68, hz + 11.05); T.add(hs);
    for (const [ox, oz, w, h] of [[-26, -6, 14, 38], [26, -4, 16, 30], [-12, -34, 18, 52], [18, -30, 14, 44], [-44, -10, 12, 26]]) b.add(boxGeo(V(hx + ox - w / 2, 0, hz + oz - w / 2), V(hx + ox + w / 2, h, hz + oz + w / 2), 12), lam("officeT", () => ({ map: glassTower() })));
    b.build(T);
  }

  // ================= INTERIORS =================
  /** open-front, open-top room: floor + back + side walls (room x in -w/2..w/2, z in -d..+d/2 open toward +z) */
  private room(X: number, w: number, d: number, h: number, floor: THREE.Material, wall: THREE.Material) {
    const g = new THREE.Group(); g.position.x = X; this.root.add(g);
    const b = new Batch();
    b.add(boxGeo(V(-w / 2 - 0.3, -0.3, -d - 0.3), V(w / 2 + 0.3, 0, d / 2 + 6), 2.5), floor);
    b.add(quad(V(-w / 2, 0, -d), V(w / 2, 0, -d), V(w / 2, h, -d), V(-w / 2, h, -d), 2, 1), wall);
    b.add(quad(V(-w / 2, 0, d / 2), V(-w / 2, 0, -d), V(-w / 2, h, -d), V(-w / 2, h, d / 2), 1.5, 1), wall);
    b.add(quad(V(w / 2, 0, -d), V(w / 2, 0, d / 2), V(w / 2, h, d / 2), V(w / 2, h, -d), 1.5, 1), wall);
    // backsides so the sun is blocked like a real room
    b.add(boxGeo(V(-w / 2 - 0.25, 0, -d - 0.25), V(w / 2 + 0.25, h, -d - 0.02), 0), col("roomOut", "#d8d0c4"));
    b.add(boxGeo(V(-w / 2 - 0.25, 0, -d), V(-w / 2 - 0.02, h, d / 2), 0), col("roomOut", "#d8d0c4"));
    b.add(boxGeo(V(w / 2 + 0.02, 0, -d), V(w / 2 + 0.25, h, d / 2), 0), col("roomOut", "#d8d0c4"));
    b.build(g);
    return g;
  }
  private window(g: THREE.Group, x: number, y: number, z: number, w: number, h: number, sky: THREE.Texture) {
    g.add(at(board(w, h, 0.12, picMat(sky), "#f4f1ea"), x, y, z));
    g.add(at(box(0.08, h, 0.14, col("trimW", "#f4f1ea")), x, y, z + 0.03));
    g.add(at(box(w, 0.08, 0.14, col("trimW", "#f4f1ea")), x, y, z + 0.03));
  }

  tvScreen!: THREE.Mesh;
  calc = new THREE.Group();
  private dorm() {
    const g = this.room(ROOM.dorm, 10, 5, 3.8, lam("dormFloor", () => ({ map: woodFloor() })), lam("dormWall", () => ({ map: wallPaint("dormW", "#8fb7d9", "#5f86b0", true) })));
    // bed (left)
    g.add(at(box(2.1, 0.45, 3.2, col("bedFrame", "#7a4f33")), -3.7, 0.25, -3.2));
    g.add(at(box(2.0, 0.25, 3.1, col("mattress", "#f4f1ea")), -3.7, 0.6, -3.2));
    g.add(at(box(2.04, 0.22, 2.2, col("blanket", "#e2453c")), -3.7, 0.72, -2.7));
    g.add(at(box(1.2, 0.2, 0.55, col("pillow", "#ffffff")), -3.7, 0.82, -4.4));
    // desk (right) with lamp, books, calculator, catalogue
    g.add(at(box(2.4, 0.08, 1.1, col("desk", "#c8a070")), 3.4, 0.95, -3.9));
    for (const sx of [-1.1, 1.1]) g.add(at(box(0.08, 0.95, 1.0, col("deskLeg", "#8a5a3c")), 3.4 + sx, 0.47, -3.9));
    g.add(at(box(0.5, 0.06, 0.38, col("book1", "#3f6fb5")), 4.3, 1.02, -4.1)); g.add(at(box(0.46, 0.06, 0.34, col("book2", "#5d7a3a")), 4.3, 1.08, -4.1));
    const lampA = cyl(0.03, 0.03, 0.6, col("lampPost", "#3a3f4e"), 8); lampA.rotation.z = 0.3; g.add(at(lampA, 2.5, 1.25, -4.2));
    g.add(at(mesh(new THREE.ConeGeometry(0.18, 0.22, 16, 1, true), col("lampShade", "#f2c94c")), 2.65, 1.55, -4.2));
    this.catalog.rotation.x = -Math.PI / 2; at(this.catalog, 3.3, 1.0, -3.75); this.catalog.rotation.z = 0.12; g.add(this.catalog);
    // calculator (dynamic display)
    this.calc.add(box(0.26, 0.04, 0.36, col("calcB", "#3a3f4e")));
    const disp = new THREE.Mesh(new THREE.PlaneGeometry(0.22, 0.08), picMat(this.calcTex.tex)); disp.rotation.x = -Math.PI / 2; disp.position.set(0, 0.022, -0.12); this.calc.add(disp);
    for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) this.calc.add(at(box(0.04, 0.02, 0.035, col(i === 3 ? "keyO" : "keyG", i === 3 ? "#f08a2c" : "#d7d9de")), -0.08 + i * 0.054, 0.025, -0.03 + j * 0.05));
    at(this.calc, 3.95, 1.01, -3.65); this.calc.rotation.y = -0.2; g.add(this.calc);
    // TV on a dresser, centre back
    g.add(at(box(2.0, 0.9, 0.7, col("dresser", "#8a5a3c")), 0.4, 0.45, -4.6));
    g.add(at(box(1.7, 1.05, 0.25, col("tvBody", "#25252c")), 0.4, 1.45, -4.62));
    this.tvScreen = new THREE.Mesh(new THREE.PlaneGeometry(1.52, 0.9), picMat(this.tvTex.tex)); at(this.tvScreen, 0.4, 1.45, -4.48); g.add(this.tvScreen);
    // posters + window
    const p1 = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 1.3), picMat(signTex("poster1", ["JET", "LIFE"], { bg: "#241726", fg: "#f2c94c", w: 512, h: 740, sizes: [170, 170] })));
    at(p1, -2.0, 2.5, -4.98); g.add(p1);
    const p2 = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 0.7), picMat(signTex("poster2", ["STUDY?", "LATER"], { bg: "#e2453c", fg: "#ffffff", w: 600, h: 420, sizes: [110, 90] })));
    at(p2, 2.8, 2.6, -4.98); p2.rotation.z = -0.05; g.add(p2);
    // can pile next to bed
    at(this.cansDorm, -1.4, 0, -3.6); g.add(this.cansDorm);
    at(this.cansMega, -2.6, 0, -1.6); g.add(this.cansMega);
    // rug
    g.add(at(box(3.2, 0.02, 2.2, lam("rug", () => ({ map: carpet("rug", "#7b5ac9") }))), 0.6, 0.01, -1.6));
  }
  private classroom() {
    const g = this.room(ROOM.class, 12, 6, 4.2, lam("classFloor", () => ({ map: woodFloor("classF", "#c09060") })), lam("classWall", () => ({ map: wallPaint("classW", "#f2e3c4", "#6a9a7a") })));
    const cb = board(4.6, 2.3, 0.1, picMat(chalkboard(["ARBITRAGE", "BUY CHEAP: 10¢ points", "→ WORTH WAY MORE: $$$ JET"], "chalkArb")), "#6a4a2c");
    at(cb, 0, 2.2, -5.92); g.add(cb);
    g.add(at(box(2.0, 0.85, 0.9, col("tdesk", "#8a5a3c")), 2.8, 0.42, -4.2));
    g.add(at(canMesh(1.6), 2.4, 0.85, -4.1));
    for (let r = 0; r < 3; r++) for (let c = 0; c < 4; c++) {
      const x = -4.2 + c * 2.8, z = -1.2 + r * 2.2;
      g.add(at(box(1.1, 0.06, 0.7, col("sdesk", "#c8a070")), x, 0.76, z));
      for (const sx of [-0.48, 0.48]) g.add(at(box(0.05, 0.76, 0.6, col("deskLeg", "#3a3f4e")), x + sx, 0.38, z));
    }
    const clock = new THREE.Mesh(new THREE.CircleGeometry(0.4, 32), picMat(signTex("clockC", ["3:15"], { bg: "#ffffff", fg: "#241726", w: 256, h: 256, radius: 128, sizes: [80] })));
    at(clock, -4.6, 3.4, -5.95); g.add(clock);
  }
  private boardroom() {
    const g = this.room(ROOM.board, 12, 6, 4.2, lam("boardFloor", () => ({ map: carpet("boardC", "#3a4a6a") })), lam("boardWall", () => ({ map: woodPanel() })));
    g.add(at(box(8.5, 0.12, 1.8, twoTone(new THREE.MeshPhongMaterial({ color: "#5a3420", specular: "#806050", shininess: 40 }))), 0, 0.95, -2.2));
    for (const sx of [-3.8, 3.8]) g.add(at(box(0.3, 0.9, 1.4, col("tleg", "#3a2418")), sx, 0.45, -2.2));
    // skyline window behind
    const sky = signTex("skyline", [""], { bg: "#8ab4e8", fg: "#fff", w: 512, h: 256, radius: 2 });
    g.add(at(board(9, 2.6, 0.1, picMat(sky), "#2a2028"), 0, 2.6, -5.9));
    for (let i = 0; i < 9; i++) g.add(at(box(0.9, 0.6 + ((i * 37) % 13) / 10, 0.05, col("skyBld", "#4a5f8a")), -4 + i, 1.6 + ((i * 37) % 13) / 20, -5.8));
    for (let i = 0; i < 5; i++) g.add(at(box(0.7, 1.4, 0.15, col("chairB", "#25252c")), -3.2 + i * 1.6, 1.0, -3.6));
    // money stacks + cans on the table
    for (let i = 0; i < 5; i++) for (let k = 0; k < 3; k++) g.add(at(box(0.32, 0.06, 0.16, col("cash", "#5d9a4a")), -3.2 + i * 1.6, 1.05 + k * 0.065, -1.7));
    const lb = new THREE.Mesh(new THREE.PlaneGeometry(3.4, 0.7), picMat(signTex("invest", ["OPERATION: JET"], { bg: "#f4f1ea", fg: "#c0262f", w: 1024, h: 210, sizes: [120] })));
    at(lb, 0, 3.9, -5.84); g.add(lb);
  }
  private office() {
    const g = this.room(ROOM.office, 10, 5, 4.0, lam("offFloor", () => ({ map: carpet("offC", "#5a6a8a") })), lam("offWall", () => ({ map: wallPaint("offW", "#e8e2d6", "#2f5f6a") })));
    const sky = signTex("officeSky", [""], { bg: "#9cc9f0", fg: "#fff", w: 256, h: 256, radius: 2 });
    g.add(at(board(8, 2.6, 0.1, picMat(sky), "#2a2028"), 0, 2.2, -4.92));
    for (let i = 0; i < 8; i++) g.add(at(box(0.8, 0.8 + ((i * 53) % 17) / 8, 0.05, col("skyBld2", "#6f87b8")), -3.5 + i, 1.4 + ((i * 53) % 17) / 16, -4.82));
    g.add(at(box(3.2, 0.1, 1.4, twoTone(new THREE.MeshPhongMaterial({ color: "#2a1a12", specular: "#7a6050", shininess: 50 }))), 0, 1.0, -2.6));
    g.add(at(box(3.0, 0.95, 0.12, col("deskFront", "#3a2418")), 0, 0.5, -1.95));
    g.add(at(canMesh(1.8), 1.1, 1.05, -2.5));
    const nm = new THREE.Mesh(new THREE.PlaneGeometry(1.1, 0.24), picMat(signTex("ceo", ["C.E.O."], { bg: "#e8b33a", fg: "#241726", w: 512, h: 112, sizes: [80] })));
    at(nm, -0.6, 1.17, -2.05); nm.rotation.x = -0.3; g.add(nm);
    const lg = new THREE.Mesh(new THREE.PlaneGeometry(3.2, 0.9), picMat(signTex("hqWall", ["SODA CO."], { bg: "#1d4fb8", fg: "#ffffff", w: 1024, h: 288, sizes: [170], stripe: "#d8323c" })));
    at(lg, 0, 3.75, -4.86); g.add(lg);
    for (const x of [-4.2, 4.2]) { g.add(at(cyl(0.3, 0.25, 0.6, col("pot", "#b8684a"), 12), x, 0.3, -4.2)); g.add(at(mesh(new THREE.IcosahedronGeometry(0.6, 1), col("leaf0", "#5fae4a")), x, 1.2, -4.2)); }
  }
  private courtroom() {
    const g = this.room(ROOM.court, 12, 6, 5, lam("courtFloor", () => ({ map: woodFloor("courtF", "#8a5a3c") })), lam("courtWall", () => ({ map: woodPanel() })));
    // raised bench
    g.add(at(box(5, 1.6, 1.4, lam("bench", () => ({ map: woodPanel() }))), 0, 0.8, -4.6));
    g.add(at(box(5.3, 0.12, 1.6, col("benchTop", "#3a2418")), 0, 1.66, -4.5));
    const seal = new THREE.Mesh(new THREE.CircleGeometry(0.9, 40), picMat(signTex("seal", ["⚖"], { bg: "#e8b33a", fg: "#3a2418", w: 256, h: 256, radius: 128, sizes: [170], shadow: false })));
    at(seal, 0, 3.9, -5.92); g.add(seal);
    for (const x of [-3.4, 3.4]) {
      g.add(at(cyl(0.04, 0.04, 3.2, col("pole", "#d7d9de"), 8), x, 1.6, -5.3));
      const f = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 0.7), lam("usFlag", () => ({ side: THREE.DoubleSide }))); at(f, x + 0.5, 2.8, -5.3); g.add(f);
    }
    // plaintiff table + gallery benches
    g.add(at(box(2.6, 0.08, 0.9, col("desk", "#c8a070")), -2.4, 0.9, -1.2));
    for (const sx of [-1.2, 1.2]) g.add(at(box(0.08, 0.9, 0.8, col("deskLeg", "#8a5a3c")), -2.4 + sx, 0.45, -1.2));
    for (let r = 0; r < 2; r++) for (const x of [-3, 3]) { g.add(at(box(4, 0.5, 0.5, col("pew", "#7a4f33")), x, 0.25, 1.2 + r * 1.6)); g.add(at(box(4, 0.9, 0.12, col("pew", "#7a4f33")), x, 0.75, 1.5 + r * 1.6)); }
    g.add(at(box(11.6, 1.0, 0.1, col("rail", "#5a3420")), 0, 0.5, 0.2));
  }
}

/** sign drawing reused by the dynamic price board */
export const drawPrice = (g: CanvasRenderingContext2D, W: number, H: number, big: string, small: string, tiny: string, o?: Partial<SignOpts>) => {
  drawSign(g, W, H, [], { bg: o?.bg ?? "#fff36b", fg: "#e2453c", radius: 40 });
  g.textAlign = "center"; g.textBaseline = "middle";
  g.fillStyle = "#241726"; g.font = '900 104px "Arial Black", Arial'; g.fillText("PRICE:", W / 2, H * 0.17);
  g.fillStyle = o?.fg ?? "#e2453c"; g.font = '900 210px "Arial Black", Arial';
  let s = 1; const mw = g.measureText(big).width; if (mw > W * 0.92) s = (W * 0.92) / mw;
  g.save(); g.translate(W / 2, H * 0.43); g.scale(s, 1); g.fillText(big, 0, 0); g.restore();
  g.fillStyle = "#241726"; g.font = '900 124px "Arial Black", Arial'; g.fillText(small, W / 2, H * 0.7);
  if (tiny) { g.fillStyle = "#6a6070"; g.font = '700 20px Arial'; g.fillText(tiny, W * 0.79, H * 0.92); }
};
