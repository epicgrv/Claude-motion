// v5 cast: flat 2D characters with a real rig (2-bone IK arms with elbows, breathing, weight shift, head nods),
// mouths opened by the voice loudness of whoever speaks, calm 3-frame blinks every 2.5-5.5 s, smooth eye drift,
// props drawn in their hands. Smooth 30 fps motion (no stepped poses). Effects are unlit 2D cards.
import * as THREE from "three";
import { Pen, bodyFront, Outfit, Expr, FrontOpts, Prop, INK, KID, SKINS, townsfolk, fxBurst, fxPuff, fxShadow, fxContact, ArmPose, Hold } from "./toon";
import { Place, FxPlace } from "../bridge/cast";
import { LINES, MOUTH, VISEME } from "./vo";
import { FPS, Light, BOARD, ARROW, arrowH, ROOF_JET, jetHero } from "./story";
import { ROOM, A, V3 } from "./sets";
import { chequeTex, catalogTex, couponTex } from "./tex";

export type Stage = { places: Place[]; fx: FxPlace[] };

// ---------------- the cast ----------------
const JOHN: Outfit = { jacket: "#3f7fd0", pants: "#3b3f52", boots: "#f4f1ea", hat: "hair", hair: "#5a3b2a", strings: "#f4f1ea", buttons: "#3f7fd0" };
const BUDDY: Outfit = { jacket: "#f08a2c", pants: "#56607a", boots: "#e2453c", hat: "cap", cap: "#2fa05a", build: "stout", skin: "#c99067" };
const TEEN: Outfit = { jacket: "#c0353a", pants: "#2f3550", boots: "#f4f1ea", hat: "hair", hair: "#e8c45a", build: "kid", skin: "#f5c9a0" };
const EXEC: Outfit = { jacket: "#2b3448", pants: "#2b3448", boots: INK, hat: "hair", hair: "#c9c9d1", moustache: "#8a8a96", build: "stout", buttons: "#e8c45a", collar: "#ffffff", tie: "#d8323c" };
const ASSIST: Outfit = { jacket: "#5a4a8c", pants: "#3b3f52", boots: "#4a3426", hat: "hair", hair: "#2a201a", skin: "#ecd0b6", collar: "#ffffff", tie: "#2f5f6a" };
const JUDGE: Outfit = { jacket: "#1e1e26", pants: "#1e1e26", boots: INK, hat: "hair", hair: "#f1efe6", moustache: "#f1efe6", build: "stout", skin: "#ecd0b6", collar: "#ffffff", buttons: "#1e1e26" };
const DRIVER: Outfit = { jacket: "#e8b33a", pants: "#3b3f52", boots: INK, hat: "cap", cap: "#2f5f6a", moustache: "#4a3020", build: "stout", skin: "#f5c9a0" };
const INV: Outfit[] = ["#3f6fb5", "#8c3b4a", "#2f5f6a", "#5d7a3a", "#7b5ac9"].map((c, i) => ({
  jacket: c, pants: "#2b2b34", boots: INK, hat: i % 2 ? "tophat" : "hair", hair: ["#5a3b2a", "#2a201a", "#c9c9d1", "#8a5a3c", "#e8c45a"][i],
  moustache: i === 1 || i === 2 ? "#3a2a20" : undefined, build: i % 2 ? "stout" : "adult", skin: SKINS[(i + 1) % 4], buttons: "#e8c45a", collar: "#ffffff", tie: ["#d8323c", "#f2c94c", "#3fae8a", "#e2453c", "#3f7fd0"][i],
}));
const KIDS: Outfit[] = ["#f08a2c", "#3fae8a", "#7b5ac9", "#e2453c", "#3f7fd0", "#e8b33a"].map((c, i) => ({ ...KID, jacket: c, cap: ["#e2453c", "#3f6fb5", "#f2c94c"][i % 3], skin: SKINS[i % 4], hat: i % 2 ? "cap" : "hair", hair: "#5a3b2a" }));
const FOLK = [0, 1, 2, 3, 4, 5].map((v) => townsfolk(v));
const OUT: Record<string, Outfit> = { JOHN, BUDDY, TEEN, EXEC, ASSIST, JUDGE, DRIVER };
const SEED: Record<string, number> = { JOHN: 3, BUDDY: 6, TEEN: 2, EXEC: 5, ASSIST: 1, JUDGE: 4, DRIVER: 7 };

// ---------------- held things (canvas images) ----------------
const img = (t: THREE.Texture) => t.image as HTMLCanvasElement;
const CHQ1 = () => img(chequeTex("$700,000.00", "Seven hundred thousand & 00/100"));
const CHQ2 = () => img(chequeTex("$700,008.50", "Seven hundred thousand eight & 50/100"));
const CAT = () => img(catalogTex());
const CPN = () => img(couponTex());
const holdCheque = (amount: 1 | 2, side: -1 | 1, w = 1.5, rot = -0.08, dx = 0, dy = -0.3): Hold =>
  ({ side, img: amount === 1 ? CHQ1() : CHQ2(), w, h: w * 620 / 1400, rot, dx, dy, key: `chq${amount}` });

// ---------------- life ----------------
const hh = (i: number, s = 0) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };
const noise = (x: number, s: number) => { const i = Math.floor(x), f = x - i, w = f * f * (3 - 2 * f); return (hh(i, s) * (1 - w) + hh(i + 1, s) * w) * 2 - 1; };
/** calm blinks: half / shut / half, every 2.5-5.5 s, never in the first 6 frames of a shot */
const lidAt = (t: number, i: number, shotStart: number) => {
  const f = Math.round(t * FPS);
  if (f - Math.round(shotStart * FPS) < 6) return 0;
  let s = Math.round(-90 * hh(i, 9));
  for (let n = 0; s <= f && n < 400; n++) {
    const k = f - s;
    if (k >= 0 && k < 3) return [0.5, 1, 0.5][k];
    s += Math.round(75 + 90 * hh(i * 31 + n, 13));
  }
  return 0;
};
const lineAt = (t: number) => LINES.find((l) => t >= l.s - 0.04 && t <= l.e + 0.04);
/** mouth opening 0..1 of `who` at real time t (voice loudness, 30 fps) */
const visOf = (t: number) => { const f = Math.round(t * FPS); return f >= 0 && f < VISEME.length ? Number(VISEME[f]) : 0; };
const mouthOf = (who: string, t: number) => {
  const l = lineAt(t);
  if (!l || l.who !== who) return 0;
  const f = Math.round(t * FPS);
  return f >= 0 && f < MOUTH.length ? Number(MOUTH[f]) / 4 : 0;
};
/** smoothed speaking energy (for gestures / nods) */
const energy = (who: string, t: number) => {
  let a = 0;
  for (let k = -4; k <= 4; k++) a += mouthOf(who, t + k / FPS);
  return Math.min(1, (a / 9) * 1.6);
};

// ---------------- arm poses (hand target from the shoulder, in head heights; x outward, y down) ----------------
type AP = ArmPose;
export const REST: AP = { x: 0.16, y: 1.02 };
const HIP: AP = { x: 0.5, y: 0.7 };
const UP: AP = { x: 0.3, y: -1.05 };
const POINT: AP = { x: 1.15, y: -0.1 };
const SHRUG: AP = { x: 0.78, y: 0.12 };
const SHOW: AP = { x: -0.1, y: 0.42, front: true };
const SHOWHI: AP = { x: 0.05, y: 0.0, front: true };
const CROSS: AP = { x: -0.55, y: 0.62, front: true };
const FACEP: AP = { x: -0.42, y: -0.35, front: true };
const lerpA = (a: AP, b: AP, k: number): AP => ({ x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k, front: k < 0.5 ? a.front : b.front, bend: b.bend ?? a.bend });
const sm = (x: number) => { const u = Math.min(1, Math.max(0, x)); return u * u * (3 - 2 * u); };
/** pose keys [time, pose]: hold each pose, blend to the next over `dur` s ending at its key time */
const keys = (t: number, k: [number, AP][], dur = 0.32): AP => {
  if (t <= k[0][0]) return k[0][1];
  for (let i = 0; i + 1 < k.length; i++) {
    const [t1, b] = k[i + 1];
    if (t < t1) { const a = k[i][1], u = sm((t - (t1 - dur)) / dur); return lerpA(a, b, u); }
  }
  return k[k.length - 1][1];
};
/** talking hand: rises with the voice energy, small beats */
const talkArm = (e: number, t: number, seed: number, base: AP = { x: 0.42, y: 0.78 }): AP =>
  ({ x: base.x + 0.18 * e + 0.05 * e * Math.sin(t * 7.3 + seed), y: base.y - 0.5 * e - 0.08 * e * Math.sin(t * 9.1 + seed * 2) });
const breathe = (a: AP, t: number, seed: number): AP => ({ ...a, x: a.x + 0.012 * Math.sin(t * 1.7 + seed), y: a.y + 0.02 * Math.sin(t * 1.9 + seed) });

// ---------------- drawing helpers ----------------
const q = (v: number, n = 160) => Math.round(v * n) / n;
const fkey = (o: object) => JSON.stringify(o, (_k, v) => (typeof v === "number" ? q(v) : v && typeof v === "object" && "img" in v ? { ...v, img: undefined } : v));
const tier = (d: number): [number, number, number] => (d < 3.0 ? [1200, 2000, 2.0] : d < 6.5 ? [900, 1500, 1.5] : d < 16 ? [480, 800, 0.8] : [240, 400, 0.4]);
export type CamInfo = { pos: THREE.Vector3; right: THREE.Vector3; sun: THREE.Vector3 };
const light2D = (cam: CamInfo) => Math.round(Math.atan2(-cam.sun.y, cam.sun.dot(cam.right)) / (Math.PI / 4)) * (Math.PI / 4);
const tmp = new THREE.Vector3();

type Who = { id: string; o?: Outfit; seed?: number; i?: number };
type Act = {
  expr?: Expr; mode?: FrontOpts["mode"]; look?: number; facing?: -1 | 0 | 1; prop?: Prop; tilt?: number; headTilt?: number; phase?: number; scale?: number; blob?: boolean;
  armL?: AP; armR?: AP; hold?: Hold; talkSide?: -1 | 1; still?: boolean;
};

const blob = (out: Stage, cam: CamInfo, x: number, y: number, z: number, sc: number, light: Light) => {
  const hl = Math.hypot(cam.sun.x, cam.sun.z) || 1, ox = -cam.sun.x / hl, oz = -cam.sun.z / hl, rot = Math.atan2(-ox, -oz);
  if (light === "day") {
    const el = Math.asin(Math.min(0.99, Math.max(0.1, cam.sun.y)));
    const len = Math.min(2.4, Math.max(0.5, 1.6 / Math.tan(el))) * sc, h = len + 0.55 * sc, c = 0.3 * h;
    out.fx.push({ key: "blob|shadow|#a9adc4", cw: 128, ch: 256, draw: (p) => fxShadow(p, "#a9adc4"), x: x + ox * c, y: y + 0.018, z: z + oz * c, w: 0.72 * sc, h, flat: true, rot });
  }
  out.fx.push({ key: "blob|contact|#7a7c9a", cw: 128, ch: 128, draw: (p) => fxContact(p, "#7a7c9a"), x, y: y + 0.022, z, w: 0.52 * sc, h: 0.4 * sc, flat: true, rot });
};

type Ctx = { out: Stage; cam: CamInfo; t: number; tr: number; s0: number; light: Light };
/** a living character: breathing, weight shift, voice-driven mouth + nods + talking hand, calm blinks, smooth eyes */
const person = (c: Ctx, who: Who, p: V3, a: Act = {}) => {
  const o = who.o ?? OUT[who.id], seed = who.seed ?? SEED[who.id] ?? 1, idx = who.i ?? seed, tr = c.tr;
  const sc = a.scale ?? 1;
  const d = c.cam.pos.distanceTo(tmp.set(p[0], p[1] + 1.3 * sc, p[2])) / sc;
  const [w, h, k] = tier(d);
  const m = mouthOf(who.id, tr), e = energy(who.id, tr), live = !a.still;
  const ts = a.talkSide ?? 1;
  let armR = a.armR, armL = a.armL;
  if (e > 0.05 && live) { // talking hand on the free side
    if (ts > 0 && !a.armR) armR = talkArm(e, tr, seed); else if (ts < 0 && !a.armL) armL = talkArm(e, tr, seed + 3);
  }
  if (live) { armR = breathe(armR ?? REST, tr, seed); armL = breathe(armL ?? REST, tr, seed + 1.3); }
  const fo: FrontOpts = {
    expr: a.expr ?? "neutral", mode: a.mode ?? "stand", facing: a.facing ?? 0, prop: a.prop ?? null, phase: a.phase ?? 0,
    look: (a.look ?? 0) + (live ? 0.18 * noise(tr * 0.45, seed) : 0),
    tilt: (a.tilt ?? 0) + (live ? 1.1 * Math.sin(tr * 1.35 + seed) + 2.2 * e * Math.sin(tr * 4.1 + seed) : 0),
    headTilt: (a.headTilt ?? 0) + (live ? 1.5 * noise(tr * 0.6, seed + 5) + 3.5 * e * Math.sin(tr * 6.2 + seed) : 0),
    rise: live ? Math.sin(tr * 1.9 + seed) : 0, mouth: m, viseme: m > 0.08 ? visOf(tr) : 0, brow: Math.min(1, e * 1.1),
    blink: lidAt(tr, idx, c.s0), light: light2D(c.cam), seed, armL, armR, hold: a.hold,
  };
  c.out.places.push({ key: `F|${who.id}${who.i ?? ""}|${fkey(fo)}`, x: p[0], y: p[1], z: p[2], scale: sc, draw: (pp: Pen) => bodyFront(pp, o, fo), size: [w, h, k] });
  if (a.blob !== false) blob(c.out, c.cam, p[0], p[1], p[2], sc, c.light);
};

/** unlit 2D effect cards */
const burst = (out: Stage, t: number, t0: number, dur: number, p: V3, size: number, col = "#fff3b0") => {
  const u = (t - t0) / dur; if (u < 0 || u > 1) return;
  const uq = q(u, 30);
  out.fx.push({ key: `burst${col}${uq}`, cw: 500, ch: 500, draw: (pp) => fxBurst(pp, uq, col, 12), x: p[0], y: p[1], z: p[2], w: size, h: size });
};
const puff = (out: Stage, t: number, t0: number, dur: number, p: V3, size: number) => {
  const u = (t - t0) / dur; if (u < 0 || u > 1) return;
  const uq = q(u, 30);
  out.fx.push({ key: `puff${uq}`, cw: 300, ch: 300, draw: (pp) => fxPuff(pp, uq), x: p[0], y: p[1], z: p[2], w: size, h: size, soft: true });
};
/** comic label popping in with overshoot */
const pop = (out: Stage, t: number, t0: number, t1: number, p: V3, h: number, text: string, fg = "#ffffff", bg = "#e2453c", rot = 0) => {
  if (t < t0 || t > t1) return;
  const u = Math.min(1, (t - t0) / 0.16), s = u < 1 ? 0.2 + 1.0 * sm(u) * 1.1 : 1 + 0.05 * Math.sin((t - t0) * 10) * Math.exp(-(t - t0) * 4);
  const cw = Math.max(400, 110 * text.length + 120), ch = 240;
  out.fx.push({ key: `pop|${text}|${bg}`, cw, ch, draw: (pp) => drawPop(pp.g, cw, ch, text, fg, bg), x: p[0], y: p[1], z: p[2], w: (h * cw / ch) * s, h: h * s, rot });
};
const drawPop = (g: CanvasRenderingContext2D, W: number, H: number, text: string, fg: string, bg: string) => {
  g.fillStyle = bg; g.strokeStyle = INK; g.lineWidth = 14;
  g.beginPath(); g.roundRect(10, 10, W - 20, H - 20, 40); g.fill(); g.stroke();
  g.font = '900 150px "Arial Black", Arial, sans-serif'; g.textAlign = "center"; g.textBaseline = "middle";
  let s = 1; const mw = g.measureText(text).width; if (mw > W - 80) s = (W - 80) / mw;
  g.save(); g.translate(W / 2, H / 2 + 8); g.scale(s, 1);
  g.lineWidth = 18; g.strokeStyle = INK; g.strokeText(text, 0, 0); g.fillStyle = fg; g.fillText(text, 0, 0); g.restore();
};
const speed = (out: Stage, t: number, p: V3, size: number) => {
  const k = Math.floor(t * 15) % 4;
  out.fx.push({ key: `speed${k}`, cw: 512, ch: 512, soft: true, draw: (pp) => {
    const g = pp.g; g.strokeStyle = "rgba(255,255,255,0.85)"; g.lineCap = "round";
    for (let i = 0; i < 26; i++) { const a = (i / 26) * Math.PI * 2 + k * 0.4 + hh(i, k) * 0.2, r0 = 150 + 60 * hh(i, k + 3), r1 = 256 * 1.4;
      g.lineWidth = 3 + 6 * hh(i, k + 7); g.beginPath(); g.moveTo(256 + r0 * Math.cos(a), 256 + r0 * Math.sin(a)); g.lineTo(256 + r1 * Math.cos(a), 256 + r1 * Math.sin(a)); g.stroke(); }
  }, x: p[0], y: p[1], z: p[2], w: size, h: size });
};
const sweat = (out: Stage, t: number, p: V3, size: number) => {
  const k = q((t * 1.5) % 1, 15);
  out.fx.push({ key: `sweat${k}`, cw: 200, ch: 240, draw: (pp) => {
    const g = pp.g; g.fillStyle = "#bfe8ff"; g.strokeStyle = INK; g.lineWidth = 10;
    for (const [x, y] of [[60, 70 + k * 60], [140, 100 + ((k + 0.5) % 1) * 60]]) { g.beginPath(); g.moveTo(x, y - 40); g.quadraticCurveTo(x + 30, y + 10, x, y + 26); g.quadraticCurveTo(x - 30, y + 10, x, y - 40); g.fill(); g.stroke(); }
  }, x: p[0], y: p[1], z: p[2], w: size, h: size * 1.2 });
};
const coupon = (out: Stage, p: V3, rot: number, size: number) => {
  out.fx.push({ key: "couponFx", cw: 320, ch: 160, draw: (pp) => {
    const g = pp.g; g.fillStyle = "#fff4c2"; g.fillRect(4, 4, 312, 152); g.setLineDash([10, 8]); g.strokeStyle = INK; g.lineWidth = 6; g.strokeRect(10, 10, 300, 140); g.setLineDash([]);
    g.fillStyle = "#d8323c"; g.font = '900 64px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("FREE", 160, 62);
    g.fillStyle = "#1d4fb8"; g.font = '900 40px "Arial Black", Arial'; g.fillText("SODA!", 160, 116);
  }, x: p[0], y: p[1], z: p[2], w: size, h: size / 2, rot });
};
const R = (k: keyof typeof ROOM, x: number, y: number, z: number): V3 => [x + ROOM[k], y, z];
const walk = (t: number, t0: number, t1: number, a: V3, b: V3): [V3, number, boolean] => {
  const u = Math.min(1, Math.max(0, (t - t0) / (t1 - t0)));
  return [[a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u], (t - t0) * 1.7, u > 0 && u < 1];
};

// ---------------- staging per shot ----------------
/** t = story time of the shot (old timings for shots < 100), tr = real time (voice), s0 = shot start (real) */
export const stage = (id: number, t: number, tr: number, s0: number, light: Light, cam: CamInfo): Stage => {
  const out: Stage = { places: [], fx: [] };
  const c: Ctx = { out, cam, t, tr, s0, light };
  const P = (who: Who, p: V3, a?: Act) => person(c, who, p, a);
  const kid = (i: number, p: V3, e: Expr, a: Act = {}) => P({ id: "KID", o: KIDS[i], seed: i + 1, i }, p, { expr: e, look: 0.3 * Math.sin(i), ...a });
  switch (id) {
    // ================= HOOK =================
    case 101: { // "This college kid found a way to buy..." - John shows the cheque, grinning
      P({ id: "JOHN" }, [2.2, 0.15, -5.4], { expr: "grin", look: 0.2, armR: { x: -0.15, y: 0.42, front: true }, hold: holdCheque(1, 1, 1.45, -0.06, -0.22, -0.05), armL: keys(t, [[0, { x: -0.1, y: 0.45, front: true }], [1.0, { x: -0.1, y: 0.45, front: true }], [1.3, UP]]) });
      break;
    }
    case 102: { // jet hero pass + price tag
      const j = jetHero(t);
      if (t < 3.15) pop(out, t, 2.0, 3.15, [j[0] - 1, j[1] + 3.6, j[2]], 2.6, "$20,000,000", "#ffffff", "#2f7a3a", -0.05);
      if (t > 2.95 && t < 3.45) speed(out, t, [j[0] + 4, j[1] - 1, j[2]], 14);
      break;
    }
    case 103: { // "...for $700 grand" - the cheque up close, fully readable
      P({ id: "JOHN" }, [2.2, 0.15, -5.4], { expr: "grin", look: 0.5, armR: { x: -0.15, y: 0.42, front: true }, hold: holdCheque(1, 1, 1.45, -0.04, -0.22, -0.05), armL: keys(t, [[3.45, { x: -0.1, y: 0.45, front: true }], [4.25, { x: -0.1, y: 0.45, front: true }], [4.5, UP]]) });
      burst(out, t, 4.3, 0.45, [1.3, 2.3, -6.2], 1.4, "#ffe7a0");
      break;
    }
    case 104: { // "The loophole? A Pepsi ad"
      pop(out, t, 5.35, 7.05, R("dorm", 0.4, 2.35, -4.3), 0.36, "LOOPHOLE?", "#ffffff", "#e2453c", -0.06);
      break;
    }
    case 105: { // jet lands on the school roof
      for (let i = 0; i < 5; i++) kid(i, [60 + i * 3.2, 0.1, -17.5 + (i % 2) * 1.2], t > 8.4 ? "laugh" : "shock", { armR: t > 8.4 ? keys(t, [[8.4, REST], [8.7, UP]]) : SHRUG, armL: t > 8.4 ? REST : SHRUG });
      if (t > 9.05) puff(out, t, 9.05, 0.9, [ROOF_JET[0] - 3, ROOF_JET[1] + 0.8, ROOF_JET[2] + 3], 6);
      break;
    }
    case 106: { // "Sure beats the bus" - teen on the roof, the bus below
      P({ id: "TEEN" }, [76.4, 11.62, -26.0], { expr: "grin", look: -0.3, armR: keys(t, [[9.7, REST], [10.0, POINT]]), armL: HIP, blob: false });
      break;
    }
    // ================= STORY (old timings) =================
    case 5: {
      for (let i = 0; i < 4; i++) kid(i, [BOARD[0] - 4.5 + i * 3.0, 0.1, BOARD[2] + 2.4 + (i % 2)], t > 11.3 ? "shock" : "neutral", { armL: t > 11.3 ? FACEP : REST, armR: t > 11.3 ? SHRUG : REST });
      burst(out, t, 11.2, 0.45, [BOARD[0], 1.2, BOARD[2] + 0.8], 4.5, "#ffe7a0");
      puff(out, t, 11.22, 0.9, [BOARD[0] - 2.5, 0.5, BOARD[2] + 0.6], 3.5); puff(out, t, 11.22, 0.9, [BOARD[0] + 2.8, 0.5, BOARD[2] + 0.6], 3.5);
      break;
    }
    case 6: {
      P({ id: "BUDDY" }, R("dorm", -2.2, 0, -0.6), { expr: "shock", mode: "sit", look: 0.5, facing: 1, armL: keys(t, [[12.9, REST], [13.2, UP]]), talkSide: 1 });
      P({ id: "JOHN" }, R("dorm", 2.4, 0, -3.0), { expr: "smile", look: -0.6, facing: -1, armL: CROSS, armR: CROSS });
      break;
    }
    case 7: { // John reads the fine print: the catalogue in his hands, readable
      P({ id: "JOHN" }, R("dorm", 1.9, 0, -2.6), { expr: t > 16.6 ? "grin" : "stern", look: 0.4, facing: 0,
        armR: { x: 0.0, y: 0.55, front: true }, armL: { x: 0.05, y: 0.6, front: true },
        hold: { side: 1, img: CAT(), w: 1.2, h: 1.2 * 1400 / 1024, rot: 0.03, dx: -0.4, dy: 0.55, key: "cat" } });
      if (t > 16.6) pop(out, t, 16.75, 17.55, R("dorm", 1.45, 2.15, -2.4), 0.24, "!!", "#ffffff", "#e2453c", 0.1);
      break;
    }
    case 8: pop(out, t, 18.4, 19.85, R("dorm", 3.36, 1.2, -3.52), 0.06, "10¢ EACH!", "#241726", "#fff36b", -0.05); break;
    case 9: {
      P({ id: "JOHN" }, R("dorm", 2.4, 0, -4.2), { expr: t > 21.5 ? "shock" : "stern", look: 0.6, facing: 1, armR: keys(t, [[19.85, { x: 0.6, y: 0.55 }], [21.5, UP]]) });
      break;
    }
    case 10: pop(out, t, 22.75, 24.7, [ROOF_JET[0] - 2, ROOF_JET[1] + 5.2, ROOF_JET[2] + 3], 2.2, "$20,000,000+", "#ffffff", "#2f7a3a", 0.05); break;
    case 11: {
      for (let i = 0; i < 5; i++) {
        const sh = t > 25.6, [p, ph, mv] = walk(t, 24.7, 25.9, [-41 + i * 2.6, 0.15, 6.0 + (i % 2) * 0.8], [-37 + i * 3.0, 0.15, 7.6 + (i % 2) * 0.9]);
        P({ id: "FOLK", o: FOLK[i], seed: i + 2, i: i + 10 }, p, { expr: sh ? (i % 2 ? "shock" : "laugh") : "smile", mode: mv ? "stroll" : "stand", phase: ph,
          armR: sh ? keys(t, [[25.6, REST], [25.9, i % 2 ? FACEP : UP]]) : undefined, armL: sh && i % 2 ? FACEP : undefined, look: 0.4 * Math.sin(i * 2) });
      }
      break;
    }
    case 12: case 13: {
      P({ id: "JOHN" }, R("class", 2.9, 0, -5.2), { expr: "grin", look: -0.6, facing: -1, talkSide: 1,
        armL: id === 13 ? keys(t, [[30.3, REST], [30.6, { x: 1.2, y: -0.35 }], [31.9, { x: 1.2, y: -0.35 }], [32.2, { x: 0.9, y: -0.6 }]]) : { x: 1.0, y: -0.2 } });
      if (id === 12) P({ id: "BUDDY" }, R("class", -1.4, 0, -1.75), { expr: "nervous", mode: "sit", look: 0.4, blob: false, armL: FACEP });
      break;
    }
    case 14: {
      P({ id: "BUDDY" }, R("class", -1.4, 0, -1.75), { expr: "shock", mode: "sit", look: 0, blob: false, armL: { x: 0.2, y: -0.9 }, armR: { x: 0.2, y: -0.9 } });
      sweat(out, t, R("class", -0.95, 1.75, -1.6), 0.24);
      break;
    }
    case 15: case 16: case 17: {
      for (let i = 0; i < 5; i++) P({ id: i === 2 ? "INVESTOR" : "INV", o: INV[i], seed: 1 + ((i * 3) % 7), i: i + 20 }, R("board", -3.2 + i * 1.6, 0, -3.0),
        { expr: i === 2 && id >= 16 ? "nervous" : i % 2 ? "grin" : "smile", look: id === 17 ? 0.8 : 0.3 * Math.sin(i), blob: false, armL: i % 2 ? HIP : CROSS, armR: i % 2 ? HIP : CROSS });
      P({ id: "JOHN" }, R("board", 4.6, 0, -1.4), { expr: id === 17 ? "grin" : "smile_closed", look: -0.7, facing: -1, headTilt: id === 17 ? 10 : 0,
        armL: id === 17 ? SHRUG : REST, armR: id === 17 ? SHRUG : HIP });
      if (id === 17) pop(out, t, 37.0, 37.6, R("board", 4.0, 2.55, -1.2), 0.3, "?", "#ffffff", "#3f7fd0");
      break;
    }
    case 18: { // mails the cheque: show it, open the mailbox door, slide it in, close, flag up
      const reach = keys(t, [[37.6, SHOWHI], [39.15, SHOWHI], [39.55, { x: 0.95, y: 0.2 }], [39.95, { x: 1.2, y: 0.18 }], [40.35, REST]], 0.35);
      P({ id: "JOHN" }, [2.9, 0.15, -6.5], { expr: t > 40.3 ? "grin" : "smile_closed", look: t > 39.1 && t < 40.3 ? 0.9 : 0.3, armR: reach, armL: HIP,
        hold: t < 39.95 ? holdCheque(2, 1, t < 39.15 ? 1.5 : 0.9, t < 39.15 ? -0.06 : 0.1, t < 39.15 ? -0.15 : 0.1, t < 39.15 ? -0.35 : -0.05) : undefined });
      if (t > 40.5) pop(out, t, 40.5, 41.7, [3.0, 2.15, -6.7], 0.26, "+$8.50 SHIPPING", "#241726", "#fff36b", 0.06);
      break;
    }
    case 19: pop(out, t, 43.15, 44.3, [-124.5, 22.4, -19.9], 3.6, "CRIMINAL?!", "#ffffff", "#241726", -0.08); break;
    case 20: case 21: {
      P({ id: "EXEC" }, R("office", -0.1, 0.05, -3.0), { expr: "laugh", look: 0, blob: false, armL: id === 21 ? { x: -0.35, y: 0.62, front: true } : HIP,
        armR: { x: 0.85, y: 0.15 }, tilt: 3 * Math.sin(tr * 9) });
      if (id === 20) P({ id: "ASSIST" }, R("office", 1.7, 0, -2.4), { expr: "laugh", look: -0.6, facing: -1, tilt: -3 * Math.sin(tr * 8.5), armL: CROSS, armR: { x: 0.3, y: -0.2 } });
      if (id === 21) pop(out, t, 46.45, 48.2, R("office", -0.75, 2.45, -2.6), 0.32, "HA HA HA", "#ffffff", "#e2453c", -0.1);
      break;
    }
    case 22: {
      const showC = t > 52.3;
      P({ id: "JOHN" }, [0, 0.1, -7.75], { expr: t > 49.7 ? (showC ? "smile" : "dazed") : "neutral", mode: "sit", look: 0.3,
        armR: showC ? keys(t, [[52.3, REST], [52.6, SHOWHI]]) : { x: 0.1, y: 0.45, front: true },
        hold: showC ? { side: 1, img: CPN(), w: 1.0, h: 0.5, rot: -0.12, dx: 0, dy: -0.22, key: "cpn" } : t < 50 ? undefined : holdCheque(2, 1, 0.8, 0.2, 0, -0.1) });
      for (let i = 0; i < 9; i++) {
        const t0 = 49.5 + i * 0.25; if (t < t0) continue;
        const u = Math.min(1, (t - t0) / 1.6);
        coupon(out, [-1.2 + (i * 0.37) % 2.4 + 0.25 * Math.sin((t - t0) * 4 + i), 3.0 - 2.75 * u + 0.12 * (i % 3), -7.4 + 0.25 * (i % 3)], 0.6 * Math.sin((t - t0) * 3 + i), 0.42);
      }
      pop(out, t, 52.4, 53.75, [0.6, 2.1, -7.5], 0.3, "+1 POINT", "#ffffff", "#1d4fb8", 0.08);
      break;
    }
    case 23: { const [p, ph] = walk(t, 53.75, 55.0, [-74.2, 0.15, 13.5], [-74.2, 1.35, 18.0]); P({ id: "JOHN" }, p, { mode: "stroll", phase: ph, expr: "stern", look: 0 }); break; }
    case 24: case 25: case 26: {
      const strike = id === 26 ? (t < 61.98 ? 0 : Math.min(1, (t - 61.98) / 0.06)) : 0;
      P({ id: "JUDGE" }, R("court", 0, 0.85, -5.1), { expr: "stern", look: id === 25 ? 0.7 : 0, blob: false, prop: id === 26 ? ["hammer", strike] : null,
        armL: id === 24 ? { x: 0.6, y: 0.35 } : REST, talkSide: -1 });
      if (id === 24) P({ id: "JOHN" }, R("court", -2.4, 0, -0.5), { expr: t > 57 ? "nervous" : "smile", look: -0.3, facing: 1, armL: t > 57 ? FACEP : REST });
      if (id === 25 || id === 24) {
        P({ id: "BUDDY" }, R("court", 2.5, 0, 2.35), { expr: "grin", mode: id === 25 ? "stand" : "sit", blob: false, armR: id === 25 ? keys(t, [[59.7, REST], [59.95, UP]]) : undefined, armL: id === 25 ? keys(t, [[60.9, REST], [61.2, { x: -0.3, y: 0.4, front: true }]]) : undefined, talkSide: -1 });
        for (let i = 0; i < 3; i++) P({ id: "FOLK", o: FOLK[i + 2], seed: i + 3, i: i + 30 }, R("court", -4.2 + i * 1.3 + (i > 1 ? 4.6 : 0), 0, 2.15 + (i % 2) * 1.6), { expr: id === 25 ? "nervous" : "neutral", mode: "sit", look: 0.6, blob: false });
      }
      if (id === 26) { burst(out, t, 62.0, 0.4, R("court", 0.6, 1.75, -4.75), 1.3, "#fff3b0"); pop(out, t, 62.1, 63.4, R("court", 0.55, 2.4, -3.6), 0.3, "LOST", "#ffffff", "#e2453c", 0.1); }
      break;
    }
    case 27: {
      P({ id: "DRIVER" }, [57.6, 1.42, 1.7], { expr: t > 64.4 ? "relief" : "nervous", mode: "sit", look: 0.2, blob: false, headTilt: t > 64.4 ? -6 : 0,
        armL: { x: -0.1, y: 0.5, front: true }, armR: t > 64.4 ? keys(t, [[64.4, { x: -0.1, y: 0.5, front: true }], [64.7, FACEP]]) : { x: -0.1, y: 0.5, front: true } });
      if (t > 64.4) puff(out, t, 64.45, 1.0, [56.9, 2.55, 1.55], 0.8);
      break;
    }
    case 29: {
      for (let i = 0; i < 4; i++) kid(i, [BOARD[0] - 4.5 + i * 3.0, 0.1, BOARD[2] + 2.4 + (i % 2)], t > 69.3 ? "shock" : "neutral", { armL: t > 69.3 ? UP : REST, armR: t > 69.3 ? UP : REST });
      burst(out, t, 69.3, 0.5, [BOARD[0], 6.4, BOARD[2] + 0.6], 7, "#ffe7a0");
      break;
    }
    case 30: {
      for (let i = 0; i < 4; i++) P({ id: "FOLK", o: FOLK[i], seed: i + 2, i: i + 40 }, [ARROW[0] + 8 + i * 2.6, 0.0, 3.0 + (i % 2) * 1.5], { expr: "shock", look: 0.2, headTilt: -8, armL: i % 2 ? FACEP : UP, armR: i % 2 ? UP : SHRUG });
      const h = arrowH(t);
      if (t > 70.9) pop(out, t, 71.2, 75.05, [ARROW[0] + 3, Math.min(h * 0.75, 40), ARROW[2] + 5], 3.2, "+9,900%", "#ffffff", "#e2453c", 0.08);
      if (t > 70.9 && t < 71.6) burst(out, t, 70.9, 0.7, [ARROW[0], 2.5, ARROW[2] + 1.5], 10, "#ffe7a0");
      break;
    }
    case 32: {
      P({ id: "BUDDY" }, R("dorm", -2.0, 0, -0.4), { expr: "grin", mode: "sit", look: 0.6, facing: 1, armL: SHRUG, talkSide: 1 });
      break;
    }
  }
  return out;
};
