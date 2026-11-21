// The cut: 31 shots timed to the voiceover (seconds), each a camera move through the one 3D world.
// Camera = eased dolly between two poses + impact kicks (decaying shake) + a faint handheld drift.
import { ROOM, A, V3 } from "./sets";
import { VO_DUR } from "./vo";

export const FPS = 30;
export const TOTAL = Math.ceil((VO_DUR + 0.25) * FPS);
export type Light = "day" | "golden";
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type Key = { p0: V3; l0: V3; p1?: V3; l1?: V3; fov?: [number, number] | number; roll?: [number, number] | number; ease?: "io" | "o" | "i" | "lin" };
export type Shot = { id: number; name: string; s: number; e: number; off?: number; light: Light; cam: Key | ((t: number, u: number) => Cam); dof: number; sunAz?: number; sunEl?: number };

const X = (k: keyof typeof ROOM, p: V3): V3 => [p[0] + ROOM[k], p[1], p[2]];
const [JX, , JZ] = A.jetLawn;
export const BOARD: V3 = [JX - 4, 0.1, JZ + 4.5]; // price board base (faces +z toward the road)
/** v5: the jet lands on the school roof here (nose +x) */
export const ROOF_JET: V3 = [70, 11.62, -32.5];
/** hook jet pass: nose-first down the street toward +x, overhead at t = 3.1 */
export const jetHero = (t: number): V3 => [5 - 68 * (3.1 - t), 8.0 + 1.6 * (3.1 - t), -1.2];
/** roof landing (shot 105): decelerating approach, flare, vertical settle at 9.05..9.55 */
export const jetLand = (t: number): { p: V3; pitch: number; noz: number } => {
  const u = Math.min(1, Math.max(0, (t - 7.05) / 2.0)), e = 1 - (1 - u) ** 2.4;
  const x = 8 + (ROOF_JET[0] - 8) * e, yA = 27 - (27 - 14.4) * e;
  const v = Math.min(1, Math.max(0, (t - 9.05) / 0.5)), y = v > 0 ? 14.4 - (14.4 - ROOF_JET[1]) * (v * v * (3 - 2 * v)) : yA;
  return { p: [x, y, ROOF_JET[2]], pitch: -0.18 * Math.sin(Math.PI * Math.min(1, u * 1.15)) * (1 - v), noz: -1.3 * (1 - Math.min(1, u * 1.3)) };
};
/** jet flight in S2: passes overhead at t = 4.4 */
export const jetPass = (t: number): V3 => [8 - 62 * (4.4 - t), 9.5 + 0.8 * (4.4 - t), -3.0];
/** arrow tip height in S29 */
export const arrowH = (t: number) => (t < 70.9 ? 0 : 4 + 90 * Math.pow(Math.min(1, (t - 70.9) / 3.6), 0.7));
export const ARROW: V3 = [-44, 0, -1];

export const SHOTS: Shot[] = [
  // ---- hook (v5): topic + contrast in the first 2 s ----
  { id: 101, name: "kid shows cheque", s: 0, e: 1.9, light: "day", dof: 10,
    cam: { p0: [4.6, 0.7, 2.4], l0: [2.2, 1.35, -5.4], p1: [3.0, 1.3, -2.3], l1: [2.25, 1.45, -5.4], fov: [46, 36], roll: [-0.05, 0.0], ease: "o" } },
  { id: 102, name: "jet hero", s: 1.9, e: 3.45, light: "day", dof: 0,
    cam: (t) => {
      const j = jetHero(t), k = Math.min(1, Math.max(0, (t - 2.0) / 1.2));
      const base: V3 = [-40, 7, -2];
      return { pos: [9, 1.0, 1.6], look: [base[0] + (j[0] - base[0]) * k, base[1] + (j[1] - base[1]) * k * 0.9, base[2]], fov: 48, roll: 0.04 * k };
    } },
  { id: 103, name: "cheque close", s: 3.45, e: 5.18, light: "day", dof: 12,
    cam: { p0: [2.4, 1.4, -2.6], l0: [2.2, 1.1, -5.4], p1: [2.35, 1.38, -3.0], l1: [2.2, 1.12, -5.4], fov: [42, 40], ease: "io" } },
  { id: 104, name: "tv loophole", s: 5.18, e: 7.05, light: "day", dof: 6, sunAz: 160, sunEl: 62,
    cam: { p0: X("dorm", [0.4, 1.5, 1.4]), l0: X("dorm", [0.4, 1.5, -4.5]), p1: X("dorm", [0.4, 1.47, -2.3]), l1: X("dorm", [0.4, 1.46, -4.5]), fov: [42, 40], ease: "io" } },
  { id: 105, name: "roof landing", s: 7.05, e: 9.68, light: "day", dof: 0,
    cam: (t) => {
      const u = Math.min(1, Math.max(0, (t - 7.05) / 2.63)), e = u * u * (3 - 2 * u), j = jetLand(t).p;
      return { pos: [58 + 26 * e, 5 + 9 * e, 8 - 4 * e], look: [j[0] * 0.8 + ROOF_JET[0] * 0.2, j[1] - 0.5, j[2] * 0.7 + ROOF_JET[2] * 0.3], fov: 50 - 6 * e, roll: 0 };
    } },
  { id: 106, name: "teen roof", s: 9.68, e: 10.87, light: "day", dof: 8,
    cam: { p0: [80.6, 13.5, -31.2], l0: [76.2, 12.7, -25.6], p1: [80.0, 13.4, -30.4], l1: [76.2, 12.7, -25.6], fov: [44, 40], ease: "o" } },
  { id: 5, name: "price drop", s: 10.72, e: 12.9, light: "day", dof: 0,
    cam: { p0: [BOARD[0], 1.3, BOARD[2] + 10.5], l0: [BOARD[0], 5.0, BOARD[2]], p1: [BOARD[0] + 0.8, 1.2, BOARD[2] + 13], l1: [BOARD[0] + 0.4, 4.8, BOARD[2]], fov: [46, 50], ease: "o" } },
  // ---- dorm ----
  { id: 6, name: "buddy cans", s: 12.9, e: 15.33, light: "day", dof: 8, sunAz: 160, sunEl: 62,
    cam: { p0: X("dorm", [0.6, 1.45, 2.8]), l0: X("dorm", [-2.4, 1.1, -1.6]), p1: X("dorm", [-0.6, 1.25, 1.2]), l1: X("dorm", [-2.6, 1.05, -1.4]), fov: [42, 38], ease: "io" } },
  { id: 7, name: "fine print", s: 15.33, e: 17.55, light: "day", dof: 10, sunAz: 160, sunEl: 62,
    cam: { p0: X("dorm", [2.3, 1.45, 0.9]), l0: X("dorm", [1.75, 1.3, -2.6]), p1: X("dorm", [2.05, 1.42, -0.2]), l1: X("dorm", [1.72, 1.3, -2.6]), fov: [42, 40], ease: "io" } },
  { id: 8, name: "ten cents", s: 17.55, e: 19.85, light: "day", dof: 6, sunAz: 160, sunEl: 66,
    cam: { p0: X("dorm", [3.3, 2.35, -3.42]), l0: X("dorm", [3.3, 1.0, -3.76]), p1: X("dorm", [3.3, 2.2, -3.45]), l1: X("dorm", [3.3, 1.0, -3.76]), fov: [36, 34], ease: "io" } },
  { id: 9, name: "calculator", s: 19.85, e: 22.55, light: "day", dof: 14, sunAz: 160, sunEl: 62,
    cam: { p0: X("dorm", [4.12, 1.42, -3.3]), l0: X("dorm", [3.974, 1.03, -3.77]), p1: X("dorm", [4.06, 1.36, -3.38]), l1: X("dorm", [3.974, 1.03, -3.77]), fov: [40, 36], ease: "io" } },
  { id: 10, name: "worth 20M", s: 22.55, e: 24.7, light: "day", dof: 0,
    cam: { p0: [52, 15.5, -17], l0: [70, 13.2, -32.5], p1: [57, 14.6, -15.5], l1: [70.5, 13.4, -32.5], fov: [48, 44], ease: "io" } },
  { id: 11, name: "96% off", s: 24.7, e: 28.55, light: "day", dof: 4,
    cam: { p0: [-30, 7.5, -3.5], l0: [-30, 3.0, 10.4], p1: [-28.5, 1.7, -2.2], l1: [-30.5, 3.0, 10.4], fov: [44, 40], ease: "io" } },
  // ---- class ----
  { id: 12, name: "arbitrage wide", s: 28.55, e: 30.3, light: "day", dof: 4, sunAz: 170, sunEl: 64,
    cam: { p0: X("class", [1.0, 1.7, 5.0]), l0: X("class", [0.9, 1.9, -5.9]), p1: X("class", [0.9, 1.7, 3.6]), l1: X("class", [0.9, 1.95, -5.9]), fov: [48, 46], ease: "io" } },
  { id: 13, name: "arbitrage board", s: 30.3, e: 32.8, light: "day", dof: 6, sunAz: 170, sunEl: 64,
    cam: { p0: X("class", [2.4, 1.9, -0.4]), l0: X("class", [2.1, 1.95, -5.9]), p1: X("class", [2.2, 1.95, -1.5]), l1: X("class", [2.1, 1.95, -5.9]), fov: [46, 46], ease: "io" } },
  { id: 14, name: "insanity", s: 32.8, e: 33.9, light: "day", dof: 12, sunAz: 170, sunEl: 64,
    cam: { p0: X("class", [-1.1, 1.4, 0.7]), l0: X("class", [-1.4, 1.3, -1.75]), p1: X("class", [-1.2, 1.4, 0.3]), l1: X("class", [-1.4, 1.3, -1.75]), fov: [34, 30], roll: [0.08, -0.04], ease: "o" } },
  // ---- boardroom ----
  { id: 15, name: "five investors", s: 33.9, e: 35.68, light: "day", dof: 6, sunAz: 165, sunEl: 64,
    cam: { p0: X("board", [-4.2, 1.7, 2.6]), l0: X("board", [-1.8, 1.6, -3.2]), p1: X("board", [3.4, 1.7, 2.4]), l1: X("board", [1.6, 1.6, -3.2]), fov: [42, 42], ease: "io" } },
  { id: 16, name: "park it", s: 35.68, e: 36.8, light: "day", dof: 12, sunAz: 165, sunEl: 64,
    cam: { p0: X("board", [0.35, 1.85, -0.4]), l0: X("board", [0, 1.85, -3.2]), p1: X("board", [0.3, 1.85, -0.8]), l1: X("board", [0, 1.85, -3.2]), fov: [34, 32], ease: "o" } },
  { id: 17, name: "school?", s: 36.8, e: 37.6, light: "day", dof: 12, sunAz: 165, sunEl: 64,
    cam: { p0: X("board", [3.3, 1.8, 1.4]), l0: X("board", [4.6, 1.75, -1.4]), p1: X("board", [3.5, 1.8, 0.9]), l1: X("board", [4.6, 1.75, -1.4]), fov: [34, 31], roll: [-0.05, 0.03], ease: "o" } },
  // ---- the cheque ----
  { id: 18, name: "cheque 700,008.50", s: 37.6, e: 41.7, light: "day", dof: 12,
    cam: { p0: [3.4, 1.45, -3.2], l0: [3.15, 1.25, -6.7], p1: [3.35, 1.4, -3.8], l1: [3.2, 1.22, -6.7], fov: [42, 40], ease: "io" } },
  { id: 19, name: "HQ tower", s: 41.7, e: 44.3, light: "golden", dof: 0,
    cam: { p0: [-116, 1.4, -4], l0: [-130, 12, -31], p1: [-119, 2.4, -9], l1: [-130, 62, -31], fov: [50, 52], ease: "io" } },
  // ---- office ----
  { id: 20, name: "execs laugh", s: 44.3, e: 46.05, light: "day", dof: 6, sunAz: 165, sunEl: 62,
    cam: { p0: X("office", [0.8, 1.6, 2.4]), l0: X("office", [0.3, 1.5, -2.8]), p1: X("office", [0.3, 1.6, 0.2]), l1: X("office", [0.3, 1.55, -2.8]), fov: [42, 40], ease: "io" } },
  { id: 21, name: "commercial kid", s: 46.05, e: 48.2, light: "day", dof: 14, sunAz: 165, sunEl: 62,
    cam: { p0: X("office", [0.15, 1.75, -0.4]), l0: X("office", [-0.1, 1.6, -3.0]), p1: X("office", [0.12, 1.75, -0.8]), l1: X("office", [-0.1, 1.62, -3.0]), fov: [34, 30], roll: [0.04, -0.03], ease: "o" } },
  // ---- porch ----
  { id: 22, name: "coupons", s: 48.2, e: 53.75, light: "day", dof: 8,
    cam: { p0: [2.6, 1.15, -3.2], l0: [0.0, 1.0, -7.9], p1: [1.1, 1.0, -5.4], l1: [0.0, 1.0, -7.9], fov: [42, 36], ease: "io" } },
  // ---- court ----
  { id: 23, name: "courthouse", s: 53.75, e: 55.0, light: "day", dof: 0,
    cam: { p0: [-75, 0.9, 2.5], l0: [-75, 5, 16], p1: [-75, 2.4, 4.5], l1: [-75, 10, 17], fov: [50, 50], ease: "o" } },
  { id: 24, name: "judge rules", s: 55.0, e: 59.7, light: "day", dof: 6, sunAz: 170, sunEl: 66,
    cam: { p0: X("court", [0.6, 1.5, 3.4]), l0: X("court", [0, 2.0, -5]), p1: X("court", [0.3, 1.95, 0.4]), l1: X("court", [0, 2.15, -5]), fov: [44, 40], ease: "io" } },
  { id: 25, name: "unreasonable", s: 59.7, e: 61.8, light: "day", dof: 10, sunAz: 20, sunEl: 66,
    cam: { p0: X("court", [1.2, 1.55, -1.2]), l0: X("court", [2.5, 1.3, 2.1]), p1: X("court", [1.5, 1.5, -0.4]), l1: X("court", [2.5, 1.35, 2.1]), fov: [40, 36], ease: "io" } },
  { id: 26, name: "gavel", s: 61.8, e: 63.4, light: "day", dof: 12, sunAz: 170, sunEl: 66,
    cam: { p0: X("court", [1.0, 2.25, -1.5]), l0: X("court", [0.25, 1.95, -5.0]), p1: X("court", [0.85, 2.2, -2.1]), l1: X("court", [0.25, 1.95, -5.0]), fov: [38, 34], ease: "o" } },
  // ---- bus ----
  { id: 27, name: "bus driver", s: 63.4, e: 65.6, light: "day", dof: 10,
    cam: { p0: [52.2, 2.5, -0.2], l0: [57.4, 2.35, 1.6], p1: [53.4, 2.45, 0.4], l1: [57.4, 2.35, 1.65], fov: [36, 32], ease: "io" } },
  // ---- re-air ----
  { id: 28, name: "tv re-air", s: 65.6, e: 68.5, light: "day", dof: 6, sunAz: 160, sunEl: 62,
    cam: { p0: X("dorm", [0.4, 1.5, 1.8]), l0: X("dorm", [0.4, 1.42, -4.5]), p1: X("dorm", [0.4, 1.45, -2.5]), l1: X("dorm", [0.4, 1.45, -4.5]), fov: [42, 40], ease: "i" } },
  { id: 29, name: "700M", s: 68.5, e: 70.8, light: "day", dof: 0,
    cam: { p0: [BOARD[0] + 1, 1.6, BOARD[2] + 14], l0: [BOARD[0], 5.2, BOARD[2]], p1: [BOARD[0] + 0.5, 3.0, BOARD[2] + 11], l1: [BOARD[0], 5.4, BOARD[2]], fov: [46, 44], ease: "io" } },
  { id: 30, name: "inflation arrow", s: 70.8, e: 75.05, light: "day", dof: 0,
    cam: (t) => {
      const u = Math.min(1, Math.max(0, (t - 70.8) / 4.25)), e = u * u * (3 - 2 * u), h = arrowH(t);
      return { pos: [-28 + 2 * e, 1.5 + 1.0 * e, 7 + 2 * e], look: [ARROW[0] + 1, Math.max(5, h * 0.8), ARROW[2]], fov: 52 + 8 * e, roll: 0 };
    } },
  { id: 31, name: "just kidding", s: 75.05, e: 78.2, light: "day", dof: 0,
    cam: { p0: [BOARD[0] + 0.5, 4.6, BOARD[2] + 9], l0: [BOARD[0] + 0.6, 5.2, BOARD[2]], p1: [BOARD[0] + 1.53, 3.71, BOARD[2] + 1.9], l1: [BOARD[0] + 1.53, 3.71, BOARD[2]], fov: [44, 34], ease: "i" } },
  // ---- button ----
  { id: 32, name: "keeping the cans", s: 78.2, e: TOTAL / FPS, light: "day", dof: 8, sunAz: 160, sunEl: 62,
    cam: { p0: X("dorm", [-1.4, 1.3, 0.8]), l0: X("dorm", [-2.5, 1.2, -1.0]), p1: X("dorm", [-0.4, 1.7, 2.6]), l1: X("dorm", [-2.5, 1.4, -1.4]), fov: [36, 44], ease: "io" } },
];
// story shots keep their v4 timings; the v5 voice starts them 0.15 s later
const D = 0.15;
for (const sh of SHOTS) if (sh.id < 100) { sh.s += D; if (sh.id !== 32) sh.e += D; sh.off = D; }
export const shotAt = (t: number) => { let i = 0; while (i + 1 < SHOTS.length && t >= SHOTS[i + 1].s) i++; return SHOTS[i]; };

// ---------------- camera ----------------
const EASE = { io: (u: number) => u * u * (3 - 2 * u), o: (u: number) => 1 - (1 - u) ** 3, i: (u: number) => u * u * u, lin: (u: number) => u };
const lerp = (a: number, b: number, u: number) => a + (b - a) * u;
const L3 = (a: V3, b: V3, u: number): V3 => [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
/** impact kicks: time, strength (m of shake at the start), decay (1/s) */
export const KICKS: [number, number, number][] = [
  [0.02, 0.05, 6], [3.05, 0.12, 5], [4.3, 0.04, 8], [9.5, 0.08, 6],
  ...([[11.22, 0.09, 7], [29.6, 0.03, 8], [40.3, 0.025, 9], [46.44, 0.03, 6], [62.02, 0.08, 7], [69.3, 0.06, 7], [70.9, 0.1, 4], [77.2, 0.05, 8]] as [number, number, number][]).map(([a, b, c]) => [a + 0.15, b, c] as [number, number, number]),
];
const hash = (n: number) => { const v = Math.sin(n * 127.1) * 43758.5453; return v - Math.floor(v); };
const noise1 = (x: number, s: number) => { const i = Math.floor(x), f = x - i, w = f * f * (3 - 2 * f); return lerp(hash(i + s * 57), hash(i + 1 + s * 57), w) * 2 - 1; };

export const camAt = (f: number): Cam => {
  const t = f / FPS, s = shotAt(t), u = Math.min(1, Math.max(0, (t - s.s) / (s.e - s.s)));
  let c: Cam;
  if (typeof s.cam === "function") c = s.cam(t - (s.off ?? 0), u);
  else {
    const k = s.cam, e = EASE[k.ease ?? "io"](u);
    const fv = typeof k.fov === "number" ? [k.fov, k.fov] : k.fov ?? [40, 40], rl = typeof k.roll === "number" ? [k.roll, k.roll] : k.roll ?? [0, 0];
    c = { pos: L3(k.p0, k.p1 ?? k.p0, e), look: L3(k.l0, k.l1 ?? k.l0, e), fov: lerp(fv[0], fv[1], e), roll: lerp(rl[0], rl[1], e) };
  }
  // handheld drift (tiny) + kicks
  const d = Math.hypot(c.pos[0] - c.look[0], c.pos[1] - c.look[1], c.pos[2] - c.look[2]);
  let sx = 0.004 * d * noise1(t * 0.9, 1), sy = 0.003 * d * noise1(t * 0.8, 2), rr = 0;
  for (const [tk, a, dec] of KICKS) {
    if (t < tk || t > tk + 1.2) continue;
    const env = a * Math.exp(-dec * (t - tk));
    sx += env * Math.sin((t - tk) * 55) * 1.0; sy += env * Math.cos((t - tk) * 47) * 0.8; rr += env * 0.15 * Math.sin((t - tk) * 40);
  }
  c.look = [c.look[0] + sx, c.look[1] + sy, c.look[2]];
  c.roll += rr;
  return c;
};
export const shotIndexAt = (f: number) => shotAt(f / FPS).id;
