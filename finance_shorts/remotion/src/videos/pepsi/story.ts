// The cut: 31 shots timed to the voiceover (seconds), each a camera move through the one 3D world.
// Camera = eased dolly between two poses + impact kicks (decaying shake) + a faint handheld drift.
import { ROOM, A, V3 } from "./sets";
import { VO_DUR } from "./vo";

export const FPS = 30;
export const TOTAL = Math.ceil((VO_DUR + 0.25) * FPS);
export type Light = "day" | "golden";
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type Key = { p0: V3; l0: V3; p1?: V3; l1?: V3; fov?: [number, number] | number; roll?: [number, number] | number; ease?: "io" | "o" | "i" | "lin" };
export type Shot = { id: number; name: string; s: number; e: number; light: Light; cam: Key | ((t: number, u: number) => Cam); dof: number; sunAz?: number; sunEl?: number };

const X = (k: keyof typeof ROOM, p: V3): V3 => [p[0] + ROOM[k], p[1], p[2]];
const [JX, , JZ] = A.jetLawn;
export const BOARD: V3 = [JX - 4, 0.1, JZ + 4.5]; // price board base (faces +z toward the road)
/** jet flight in S2: passes overhead at t = 4.4 */
export const jetPass = (t: number): V3 => [8 - 62 * (4.4 - t), 11 + 0.8 * (4.4 - t), -1.5];
/** arrow tip height in S29 */
export const arrowH = (t: number) => (t < 70.9 ? 0 : 4 + 90 * Math.pow(Math.min(1, (t - 70.9) / 3.6), 0.7));
export const ARROW: V3 = [-58, 0, 0];

export const SHOTS: Shot[] = [
  // ---- hook ----
  { id: 1, name: "mailbox hook", s: 0, e: 2.55, light: "day", dof: 12,
    cam: { p0: [6.0, 0.7, 1.4], l0: [3.0, 1.3, -6.4], p1: [4.9, 0.85, -1.4], l1: [3.1, 1.25, -6.4], fov: [44, 38], roll: [-0.06, 0.02], ease: "o" } },
  { id: 2, name: "jet flyover", s: 2.55, e: 5.8, light: "day", dof: 0,
    cam: (t) => {
      const j = jetPass(t), k = Math.min(1, Math.max(0, (t - 3.2) / 1.6));
      const base: V3 = [-30, 8, -4], look: V3 = [base[0] + (j[0] - base[0]) * k * 0.95, base[1] + (j[1] - base[1]) * k * 0.95, base[2] + (j[2] - base[2]) * k];
      return { pos: [10, 1.1, 1.2], look, fov: 46, roll: 0.05 * Math.sin(t * 3) * k };
    } },
  { id: 3, name: "jet lands at school", s: 5.8, e: 9.5, light: "day", dof: 0,
    cam: { p0: [77, 1.2, 7.5], l0: [JX + 1, 7, JZ], p1: [74.5, 1.5, 3.5], l1: [JX + 1, 2.8, JZ], fov: [46, 42], ease: "io" } },
  { id: 4, name: "teen on jet", s: 9.5, e: 10.72, light: "day", dof: 10,
    cam: { p0: [68.2, 4.6, -21.0], l0: [71.6, 3.9, -14.6], p1: [69.0, 4.4, -20.0], l1: [71.6, 3.9, -14.6], fov: [36, 33], ease: "o" } },
  { id: 5, name: "price drop", s: 10.72, e: 12.9, light: "day", dof: 0,
    cam: { p0: [BOARD[0] + 1.5, 1.4, 3.2], l0: [BOARD[0] + 1, 6.4, BOARD[2]], p1: [BOARD[0] + 3, 1.2, 5.6], l1: [BOARD[0] + 1.5, 6.0, BOARD[2] - 2], fov: [46, 48], ease: "o" } },
  // ---- dorm ----
  { id: 6, name: "buddy cans", s: 12.9, e: 15.33, light: "day", dof: 8, sunAz: 160, sunEl: 62,
    cam: { p0: X("dorm", [0.6, 1.45, 2.8]), l0: X("dorm", [-2.4, 1.1, -1.6]), p1: X("dorm", [-0.6, 1.25, 1.2]), l1: X("dorm", [-2.6, 1.05, -1.4]), fov: [42, 38], ease: "io" } },
  { id: 7, name: "fine print", s: 15.33, e: 17.55, light: "day", dof: 10, sunAz: 160, sunEl: 62,
    cam: { p0: X("dorm", [4.6, 1.75, -0.6]), l0: X("dorm", [2.6, 1.25, -3.6]), p1: X("dorm", [4.0, 1.6, -1.6]), l1: X("dorm", [2.7, 1.2, -3.6]), fov: [40, 34], ease: "io" } },
  { id: 8, name: "ten cents", s: 17.55, e: 19.85, light: "day", dof: 6, sunAz: 160, sunEl: 66,
    cam: { p0: X("dorm", [3.25, 1.95, -3.0]), l0: X("dorm", [3.28, 1.0, -3.68]), p1: X("dorm", [3.3, 1.62, -3.35]), l1: X("dorm", [3.36, 1.0, -3.72]), fov: [34, 30], ease: "io" } },
  { id: 9, name: "calculator", s: 19.85, e: 22.55, light: "day", dof: 14, sunAz: 160, sunEl: 62,
    cam: { p0: X("dorm", [4.45, 1.42, -3.05]), l0: X("dorm", [3.92, 1.03, -3.7]), p1: X("dorm", [4.25, 1.3, -3.25]), l1: X("dorm", [3.93, 1.03, -3.68]), fov: [36, 32], ease: "io" } },
  { id: 10, name: "worth 20M", s: 22.55, e: 24.7, light: "day", dof: 0,
    cam: { p0: [JX - 9, 1.0, JZ + 9], l0: [JX - 2, 2.4, JZ], p1: [JX + 1, 1.3, JZ + 10.5], l1: [JX + 1, 2.4, JZ], fov: [40, 38], ease: "io" } },
  { id: 11, name: "96% off", s: 24.7, e: 28.55, light: "day", dof: 4,
    cam: { p0: [-30, 7.5, -3.5], l0: [-30, 3.0, 10.4], p1: [-27.6, 1.5, 1.6], l1: [-30.5, 2.4, 10.4], fov: [44, 40], ease: "io" } },
  // ---- class ----
  { id: 12, name: "arbitrage wide", s: 28.55, e: 30.3, light: "day", dof: 4, sunAz: 170, sunEl: 64,
    cam: { p0: X("class", [-0.8, 1.7, 3.2]), l0: X("class", [0.4, 2.0, -5.9]), p1: X("class", [-0.4, 1.7, 1.6]), l1: X("class", [0.5, 2.0, -5.9]), fov: [44, 42], ease: "io" } },
  { id: 13, name: "arbitrage board", s: 30.3, e: 32.8, light: "day", dof: 6, sunAz: 170, sunEl: 64,
    cam: { p0: X("class", [1.4, 1.9, -1.0]), l0: X("class", [0.3, 2.1, -5.9]), p1: X("class", [1.0, 2.0, -2.0]), l1: X("class", [0.3, 2.1, -5.9]), fov: [44, 44], ease: "io" } },
  { id: 14, name: "insanity", s: 32.8, e: 33.9, light: "day", dof: 12, sunAz: 170, sunEl: 64,
    cam: { p0: X("class", [-1.0, 1.25, 1.4]), l0: X("class", [-1.4, 1.2, -1.2]), p1: X("class", [-1.15, 1.25, 0.9]), l1: X("class", [-1.4, 1.2, -1.2]), fov: [34, 30], roll: [0.08, -0.04], ease: "o" } },
  // ---- boardroom ----
  { id: 15, name: "five investors", s: 33.9, e: 35.68, light: "day", dof: 6, sunAz: 165, sunEl: 64,
    cam: { p0: X("board", [-4.2, 1.7, 1.4]), l0: X("board", [-1.8, 1.6, -3.2]), p1: X("board", [3.4, 1.7, 1.2]), l1: X("board", [1.6, 1.6, -3.2]), fov: [42, 42], ease: "io" } },
  { id: 16, name: "park it", s: 35.68, e: 36.8, light: "day", dof: 12, sunAz: 165, sunEl: 64,
    cam: { p0: X("board", [0.35, 1.85, -0.4]), l0: X("board", [0, 1.85, -3.2]), p1: X("board", [0.3, 1.85, -0.8]), l1: X("board", [0, 1.85, -3.2]), fov: [34, 32], ease: "o" } },
  { id: 17, name: "school?", s: 36.8, e: 37.6, light: "day", dof: 12, sunAz: 165, sunEl: 64,
    cam: { p0: X("board", [3.6, 1.75, 0.6]), l0: X("board", [4.6, 1.75, -1.4]), p1: X("board", [3.75, 1.75, 0.2]), l1: X("board", [4.6, 1.75, -1.4]), fov: [34, 31], roll: [-0.05, 0.03], ease: "o" } },
  // ---- the cheque ----
  { id: 18, name: "cheque 700,008.50", s: 37.6, e: 41.7, light: "day", dof: 12,
    cam: { p0: [4.9, 1.35, -3.9], l0: [3.3, 1.12, -6.5], p1: [4.2, 1.22, -5.0], l1: [3.3, 1.12, -6.6], fov: [38, 32], ease: "io" } },
  { id: 19, name: "HQ tower", s: 41.7, e: 44.3, light: "golden", dof: 0,
    cam: { p0: [-116, 1.4, -4], l0: [-130, 12, -31], p1: [-119, 2.4, -9], l1: [-130, 62, -31], fov: [50, 52], ease: "io" } },
  // ---- office ----
  { id: 20, name: "execs laugh", s: 44.3, e: 46.05, light: "day", dof: 6, sunAz: 165, sunEl: 62,
    cam: { p0: X("office", [0.8, 1.6, 2.4]), l0: X("office", [0.3, 1.5, -2.8]), p1: X("office", [0.4, 1.6, 1.2]), l1: X("office", [0.3, 1.55, -2.8]), fov: [42, 40], ease: "io" } },
  { id: 21, name: "commercial kid", s: 46.05, e: 48.2, light: "day", dof: 14, sunAz: 165, sunEl: 62,
    cam: { p0: X("office", [0.15, 1.9, -0.9]), l0: X("office", [-0.1, 1.9, -3.0]), p1: X("office", [0.12, 1.92, -1.25]), l1: X("office", [-0.1, 1.9, -3.0]), fov: [34, 30], roll: [0.04, -0.03], ease: "o" } },
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
    cam: { p0: X("court", [1.1, 2.15, -2.4]), l0: X("court", [0.1, 2.0, -4.8]), p1: X("court", [0.95, 2.1, -2.9]), l1: X("court", [0.1, 2.0, -4.8]), fov: [38, 34], ease: "o" } },
  // ---- bus ----
  { id: 27, name: "bus driver", s: 63.4, e: 65.6, light: "day", dof: 10,
    cam: { p0: [52.2, 2.5, -0.2], l0: [57.4, 2.35, 1.6], p1: [53.4, 2.45, 0.4], l1: [57.4, 2.35, 1.65], fov: [36, 32], ease: "io" } },
  // ---- re-air ----
  { id: 28, name: "tv re-air", s: 65.6, e: 68.5, light: "day", dof: 6, sunAz: 160, sunEl: 62,
    cam: { p0: X("dorm", [0.4, 1.5, 1.8]), l0: X("dorm", [0.4, 1.42, -4.5]), p1: X("dorm", [0.4, 1.45, -2.5]), l1: X("dorm", [0.4, 1.45, -4.5]), fov: [42, 40], ease: "i" } },
  { id: 29, name: "700M", s: 68.5, e: 70.8, light: "golden", dof: 0,
    cam: { p0: [BOARD[0] + 1.2, 1.6, 6.5], l0: [BOARD[0] + 0.6, 6.2, BOARD[2]], p1: [BOARD[0] + 0.8, 3.4, 4.0], l1: [BOARD[0] + 0.4, 6.3, BOARD[2]], fov: [46, 42], ease: "io" } },
  { id: 30, name: "inflation arrow", s: 70.8, e: 75.05, light: "golden", dof: 0,
    cam: (t) => {
      const u = Math.min(1, Math.max(0, (t - 70.8) / 4.25)), e = u * u * (3 - 2 * u), h = arrowH(t);
      return { pos: [-30 + 2 * e, 1.6 + 1.2 * e, 3.5 + 1.5 * e], look: [ARROW[0] + 1, Math.max(6, h * 0.82), ARROW[2]], fov: 50 + 6 * e, roll: 0 };
    } },
  { id: 31, name: "just kidding", s: 75.05, e: 78.2, light: "golden", dof: 0,
    cam: { p0: [BOARD[0] + 1.0, 4.6, 4.0], l0: [BOARD[0] + 1.6, 5.0, BOARD[2]], p1: [BOARD[0] + 2.45, 4.32, BOARD[2] + 1.15], l1: [BOARD[0] + 2.45, 4.3, BOARD[2]], fov: [44, 34], ease: "i" } },
  // ---- button ----
  { id: 32, name: "keeping the cans", s: 78.2, e: TOTAL / FPS, light: "day", dof: 8, sunAz: 160, sunEl: 62,
    cam: { p0: X("dorm", [-1.4, 1.3, 0.8]), l0: X("dorm", [-2.5, 1.2, -1.0]), p1: X("dorm", [-0.4, 1.7, 2.6]), l1: X("dorm", [-2.5, 1.4, -1.4]), fov: [36, 44], ease: "io" } },
];
export const shotAt = (t: number) => { let i = 0; while (i + 1 < SHOTS.length && t >= SHOTS[i + 1].s) i++; return SHOTS[i]; };

// ---------------- camera ----------------
const EASE = { io: (u: number) => u * u * (3 - 2 * u), o: (u: number) => 1 - (1 - u) ** 3, i: (u: number) => u * u * u, lin: (u: number) => u };
const lerp = (a: number, b: number, u: number) => a + (b - a) * u;
const L3 = (a: V3, b: V3, u: number): V3 => [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
/** impact kicks: time, strength (m of shake at the start), decay (1/s) */
export const KICKS: [number, number, number][] = [
  [4.3, 0.12, 5], [11.22, 0.09, 7], [29.6, 0.03, 8], [40.3, 0.025, 9], [46.44, 0.03, 6], [62.02, 0.08, 7], [69.3, 0.06, 7], [70.9, 0.1, 4], [77.2, 0.05, 8],
];
const hash = (n: number) => { const v = Math.sin(n * 127.1) * 43758.5453; return v - Math.floor(v); };
const noise1 = (x: number, s: number) => { const i = Math.floor(x), f = x - i, w = f * f * (3 - 2 * f); return lerp(hash(i + s * 57), hash(i + 1 + s * 57), w) * 2 - 1; };

export const camAt = (f: number): Cam => {
  const t = f / FPS, s = shotAt(t), u = Math.min(1, Math.max(0, (t - s.s) / (s.e - s.s)));
  let c: Cam;
  if (typeof s.cam === "function") c = s.cam(t, u);
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
