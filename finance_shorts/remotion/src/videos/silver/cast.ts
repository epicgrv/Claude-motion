// Silver cast: flat 2D characters with the v5 rig (2-bone IK arms, breathing, weight shift, nods, calm blinks,
// smooth eyes; mouths only move on lines a character speaks). Props drawn in hands; effects are unlit 2D cards.
import * as THREE from "three";
import { Pen, bodyFront, Outfit, Expr, FrontOpts, INK, fxBurst, fxPuff, fxShadow, fxContact, ArmPose, Hold } from "../pepsi/toon";
import { Place, FxPlace } from "../bridge/cast";
import { LINES, MOUTH, VISEME } from "./vo";
import { FPS, Light, OFFICIAL, BUNKER, HERBERT, BUNKER_R, HERBERT_R, RIP, SLIDE, GUSH, MONEY } from "./story";
import { V3, RANCH } from "./sets";

export type Stage = { places: Place[]; fx: FxPlace[] };

// ---------------- the cast (our own designs) ----------------
const BUNK: Outfit = { jacket: "#8a5a34", pants: "#6a4630", boots: "#3a2618", hat: "cowboy", hatCol: "#f3ede0", band: "#3a2a20", glasses: INK,
  build: "stout", skin: "#f5c9a0", buttons: "#e8c45a", collar: "#ffffff", tie: "#2f2a26" };
const HERB: Outfit = { jacket: "#6f7584", pants: "#4a4e5a", boots: "#3a2618", hat: "cowboy", hatCol: "#c9a26a", band: "#5a3b2a", moustache: "#8a7a6a",
  skin: "#ffe2c2", buttons: "#d9dde0", collar: "#ffffff", tie: "#8c2f35" };
const SUIT: Outfit = { jacket: "#1f2a44", pants: "#1f2a44", boots: INK, hat: "hair", hair: "#2a201a", skin: "#ecd0b6", collar: "#ffffff", tie: "#d8323c", buttons: "#c9ccd2" };
const OUT: Record<string, Outfit> = { BUNKER: BUNK, HERBERT: HERB, OFFICIAL: SUIT };
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
  }
  return out;
};
