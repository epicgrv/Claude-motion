// Silver cast: flat 2D characters with the v5 rig (2-bone IK arms, breathing, weight shift, nods, calm blinks,
// smooth eyes; mouths only move on lines a character speaks). Props drawn in hands; effects are unlit 2D cards.
import * as THREE from "three";
import { Pen, bodyFront, Outfit, Expr, FrontOpts, INK, fxBurst, fxPuff, fxShadow, fxContact, ArmPose, Hold } from "../pepsi/toon";
import { Place, FxPlace } from "../bridge/cast";
import { LINES, MOUTH, VISEME } from "./vo";
import { FPS, Light, OFFICIAL, BUNKER, HERBERT, BUNKER_R, HERBERT_R, RIP, SLIDE, GUSH, MONEY } from "./story";
import { V3, RANCH, EXCH, EX_STEP_Y } from "./sets";
import { TOWN, OFFICE, FLOOR, COURT, VAULT } from "./places";
import { cartPath } from "./screens";
import { planeAt } from "./story";

export type Stage = { places: Place[]; fx: FxPlace[] };

// ---------------- the cast (our own designs) ----------------
const BUNK: Outfit = { jacket: "#8a5a34", pants: "#6a4630", boots: "#3a2618", hat: "cowboy", hatCol: "#f3ede0", band: "#3a2a20", glasses: INK,
  build: "stout", skin: "#f5c9a0", buttons: "#e8c45a", collar: "#ffffff", tie: "#2f2a26" };
const HERB: Outfit = { jacket: "#6f7584", pants: "#4a4e5a", boots: "#3a2618", hat: "cowboy", hatCol: "#c9a26a", band: "#5a3b2a", moustache: "#8a7a6a",
  skin: "#ffe2c2", buttons: "#d9dde0", collar: "#ffffff", tie: "#8c2f35" };
const SUIT: Outfit = { jacket: "#1f2a44", pants: "#1f2a44", boots: INK, hat: "hair", hair: "#2a201a", skin: "#ecd0b6", collar: "#ffffff", tie: "#d8323c", buttons: "#c9ccd2" };
const GRANNY: Outfit = { jacket: "#b07ac9", pants: "#5a4a8c", boots: "#5a3b2a", hat: "hair", hair: "#e6e6ea", dress: "#7b5ac9", glasses: INK, skin: "#ffe2c2", build: "stout" };
const SHOPPER: Outfit = { jacket: "#f08a2c", pants: "#56607a", boots: "#5a3b2a", hat: "hair", hair: "#8a5a3c", dress: "#e8b33a", skin: "#ecd0b6" };
const GUARD: Outfit = { jacket: "#1f2a44", pants: "#1f2a44", boots: INK, hat: "cap", cap: "#1f2a44", buttons: "#e8c45a", moustache: "#3a2a20", build: "stout", skin: "#c99067" };
const JUDGE: Outfit = { jacket: "#1e1e26", pants: "#1e1e26", boots: INK, hat: "hair", hair: "#f1efe6", build: "stout", skin: "#ecd0b6", collar: "#ffffff", buttons: "#1e1e26", glasses: INK };
const BANKER: Outfit = { jacket: "#2b3448", pants: "#2b3448", boots: INK, hat: "tophat", moustache: "#c9c9d1", build: "stout", skin: "#f5c9a0", collar: "#ffffff", tie: "#e8c45a", buttons: "#e8c45a" };
const FOLKS: Outfit[] = [
  { jacket: "#c46a2c", pants: "#5a4630", boots: "#3a2618", hat: "hair", hair: "#5a3b2a", skin: "#f5c9a0", moustache: "#5a3b2a" },
  { jacket: "#3fae8a", pants: "#3b3f52", boots: "#f4f1ea", hat: "hair", hair: "#2a201a", dress: "#3fae8a", skin: "#c99067" },
  { jacket: "#e8b33a", pants: "#3b5b9a", boots: "#f4f1ea", hat: "cap", cap: "#e2453c", build: "kid", skin: "#ffe2c2" },
  { jacket: "#7b5ac9", pants: "#3b3f52", boots: "#5a3b2a", hat: "hair", hair: "#e8c45a", dress: "#c25a7a", skin: "#ffe2c2" },
  { jacket: "#5d7a3a", pants: "#4a4e5a", boots: "#3a2618", hat: "cowboy", hatCol: "#8a5a34", band: "#3a2a20", skin: "#ecd0b6", build: "stout" },
  { jacket: "#3f6fb5", pants: "#2f3550", boots: "#3a2618", hat: "cap", cap: "#3f6fb5", skin: "#c99067" },
];
const TRADERS: Outfit[] = ["#e8b33a", "#3f7fd0", "#c0353a", "#3fae8a", "#f08a2c", "#7b5ac9", "#e2453c", "#2f5f6a"].map((c, i) => ({
  jacket: c, pants: "#2b2b34", boots: INK, hat: "hair", hair: ["#5a3b2a", "#2a201a", "#c9c9d1", "#8a5a3c", "#e8c45a"][i % 5], collar: "#ffffff", tie: ["#241726", "#d8323c", "#f2c94c", "#3f7fd0"][i % 4],
  skin: ["#ffe2c2", "#f5c9a0", "#ecd0b6", "#c99067"][i % 4], build: i % 3 === 0 ? "stout" : "adult", moustache: i % 4 === 1 ? "#3a2a20" : undefined, glasses: i % 5 === 2 ? INK : undefined,
}));
const OUT: Record<string, Outfit> = { BUNKER: BUNK, HERBERT: HERB, OFFICIAL: SUIT, GRANNY, SHOPPER, GUARD, JUDGE };
const SEED: Record<string, number> = { BUNKER: 3, HERBERT: 6, OFFICIAL: 5 };

// ---------------- held things ----------------
const bookCv = (half: 0 | 1 | 2) => {
  const W = half ? 380 : 720, H = 520, cv = document.createElement("canvas"); cv.width = W; cv.height = H;
  const g = cv.getContext("2d")!;
  g.fillStyle = "#7a1f2a"; g.strokeStyle = INK; g.lineWidth = 16;
  g.beginPath(); g.roundRect(10, 10, W - 20, H - 20, 26); g.fill(); g.stroke();
  g.fillStyle = "#f2e6c8"; g.fillRect(half === 2 ? 10 : 30, H - 70, W - 60, 34);       // page edges
  if (half === 0) {
    g.fillStyle = "#e8c45a"; g.font = '900 120px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle";
    g.fillText("RULES", W / 2, 190); g.font = '900 48px "Arial Black", Arial'; g.fillText("SILVERMART", W / 2, 300);
    g.strokeStyle = "#e8c45a"; g.lineWidth = 8; g.strokeRect(60, 70, W - 120, 300);
  } else {
    // torn edge
    g.fillStyle = "#f2e6c8"; g.beginPath(); const x = half === 1 ? W - 14 : 14;
    g.moveTo(x, 10); for (let y = 10; y < H - 10; y += 34) g.lineTo(x + (half === 1 ? -1 : 1) * (y / 34 % 2 ? 26 : 4), y + 17); g.lineTo(x, H - 10); g.closePath(); g.fill();
    g.fillStyle = "#e8c45a"; g.font = '900 110px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(half === 1 ? "RU" : "LES", W / 2, 190);
  }
  return cv;
};
let BOOK: HTMLCanvasElement[] | null = null;
const book = (i: 0 | 1 | 2) => (BOOK ??= [bookCv(0), bookCv(1), bookCv(2)])[i];
const barCv = (() => { let c: HTMLCanvasElement | null = null; return () => {
  if (c) return c; c = document.createElement("canvas"); c.width = 400; c.height = 200; const g = c.getContext("2d")!;
  const gr = g.createLinearGradient(0, 0, 0, 200); gr.addColorStop(0, "#ffffff"); gr.addColorStop(0.5, "#cfd6e0"); gr.addColorStop(1, "#8e9aad");
  g.fillStyle = gr; g.strokeStyle = INK; g.lineWidth = 14; g.beginPath(); g.moveTo(60, 20); g.lineTo(340, 20); g.lineTo(390, 180); g.lineTo(10, 180); g.closePath(); g.fill(); g.stroke();
  g.fillStyle = "rgba(255,255,255,.8)"; g.fillRect(80, 36, 220, 14);
  g.fillStyle = "#5a6478"; g.font = '900 54px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("Ag", 200, 115);
  return c; }; })();

/** small held-object canvases, drawn once and cached */
const cvCache = new Map<string, HTMLCanvasElement>();
const cvs = (key: string, w: number, h: number, draw: (g: CanvasRenderingContext2D) => void) => {
  let c = cvCache.get(key); if (c) return c;
  c = document.createElement("canvas"); c.width = w; c.height = h; const g = c.getContext("2d")!; g.lineJoin = "round"; g.strokeStyle = INK; g.lineWidth = 12; draw(g); cvCache.set(key, c); return c;
};
const H = (key: string, w: number, h: number, side: -1 | 1, ww: number, rot: number, dx: number, dy: number, draw: (g: CanvasRenderingContext2D) => void): Hold =>
  ({ side, img: cvs(key, w, h, draw), w: ww, h: (ww * h) / w, rot, dx, dy, key });
const silverFill = (g: CanvasRenderingContext2D, y0: number, y1: number) => { const gr = g.createLinearGradient(0, y0, 0, y1); gr.addColorStop(0, "#ffffff"); gr.addColorStop(0.5, "#c9d1dc"); gr.addColorStop(1, "#8e9aad"); return gr; };
const billDraw = (g: CanvasRenderingContext2D) => {
  g.fillStyle = "#9bd88f"; g.strokeStyle = "#1f5a2a"; g.beginPath(); g.roundRect(8, 8, 384, 184, 14); g.fill(); g.stroke();
  g.strokeStyle = "rgba(31,90,42,.6)"; g.lineWidth = 5; g.strokeRect(30, 28, 340, 144);
  g.fillStyle = "#1f5a2a"; g.beginPath(); g.ellipse(200, 100, 48, 56, 0, 0, 7); g.fill(); g.fillStyle = "#9bd88f"; g.font = '900 72px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("$", 200, 104);
};
const HOLD = {
  bill: (w: number) => H("bill", 400, 200, 1, w * 1.6, -0.1, -0.1, -0.1, billDraw),
  forks: () => H("forks", 300, 420, 1, 0.85, -0.15, 0, -0.45, (g) => {
    for (let i = 0; i < 4; i++) { g.save(); g.translate(90 + i * 40, 400); g.rotate(-0.2 + i * 0.14); g.fillStyle = silverFill(g, -380, 0);
      g.beginPath(); g.roundRect(-12, -250, 24, 250, 10); g.fill(); g.stroke(); g.beginPath(); g.roundRect(-34, -380, 68, 140, 12); g.fill(); g.stroke();
      for (const x of [-18, 0, 18]) { g.beginPath(); g.moveTo(x, -380); g.lineTo(x, -300); g.stroke(); } g.restore(); }
  }),
  candle: () => H("candle", 260, 460, 1, 0.75, 0.05, 0, -0.55, (g) => {
    g.fillStyle = silverFill(g, 100, 440); g.beginPath(); g.moveTo(60, 440); g.lineTo(200, 440); g.lineTo(150, 380); g.lineTo(150, 170); g.lineTo(190, 150); g.lineTo(70, 150); g.lineTo(110, 170); g.lineTo(110, 380); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = "#f4f1ea"; g.fillRect(105, 40, 50, 110); g.strokeRect(105, 40, 50, 110); g.fillStyle = "#f2c94c"; g.beginPath(); g.ellipse(130, 22, 14, 22, 0, 0, 7); g.fill();
  }),
  trophy: () => H("trophy", 320, 380, 1, 0.8, 0, 0, -0.5, (g) => {
    g.fillStyle = silverFill(g, 20, 360); g.beginPath(); g.moveTo(60, 30); g.lineTo(260, 30); g.quadraticCurveTo(250, 200, 160, 220); g.quadraticCurveTo(70, 200, 60, 30); g.fill(); g.stroke();
    for (const s of [-1, 1]) { g.beginPath(); g.ellipse(160 + s * 115, 100, 40, 55, 0, 0, 7); g.stroke(); }
    g.beginPath(); g.rect(140, 220, 40, 70); g.fill(); g.stroke(); g.beginPath(); g.rect(90, 290, 140, 60); g.fill(); g.stroke();
  }),
  teapot: () => H("teapot", 380, 300, 1, 0.9, 0, 0, -0.35, (g) => {
    g.fillStyle = silverFill(g, 40, 280); g.beginPath(); g.ellipse(190, 180, 120, 95, 0, 0, 7); g.fill(); g.stroke();
    g.beginPath(); g.moveTo(300, 170); g.quadraticCurveTo(360, 150, 370, 90); g.lineTo(350, 90); g.quadraticCurveTo(330, 140, 300, 140); g.fill(); g.stroke();
    g.beginPath(); g.ellipse(70, 170, 34, 50, 0, 0, 7); g.stroke(); g.beginPath(); g.ellipse(190, 80, 40, 18, 0, 0, 7); g.fill(); g.stroke();
  }),
  profit: () => H("profit", 360, 460, 1, 0.9, -0.12, 0, -0.55, (g) => {
    g.fillStyle = "#f4f1ea"; g.beginPath(); g.roundRect(10, 10, 340, 440, 10); g.fill(); g.stroke();
    g.fillStyle = "#2f7a3a"; g.font = '900 54px "Arial Black", Arial'; g.textAlign = "center"; g.fillText("PROFIT", 180, 80);
    g.font = '900 96px "Arial Black", Arial'; g.fillText("+$$$", 180, 200); g.fillStyle = "#241726"; g.font = '700 40px Arial'; g.fillText("BILLIONS", 180, 270);
    g.strokeStyle = "#2f7a3a"; g.lineWidth = 10; g.beginPath(); g.moveTo(50, 420); g.lineTo(120, 380); g.lineTo(190, 395); g.lineTo(300, 300); g.stroke();
  }),
  stamp: () => H("stamp", 300, 420, 1, 0.75, 0, 0, -0.5, (g) => {
    g.fillStyle = "#7a4a2c"; g.beginPath(); g.ellipse(150, 70, 70, 60, 0, 0, 7); g.fill(); g.stroke();
    g.fillRect(125, 120, 50, 150); g.strokeRect(125, 120, 50, 150);
    g.fillStyle = "#c0262f"; g.beginPath(); g.roundRect(40, 270, 220, 120, 12); g.fill(); g.stroke();
  }),
  handset: () => H("handset", 420, 160, 1, 0.95, -0.55, 0.05, -0.05, (g) => {
    g.fillStyle = "#c0262f"; g.beginPath(); g.roundRect(60, 40, 300, 50, 25); g.fill(); g.stroke();
    for (const x of [70, 350]) { g.beginPath(); g.ellipse(x, 100, 52, 40, 0, 0, 7); g.fill(); g.stroke(); }
  }),
  wallet: () => H("wallet", 400, 280, 1, 0.9, 0.05, -0.1, -0.35, (g) => {
    g.fillStyle = "#26202c"; g.beginPath(); g.roundRect(10, 40, 380, 230, 18); g.fill(); g.stroke();
    g.fillStyle = "#2a1a12"; g.beginPath(); g.roundRect(40, 60, 320, 70, 10); g.fill();
    g.strokeStyle = "#c9a26a"; g.lineWidth = 6; g.setLineDash([14, 10]); g.strokeRect(30, 150, 340, 100);
  }),
  bag: (i: number) => H("bag", 300, 340, 1, 0.95, 0.1 * (i % 2 ? 1 : -1), 0, -0.1, (g) => {
    g.fillStyle = "#c9a26a"; g.beginPath(); g.moveTo(110, 60); g.lineTo(190, 60); g.lineTo(170, 100); g.quadraticCurveTo(300, 160, 270, 290); g.quadraticCurveTo(150, 340, 30, 290); g.quadraticCurveTo(0, 160, 130, 100); g.closePath(); g.fill(); g.stroke();
    g.fillStyle = "#2f7a3a"; g.font = '900 120px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("$", 150, 220);
  }),
  verdict: () => H("verdict", 360, 300, 1, 1.0, -0.08, 0, -0.5, (g) => {
    g.fillStyle = "#f4f1ea"; g.beginPath(); g.roundRect(10, 10, 340, 280, 10); g.fill(); g.stroke();
    g.fillStyle = "#c0262f"; g.font = '900 74px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("LIABLE", 180, 110);
    g.fillStyle = "#241726"; g.font = '700 34px Arial'; g.fillText("RIGGED THE MARKET", 180, 200);
  }),
  coin: () => H("coin", 220, 220, 1, 0.45, 0, -0.05, -0.25, (g) => {
    g.fillStyle = silverFill(g, 10, 210); g.beginPath(); g.arc(110, 110, 96, 0, 7); g.fill(); g.stroke();
    g.lineWidth = 6; g.beginPath(); g.arc(110, 110, 70, 0, 7); g.stroke(); g.fillStyle = "#5a6478"; g.font = '900 70px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("1", 110, 114);
  }),
};

// ---------------- life ----------------
const hh = (i: number, s = 0) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };
const noise = (x: number, s: number) => { const i = Math.floor(x), f = x - i, w = f * f * (3 - 2 * f); return (hh(i, s) * (1 - w) + hh(i + 1, s) * w) * 2 - 1; };
const lidAt = (t: number, i: number, shotStart: number) => {
  const f = Math.round(t * FPS);
  if (f - Math.round(shotStart * FPS) < 6) return 0;
  let s = Math.round(-90 * hh(i, 9));
  for (let n = 0; s <= f && n < 400; n++) { const k = f - s; if (k >= 0 && k < 3) return [0.5, 1, 0.5][k]; s += Math.round(75 + 90 * hh(i * 31 + n, 13)); }
  return 0;
};
const lineAt = (t: number) => LINES.find((l) => t >= l.s - 0.04 && t <= l.e + 0.04);
const visOf = (t: number) => { const f = Math.round(t * FPS); return f >= 0 && f < VISEME.length ? Number(VISEME[f]) : 0; };
const mouthOf = (who: string, t: number) => {
  const l = lineAt(t); if (!l || l.who !== who) return 0;
  const f = Math.round(t * FPS); return f >= 0 && f < MOUTH.length ? Number(MOUTH[f]) / 4 : 0;
};
const energy = (who: string, t: number) => { let a = 0; for (let k = -4; k <= 4; k++) a += mouthOf(who, t + k / FPS); return Math.min(1, (a / 9) * 1.6); };

// ---------------- arm poses (hand target from the shoulder, in head heights; x outward, y down) ----------------
type AP = ArmPose;
const REST: AP = { x: 0.16, y: 1.02 };
const HIP: AP = { x: 0.5, y: 0.7 };
const UP: AP = { x: 0.3, y: -1.05 };
const WIDE: AP = { x: 1.1, y: -0.35 };
const SHRUG: AP = { x: 0.78, y: 0.12 };
const SHOWHI: AP = { x: 0.05, y: 0.0, front: true };
const FACEP: AP = { x: -0.42, y: -0.35, front: true };
const THUMB: AP = { x: -0.25, y: 0.35, front: true };
const CROSSA: AP = { x: -0.55, y: 0.62, front: true };
const lerpA = (a: AP, b: AP, k: number): AP => ({ x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k, front: k < 0.5 ? a.front : b.front, bend: b.bend ?? a.bend });
const sm = (x: number) => { const u = Math.min(1, Math.max(0, x)); return u * u * (3 - 2 * u); };
const keys = (t: number, k: [number, AP][], dur = 0.28): AP => {
  if (t <= k[0][0]) return k[0][1];
  for (let i = 0; i + 1 < k.length; i++) { const [t1, b] = k[i + 1]; if (t < t1) { const a = k[i][1], u = sm((t - (t1 - dur)) / dur); return lerpA(a, b, u); } }
  return k[k.length - 1][1];
};
const breathe = (a: AP, t: number, seed: number): AP => ({ ...a, x: a.x + 0.012 * Math.sin(t * 1.7 + seed), y: a.y + 0.02 * Math.sin(t * 1.9 + seed) });
/** excited wave: arm pumping up and down */
const pump = (t: number, seed: number, base = UP): AP => ({ ...base, x: base.x + 0.08 * Math.sin(t * 8 + seed), y: base.y + 0.22 * Math.sin(t * 8 + seed) });

// ---------------- drawing helpers ----------------
const q = (v: number, n = 160) => Math.round(v * n) / n;
const fkey = (o: object) => JSON.stringify(o, (_k, v) => (typeof v === "number" ? q(v) : v && typeof v === "object" && "img" in v ? { ...v, img: undefined } : v));
const tier = (d: number): [number, number, number] => (d < 3.0 ? [1200, 2000, 2.0] : d < 6.5 ? [900, 1500, 1.5] : d < 16 ? [480, 800, 0.8] : [240, 400, 0.4]);
export type CamInfo = { pos: THREE.Vector3; right: THREE.Vector3; sun: THREE.Vector3 };
const light2D = (cam: CamInfo) => Math.round(Math.atan2(-cam.sun.y, cam.sun.dot(cam.right)) / (Math.PI / 4)) * (Math.PI / 4);
const tmp = new THREE.Vector3();
type Who = { id: string; o?: Outfit; seed?: number; i?: number };
type Act = { expr?: Expr; mode?: FrontOpts["mode"]; look?: number; facing?: -1 | 0 | 1; tilt?: number; headTilt?: number; phase?: number; scale?: number; blob?: boolean;
  armL?: AP; armR?: AP; hold?: Hold; still?: boolean; bounce?: number };
type Ctx = { out: Stage; cam: CamInfo; t: number; s0: number; light: Light };

const blob = (out: Stage, cam: CamInfo, x: number, y: number, z: number, sc: number, light: Light) => {
  const hl = Math.hypot(cam.sun.x, cam.sun.z) || 1, ox = -cam.sun.x / hl, oz = -cam.sun.z / hl, rot = Math.atan2(-ox, -oz);
  const el = Math.asin(Math.min(0.99, Math.max(0.1, cam.sun.y)));
  const len = Math.min(light === "golden" ? 3.4 : 2.4, Math.max(0.5, 1.6 / Math.tan(el))) * sc, h = len + 0.55 * sc, c = 0.3 * h;
  const sh = light === "golden" ? "#a2758a" : "#a9adc4";
  out.fx.push({ key: `blob|shadow|${sh}`, cw: 128, ch: 256, draw: (p) => fxShadow(p, sh), x: x + ox * c, y: y + 0.018, z: z + oz * c, w: 0.72 * sc, h, flat: true, rot });
  out.fx.push({ key: "blob|contact|#7a7c9a", cw: 128, ch: 128, draw: (p) => fxContact(p, "#7a7c9a"), x, y: y + 0.022, z, w: 0.52 * sc, h: 0.4 * sc, flat: true, rot });
};

const person = (c: Ctx, who: Who, p: V3, a: Act = {}) => {
  const o = who.o ?? OUT[who.id], seed = who.seed ?? SEED[who.id] ?? 1, idx = who.i ?? seed, t = c.t;
  const sc = a.scale ?? 1;
  const d = c.cam.pos.distanceTo(tmp.set(p[0], p[1] + 1.3 * sc, p[2])) / sc;
  const [w, h, k] = tier(d);
  const m = mouthOf(who.id, t), e = energy(who.id, t), live = !a.still;
  let armR = a.armR, armL = a.armL;
  if (live) { armR = breathe(armR ?? REST, t, seed); armL = breathe(armL ?? REST, t, seed + 1.3); }
  const fo: FrontOpts = {
    expr: a.expr ?? "neutral", mode: a.mode ?? "stand", facing: a.facing ?? 0, prop: null, phase: a.phase ?? 0,
    look: (a.look ?? 0) + (live ? 0.18 * noise(t * 0.45, seed) : 0),
    tilt: (a.tilt ?? 0) + (live ? 1.1 * Math.sin(t * 1.35 + seed) + 2.2 * e * Math.sin(t * 4.1 + seed) : 0),
    headTilt: (a.headTilt ?? 0) + (live ? 1.5 * noise(t * 0.6, seed + 5) + 3.5 * e * Math.sin(t * 6.2 + seed) : 0),
    rise: live ? Math.sin(t * 1.9 + seed) : 0, mouth: m, viseme: m > 0.08 ? visOf(t) : 0, brow: Math.min(1, e * 1.1),
    blink: lidAt(t, idx, c.s0), light: light2D(c.cam), seed, armL, armR, hold: a.hold,
  };
  c.out.places.push({ key: `F|${who.id}${who.i ?? ""}|${fkey(fo)}`, x: p[0], y: p[1] + 0.06 * (a.bounce ?? 0), z: p[2], scale: sc, draw: (pp: Pen) => bodyFront(pp, o, fo), size: [w, h, k] });
  if (a.blob !== false) blob(c.out, c.cam, p[0], p[1], p[2], sc, c.light);
};

// ---------------- effect cards ----------------
const burst = (out: Stage, t: number, t0: number, dur: number, p: V3, size: number, col = "#fff3b0", rays = 12) => {
  const u = (t - t0) / dur; if (u < 0 || u > 1) return;
  const uq = q(u, 30);
  out.fx.push({ key: `burst${col}${rays}${uq}`, cw: 500, ch: 500, draw: (pp) => fxBurst(pp, uq, col, rays), x: p[0], y: p[1], z: p[2], w: size, h: size });
};
const puff = (out: Stage, t: number, t0: number, dur: number, p: V3, size: number) => {
  const u = (t - t0) / dur; if (u < 0 || u > 1) return;
  const uq = q(u, 30);
  out.fx.push({ key: `puff${uq}`, cw: 300, ch: 300, draw: (pp) => fxPuff(pp, uq), x: p[0], y: p[1], z: p[2], w: size, h: size, soft: true });
};
/** 4-point star glint on silver */
const glint = (out: Stage, t: number, t0: number, p: V3, size: number) => {
  const u = (t - t0) / 0.45; if (u < 0 || u > 1) return;
  const s = Math.sin(Math.PI * u), uq = q(s, 12);
  out.fx.push({ key: `glint${uq}`, cw: 256, ch: 256, draw: (pp) => {
    const g = pp.g; g.fillStyle = "#ffffff"; g.translate(128, 128);
    const r = 120 * uq, w = 16 * uq + 2;
    g.beginPath(); g.moveTo(0, -r); g.quadraticCurveTo(w * 0.4, -w * 0.4, r, 0); g.quadraticCurveTo(w * 0.4, w * 0.4, 0, r); g.quadraticCurveTo(-w * 0.4, w * 0.4, -r, 0); g.quadraticCurveTo(-w * 0.4, -w * 0.4, 0, -r); g.fill();
    const gr = g.createRadialGradient(0, 0, 0, 0, 0, 60 * uq + 1); gr.addColorStop(0, "rgba(255,255,255,0.9)"); gr.addColorStop(1, "rgba(255,255,255,0)"); g.fillStyle = gr; g.fillRect(-128, -128, 256, 256);
  }, x: p[0], y: p[1], z: p[2], w: size, h: size, soft: true, rot: 0.3 });
};
const pop = (out: Stage, t: number, t0: number, t1: number, p: V3, h: number, text: string, fg = "#ffffff", bg = "#e2453c", rot = 0) => {
  if (t < t0 || t > t1) return;
  const u = Math.min(1, (t - t0) / 0.16), s = u < 1 ? 0.2 + 1.0 * sm(u) * 1.1 : 1 + 0.05 * Math.sin((t - t0) * 10) * Math.exp(-(t - t0) * 4);
  const cw = Math.max(400, 110 * text.length + 120), ch = 240;
  out.fx.push({ key: `pop|${text}|${bg}`, cw, ch, draw: (pp) => {
    const g = pp.g; g.fillStyle = bg; g.strokeStyle = INK; g.lineWidth = 14; g.beginPath(); g.roundRect(10, 10, cw - 20, ch - 20, 40); g.fill(); g.stroke();
    g.font = '900 150px "Arial Black", Arial, sans-serif'; g.textAlign = "center"; g.textBaseline = "middle";
    let k = 1; const mw = g.measureText(text).width; if (mw > cw - 80) k = (cw - 80) / mw;
    g.save(); g.translate(cw / 2, ch / 2 + 8); g.scale(k, 1); g.lineWidth = 18; g.strokeText(text, 0, 0); g.fillStyle = fg; g.fillText(text, 0, 0); g.restore();
  }, x: p[0], y: p[1], z: p[2], w: (h * cw / ch) * s, h: h * s, rot });
};
/** torn paper scraps */
const scraps = (out: Stage, t: number, t0: number, c: V3) => {
  if (t < t0 || t > t0 + 1.4) return;
  for (let i = 0; i < 10; i++) {
    const a = hh(i, 2) * Math.PI * 2, v = 1.4 + 1.6 * hh(i, 3), k = t - t0;
    const x = c[0] + Math.cos(a) * v * k, y = c[1] + 1.6 * k - 2.2 * k * k + 0.4 * Math.sin(a) * v * k, z = c[2] + 0.3 + 0.6 * hh(i, 4) * k;
    out.fx.push({ key: `scrap${i % 3}`, cw: 120, ch: 120, draw: (pp) => {
      const g = pp.g; g.fillStyle = i % 3 ? "#f2e6c8" : "#7a1f2a"; g.strokeStyle = INK; g.lineWidth = 7;
      g.beginPath(); g.moveTo(18, 20); g.lineTo(100, 12); g.lineTo(92, 64); g.lineTo(104, 100); g.lineTo(24, 96); g.lineTo(30, 58); g.closePath(); g.fill(); g.stroke();
    }, x, y, z, w: 0.22, h: 0.22, rot: k * (6 + 6 * hh(i, 5)) });
  }
};
/** oil gusher: a column of glossy black blobs rising, arcing and falling */
const gusher = (out: Stage, t: number, t0: number, top: V3) => {
  if (t < t0) return;
  const k = t - t0, grow = Math.min(1, k / 0.35);
  for (let i = 0; i < 34; i++) {
    const life = 1.3, ph = ((k + i * (life / 34)) % life) / life, born = k - ph * life; if (born < -0.02) continue;
    const a = hh(i, 7) * Math.PI * 2, spread = 0.6 + 1.6 * hh(i, 8);
    const h = 9 * grow * (ph * 2.2 - 1.25 * ph * ph * 2.2), x = top[0] + Math.cos(a) * spread * ph * 3, z = top[2] + Math.sin(a) * spread * ph * 3;
    const sz = 1.3 + 1.6 * hh(i, 9) * (0.5 + ph);
    out.fx.push({ key: `oil${i % 4}`, cw: 160, ch: 160, draw: (pp) => {
      const g = pp.g; g.fillStyle = "#15111c"; g.strokeStyle = INK; g.lineWidth = 6;
      g.beginPath(); g.ellipse(80, 84, 62 - (i % 4) * 6, 56, 0.3 * (i % 4), 0, Math.PI * 2); g.fill();
      g.fillStyle = "rgba(255,255,255,0.75)"; g.beginPath(); g.ellipse(58, 62, 14, 8, -0.6, 0, Math.PI * 2); g.fill();
    }, x, y: top[1] + Math.max(0, h), z, w: sz, h: sz });
  }
};
/** dollar bills fluttering down */
const money = (out: Stage, t: number, t0: number, c: V3, n = 22) => {
  if (t < t0) return;
  const k = t - t0;
  for (let i = 0; i < n; i++) {
    const d = hh(i, 2) * 0.9, kk = k - d; if (kk < 0) continue;
    const x = c[0] + (hh(i, 3) - 0.5) * 7 + 0.5 * Math.sin(kk * 3 + i), y = c[1] + 6.5 - 2.4 * kk, z = c[2] + (hh(i, 4) - 0.5) * 3;
    if (y < 0.1) continue;
    out.fx.push({ key: `bill${i % 2}`, cw: 260, ch: 130, draw: (pp) => {
      const g = pp.g; g.fillStyle = i % 2 ? "#7fc77a" : "#9bd88f"; g.strokeStyle = "#1f5a2a"; g.lineWidth = 8; g.beginPath(); g.roundRect(6, 6, 248, 118, 10); g.fill(); g.stroke();
      g.strokeStyle = "rgba(31,90,42,.6)"; g.lineWidth = 4; g.strokeRect(22, 20, 216, 90);
      g.fillStyle = "#1f5a2a"; g.beginPath(); g.ellipse(130, 65, 30, 34, 0, 0, Math.PI * 2); g.fill();
      g.fillStyle = "#9bd88f"; g.font = '900 46px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("$", 130, 68);
    }, x, y, z, w: 0.72, h: 0.36 * Math.abs(Math.cos(kk * 4 + i)) + 0.06, rot: 0.6 * Math.sin(kk * 3.3 + i) });
  }
};

const sweat = (out: Stage, t: number, p: V3, size: number) => {
  const k = q((t * 1.5) % 1, 15);
  out.fx.push({ key: `sweat${k}`, cw: 200, ch: 240, draw: (pp) => {
    const g = pp.g; g.fillStyle = "#bfe8ff"; g.strokeStyle = INK; g.lineWidth = 10;
    for (const [x, y] of [[60, 70 + k * 60], [140, 100 + ((k + 0.5) % 1) * 60]]) { g.beginPath(); g.moveTo(x, y - 40); g.quadraticCurveTo(x + 30, y + 10, x, y + 26); g.quadraticCurveTo(x - 30, y + 10, x, y - 40); g.fill(); g.stroke(); }
  }, x: p[0], y: p[1], z: p[2], w: size, h: size * 1.2 });
};
/** a card that just draws a canvas (caution tape, IOUs, tape strip, bill, moth) */
const card = (out: Stage, key: string, cw: number, ch: number, p: V3, w: number, h: number, rot: number, draw: (g: CanvasRenderingContext2D) => void) =>
  out.fx.push({ key, cw, ch, draw: (pp) => { pp.g.lineJoin = "round"; draw(pp.g); }, x: p[0], y: p[1], z: p[2], w, h, rot });
const tape = (g: CanvasRenderingContext2D) => { g.fillStyle = "#f2c94c"; g.fillRect(0, 0, 800, 80); g.fillStyle = INK; for (let x = -80; x < 800; x += 80) { g.beginPath(); g.moveTo(x, 80); g.lineTo(x + 40, 0); g.lineTo(x + 80, 0); g.lineTo(x + 40, 80); g.fill(); } };
const iou = (g: CanvasRenderingContext2D) => { g.fillStyle = "#f4f1ea"; g.strokeStyle = INK; g.lineWidth = 8; g.fillRect(4, 4, 232, 152); g.strokeRect(4, 4, 232, 152); g.fillStyle = "#c0262f"; g.font = '900 70px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("IOU", 120, 70); g.fillStyle = INK; g.font = '700 28px Arial'; g.fillText("$$$,$$$,$$$", 120, 124); };
const bigBill = (g: CanvasRenderingContext2D) => {
  g.fillStyle = "#f4f1ea"; g.strokeStyle = INK; g.lineWidth = 14; g.beginPath(); g.roundRect(8, 8, 784, 464, 20); g.fill(); g.stroke();
  g.fillStyle = "#c0262f"; g.fillRect(8, 8, 784, 110); g.fillStyle = "#ffffff"; g.font = '900 70px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("MARGIN CALL", 400, 66);
  g.fillStyle = INK; g.font = '900 96px "Arial Black", Arial'; g.fillText("$100,000,000+", 400, 250);
  g.fillStyle = "#c0262f"; g.font = '900 80px "Arial Black", Arial'; g.fillText("DUE TODAY", 400, 380);
};
const moth = (g: CanvasRenderingContext2D) => { g.fillStyle = "#c9b79a"; g.strokeStyle = INK; g.lineWidth = 6; for (const s of [-1, 1]) { g.beginPath(); g.ellipse(64 + s * 30, 56, 30, 22, s * 0.5, 0, 7); g.fill(); g.stroke(); } g.fillStyle = "#5a4630"; g.beginPath(); g.ellipse(64, 64, 8, 22, 0, 0, 7); g.fill(); };

// ---------------- staging per shot ----------------
export const stage = (id: number, t: number, s0: number, light: Light, cam: CamInfo): Stage => {
  const out: Stage = { places: [], fx: [] };
  const c: Ctx = { out, cam, t, s0, light };
  const P = (who: Who, p: V3, a?: Act) => person(c, who, p, a);
  switch (id) {
    case 1: case 2: { // on top of the silver: Bunker hoists a bar, Herbert pumps a fist
      const hop = id === 2 ? Math.max(0, Math.sin((t - 2.3) * 9)) * (t > 2.3 && t < 2.65 ? 1 : 0) : 0;
      P({ id: "BUNKER" }, BUNKER, { expr: "grin", look: 0.35, armR: id === 1 ? UP : keys(t, [[1.9, UP], [2.6, UP], [2.9, SHOWHI]]), armL: id === 1 ? WIDE : keys(t, [[1.9, WIDE], [2.7, HIP]]),
        hold: { side: 1, img: barCv(), w: 0.62, h: 0.31, rot: -0.15, dx: 0, dy: -0.1, key: "bar" }, bounce: hop * 3 });
      P({ id: "HERBERT" }, HERBERT, { expr: id === 1 ? "laugh" : "grin", look: -0.45, armR: pump(t, 1), armL: id === 2 ? keys(t, [[1.9, HIP], [2.4, THUMB]]) : HIP });
      for (let i = 0; i < 9; i++) {
        const t0 = 0.15 + i * 0.37, a = i * 2.4, L = 3 + (i * 7) % 14, r = 10.5 * Math.pow(1 - L / 20, 0.85) + 1.6 * (L / 20);
        glint(out, t, t0, [Math.sin(a) * r * 0.9, L * 0.3 + 0.35, Math.abs(Math.cos(a)) * r * 0.9 + 0.3], id === 1 ? 1.2 : 0.7);
      }
      if (id === 2) burst(out, t, 2.88, 0.4, [BUNKER[0] + 0.7, BUNKER[1] + 2.2, BUNKER[2] + 0.4], 1.1, "#ffffff", 10);
      break;
    }
    case 3: { // the exchange: the official on the top step, book up
      P({ id: "OFFICIAL" }, OFFICIAL, { expr: "stern", look: 0, armR: SHOWHI, armL: { x: -0.1, y: 0.0, front: true }, hold: { side: 1, img: book(0), w: 0.85, h: 0.61, rot: 0.04, dx: -0.3, dy: -0.15, key: "book" } });
      break;
    }
    case 4: { // rip on "rules": halves fly apart, scraps burst
      const ripped = t >= RIP;
      P({ id: "OFFICIAL" }, OFFICIAL, { expr: ripped ? "grin" : "stern", look: 0, headTilt: ripped ? -5 : 0,
        armR: ripped ? keys(t, [[RIP, SHOWHI], [RIP + 0.12, WIDE]], 0.12) : SHOWHI,
        armL: ripped ? keys(t, [[RIP, { x: -0.1, y: 0.0, front: true }], [RIP + 0.12, WIDE]], 0.12) : { x: -0.1, y: 0.0, front: true },
        hold: ripped ? { side: 1, img: book(1), w: 0.45, h: 0.61, rot: -0.3, dx: 0, dy: -0.1, key: "bookR" } : { side: 1, img: book(0), w: 0.85, h: 0.61, rot: 0.04 + 0.05 * Math.sin(t * 30) * (t > RIP - 0.35 ? 1 : 0), dx: -0.3, dy: -0.15, key: "book" } });
      if (ripped) {
        const k = t - RIP, hx = OFFICIAL[0] - 0.9 - 1.6 * k, hy = OFFICIAL[1] + 1.55 + 1.2 * k - 3 * k * k;
        out.fx.push({ key: "bookL", cw: 380, ch: 520, draw: (pp) => { pp.g.drawImage(book(2), 0, 0); }, x: hx, y: hy, z: OFFICIAL[2] + 0.4, w: 0.45, h: 0.62, rot: 0.4 + 5 * k });
        scraps(out, t, RIP, [OFFICIAL[0], OFFICIAL[1] + 1.6, OFFICIAL[2]]);
        burst(out, t, RIP, 0.3, [OFFICIAL[0] + 0.55, OFFICIAL[1] + 1.05, OFFICIAL[2] + 0.5], 0.7, "#fff3b0", 10);
      }
      break;
    }
    case 5: { // the silver slides: brothers panic
      P({ id: "BUNKER" }, BUNKER, { expr: "shock", look: 0.6, armR: FACEP, armL: SHRUG, headTilt: -6 });
      P({ id: "HERBERT" }, HERBERT, { expr: "shock", look: 0.8, armR: UP, armL: UP, bounce: Math.max(0, Math.sin((t - SLIDE) * 10)) * (t - SLIDE < 0.32 ? 2.5 : 0) });
      puff(out, t, SLIDE + 0.05, 0.7, [3.2, 4.0, 3.2], 2.2);
      puff(out, t, SLIDE + 0.2, 0.7, [4.6, 2.4, 4.4], 2.6);
      break;
    }
    case 6: { // ranch gate, golden hour
      P({ id: "BUNKER" }, BUNKER_R, { expr: "smile", look: 0.3, armR: HIP, armL: THUMB });
      P({ id: "HERBERT" }, HERBERT_R, { expr: "grin", look: -0.3, armL: HIP, armR: keys(t, [[6.95, REST], [7.3, { x: 0.9, y: -0.75 }]]) });
      break;
    }
    case 7: { // "Texas oil billionaires": gusher + money rain
      const rich = t > MONEY;
      P({ id: "BUNKER" }, BUNKER_R, { expr: rich ? "laugh" : "grin", look: 0.35, armR: rich ? pump(t, 2) : keys(t, [[8.3, HIP], [GUSH, { x: 0.9, y: -0.6 }]]), armL: rich ? pump(t, 4) : THUMB, bounce: rich ? 0.6 * Math.max(0, Math.sin(t * 8)) : 0 });
      P({ id: "HERBERT" }, HERBERT_R, { expr: rich ? "laugh" : "shock", look: -0.5, armL: rich ? UP : SHRUG, armR: rich ? pump(t, 0, WIDE) : SHRUG });
      gusher(out, t, GUSH, [RANCH[0] - 7.5, 13.6, -8]);
      burst(out, t, GUSH, 0.4, [RANCH[0] - 7.5, 13.8, -7.5], 5, "#2b2433", 14);
      money(out, t, MONEY, [RANCH[0] + 0.2, 0, 9.0]);
      if (rich) pop(out, t, MONEY + 0.1, 10.42, [RANCH[0] - 2.8, 4.6, 8.6], 0.9, "$$$", "#ffffff", "#2f9a52", -0.12);
      break;
    }
    case 8: { // 1970s main street: people strolling
      const [TX, , TZ] = TOWN;
      for (let i = 0; i < 4; i++) {
        const dir = i % 2 ? -1 : 1, x = TX - 6 + i * 3.4 + dir * 0.9 * (t - 10.42), z = TZ + 7.2 + (i % 2) * 1.6;
        P({ id: "F", o: FOLKS[i], seed: i + 2, i: 50 + i }, [x, 0.15, z], { mode: "stroll", phase: (t - 10.42) * 1.7 + i, facing: dir as -1 | 1, expr: "smile", look: 0.4 * dir });
      }
      break;
    }
    case 9: { // inflation: prices climb, the bill in her hand shrinks
      const [TX, , TZ] = TOWN, k = Math.min(1, Math.max(0, (t - 12.5) / 1.6));
      P({ id: "SHOPPER" }, [TX - 17.2, 0.15, TZ + 7.6], { expr: t > 13.0 ? "shock" : "neutral", look: -0.7, facing: -1, armR: SHOWHI, hold: HOLD.bill(0.55 * (1 - 0.6 * k)), armL: t > 13.0 ? FACEP : REST });
      pop(out, t, 13.0, 14.4, [TX - 20.2, 3.75, TZ + 10.4], 0.75, "INFLATION!", "#ffffff", "#e2453c", -0.06);
      break;
    }
    case 10: { // "Gold? Banned for Americans."
      const X = OFFICE;
      P({ id: "BUNKER" }, [X - 0.85, 0, -3.1], { expr: t > 15.2 ? "shock" : "smile", look: 0.4, armR: t > 15.2 ? FACEP : HIP, blob: false });
      P({ id: "HERBERT" }, [X + 0.85, 0, -2.95], { expr: t > 15.2 ? "nervous" : "grin", look: -0.6, armL: keys(t, [[14.4, REST], [14.6, { x: 0.95, y: 0.55 }]]), blob: false });
      if (t > 15.18) {
        const u = Math.min(1, (t - 15.18) / 0.12);
        for (const sgn of [-1, 1]) card(out, "tapeX", 800, 80, [X - 0.4, 1.12, -1.6], 0.95 * u, 0.1, sgn * 0.45, tape);
        pop(out, t, 15.25, 16.55, [X - 0.35, 1.75, -1.6], 0.32, "BANNED", "#ffffff", "#c0262f", -0.12);
      }
      break;
    }
    case 11: case 12: { // carts of silver rolling out of the exchange
      for (let i = 0; i < (id === 12 ? 10 : 2); i++) {
        const c = cartPath(i, t, id); if (!c) continue;
        const pz = c[2] - 0.95, ph = (t - 16.55) * 1.9 + i;
        if (i === 0) P({ id: "BUNKER" }, [c[0], 0.08, pz], { mode: "stroll", phase: ph, expr: "grin", look: 0.3, armR: { x: 0.35, y: 0.55, front: true }, armL: { x: 0.35, y: 0.55, front: true } });
        else if (i === 1) P({ id: "HERBERT" }, [c[0], 0.08, pz], { mode: "stroll", phase: ph, expr: id === 12 ? "laugh" : "grin", look: -0.3, armR: { x: 0.35, y: 0.55, front: true }, armL: { x: 0.35, y: 0.55, front: true } });
        else P({ id: "F", o: FOLKS[(i - 2) % FOLKS.length], seed: i, i: 60 + i }, [c[0], 0.08, pz], { mode: "stroll", phase: ph, expr: "smile", look: 0, armR: { x: 0.35, y: 0.55, front: true }, armL: { x: 0.35, y: 0.55, front: true } });
      }
      if (id === 12) pop(out, t, 19.3, 20.6, [EXCH[0] + 3.2, 4.2, 12], 1.0, "NOT A LITTLE", "#241726", "#fff36b", 0.06);
      break;
    }
    case 13: { const pp = planeAt(t); pop(out, t, 21.1, 22.75, [pp[0] + 4, pp[1] + 12, pp[2] + 4], 5.0, "SWITZERLAND", "#ffffff", "#d8323c", -0.05); break; }
    case 14: { // spinning the globe
      const X = OFFICE;
      P({ id: "BUNKER" }, [X + 2.25, 0, -3.9], { expr: "grin", look: 0.6, armR: { x: 0.95, y: 0.05 + 0.08 * Math.sin(t * 9) }, armL: HIP, blob: false });
      P({ id: "HERBERT" }, [X + 4.95, 0, -3.95], { expr: "grin", look: -0.6, armL: { x: 0.9, y: 0.1 }, armR: HIP, blob: false });
      break;
    }
    case 15: pop(out, t, 26.0, 27.45, [OFFICE + 4.15, 2.95, -3.6], 0.42, "1/3 OF ALL SILVER", "#241726", "#e8edf5", 0.06); break;
    case 16: case 24: case 25: { // trading floor crowd
      const X = FLOOR, spots: V3[] = [[X - 6, 0, -2.7], [X - 1.5, 0, -2.6], [X + 3.2, 0, -2.8], [X + 7, 0, -2.6], [X - 3.8, 0, -6.9], [X + 1, 0, -6.8], [X + 5.5, 0, -7.0]];
      spots.forEach((p, i) => {
        const cheer = id === 16 && t > 29.2, panic = id === 25 || (id === 24 && t > 49.9);
        P({ id: "T", o: TRADERS[i], seed: i + 3, i: 70 + i }, p, {
          expr: cheer ? (i % 2 ? "laugh" : "grin") : panic ? (i % 3 ? "shock" : "nervous") : "neutral", look: 0.3 * Math.sin(i * 2), headTilt: panic ? 6 * Math.sin(t * 7 + i) : -4,
          armR: cheer ? pump(t, i) : panic ? (i % 2 ? FACEP : UP) : REST, armL: cheer ? (i % 2 ? UP : HIP) : panic ? (i % 2 ? SHRUG : FACEP) : REST, bounce: cheer ? Math.max(0, Math.sin(t * 9 + i)) * 1.5 : 0 });
      });
      if (id === 25) { scraps(out, t, 51.0, [X - 3, 2.2, -4]); scraps(out, t, 51.5, [X + 2.5, 2.4, -5]); scraps(out, t, 52.0, [X - 0.5, 2.0, -3]); }
      break;
    }
    case 17: { // queue at "WE BUY SILVER"
      const [TX, , TZ] = TOWN, items = [HOLD.forks(), HOLD.candle(), HOLD.trophy(), HOLD.teapot(), HOLD.forks()];
      const who: [Outfit, string][] = [[GRANNY, "GRANNY"], [FOLKS[0], "F0"], [FOLKS[2], "F2"], [FOLKS[3], "F3"], [FOLKS[4], "F4"]];
      who.forEach(([o, nm], i) => P({ id: i ? "F" : "GRANNY", o, seed: i + 4, i: 80 + i }, [TX + 3.3 + i * 1.55, 0.15, TZ + 7.9 - 0.12 * i], {
        expr: i === 0 ? "grin" : i === 2 ? "smile" : "neutral", look: -0.5, facing: -1, armR: SHOWHI, hold: items[i], armL: i === 0 ? keys(t, [[31.25, REST], [32.4, REST], [32.7, UP]]) : REST }));
      if (t > 32.7) pop(out, t, 32.75, 34.45, [TOWN[0] + 3.0, 3.3, TOWN[2] + 7.6], 0.5, "CASH!", "#241726", "#5cf5a6", 0.08);
      break;
    }
    case 18: { // "up billions on paper"
      const X = OFFICE;
      P({ id: "BUNKER" }, [X - 0.85, 0, -3.1], { expr: "laugh", look: 0.3, armR: SHOWHI, hold: HOLD.profit(), armL: pump(t, 1), blob: false });
      P({ id: "HERBERT" }, [X + 0.85, 0, -2.95], { expr: "laugh", look: -0.4, armL: UP, armR: pump(t, 3), blob: false, bounce: Math.max(0, Math.sin(t * 8)) });
      // adding-machine tape spilling up off the desk
      const L = Math.min(1.8, (t - 34.6) * 0.9);
      if (L > 0) card(out, "tape" + Math.round(L * 10), 120, 600, [X + 1.6, 0.97 + L / 2, -1.7], 0.14, L, 0.15 * Math.sin(t * 2), (g) => {
        g.fillStyle = "#f4f1ea"; g.fillRect(10, 0, 100, 600); g.strokeStyle = "#241726"; g.lineWidth = 5; g.strokeRect(10, 0, 100, 600);
        g.fillStyle = "#2f7a3a"; g.font = '700 30px "Courier New", monospace'; for (let y = 30; y < 600; y += 40) g.fillText("+" + ((y * 37) % 900 + 100), 20, y);
      });
      pop(out, t, 35.3, 37.45, [X, 2.5, -2.0], 0.5, "+$ BILLIONS", "#ffffff", "#2f9a52", -0.06);
      break;
    }
    case 19: { // the official stamps the new rule
      const X = FLOOR, slam = 38.6;
      P({ id: "OFFICIAL" }, [X, 0.75, -13.1], { expr: t > slam ? "grin" : "stern", look: 0, armR: keys(t, [[37.45, SHOWHI], [38.25, UP], [slam, { x: 0.1, y: 0.62, front: true }]], 0.2), hold: HOLD.stamp(), armL: HIP, blob: false });
      if (t > slam) { burst(out, t, slam, 0.35, [X + 0.1, 1.25, -12.2], 0.9, "#fff3b0", 10); pop(out, t, slam + 0.05, 40.0, [X + 0.45, 2.95, -12.0], 0.5, "NEW RULE", "#ffffff", "#c0262f", -0.1); }
      break;
    }
    case 21: { // only SELL works
      const X = FLOOR;
      P({ id: "T", o: TRADERS[2], seed: 5, i: 72 }, [X + 4.5, 0, 0.15], { expr: "shock", look: 0, armR: { x: -0.05, y: 0.55 + 0.12 * Math.abs(Math.sin(t * 9)), front: true }, armL: FACEP, blob: false });
      P({ id: "T", o: TRADERS[4], seed: 7, i: 74 }, [X + 1.8, 0, -2.6], { expr: "nervous", look: 0.5, armL: UP, armR: FACEP });
      pop(out, t, 43.0, 45.0, [X + 5.6, 2.25, 0.6], 0.32, "SELL! SELL!", "#ffffff", "#c0262f", 0.08);
      break;
    }
    case 22: { // "the Hunts borrowed big"
      const X = OFFICE;
      P({ id: "BUNKER" }, [X - 0.7, 0, -3.1], { expr: "nervous", look: 0.3, armR: { x: -0.32, y: 0.2, front: true }, armL: HIP, blob: false });
      P({ id: "HERBERT" }, [X + 0.85, 0, -2.95], { expr: "nervous", look: -0.5, armL: FACEP, blob: false });
      sweat(out, t, [X + 1.35, 2.35, -2.8], 0.3); sweat(out, t + 0.4, [X - 0.2, 2.35, -2.9], 0.3);
      for (let i = 0; i < 7; i++) { const t0 = 45.2 + i * 0.18; if (t < t0) continue; const u = Math.min(1, (t - t0) / 0.5);
        card(out, "iou", 240, 160, [X - 1.0 + i * 0.32, 2.4 - 1.35 * u * u, -1.75 + 0.02 * i], 0.36, 0.24 * (0.4 + 0.6 * u), (1 - u) * 2 + (i % 3 - 1) * 0.2, iou); }
      pop(out, t, 45.7, 47.25, [X + 0.1, 2.55, -2.1], 0.4, "BORROWED", "#ffffff", "#c0262f", 0.06);
      break;
    }
    case 23: if (t > 47.95) { puff(out, t, 47.95, 0.6, [FLOOR - 10, 4.6, -15.6], 2.4); burst(out, t, 47.95, 0.35, [FLOOR - 10, 4.6, -15.7], 2.6, "#fff3b0", 12); } break;
    case 26: { // the margin call
      const X = OFFICE, pick = t >= 54.0;
      P({ id: "BUNKER" }, [X - 0.25, 0, -3.05], { expr: t > 55.0 ? "shock" : pick ? "neutral" : "smile", look: 0.4, armR: pick ? keys(t, [[54.0, { x: 0.6, y: 0.5 }], [54.3, { x: -0.06, y: -0.28, front: true }]]) : { x: 0.6, y: 0.6 }, hold: pick ? HOLD.handset() : undefined, armL: t > 55.0 ? FACEP : HIP, blob: false });
      P({ id: "HERBERT" }, [X + 1.35, 0, -2.9], { expr: t > 55.0 ? "nervous" : "neutral", look: -0.7, armL: CROSSA, armR: CROSSA, blob: false });
      if (t > 55.1) { const u = Math.min(1, (t - 55.1) / 0.18), sc2 = 0.3 + 0.7 * u + 0.04 * Math.sin((t - 55.1) * 12) * Math.exp(-(t - 55.1) * 3);
        card(out, "marginBill", 800, 480, [X + 0.25, 2.5, -1.5], 1.5 * sc2, 0.9 * sc2, -0.06, bigBill); }
      break;
    }
    case 27: { // they can't pay
      const X = OFFICE;
      P({ id: "BUNKER" }, [X - 0.55, 0, -3.0], { expr: "dazed", look: 0.2, armR: SHOWHI, hold: HOLD.wallet(), armL: SHRUG, blob: false });
      P({ id: "HERBERT" }, [X + 0.7, 0, -2.9], { expr: "dazed", look: -0.3, armL: SHRUG, armR: SHRUG, blob: false });
      const u = Math.max(0, t - 57.6); if (u > 0) card(out, "moth", 128, 128, [X - 0.6 + 0.4 * u, 1.55 + 0.7 * u + 0.08 * Math.sin(t * 20), -2.4], 0.2, 0.16 * (0.6 + 0.4 * Math.abs(Math.sin(t * 22))), 0.2 * Math.sin(t * 9), moth);
      break;
    }
    case 28: { // bankers rush in with bags of money
      for (let i = 0; i < 4; i++) {
        const z = 19.5 - 2.6 * (t - 58.95) - (i % 2) * 1.2, x = EXCH[0] - 3 + i * 2;
        P({ id: "B", o: BANKER, seed: i + 2, i: 90 + i }, [x, 0.08, Math.max(9.8, z)], { mode: "stroll", phase: (t - 58.95) * 2.6 + i, expr: "nervous", look: 0.2 * (i - 1.5), armR: SHOWHI, hold: HOLD.bag(i), armL: UP });
      }
      pop(out, t, 60.3, 62.85, [EXCH[0], 6.6, 8], 1.25, "$1.1 BILLION LOAN", "#ffffff", "#2f9a52", -0.05);
      break;
    }
    case 29: case 30: { // the jury
      const X = COURT, verdict = id === 29 && t > 64.2;
      P({ id: "JUDGE" }, [X, 0.5, -7.95], { expr: "stern", look: 0.3, blob: false, armL: REST });
      for (let i = 0; i < 6; i++) {
        const front = i < 3, stand = verdict && i === 1;
        P({ id: "J", o: FOLKS[(i + 1) % FOLKS.length], seed: i + 8, i: 100 + i }, [X + 3.25 + (i % 3) * 1.05, front ? 0.3 : 0.6, front ? -2.3 : -3.55], {
          expr: stand ? "stern" : "neutral", mode: stand ? "stand" : "sit", look: -0.5, blob: false, armR: stand ? SHOWHI : undefined, hold: stand ? HOLD.verdict() : undefined });
      }
      const bad = id === 30 || t > 64.6;
      P({ id: "BUNKER" }, [X - 3.75, 0, -2.0], { expr: bad ? (id === 30 ? "dazed" : "shock") : "nervous", look: 0.6, armR: id === 30 ? SHRUG : REST, armL: id === 30 ? FACEP : REST, blob: false });
      P({ id: "HERBERT" }, [X - 2.2, 0, -2.0], { expr: bad ? "shock" : "nervous", look: 0.7, armL: id === 30 ? UP : REST, armR: id === 30 ? UP : REST, blob: false });
      if (id === 30) { burst(out, t, 66.2, 0.4, [X - 3.0, 1.8, -1.2], 2.0, "#ffd0d0", 12); pop(out, t, 66.25, 66.95, [X - 3.0, 1.85, -1.1], 0.62, "BANKRUPT", "#ffffff", "#c0262f", -0.14); }
      break;
    }
    case 31: { // banned from trading
      P({ id: "GUARD" }, [EXCH[0], EX_STEP_Y, 5.2], { expr: "stern", look: 0, armR: { x: 0.05, y: -0.35, front: true }, armL: HIP });
      P({ id: "BUNKER" }, [EXCH[0] - 0.95, 0.08, 11.2], { expr: "nervous", look: 0.3, armR: SHRUG, armL: REST });
      P({ id: "HERBERT" }, [EXCH[0] + 0.95, 0.08, 11.0], { expr: "dazed", look: -0.3, armL: SHRUG, armR: REST });
      pop(out, t, 67.3, 68.65, [EXCH[0], 4.6, 6.5], 1.0, "BANNED", "#ffffff", "#c0262f", -0.08);
      break;
    }
    case 32: { // "A billion dollars isn't what it used to be."
      P({ id: "BUNKER" }, [VAULT, 0, -3.3], { expr: t > 71.2 ? "smile" : "smile_closed", look: 0, armR: SHOWHI, hold: HOLD.coin(), armL: t > 71.2 ? SHRUG : HIP });
      glint(out, t, 69.0, [VAULT - 0.15, 1.95, -2.9], 0.5); glint(out, t, 70.6, [VAULT - 0.15, 1.95, -2.9], 0.4);
      break;
    }
    case 33: { // "So... cheaters?"
      P({ id: "BUNKER" }, BUNKER, { expr: "nervous", look: 0.9, armR: { x: -0.3, y: 0.2, front: true }, armL: HIP });
      P({ id: "HERBERT" }, HERBERT, { expr: "whistle", look: -0.9, armL: CROSSA, armR: CROSSA });
      pop(out, t, 72.5, 73.6, [0.0, 8.25, 0.8], 0.4, "CHEATERS?", "#ffffff", "#c0262f", -0.08);
      break;
    }
    case 34: { // "...or did Wall Street change the rules?"
      P({ id: "OFFICIAL" }, OFFICIAL, { expr: "grin", look: 0, headTilt: -6, armR: SHOWHI, hold: { side: 1, img: book(1), w: 0.45, h: 0.61, rot: -0.3, dx: 0, dy: -0.1, key: "bookR" }, armL: HIP });
      pop(out, t, 74.3, 76.95, [OFFICIAL[0] + 0.15, EX_STEP_Y + 2.15, 4.6], 0.34, "RIGGED?", "#ffffff", "#1d3f8a", 0.08);
      break;
    }
    case 35: { // comment below
      P({ id: "BUNKER" }, BUNKER, { expr: "grin", look: 0.2, armR: { x: 0.05, y: 0.35, front: true }, armL: HIP });
      P({ id: "HERBERT" }, HERBERT, { expr: "grin", look: -0.2, armL: { x: 0.05, y: 0.35, front: true }, armR: HIP });
      pop(out, t, 77.1, 78.5, [0.05, 8.75, 0.8], 0.5, "YOU DECIDE!", "#241726", "#fff36b", 0.05);
      break;
    }
  }
  return out;
};
