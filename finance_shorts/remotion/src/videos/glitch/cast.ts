// Glitch cast on the v5 rig: Dan (casual customer look), the bartender, friends, strangers, a sleeping guard, a police
// officer. Hands stay beside the body or out to the side (never behind or over a face). No floor-shadow cards.
// Money: detailed bills that fall like real paper (sway + tilt + 3D flip), or burst out from behind the phone.
import * as THREE from "three";
import { Pen, bodyFront, Outfit, Expr, FrontOpts, INK, ArmPose, Hold } from "../pepsi/toon";
import { Place, FxPlace } from "../bridge/cast";
import { LINES, MOUTH, VISEME } from "./vo";
import { FPS, Light, DAN_CUST, DAN_WORK, BARTENDER, RAIN_T, TAP_T, TAPS } from "./story";
import { V3, RUNWAY, STREET, PHONE, SERVER, BEDROOM, POLICE, HOTEL_X, COPS_X } from "./sets";
import { balanceAt } from "./screens";

export type Stage = { places: Place[]; fx: FxPlace[] };
const DAN: Outfit = { jacket: "#3f6fb5", pants: "#2b2b34", boots: "#f4f1ea", hat: "hair", hair: "#5a3b2a", skin: "#f5c9a0", collar: "#f4f1ea", buttons: "#c9d3e6", moustache: "#6a4a30" };
const BARMAN: Outfit = { jacket: "#1f1f26", pants: "#1f1f26", boots: INK, hat: "hair", hair: "#c9c9d1", skin: "#ecd0b6", collar: "#ffffff", tie: "#c0262f", buttons: "#d9d2c2", moustache: "#c9c9d1", build: "stout" };
const GUARD: Outfit = { jacket: "#2b3448", pants: "#2b3448", boots: INK, hat: "cap", cap: "#2b3448", skin: "#c99067", buttons: "#e8c45a", build: "stout", moustache: "#3a2a20" };
const COP: Outfit = { jacket: "#1d3f8a", pants: "#1d3f8a", boots: INK, hat: "cap", cap: "#14213f", skin: "#ecd0b6", buttons: "#e8c45a", collar: "#c9d3e6", tie: "#14213f" };
const DOORMAN: Outfit = { jacket: "#9c2b35", pants: "#241726", boots: INK, hat: "cap", cap: "#9c2b35", skin: "#f5c9a0", buttons: "#e8c45a" };
const FOLK: Outfit[] = [
  { jacket: "#e8b33a", pants: "#3b3f52", boots: "#f4f1ea", hat: "hair", hair: "#2a201a", skin: "#c99067" },
  { jacket: "#3fae8a", pants: "#3b3f52", boots: "#f4f1ea", hat: "hair", hair: "#e8c45a", dress: "#3fae8a", skin: "#ffe2c2" },
  { jacket: "#7b5ac9", pants: "#2f3550", boots: "#3a2618", hat: "cap", cap: "#e2453c", skin: "#ecd0b6" },
  { jacket: "#e2453c", pants: "#56607a", boots: "#f4f1ea", hat: "hair", hair: "#8a5a3c", dress: "#e2453c", skin: "#f5c9a0" },
  { jacket: "#3f7fd0", pants: "#2b2b34", boots: INK, hat: "hair", hair: "#5a3b2a", skin: "#ffe2c2", glasses: INK },
];

// ---------------- life ----------------
const hh = (i: number, s = 0) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };
const noise = (x: number, s: number) => { const i = Math.floor(x), f = x - i, w = f * f * (3 - 2 * f); return (hh(i, s) * (1 - w) + hh(i + 1, s) * w) * 2 - 1; };
const lidAt = (t: number, i: number, s0: number) => {
  const f = Math.round(t * FPS); if (f - Math.round(s0 * FPS) < 6) return 0;
  let s = Math.round(-90 * hh(i, 9));
  for (let n = 0; s <= f && n < 400; n++) { const k = f - s; if (k >= 0 && k < 3) return [0.5, 1, 0.5][k]; s += Math.round(75 + 90 * hh(i * 31 + n, 13)); }
  return 0;
};
const lineAt = (t: number) => LINES.find((l) => t >= l.s - 0.04 && t <= l.e + 0.04);
const visOf = (t: number) => { const f = Math.round(t * FPS); return f >= 0 && f < VISEME.length ? Number(VISEME[f]) : 0; };
const mouthOf = (who: string, t: number) => { const l = lineAt(t); if (!l || l.who !== who) return 0; const f = Math.round(t * FPS); return f >= 0 && f < MOUTH.length ? Number(MOUTH[f]) / 4 : 0; };

type AP = ArmPose;
const REST: AP = { x: 0.16, y: 1.02 }, HIP: AP = { x: 0.5, y: 0.7 }, WIDE: AP = { x: 1.1, y: -0.3 }, CHEER: AP = { x: 1.05, y: -0.45 };
const SIDE: AP = { x: 0.95, y: 0.2 }, SHRUG: AP = { x: 0.85, y: 0.1 }, LOW: AP = { x: 0.1, y: 0.62, front: true }, EAR: AP = { x: 0.66, y: -0.38 };
const sm = (x: number) => { const u = Math.min(1, Math.max(0, x)); return u * u * (3 - 2 * u); };
const lerpA = (a: AP, b: AP, k: number): AP => ({ x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k, front: k < 0.5 ? a.front : b.front });
const keys = (t: number, k: [number, AP][], dur = 0.25): AP => { if (t <= k[0][0]) return k[0][1]; for (let i = 0; i + 1 < k.length; i++) { const [t1, b] = k[i + 1]; if (t < t1) return lerpA(k[i][1], b, sm((t - (t1 - dur)) / dur)); } return k[k.length - 1][1]; };
const breathe = (a: AP, t: number, s: number): AP => ({ ...a, x: a.x + 0.012 * Math.sin(t * 1.7 + s), y: a.y + 0.02 * Math.sin(t * 1.9 + s) });
/** cheering: arm out to the side, pumping at head height (never above / behind the head) */
const cheer = (t: number, s: number): AP => ({ x: CHEER.x + 0.05 * Math.sin(t * 8 + s), y: CHEER.y + 0.16 * Math.sin(t * 8 + s) });

// ---------------- props (drawn once, cached) ----------------
const cvCache = new Map<string, HTMLCanvasElement>();
const cvs = (key: string, w: number, h: number, draw: (g: CanvasRenderingContext2D) => void) => { let c = cvCache.get(key); if (c) return c; c = document.createElement("canvas"); c.width = w; c.height = h; const g = c.getContext("2d")!; g.lineJoin = "round"; g.strokeStyle = INK; g.lineWidth = 10; draw(g); cvCache.set(key, c); return c; };
const hold = (key: string, w: number, h: number, ww: number, rot: number, dx: number, dy: number, draw: (g: CanvasRenderingContext2D) => void): Hold => ({ side: 1, img: cvs(key, w, h, draw), w: ww, h: (ww * h) / w, rot, dx, dy, key, bare: true });
const phoneImg = (bal: number) => (g: CanvasRenderingContext2D) => {
  g.fillStyle = "#14101a"; g.beginPath(); g.roundRect(6, 6, 188, 388, 26); g.fill(); g.stroke();
  g.fillStyle = "#14213f"; g.beginPath(); g.roundRect(18, 22, 164, 356, 16); g.fill();
  g.fillStyle = "#e8c45a"; g.font = '900 20px "Arial Black", Arial'; g.textAlign = "center"; g.fillText("GOLDLEAF", 100, 70);
  g.fillStyle = "#5cf5a6"; g.font = '900 24px "Arial Black", Arial'; g.fillText("$" + Math.round(bal).toLocaleString("en-US"), 100, 170);
};
const phoneHold = (bal: number, ww = 0.42, rot = -0.1): Hold => hold("ph" + Math.round(bal), 200, 400, ww, rot, 0.06, -0.3, phoneImg(bal));
const HOLDS = {
  champ: () => hold("champ", 120, 300, 0.32, 0.15, 0, -0.3, (g) => { g.fillStyle = "#2f6a4a"; g.beginPath(); g.moveTo(45, 290); g.lineTo(75, 290); g.lineTo(80, 120); g.lineTo(68, 80); g.lineTo(68, 20); g.lineTo(52, 20); g.lineTo(52, 80); g.lineTo(40, 120); g.closePath(); g.fill(); g.stroke(); g.fillStyle = "#e8c45a"; g.fillRect(50, 14, 20, 40); g.fillStyle = "#f4f1ea"; g.fillRect(44, 170, 32, 50); }),
  glass: () => hold("glassRag", 260, 260, 0.42, 0, -0.05, -0.15, (g) => { g.fillStyle = "rgba(220,240,255,.85)"; g.beginPath(); g.moveTo(70, 40); g.lineTo(190, 40); g.lineTo(175, 230); g.lineTo(85, 230); g.closePath(); g.fill(); g.stroke(); g.fillStyle = "#f4f1ea"; g.beginPath(); g.moveTo(40, 120); g.quadraticCurveTo(130, 90, 220, 140); g.lineTo(210, 190); g.quadraticCurveTo(130, 150, 50, 180); g.closePath(); g.fill(); g.stroke(); }),
  drink: () => hold("drink", 160, 220, 0.3, 0, 0, -0.15, (g) => { g.fillStyle = "rgba(220,240,255,.7)"; g.beginPath(); g.moveTo(25, 30); g.lineTo(135, 30); g.lineTo(125, 200); g.lineTo(35, 200); g.closePath(); g.fill(); g.stroke(); g.fillStyle = "#c9893a"; g.fillRect(36, 110, 88, 86); g.fillStyle = "rgba(255,255,255,.6)"; g.fillRect(48, 120, 18, 60); }),
  cash: () => hold("cashStack", 300, 200, 0.55, -0.1, 0, -0.2, (g) => { for (let k = 0; k < 4; k++) { g.save(); g.translate(150, 100); g.rotate(-0.25 + k * 0.17); billDraw(g, -130, -55, 260, 110, k); g.restore(); } }),
};

// ---------------- money ----------------
/** a detailed bill (made-up design: green, ornate border, portrait oval, 100 corners) */
const billDraw = (g: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, v = 0) => {
  const gr = g.createLinearGradient(x, y, x + w, y + h); gr.addColorStop(0, v % 2 ? "#bfe3b0" : "#cfe9bf"); gr.addColorStop(1, "#8fc98a");
  g.fillStyle = gr; g.strokeStyle = "#1f5a2a"; g.lineWidth = Math.max(3, h * 0.05); g.beginPath(); g.roundRect(x, y, w, h, h * 0.08); g.fill(); g.stroke();
  g.strokeStyle = "rgba(31,90,42,.7)"; g.lineWidth = Math.max(2, h * 0.025); g.strokeRect(x + w * 0.05, y + h * 0.1, w * 0.9, h * 0.8);
  g.fillStyle = "#e9f5e0"; g.beginPath(); g.ellipse(x + w * 0.5, y + h * 0.5, w * 0.13, h * 0.32, 0, 0, Math.PI * 2); g.fill(); g.stroke();
  g.fillStyle = "#2f6a3a"; g.beginPath(); g.arc(x + w * 0.5, y + h * 0.44, h * 0.1, 0, Math.PI * 2); g.fill(); g.beginPath(); g.ellipse(x + w * 0.5, y + h * 0.7, h * 0.16, h * 0.1, 0, Math.PI, 0); g.fill();
  g.fillStyle = "#1f5a2a"; g.font = `900 ${Math.round(h * 0.22)}px "Arial Black", Arial`; g.textAlign = "center"; g.textBaseline = "middle";
  g.fillText("100", x + w * 0.16, y + h * 0.28); g.fillText("100", x + w * 0.84, y + h * 0.72);
  g.font = `900 ${Math.round(h * 0.3)}px "Arial Black", Arial`; g.fillText("$", x + w * 0.84, y + h * 0.3); g.fillText("$", x + w * 0.16, y + h * 0.7);
};
const billCard = (v: number) => (pp: Pen) => billDraw(pp.g, 8, 8, 404, 164, v);
/** falling bills, like real paper: drift down, sway side to side, tilt with the sway and flip slowly */
const rain = (out: Stage, t: number, t0: number, c: V3, spread: number, n = 30, top = 3.0, depth = 1.4) => {
  if (t < t0) return; const k = t - t0;
  for (let i = 0; i < n; i++) {
    const ph = hh(i, 2) * 6.28, life = 2.6 + hh(i, 5) * 1.0, ts = hh(i, 1) * 1.1;
    if (k < ts) continue; const kk = (k - ts) % life;
    const y = c[1] + top - (top + 0.2) * (kk / life); if (y < c[1] + 0.03) continue;
    const sway = Math.sin(kk * 2.6 + ph), x = c[0] + (hh(i, 3) - 0.5) * spread + 0.28 * sway;
    out.fx.push({ key: `bill${i % 2}`, cw: 420, ch: 180, draw: billCard(i), x, y, z: c[2] + (hh(i, 4) - 0.5) * depth,
      w: 0.4 * (0.35 + 0.65 * Math.abs(Math.cos(kk * 1.3 + ph))), h: 0.17, rot: 0.45 * Math.cos(kk * 2.6 + ph) });
  }
};
/** bills bursting out from BEHIND the phone's left and right edges (never over the screen) */
const burst = (out: Stage, t: number, t0: number, scr: V3, n = 16) => {
  if (t < t0) return; const k = t - t0;
  for (let i = 0; i < n; i++) {
    const side = i % 2 ? 1 : -1, kk = (k + hh(i, 1) * 1.2) % 1.2, up = 0.08 + 0.2 * hh(i, 2);
    const x = scr[0] + side * (0.13 + 0.25 * kk), y = scr[1] - 0.12 + hh(i, 3) * 0.24 + up * kk - 0.15 * kk * kk;
    out.fx.push({ key: `bill${i % 2}`, cw: 420, ch: 180, draw: billCard(i), x, y, z: scr[2] - 0.02 + 0.25 * kk,
      w: 0.09 * (0.4 + 0.6 * Math.abs(Math.cos(kk * 5 + i))), h: 0.038, rot: side * (0.3 + kk * 2) });
  }
};
/** cartoon hand with a pointing finger; tip at p */
const finger = (out: Stage, p: V3, s: number) => out.fx.push({ key: "finger", cw: 200, ch: 400, x: p[0], y: p[1] - 0.075 * s, z: p[2], w: 0.075 * s, h: 0.15 * s, draw: (pp) => {
  const g = pp.g; g.lineJoin = "round"; g.strokeStyle = INK; g.lineWidth = 9; g.fillStyle = "#f5c9a0";
  g.beginPath(); g.roundRect(78, 10, 44, 170, 22); g.fill(); g.stroke();                       // index finger
  g.beginPath(); g.roundRect(30, 160, 140, 150, 50); g.fill(); g.stroke();                       // fist
  for (const x of [56, 92, 128]) { g.beginPath(); g.moveTo(x, 190); g.lineTo(x, 230); g.stroke(); }
  g.fillStyle = "#3f6fb5"; g.fillRect(40, 300, 120, 100); g.strokeRect(40, 300, 120, 100);       // denim sleeve
  g.fillStyle = "rgba(255,255,255,.7)"; g.beginPath(); g.ellipse(100, 30, 10, 6, 0, 0, 7); g.fill();
} });
const zzz = (out: Stage, t: number, p: V3) => { for (let i = 0; i < 3; i++) { const k = (t * 0.6 + i / 3) % 1; out.fx.push({ key: "z", cw: 160, ch: 160, x: p[0] + 0.25 * k + 0.1 * i, y: p[1] + 0.7 * k, z: p[2], w: 0.22 + 0.15 * k, h: 0.22 + 0.15 * k, rot: 0.2, draw: (pp) => { const g = pp.g; g.font = '900 130px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.lineWidth = 12; g.strokeStyle = INK; g.strokeText("Z", 80, 86); g.fillStyle = "#cfe6ff"; g.fillText("Z", 80, 86); } }); } };
const sweat = (out: Stage, t: number, p: V3) => { const k = Math.round(((t * 1.5) % 1) * 15) / 15; out.fx.push({ key: `sw${k}`, cw: 200, ch: 240, x: p[0], y: p[1], z: p[2], w: 0.22, h: 0.26, draw: (pp) => { const g = pp.g; g.fillStyle = "#bfe8ff"; g.strokeStyle = INK; g.lineWidth = 9; for (const [x, y] of [[60, 70 + k * 60], [140, 100 + ((k + 0.5) % 1) * 60]]) { g.beginPath(); g.moveTo(x, y - 40); g.quadraticCurveTo(x + 30, y + 10, x, y + 26); g.quadraticCurveTo(x - 30, y + 10, x, y - 40); g.fill(); g.stroke(); } } }); };

// ---------------- staging helpers ----------------
const q = (v: number, n = 160) => Math.round(v * n) / n;
const fkey = (o: object) => JSON.stringify(o, (_k, v) => (typeof v === "number" ? q(v) : v && typeof v === "object" && "img" in v ? { ...v, img: undefined } : v));
const tier = (d: number): [number, number, number] => (d < 3.0 ? [1200, 2000, 2.0] : d < 6.5 ? [900, 1500, 1.5] : d < 16 ? [480, 800, 0.8] : [240, 400, 0.4]);
export type CamInfo = { pos: THREE.Vector3; right: THREE.Vector3; sun: THREE.Vector3 };
const light2D = (cam: CamInfo) => Math.round(Math.atan2(-cam.sun.y, cam.sun.dot(cam.right)) / (Math.PI / 4)) * (Math.PI / 4);
const tmp = new THREE.Vector3();
type Act = { expr?: Expr; mode?: FrontOpts["mode"]; look?: number; facing?: -1 | 0 | 1; armL?: AP; armR?: AP; hold?: Hold; bounce?: number; headTilt?: number; asleep?: boolean; phase?: number };
type Ctx = { out: Stage; cam: CamInfo; t: number; s0: number; light: Light };
const person = (c: Ctx, id: string, o: Outfit, seed: number, p: V3, a: Act = {}) => {
  const t = c.t, d = c.cam.pos.distanceTo(tmp.set(p[0], p[1] + 1.3, p[2])), [w, h, k] = tier(d);
  const m = mouthOf(id, t);
  const fo: FrontOpts = {
    expr: a.expr ?? "neutral", mode: a.mode ?? "stand", facing: a.facing ?? 0, prop: null, phase: a.phase ?? 0,
    look: (a.look ?? 0) + 0.15 * noise(t * 0.45, seed), tilt: 1.1 * Math.sin(t * 1.35 + seed), headTilt: (a.headTilt ?? 0) + 1.5 * noise(t * 0.6, seed + 5),
    rise: Math.sin(t * 1.9 + seed), mouth: m, viseme: m > 0.08 ? visOf(t) : 0, brow: 0, blink: a.asleep ? 1 : lidAt(t, seed, c.s0), light: light2D(c.cam), seed,
    armL: breathe(a.armL ?? REST, t, seed + 1.3), armR: breathe(a.armR ?? REST, t, seed), hold: a.hold,
  };
  c.out.places.push({ key: `F|${id}|${fkey(fo)}`, x: p[0], y: p[1] + 0.06 * (a.bounce ?? 0), z: p[2], draw: (pp: Pen) => bodyFront(pp, o, fo), size: [w, h, k] });
};
const walk = (t: number, t0: number, t1: number, a: V3, b: V3): V3 => { const u = Math.min(1, Math.max(0, (t - t0) / (t1 - t0))); return [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u]; };

// ---------------- staging per shot ----------------
export const stage = (id: number, t: number, s0: number, light: Light, cam: CamInfo): Stage => {
  const out: Stage = { places: [], fx: [] }, c: Ctx = { out, cam, t, s0, light };
  const P = (nm: string, o: Outfit, seed: number, p: V3, a?: Act) => person(c, nm, o, seed, p, a);
  const [PX, PY, PZ] = PHONE, scr: V3 = [PX, PY + 0.19, PZ];
  const barman = (expr: Expr = "smile", a: Act = {}) => P("BAR", BARMAN, 9, BARTENDER, { expr, look: 0.4, armL: HIP, ...a });
  switch (id) {
    case 1: burst(out, t, 0.7, scr); break;
    case 2:
      P("DAN", DAN, 3, DAN_CUST, { expr: t > 4.6 ? "laugh" : "grin", look: 0.1, armR: SIDE, hold: phoneHold(1_600_000), armL: cheer(t, 1), bounce: Math.max(0, Math.sin(t * 6)) * 0.6 });
      barman("shock", { armR: SHRUG });
      rain(out, t, RAIN_T, [0.1, 0, -1.0], 5.5, 34);
      break;
    case 3: {
      const u = Math.min(1, Math.max(0, (t - (TAP_T - 0.55)) / 0.5)), back = Math.min(1, Math.max(0, (t - (TAP_T + 0.45)) / 0.35));
      const e = u * u * (3 - 2 * u) - back * back, tip: V3 = [PX + 0.03 + 0.12 * (1 - e), scr[1] - 0.036 - 0.22 * (1 - e), PZ + 0.03 + (t > TAP_T && t < TAP_T + 0.12 ? -0.004 : 0)];
      if (e > 0.01) finger(out, tip, 1);
      break;
    }
    case 4: case 25: P("DAN", DAN, 3, [POLICE + 3.2, 0.25, -3.6], { expr: "dazed", look: 0, armL: REST, armR: REST, headTilt: -4 }); break;
    case 5:
      P("DAN", DAN, 3, DAN_WORK, { expr: "neutral", look: 0.2, armR: { x: 0.35, y: 0.22, front: true }, hold: HOLDS.glass(), armL: { x: 0.2, y: 0.25, front: true }, headTilt: 5 });
      barman("smile", { armR: HIP });
      break;
    case 6: P("DAN", DAN, 3, [-1.3, 0, -3.0], { expr: "nervous", look: 0.0, armL: HIP, armR: REST, headTilt: 8 }); break;
    case 8: P("DAN", DAN, 3, DAN_CUST, { expr: "neutral", look: 0.3, armR: SIDE, hold: phoneHold(312.4), armL: { x: 0.25, y: 0.55, front: true }, headTilt: 6 }); barman("neutral", { armR: HIP }); break;
    case 10: {
      const tap = TAPS.some((x) => t > x - 0.05 && t < x + 0.2);
      P("DAN", DAN, 3, DAN_CUST, { expr: t < TAPS[0] ? "shock" : "grin", look: 0.5, armR: tap ? { x: 0.1, y: 0.7, front: true } : LOW, hold: phoneHold(balanceAt(t), 0.4, 0), armL: t > TAPS[1] ? cheer(t, 2) : HIP });
      barman("neutral", { armR: HIP });
      break;
    }
    case 12: P("GUARD", GUARD, 6, [SERVER + 4.35, 0, -3.1], { expr: "relief", asleep: true, look: 0, headTilt: 14, armL: { x: 0.3, y: 0.55, front: true }, armR: { x: 0.3, y: 0.55, front: true } }); zzz(out, t, [SERVER + 4.7, 2.3, -2.9]); break;
    case 13: P("DAN", DAN, 3, DAN_CUST, { expr: "smile", look: 0, armR: SIDE, hold: phoneHold(balanceAt(32)), armL: HIP }); break;
    case 14: P("DAN", DAN, 3, DAN_CUST, { expr: "grin", look: -0.2, armR: EAR, hold: phoneHold(balanceAt(32), 0.34, -0.3), armL: HIP }); barman("neutral", { armR: HIP }); break;
    case 15: {
      P("DAN", DAN, 3, DAN_CUST, { expr: "laugh", look: -0.6, armR: WIDE, armL: WIDE });
      for (let i = 0; i < 3; i++) { const p = walk(t, 40.7, 42.0, [-6.4 + i * 0.3, 0, 0.8 - i * 0.4], [-3.6 + i * 1.1, 0, 0.5 - i * 0.4]); P("F" + i, FOLK[i], 5 + i, p, { expr: "laugh", mode: t < 42 ? "stroll" : "stand", phase: (t - 40.7) * 1.8 + i, look: 0.5, armL: cheer(t, i), armR: SIDE }); }
      break;
    }
    case 16: {
      const [RX] = RUNWAY;
      P("DAN", DAN, 3, [RX + 4.3, 0, -0.5], { expr: "laugh", look: 0.2, armR: SIDE, hold: HOLDS.champ(), armL: cheer(t, 2) });
      P("F0", FOLK[0], 5, [RX + 2.6, 0, -0.8], { expr: "grin", look: 0.4, armL: cheer(t, 3), armR: HIP });
      P("F1", FOLK[1], 7, [RX + 6.0, 0, -0.7], { expr: "laugh", look: -0.4, armR: cheer(t, 1), armL: HIP });
      break;
    }
    case 17:
      P("DAN", DAN, 3, [HOTEL_X - 0.7, 0.17, 1.6], { expr: "grin", look: 0.2, armL: WIDE, armR: SIDE, hold: HOLDS.cash() });
      P("F2", FOLK[2], 8, [HOTEL_X + 0.9, 0.17, 1.4], { expr: "laugh", look: -0.3, armR: cheer(t, 1), armL: HIP });
      P("DOOR", DOORMAN, 11, [HOTEL_X + 2.6, 0.17, -1.6], { expr: "smile", look: -0.6, armL: HIP, armR: { x: 0.9, y: -0.1 } });
      break;
    case 18:
      P("DAN", DAN, 3, [0.4, 0, 0.3], { expr: "laugh", look: 0, armR: SIDE, hold: HOLDS.cash(), armL: cheer(t, 0), bounce: Math.max(0, Math.sin(t * 7)) * 0.7 });
      [-2.6, -1.1, 1.9, 3.4].forEach((x, i) => P("S" + i, FOLK[(i + 1) % FOLK.length], 12 + i, [x, 0, -0.6 + (i % 2) * 0.25], { expr: i % 2 ? "laugh" : "grin", look: 0.3 * Math.sin(i * 2), armR: i % 2 ? cheer(t, i) : SIDE, armL: i % 2 ? HIP : cheer(t, i + 1), bounce: Math.max(0, Math.sin(t * 8 + i)) * 0.6 }));
      barman("laugh", { armR: SHRUG });
      rain(out, t, 45.7, [0.2, 0, -0.6], 7, 36);
      break;
    case 21: case 22: {
      const p: V3 = [BEDROOM + 0.2, 0, -2.9];
      if (id === 22) break;
      P("DAN", DAN, 3, p, { expr: "nervous", mode: "stand", look: 0, armL: { x: 0.3, y: 0.55, front: true }, armR: { x: 0.3, y: 0.55, front: true } });
      sweat(out, t, [p[0] + 0.45, p[1] + 1.5, p[2] + 0.2]);
      break;
    }
    case 23: { const p = walk(t, 64.3, 66.7, [COPS_X + 0.3, 0.15, 6.5], [COPS_X + 0.3, 0.15, -0.6]); P("DAN", DAN, 3, p, { expr: "nervous", mode: "stroll", phase: (t - 64.3) * 1.7, look: 0, armL: REST, armR: REST }); break; }
    case 24:
      P("COP", COP, 13, [POLICE - 3.25, 0, -4.6], { expr: t > 67.6 ? "shock" : "neutral", look: 0.5, armL: HIP, armR: t > 67.6 ? SHRUG : HIP });
      P("DAN", DAN, 3, [POLICE - 2.3, 0, -2.1], { expr: t > 68.6 ? "relief" : "nervous", look: -0.6, armL: keys(t, [[66.9, REST], [67.3, WIDE]]), armR: keys(t, [[66.9, REST], [67.3, WIDE]]) });
      break;
    case 26: P("DAN", DAN, 3, [STREET[0] + 4.4, 0.15, 4.6], { expr: t > 76.6 ? "smile" : "nervous", look: 0.6, armL: SHRUG, armR: t > 74.3 ? { x: 1.05, y: -0.1 } : SHRUG }); break;
  }
  return out;
};
