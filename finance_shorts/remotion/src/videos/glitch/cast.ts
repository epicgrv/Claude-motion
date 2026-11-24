// Glitch cast: Dan (bartender) + friends / strangers on the v5 rig (IK arms, breathing, nods, calm blinks, smooth eyes).
// Props are held beside the body, never over faces; effects are unlit 2D cards (money, sparkles).
import * as THREE from "three";
import { Pen, bodyFront, Outfit, Expr, FrontOpts, INK, fxShadow, fxContact, ArmPose, Hold } from "../pepsi/toon";
import { Place, FxPlace } from "../bridge/cast";
import { LINES, MOUTH, VISEME } from "./vo";
import { FPS, Light, DAN_BAR, RAIN_T } from "./story";
import { V3, RUNWAY, STREET, PHONE } from "./sets";
import { balanceAt } from "./screens";

export type Stage = { places: Place[]; fx: FxPlace[] };
const DAN: Outfit = { jacket: "#1f1f26", pants: "#2b2b34", boots: INK, hat: "hair", hair: "#5a3b2a", skin: "#f5c9a0", collar: "#ffffff", tie: "#c0262f", buttons: "#d9d2c2", moustache: "#6a4a30" };
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
const REST: AP = { x: 0.16, y: 1.02 }, HIP: AP = { x: 0.5, y: 0.7 }, UP: AP = { x: 0.3, y: -1.05 }, WIDE: AP = { x: 1.1, y: -0.35 };
const SIDE: AP = { x: 0.95, y: 0.2 }, SIDEUP: AP = { x: 1.0, y: -0.25 }, FACEP: AP = { x: -0.42, y: -0.35, front: true }, SHRUG: AP = { x: 0.78, y: 0.12 };
const TAP: AP = { x: 0.15, y: 0.55, front: true };
const sm = (x: number) => { const u = Math.min(1, Math.max(0, x)); return u * u * (3 - 2 * u); };
const lerpA = (a: AP, b: AP, k: number): AP => ({ x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k, front: k < 0.5 ? a.front : b.front });
const keys = (t: number, k: [number, AP][], dur = 0.25): AP => { if (t <= k[0][0]) return k[0][1]; for (let i = 0; i + 1 < k.length; i++) { const [t1, b] = k[i + 1]; if (t < t1) return lerpA(k[i][1], b, sm((t - (t1 - dur)) / dur)); } return k[k.length - 1][1]; };
const breathe = (a: AP, t: number, s: number): AP => ({ ...a, x: a.x + 0.012 * Math.sin(t * 1.7 + s), y: a.y + 0.02 * Math.sin(t * 1.9 + s) });
const pump = (t: number, s: number, base = UP): AP => ({ ...base, x: base.x + 0.08 * Math.sin(t * 8 + s), y: base.y + 0.22 * Math.sin(t * 8 + s) });

// ---------------- props ----------------
const cvCache = new Map<string, HTMLCanvasElement>();
const cvs = (key: string, w: number, h: number, draw: (g: CanvasRenderingContext2D) => void) => { let c = cvCache.get(key); if (c) return c; c = document.createElement("canvas"); c.width = w; c.height = h; const g = c.getContext("2d")!; g.lineJoin = "round"; g.strokeStyle = INK; g.lineWidth = 10; draw(g); cvCache.set(key, c); return c; };
const phoneHold = (bal: number, ww = 0.5): Hold => ({ side: 1, w: ww, h: ww * 2, rot: -0.1, dx: 0.05, dy: -0.35, key: "ph" + Math.round(bal), bare: true,
  img: cvs("ph" + Math.round(bal), 200, 400, (g) => {
    g.fillStyle = "#14101a"; g.beginPath(); g.roundRect(6, 6, 188, 388, 26); g.fill(); g.stroke();
    g.fillStyle = "#14213f"; g.beginPath(); g.roundRect(18, 22, 164, 356, 16); g.fill();
    g.fillStyle = "#e8c45a"; g.font = '900 20px "Arial Black", Arial'; g.textAlign = "center"; g.fillText("GOLDLEAF", 100, 70);
    g.fillStyle = "#5cf5a6"; g.font = '900 26px "Arial Black", Arial'; g.fillText("$" + Math.round(bal).toLocaleString("en-US"), 100, 170);
  }) });
const champagne = (): Hold => ({ side: 1, w: 0.32, h: 0.75, rot: 0.15, dx: 0, dy: -0.3, key: "champ", bare: true,
  img: cvs("champ", 120, 300, (g) => { g.fillStyle = "#2f6a4a"; g.beginPath(); g.moveTo(45, 290); g.lineTo(75, 290); g.lineTo(80, 120); g.lineTo(68, 80); g.lineTo(68, 20); g.lineTo(52, 20); g.lineTo(52, 80); g.lineTo(40, 120); g.closePath(); g.fill(); g.stroke(); g.fillStyle = "#e8c45a"; g.fillRect(50, 14, 20, 40); g.fillStyle = "#f4f1ea"; g.fillRect(44, 170, 32, 50); }) });

// ---------------- staging helpers ----------------
const q = (v: number, n = 160) => Math.round(v * n) / n;
const fkey = (o: object) => JSON.stringify(o, (_k, v) => (typeof v === "number" ? q(v) : v && typeof v === "object" && "img" in v ? { ...v, img: undefined } : v));
const tier = (d: number): [number, number, number] => (d < 3.0 ? [1200, 2000, 2.0] : d < 6.5 ? [900, 1500, 1.5] : d < 16 ? [480, 800, 0.8] : [240, 400, 0.4]);
export type CamInfo = { pos: THREE.Vector3; right: THREE.Vector3; sun: THREE.Vector3 };
const light2D = (cam: CamInfo) => Math.round(Math.atan2(-cam.sun.y, cam.sun.dot(cam.right)) / (Math.PI / 4)) * (Math.PI / 4);
const tmp = new THREE.Vector3();
type Act = { expr?: Expr; mode?: FrontOpts["mode"]; look?: number; facing?: -1 | 0 | 1; armL?: AP; armR?: AP; hold?: Hold; blob?: boolean; bounce?: number; headTilt?: number };
type Ctx = { out: Stage; cam: CamInfo; t: number; s0: number; light: Light };
const blob = (c: Ctx, x: number, y: number, z: number) => {
  const hl = Math.hypot(c.cam.sun.x, c.cam.sun.z) || 1, ox = -c.cam.sun.x / hl, oz = -c.cam.sun.z / hl, rot = Math.atan2(-ox, -oz);
  c.out.fx.push({ key: "sh", cw: 128, ch: 256, draw: (p) => fxShadow(p, "#7a6a8a"), x: x + ox * 0.5, y: y + 0.018, z: z + oz * 0.5, w: 0.72, h: 1.6, flat: true, rot });
  c.out.fx.push({ key: "ct", cw: 128, ch: 128, draw: (p) => fxContact(p, "#5a4a6a"), x, y: y + 0.022, z, w: 0.52, h: 0.4, flat: true, rot });
};
const person = (c: Ctx, id: string, o: Outfit, seed: number, p: V3, a: Act = {}) => {
  const t = c.t, d = c.cam.pos.distanceTo(tmp.set(p[0], p[1] + 1.3, p[2])), [w, h, k] = tier(d);
  const m = mouthOf(id, t);
  const fo: FrontOpts = {
    expr: a.expr ?? "neutral", mode: a.mode ?? "stand", facing: a.facing ?? 0, prop: null, phase: 0,
    look: (a.look ?? 0) + 0.18 * noise(t * 0.45, seed), tilt: 1.1 * Math.sin(t * 1.35 + seed), headTilt: (a.headTilt ?? 0) + 1.5 * noise(t * 0.6, seed + 5),
    rise: Math.sin(t * 1.9 + seed), mouth: m, viseme: m > 0.08 ? visOf(t) : 0, brow: 0, blink: lidAt(t, seed, c.s0), light: light2D(c.cam), seed,
    armL: breathe(a.armL ?? REST, t, seed + 1.3), armR: breathe(a.armR ?? REST, t, seed), hold: a.hold,
  };
  c.out.places.push({ key: `F|${id}|${fkey(fo)}`, x: p[0], y: p[1] + 0.06 * (a.bounce ?? 0), z: p[2], draw: (pp: Pen) => bodyFront(pp, o, fo), size: [w, h, k] });
  if (a.blob !== false) blob(c, p[0], p[1], p[2]);
};
/** dollar bills: fluttering rain around c (spread w), or bursting out of a point toward the camera */
const bill = (g: CanvasRenderingContext2D, i: number) => {
  g.fillStyle = i % 2 ? "#7fc77a" : "#9bd88f"; g.strokeStyle = "#1f5a2a"; g.lineWidth = 8; g.beginPath(); g.roundRect(6, 6, 248, 118, 10); g.fill(); g.stroke();
  g.strokeStyle = "rgba(31,90,42,.6)"; g.lineWidth = 4; g.strokeRect(22, 20, 216, 90); g.fillStyle = "#1f5a2a"; g.beginPath(); g.ellipse(130, 65, 30, 34, 0, 0, Math.PI * 2); g.fill();
  g.fillStyle = "#9bd88f"; g.font = '900 46px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("$", 130, 68);
};
const rain = (out: Stage, t: number, t0: number, c: V3, spread: number, n = 26, top = 3.2) => {
  if (t < t0) return; const k = t - t0;
  for (let i = 0; i < n; i++) {
    const kk = k - hh(i, 2) * 1.2; if (kk < 0) continue;
    const y = c[1] + top - 1.6 * ((kk * 0.9 + hh(i, 5) * 3) % 3.4); if (y < c[1] + 0.05) continue;
    out.fx.push({ key: `bill${i % 2}`, cw: 260, ch: 130, draw: (pp) => bill(pp.g, i), x: c[0] + (hh(i, 3) - 0.5) * spread + 0.25 * Math.sin(kk * 3 + i), y, z: c[2] + (hh(i, 4) - 0.5) * 1.6,
      w: 0.34, h: 0.17 * Math.abs(Math.cos(kk * 4 + i)) + 0.03, rot: 0.6 * Math.sin(kk * 3.3 + i) });
  }
};
const burstBills = (out: Stage, t: number, t0: number, c: V3, n = 18) => {
  if (t < t0) return; const k = t - t0;
  for (let i = 0; i < n; i++) {
    const kk = (k + hh(i, 1) * 0.8) % 1.4, a = hh(i, 2) * Math.PI * 2, r = 0.05 + kk * (0.3 + 0.25 * hh(i, 3));
    out.fx.push({ key: `bill${i % 2}`, cw: 260, ch: 130, draw: (pp) => bill(pp.g, i), x: c[0] + Math.cos(a) * r, y: c[1] + Math.sin(a) * r * 0.8 + 0.05 * kk, z: c[2] + 0.05 + kk * 0.35,
      w: 0.06 + 0.05 * kk, h: (0.03 + 0.025 * kk) * Math.abs(Math.cos(kk * 6 + i)) + 0.008, rot: a + kk * 4 });
  }
};
const sparkle = (out: Stage, t: number, t0: number, p: V3, size: number) => {
  const u = (t - t0) / 0.4; if (u < 0 || u > 1) return; const s = q(Math.sin(Math.PI * u), 12);
  out.fx.push({ key: `spk${s}`, cw: 200, ch: 200, soft: true, draw: (pp) => { const g = pp.g; g.fillStyle = "#ffffff"; g.translate(100, 100); const r = 95 * s, w = 12 * s + 2; g.beginPath(); g.moveTo(0, -r); g.quadraticCurveTo(w * 0.4, -w * 0.4, r, 0); g.quadraticCurveTo(w * 0.4, w * 0.4, 0, r); g.quadraticCurveTo(-w * 0.4, w * 0.4, -r, 0); g.quadraticCurveTo(-w * 0.4, -w * 0.4, 0, -r); g.fill(); }, x: p[0], y: p[1], z: p[2], w: size, h: size });
};

// ---------------- staging per shot ----------------
export const stage = (id: number, t: number, s0: number, light: Light, cam: CamInfo): Stage => {
  const out: Stage = { places: [], fx: [] }, c: Ctx = { out, cam, t, s0, light };
  const [PX, PY, PZ] = PHONE, scr: V3 = [PX, PY + 0.19, PZ];
  switch (id) {
    case 1: burstBills(out, t, 0.9, scr, 22); sparkle(out, t, 2.5, [PX + 0.05, PY + 0.28, PZ + 0.03], 0.12); break;
    case 2: {
      person(c, "DAN", DAN, 3, DAN_BAR, { expr: t > 4.6 ? "laugh" : "grin", look: 0.1, armR: SIDEUP, hold: phoneHold(balanceAt(2.9)), armL: pump(t, 1), blob: false });
      rain(out, t, RAIN_T, [0, 0, -2.6], 6, 34);
      break;
    }
    case 3: if (t > 26.2) sparkle(out, t, 26.2, [PX + 0.05, PY + 0.26, PZ + 0.03], 0.1); break;
    case 4: {
      const tap = [28.3, 29.6, 30.9].some((x) => t > x && t < x + 0.25);
      person(c, "DAN", DAN, 3, DAN_BAR, { expr: t < 28.3 ? "shock" : "grin", look: 0.6, armR: tap ? { x: 0.05, y: 0.62, front: true } : TAP, hold: phoneHold(balanceAt(t), 0.42), armL: t > 29.6 ? UP : HIP, blob: false });
      for (const x of [28.3, 29.6, 30.9]) sparkle(out, t, x, [DAN_BAR[0] + 0.6, 1.75, DAN_BAR[2] + 0.4], 0.35);
      break;
    }
    case 5: {
      const [RX] = RUNWAY;
      person(c, "DAN", DAN, 3, [RX + 3.4, 0, 2.0], { expr: "laugh", look: 0.2, armR: SIDEUP, hold: champagne(), armL: pump(t, 2) });
      person(c, "F0", FOLK[0], 5, [RX + 1.9, 0, 1.6], { expr: "grin", look: 0.4, armL: UP, armR: pump(t, 3) });
      person(c, "F1", FOLK[1], 7, [RX + 4.9, 0, 1.7], { expr: "laugh", look: -0.4, armR: UP, armL: HIP });
      break;
    }
    case 6: {
      person(c, "DAN", DAN, 3, DAN_BAR, { expr: "laugh", look: 0, armR: pump(t, 0, WIDE), armL: pump(t, 2, WIDE), blob: false, bounce: Math.max(0, Math.sin(t * 7)) });
      for (let i = 0; i < 4; i++) person(c, "S" + i, FOLK[(i + 1) % FOLK.length], 10 + i, [-2.4 + i * 1.6, 0, -0.35 + (i % 2) * 0.3],
        { expr: i % 2 ? "laugh" : "grin", look: 0.3 * Math.sin(i * 2), armR: i % 2 ? pump(t, i) : UP, armL: i % 2 ? HIP : pump(t, i + 1), bounce: Math.max(0, Math.sin(t * 8 + i)) });
      rain(out, t, 44.7, [0, 0, -1.4], 7, 36);
      break;
    }
    case 7: {
      const [SX] = STREET;
      person(c, "DAN", DAN, 3, [SX + 3.0, 0.15, 3.0], { expr: t > 76.6 ? "smile" : "nervous", look: 0.5, armL: SHRUG, armR: t > 74.3 ? { x: 1.05, y: -0.1 } : SHRUG });
      break;
    }
    default: person(c, "DAN", DAN, 3, DAN_BAR, { expr: "smile", look: 0, blob: false });
  }
  void SIDE; void FACEP;
  return out;
};
