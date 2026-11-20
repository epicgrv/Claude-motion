// Our cast as lit flat cards in the 3D world + unlit 2D effect cards, staged per shot. Mouths flap on the voiceover
// words of whoever speaks (stepped at 12 fps like the reference), blinks every 0.5-2.3 s.
import * as THREE from "three";
import { Pen, bodyFront, Outfit, Expr, FrontOpts, Prop, INK, KID, SKINS, townsfolk, fxBurst, fxPuff, fxStars, fxShadow, fxContact } from "../bridge/toon";
import { Place, FxPlace } from "../bridge/cast";
import { LINES } from "./vo";
import { FPS, Light, BOARD, ARROW, arrowH } from "./story";
import { ROOM, A, V3 } from "./sets";

export type Stage = { places: Place[]; fx: FxPlace[] };

// ---------------- the cast ----------------
const JOHN: Outfit = { jacket: "#3f7fd0", pants: "#3b3f52", boots: "#f4f1ea", hat: "hair", hair: "#5a3b2a" };
const BUDDY: Outfit = { jacket: "#f08a2c", pants: "#56607a", boots: "#e2453c", hat: "cap", cap: "#2fa05a", build: "stout", skin: "#c99067" };
const TEEN: Outfit = { jacket: "#c0353a", pants: "#2f3550", boots: "#f4f1ea", hat: "hair", hair: "#e8c45a", build: "kid", skin: "#f5c9a0" };
const EXEC: Outfit = { jacket: "#2b3448", pants: "#2b3448", boots: INK, hat: "hair", hair: "#c9c9d1", moustache: "#8a8a96", build: "stout", buttons: "#e8c45a" };
const ASSIST: Outfit = { jacket: "#5a4a8c", pants: "#3b3f52", boots: "#4a3426", hat: "hair", hair: "#2a201a", skin: "#ecd0b6" };
const JUDGE: Outfit = { jacket: "#1e1e26", pants: "#1e1e26", boots: INK, hat: "hair", hair: "#f1efe6", moustache: "#f1efe6", build: "stout", skin: "#ecd0b6" };
const DRIVER: Outfit = { jacket: "#e8b33a", pants: "#3b3f52", boots: INK, hat: "cap", cap: "#2f5f6a", moustache: "#4a3020", build: "stout", skin: "#f5c9a0" };
const INV: Outfit[] = ["#3f6fb5", "#8c3b4a", "#2f5f6a", "#5d7a3a", "#7b5ac9"].map((c, i) => ({
  jacket: c, pants: "#2b2b34", boots: INK, hat: i % 2 ? "tophat" : "hair", hair: ["#5a3b2a", "#2a201a", "#c9c9d1", "#8a5a3c", "#e8c45a"][i],
  moustache: i === 1 || i === 2 ? "#3a2a20" : undefined, build: i % 2 ? "stout" : "adult", skin: SKINS[(i + 1) % 4], buttons: "#e8c45a",
}));
const KIDS: Outfit[] = ["#f08a2c", "#3fae8a", "#7b5ac9", "#e2453c", "#3f7fd0", "#e8b33a"].map((c, i) => ({ ...KID, jacket: c, cap: ["#e2453c", "#3f6fb5", "#f2c94c"][i % 3], skin: SKINS[i % 4], hat: i % 2 ? "cap" : "hair", hair: "#5a3b2a" }));
const FOLK = [0, 1, 2, 3, 4, 5].map((v) => townsfolk(v));
type CharId = "JOHN" | "BUDDY" | "TEEN" | "EXEC" | "INVESTOR" | string;
const OUT: Record<string, Outfit> = { JOHN, BUDDY, TEEN, EXEC, ASSIST, JUDGE, DRIVER };
const SEED: Record<string, number> = { JOHN: 3, BUDDY: 6, TEEN: 2, EXEC: 5, ASSIST: 1, JUDGE: 4, DRIVER: 7 };

// ---------------- life ----------------
const hh = (i: number, s = 0) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };
const LID = [0.5, 1, 1, 0.5];
const lidAt = (t: number, i: number) => {
  const f = Math.round(t * FPS);
  let s = Math.round(-60 * hh(i, 9));
  for (let n = 0; s <= f && n < 600; n++) {
    const k = f - s;
    if (k >= 0 && k < 4) return LID[k];
    s += Math.round(15 + 54 * hh(i * 31 + n, 13));
  }
  return 0;
};
/** is `who` mouth-open at t? stepped at 12 fps; open on ~60 % of each syllable beat inside a word */
const talking = (who: string, t: number) => {
  const ts = Math.floor(t * 12) / 12;
  for (const l of LINES) {
    if (l.who !== who || ts < l.s - 0.05 || ts > l.e + 0.05) continue;
    for (const w of l.words) if (ts >= w.s && ts < w.e + 0.04) return Math.floor((ts - w.s) * 12) % 3 !== 2;
    return false;
  }
  return false;
};
const speaking = (who: string, t: number) => LINES.some((l) => l.who === who && t >= l.s - 0.1 && t <= l.e + 0.1);

// ---------------- drawing helpers ----------------
const q = (v: number, n = 120) => Math.round(v * n) / n;
const fkey = (o: object) => JSON.stringify(o, (_k, v) => (typeof v === "number" ? q(v) : v));
const tier = (d: number): [number, number, number] => (d < 3.0 ? [1200, 2000, 2.0] : d < 6.5 ? [900, 1500, 1.5] : d < 16 ? [480, 800, 0.8] : [240, 400, 0.4]);
export type CamInfo = { pos: THREE.Vector3; right: THREE.Vector3; sun: THREE.Vector3 };
const light2D = (cam: CamInfo) => Math.round(Math.atan2(-cam.sun.y, cam.sun.dot(cam.right)) / (Math.PI / 4)) * (Math.PI / 4);
const tmp = new THREE.Vector3();

type Who = { id: string; o?: Outfit; seed?: number; i?: number };
type Act = { expr?: Expr; talk?: Expr; mode?: FrontOpts["mode"]; look?: number; facing?: -1 | 0 | 1; prop?: Prop; wave?: number; tilt?: number; headTilt?: number; phase?: number; scale?: number; blob?: boolean };

const blob = (out: Stage, cam: CamInfo, x: number, y: number, z: number, sc: number, light: Light) => {
  const hl = Math.hypot(cam.sun.x, cam.sun.z) || 1, ox = -cam.sun.x / hl, oz = -cam.sun.z / hl, rot = Math.atan2(-ox, -oz);
  if (light === "day") {
    const el = Math.asin(Math.min(0.99, Math.max(0.1, cam.sun.y)));
    const len = Math.min(2.4, Math.max(0.5, 1.6 / Math.tan(el))) * sc, h = len + 0.55 * sc, c = 0.3 * h;
    out.fx.push({ key: "blob|shadow|#a9adc4", cw: 128, ch: 256, draw: (p) => fxShadow(p, "#a9adc4"), x: x + ox * c, y: y + 0.018, z: z + oz * c, w: 0.72 * sc, h, flat: true, rot });
  }
  out.fx.push({ key: "blob|contact|#7a7c9a", cw: 128, ch: 128, draw: (p) => fxContact(p, "#7a7c9a"), x, y: y + 0.022, z, w: 0.52 * sc, h: 0.4 * sc, flat: true, rot });
};

/** put a character in the world at (x, y, z) facing the camera */
const person = (out: Stage, cam: CamInfo, t: number, light: Light, who: Who, p: V3, a: Act = {}) => {
  const o = who.o ?? OUT[who.id], seed = who.seed ?? SEED[who.id] ?? 1, idx = who.i ?? seed;
  const sc = a.scale ?? 1;
  const d = cam.pos.distanceTo(tmp.set(p[0], p[1] + 1.3 * sc, p[2])) / sc;
  const [w, h, k] = tier(d);
  const base = a.expr ?? "neutral";
  const expr: Expr = talking(who.id, t) ? a.talk ?? openOf(base) : speaking(who.id, t) ? closedOf(base) : base;
  const fo: FrontOpts = {
    expr, mode: a.mode ?? "stand", look: a.look ?? 0, facing: a.facing ?? 0, prop: a.prop ?? null, wave: a.wave, tilt: a.tilt ?? 0, headTilt: a.headTilt ?? 0,
    phase: a.phase ?? 0, blink: lidAt(t, idx), light: light2D(cam), seed,
  };
  out.places.push({ key: `F|${who.id}${who.i ?? ""}|${fkey(fo)}`, x: p[0], y: p[1], z: p[2], scale: sc, draw: (pp: Pen) => bodyFront(pp, o, fo), size: [w, h, k] });
  if (a.blob !== false) blob(out, cam, p[0], p[1], p[2], sc, light);
};
const openOf = (e: Expr): Expr => (e === "laugh" ? "laugh" : e === "shock" ? "shock" : e === "grin" || e === "smile_closed" || e === "relief" ? "relief_open" : e === "nervous" ? "shock" : "relief_open");
const closedOf = (e: Expr): Expr => (e === "laugh" ? "grin" : e === "shock" ? "nervous" : e === "relief_open" ? "smile_closed" : e);

/** unlit 2D effect cards */
const burst = (out: Stage, t: number, t0: number, dur: number, p: V3, size: number, col = "#fff3b0") => {
  const u = (t - t0) / dur; if (u < 0 || u > 1) return;
  const uq = q(u, 15);
  out.fx.push({ key: `burst${col}${uq}`, cw: 500, ch: 500, draw: (pp) => fxBurst(pp, uq, col, 12), x: p[0], y: p[1], z: p[2], w: size, h: size });
};
const puff = (out: Stage, t: number, t0: number, dur: number, p: V3, size: number) => {
  const u = (t - t0) / dur; if (u < 0 || u > 1) return;
  const uq = q(u, 15);
  out.fx.push({ key: `puff${uq}`, cw: 300, ch: 300, draw: (pp) => fxPuff(pp, uq), x: p[0], y: p[1], z: p[2], w: size, h: size, soft: true });
};
/** comic word / label popping in with overshoot (unlit card) */
const pop = (out: Stage, t: number, t0: number, t1: number, p: V3, h: number, text: string, fg = "#ffffff", bg = "#e2453c", rot = 0) => {
  if (t < t0 || t > t1) return;
  const u = Math.min(1, (t - t0) / 0.18), s = u < 1 ? 0.3 + 0.95 * u : 1 + 0.06 * Math.sin((t - t0) * 9) * Math.exp(-(t - t0) * 3);
  const cw = Math.max(400, 110 * text.length + 120), ch = 240;
  out.fx.push({ key: `pop|${text}|${bg}`, cw, ch, draw: (pp) => drawPop(pp.g, cw, ch, text, fg, bg), x: p[0], y: p[1], z: p[2], w: (h * cw / ch) * s, h: h * s, rot });
};
const drawPop = (g: CanvasRenderingContext2D, W: number, H: number, text: string, fg: string, bg: string) => {
  g.fillStyle = bg; g.strokeStyle = INK; g.lineWidth = 14;
  g.beginPath(); g.roundRect(10, 10, W - 20, H - 20, 40); g.fill(); g.stroke();
  g.font = '900 150px "Arial Black", Arial, sans-serif'; g.textAlign = "center"; g.textBaseline = "middle";
  let sc = 1; const mw = g.measureText(text).width; if (mw > W - 80) sc = (W - 80) / mw;
  g.save(); g.translate(W / 2, H / 2 + 8); g.scale(sc, 1);
  g.lineWidth = 18; g.strokeStyle = INK; g.strokeText(text, 0, 0); g.fillStyle = fg; g.fillText(text, 0, 0); g.restore();
};
/** speed lines streaming from a point (unlit, see-through) */
const speed = (out: Stage, t: number, p: V3, size: number) => {
  const k = Math.floor(t * 12) % 4;
  out.fx.push({ key: `speed${k}`, cw: 512, ch: 512, soft: true, draw: (pp) => {
    const g = pp.g; g.strokeStyle = "rgba(255,255,255,0.85)"; g.lineCap = "round";
    for (let i = 0; i < 26; i++) { const a = (i / 26) * Math.PI * 2 + k * 0.4 + hh(i, k) * 0.2, r0 = 150 + 60 * hh(i, k + 3), r1 = 256 * 1.4;
      g.lineWidth = 3 + 6 * hh(i, k + 7); g.beginPath(); g.moveTo(256 + r0 * Math.cos(a), 256 + r0 * Math.sin(a)); g.lineTo(256 + r1 * Math.cos(a), 256 + r1 * Math.sin(a)); g.stroke(); }
  }, x: p[0], y: p[1], z: p[2], w: size, h: size });
};
const sweat = (out: Stage, t: number, p: V3, size: number) => {
  const k = Math.floor(t * 8) % 2;
  out.fx.push({ key: `sweat${k}`, cw: 200, ch: 200, draw: (pp) => {
    const g = pp.g; g.fillStyle = "#bfe8ff"; g.strokeStyle = INK; g.lineWidth = 10;
    for (const [x, y] of [[60, 70 + k * 12], [140, 110 - k * 10]]) { g.beginPath(); g.moveTo(x, y - 40); g.quadraticCurveTo(x + 30, y + 10, x, y + 26); g.quadraticCurveTo(x - 30, y + 10, x, y - 40); g.fill(); g.stroke(); }
  }, x: p[0], y: p[1], z: p[2], w: size, h: size });
};
const coupon = (out: Stage, i: number, p: V3, rot: number, size: number) => {
  out.fx.push({ key: "couponFx", cw: 320, ch: 160, draw: (pp) => {
    const g = pp.g; g.fillStyle = "#fff4c2"; g.fillRect(4, 4, 312, 152); g.setLineDash([10, 8]); g.strokeStyle = INK; g.lineWidth = 6; g.strokeRect(10, 10, 300, 140); g.setLineDash([]);
    g.fillStyle = "#d8323c"; g.font = '900 64px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("FREE", 160, 62);
    g.fillStyle = "#1d4fb8"; g.font = '900 40px "Arial Black", Arial'; g.fillText("SODA!", 160, 116);
  }, x: p[0], y: p[1], z: p[2], w: size, h: size / 2, rot });
};
const R = (k: keyof typeof ROOM, x: number, y: number, z: number): V3 => [x + ROOM[k], y, z];

// ---------------- staging per shot ----------------
export const stage = (id: number, t: number, light: Light, cam: CamInfo): Stage => {
  const out: Stage = { places: [], fx: [] };
  const P = (who: Who, p: V3, a?: Act) => person(out, cam, t, light, who, p, a);
  const step = (v: number) => Math.floor(v * 12) / 12; // stepped animation
  switch (id) {
    case 1: { // John cramming a giant cheque into the mailbox
      P({ id: "JOHN" }, [2.55, 0.15, -6.1], { expr: "grin", look: 0.6, facing: 1, tilt: -0.05 + 0.04 * Math.sin(step(t) * 9) });
      if (t > 1.6) sweat(out, t, [2.2, 1.95, -6.0], 0.3);
      break;
    }
    case 2: {
      const k = t > 3.6;
      P({ id: "JOHN" }, [5.6, 0.15, -4.6], { expr: k ? "shock" : "grin", look: k ? -0.4 : 0.3, headTilt: k ? -0.15 : 0, facing: -1 });
      if (t > 4.0 && t < 4.7) speed(out, t, [-8, 8, -3], 16);
      break;
    }
    case 3: case 4: case 5: case 10: {
      const [jx, , jz] = A.jetLawn;
      const kid = (i: number, x: number, z: number, e: Expr) => P({ id: "KID", o: KIDS[i], seed: i + 1, i }, [x, 0.1, z], { expr: e, look: 0.3 * Math.sin(i), wave: e === "laugh" ? 0.5 + 0.5 * Math.sin(step(t) * 10 + i) : undefined });
      if (id === 3) {
        for (let i = 0; i < 6; i++) kid(i, jx - 9 + i * 3.4 + (i % 2) * 0.6, jz + 6.5 + (i % 3) * 0.9, t > 8.6 ? "laugh" : "shock");
        if (t > 8.55) puff(out, t, 8.55, 0.8, [jx, 0.6, jz + 3], 6);
      }
      if (id === 4) {
        P({ id: "TEEN" }, [71.6, 2.95, -14.65], { expr: "grin", talk: "relief_open", look: -0.3, wave: 0.6 + 0.4 * Math.sin(step(t) * 12), blob: false });
        kid(2, 73.5, -12.2, "laugh"); kid(4, 69.4, -11.5, "laugh");
      }
      if (id === 5) {
        for (let i = 0; i < 4; i++) kid(i, BOARD[0] - 5 + i * 3.3, BOARD[2] + 2.2 + (i % 2), t > 11.3 ? "shock" : "neutral");
        burst(out, t, 11.2, 0.45, [BOARD[0], 1.2, BOARD[2] + 0.8], 4.5, "#ffe7a0");
        puff(out, t, 11.22, 0.9, [BOARD[0] - 2.5, 0.5, BOARD[2] + 0.6], 3.5); puff(out, t, 11.22, 0.9, [BOARD[0] + 2.8, 0.5, BOARD[2] + 0.6], 3.5);
      }
      if (id === 10) for (let i = 0; i < 3; i++) kid(i + 2, BOARD[0] - 3 + i * 3.5, BOARD[2] + 3.2, "shock");
      break;
    }
    case 6: {
      P({ id: "BUDDY" }, R("dorm", -2.2, 0, -0.6), { expr: "shock", talk: "shock", mode: "sit", look: 0.5, facing: 1 });
      P({ id: "JOHN" }, R("dorm", 2.4, 0, -3.0), { expr: "smile", look: -0.6, facing: -1 });
      break;
    }
    case 7: {
      P({ id: "JOHN" }, R("dorm", 2.05, 0, -3.55), { expr: t > 16.6 ? "grin" : "stern", look: 0.8, facing: 1, headTilt: 0.12 });
      // magnifier over the page
      out.fx.push({ key: "magnifier", cw: 400, ch: 600, draw: (pp) => {
        const g = pp.g; g.lineWidth = 26; g.strokeStyle = "#6a4a2c"; g.beginPath(); g.moveTo(200, 360); g.lineTo(200, 580); g.stroke();
        g.fillStyle = "rgba(200,230,255,.45)"; g.strokeStyle = INK; g.lineWidth = 22; g.beginPath(); g.arc(200, 200, 160, 0, 7); g.fill(); g.stroke();
        g.strokeStyle = "rgba(255,255,255,.8)"; g.lineWidth = 14; g.beginPath(); g.arc(200, 200, 118, 3.6, 4.4); g.stroke();
      }, x: ROOM.dorm + 2.85 + 0.03 * Math.sin(step(t) * 7), y: 1.22, z: -3.45, w: 0.28, h: 0.42, rot: -0.4 });
      if (t > 16.6) pop(out, t, 16.75, 17.55, R("dorm", 2.0, 2.05, -3.4), 0.28, "!!", "#ffffff", "#e2453c", 0.1);
      break;
    }
    case 8: break; // coin + page (sets)
    case 9: {
      P({ id: "JOHN" }, R("dorm", 2.4, 0, -4.2), { expr: t > 21.5 ? "shock" : "stern", look: 0.6, facing: 1 });
      break;
    }
    case 11: {
      for (let i = 0; i < 5; i++) {
        const sh = t > 25.6;
        P({ id: "FOLK", o: FOLK[i], seed: i + 2, i: i + 10 }, [-36 + i * 3.0, 0.15, 7.6 + (i % 2) * 0.9], { expr: sh ? (i % 2 ? "shock" : "laugh") : "smile", wave: sh && i % 2 === 0 ? 0.5 + 0.5 * Math.sin(step(t) * 11 + i) : undefined, look: 0.4 * Math.sin(i * 2) });
      }
      break;
    }
    case 12: case 13: {
      P({ id: "JOHN" }, R("class", 2.9, 0, -5.2), { expr: "grin", talk: "relief_open", look: -0.6, facing: -1, wave: id === 13 ? 0.8 + 0.2 * Math.sin(step(t) * 6) : 0.3 });
      if (id === 12) P({ id: "BUDDY" }, R("class", -1.4, 0, -1.75), { expr: "nervous", mode: "sit", look: 0.4, blob: false });
      break;
    }
    case 14: {
      P({ id: "BUDDY" }, R("class", -1.4, 0, -1.75), { expr: "shock", talk: "shock", mode: "sit", look: 0, blob: false, headTilt: 0.1 * Math.sin(step(t) * 20) });
      sweat(out, t, R("class", -1.0, 1.75, -1.6), 0.25);
      break;
    }
    case 15: case 16: case 17: {
      for (let i = 0; i < 5; i++) P({ id: i === 2 ? "INVESTOR" : "INV", o: INV[i], seed: 1 + ((i * 3) % 7), i: i + 20 }, R("board", -3.2 + i * 1.6, 0, -3.0), { expr: i === 2 && id >= 16 ? "nervous" : i % 2 ? "grin" : "smile", look: id === 17 ? 0.8 : 0.3 * Math.sin(i), blob: false });
      P({ id: "JOHN" }, R("board", 4.6, 0, -1.4), { expr: id === 17 ? "grin" : "smile_closed", talk: "relief_open", look: -0.7, facing: -1, headTilt: id === 17 ? 0.18 : 0 });
      if (id === 17) pop(out, t, 37.0, 37.6, R("board", 4.0, 2.55, -1.2), 0.3, "?", "#ffffff", "#3f7fd0");
      break;
    }
    case 18: {
      P({ id: "JOHN" }, [2.55, 0.15, -6.1], { expr: "smile_closed", look: 0.6, facing: 1 });
      if (t > 40.3) pop(out, t, 40.3, 41.7, [3.9, 1.9, -6.9], 0.32, "+$8.50 S&H", "#241726", "#fff36b", 0.08);
      break;
    }
    case 19: {
      pop(out, t, 43.15, 44.3, [-124.5, 22.4, -19.9], 3.6, "CRIMINAL?!", "#ffffff", "#241726", -0.08);
      break;
    }
    case 20: case 21: {
      P({ id: "EXEC" }, R("office", -0.1, 0.05, -3.0), { expr: "laugh", talk: "laugh", look: 0, tilt: 0.06 * Math.sin(step(t) * 14), blob: false });
      if (id === 20) P({ id: "ASSIST" }, R("office", 1.7, 0, -2.4), { expr: "laugh", look: -0.6, facing: -1, tilt: -0.06 * Math.sin(step(t) * 13) });
      if (id === 21) pop(out, t, 46.45, 48.2, R("office", -0.75, 2.45, -2.6), 0.32, "HA HA HA", "#ffffff", "#e2453c", -0.1);
      break;
    }
    case 22: {
      P({ id: "JOHN" }, [0, 0.1, -7.75], { expr: t > 49.7 ? (t > 52.3 ? "smile" : "dazed") : "neutral", mode: "sit", look: 0.3 });
      // coupons raining
      for (let i = 0; i < 9; i++) {
        const t0 = 49.5 + i * 0.25; if (t < t0) continue;
        const u = Math.min(1, (t - t0) / 1.6);
        const x = -1.2 + (i * 0.37) % 2.4 + 0.25 * Math.sin((t - t0) * 4 + i), y = 3.0 - 2.75 * u + 0.12 * (i % 3), z = -7.4 + 0.25 * (i % 3);
        coupon(out, i, [x, y, z], 0.6 * Math.sin((t - t0) * 3 + i), 0.42);
      }
      pop(out, t, 52.4, 53.75, [0.55, 2.05, -7.5], 0.3, "+1 POINT", "#ffffff", "#1d4fb8", 0.08);
      break;
    }
    case 23: P({ id: "JOHN" }, [-74.2, 0.15 + Math.min(1.2, Math.max(0, (t - 53.8) * 0.9)), 13.5 + Math.min(4.8, Math.max(0, (t - 53.8) * 3.6))], { mode: "stroll", phase: step(t) * 1.6, expr: "stern", look: 0 }); break;
    case 24: case 25: case 26: {
      const strike = id === 26 ? (t < 61.98 ? 0 : Math.min(1, (t - 61.98) / 0.06)) : 0;
      P({ id: "JUDGE" }, R("court", 0, 0.85, -5.1), { expr: id === 26 ? "stern" : "stern", look: id === 25 ? 0.7 : 0, blob: false, prop: id === 26 ? ["hammer", strike] : null });
      if (id === 24) P({ id: "JOHN" }, R("court", -2.4, 0, -0.5), { expr: t > 57 ? "nervous" : "smile", look: -0.3, facing: 1 });
      if (id === 25 || id === 24) {
        P({ id: "BUDDY" }, R("court", 2.5, 0, 2.35), { expr: "grin", talk: "relief_open", mode: id === 25 ? "stand" : "sit", wave: id === 25 ? 0.9 + 0.1 * Math.sin(step(t) * 9) : undefined, blob: false });
        for (let i = 0; i < 3; i++) P({ id: "FOLK", o: FOLK[i + 2], seed: i + 3, i: i + 30 }, R("court", -4.2 + i * 1.3 + (i > 1 ? 4.6 : 0), 0, 2.15 + (i % 2) * 1.6), { expr: id === 25 ? "nervous" : "neutral", mode: "sit", look: 0.6, blob: false });
      }
      if (id === 26) { burst(out, t, 62.0, 0.4, R("court", 0.6, 1.75, -4.75), 1.3, "#fff3b0"); pop(out, t, 62.1, 63.4, R("court", 0.55, 2.4, -3.6), 0.3, "LOST", "#ffffff", "#e2453c", 0.1); }
      break;
    }
    case 27: {
      P({ id: "DRIVER" }, [57.6, 1.42, 1.7], { expr: t > 64.4 ? "relief" : "nervous", mode: "sit", look: 0.2, blob: false, headTilt: t > 64.4 ? -0.1 : 0 });
      if (t > 64.4) puff(out, t, 64.45, 1.0, [56.9, 2.55, 1.55], 0.8);
      break;
    }
    case 28: break;
    case 29: {
      for (let i = 0; i < 4; i++) P({ id: "KID", o: KIDS[i], seed: i + 1, i }, [BOARD[0] - 4.5 + i * 3.0, 0.1, BOARD[2] + 2.4 + (i % 2)], { expr: t > 69.3 ? "shock" : "neutral", look: 0.3 * Math.sin(i) });
      burst(out, t, 69.3, 0.5, [BOARD[0], 6.4, BOARD[2] + 0.6], 7, "#ffe7a0");
      break;
    }
    case 30: {
      for (let i = 0; i < 4; i++) P({ id: "FOLK", o: FOLK[i], seed: i + 2, i: i + 40 }, [ARROW[0] + 8 + i * 2.6, 0.0, 3.0 + (i % 2) * 1.5], { expr: "shock", look: 0.2, headTilt: -0.15 });
      const h = arrowH(t);
      if (t > 70.9) pop(out, t, 71.2, 75.05, [ARROW[0] + 3, Math.min(h * 0.75, 40), ARROW[2] + 5], 3.2, "+9,900%", "#ffffff", "#e2453c", 0.08);
      if (t > 70.9 && t < 71.6) burst(out, t, 70.9, 0.7, [ARROW[0], 2.5, ARROW[2] + 1.5], 10, "#ffe7a0");
      break;
    }
    case 31: break;
    case 32: {
      P({ id: "BUDDY" }, R("dorm", -2.0, 0, -0.4), { expr: "grin", talk: "relief_open", mode: "sit", look: 0.6, facing: 1 });
      break;
    }
  }
  return out;
};
