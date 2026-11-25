// "Infinite Money Glitch": 26 shots timed to the ElevenLabs voiceover (tightened take, 79.2 s).
import { RUNWAY, STREET, PHONE, SERVER, BEDROOM, POLICE, HOTEL_X, COPS_X, V3 } from "./sets";
import { VO_DUR } from "./vo";

export const FPS = 30;
export const TOTAL = Math.ceil((VO_DUR + 0.25) * FPS);
export type Light = "day" | "golden";
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type Key = { p0: V3; l0: V3; p1?: V3; l1?: V3; fov?: [number, number] | number; roll?: [number, number] | number; ease?: "io" | "o" | "i" | "lin" };
export type Shot = { id: number; name: string; s: number; e: number; light: Light; cam: Key; dof: number; sunAz?: number; sunEl?: number };

const [RX] = RUNWAY, [SX] = STREET, [PX, PY, PZ] = PHONE, SY = PY + 0.19;
/** Dan as a customer, standing at the bar (counter behind him) */
export const DAN_CUST: V3 = [0.2, 0, -0.5];
/** Dan behind the counter (working his shift) */
export const DAN_WORK: V3 = [-0.6, 0, -3.1];
export const BARTENDER: V3 = [-2.2, 0, -3.1];
/** moments */
export const ERR_T = 24.8, JUMP_T = 26.2, RAIN_T = 1.6, TAP_T = 10.3, SLAM1 = 11.35, SLAM2 = 69.9, OFF_T = 32.3, GLITCH_T = 56.4, RING_T = 61.2;
export const TAPS = [28.3, 29.6, 30.9];

const PHONE_CAM = (): Key => ({ p0: [PX + 0.03, SY + 0.34, PZ + 0.95], l0: [PX, SY, PZ], p1: [PX + 0.01, SY + 0.31, PZ + 0.86], l1: [PX, SY, PZ], fov: [46, 46], ease: "io" });
const G = { light: "golden" as Light, dof: 0, sunAz: 150, sunEl: 70 };
export const SHOTS: Shot[] = [
  { id: 1, name: "phone balance explodes", s: 0, e: 3.0, ...G, cam: PHONE_CAM() },
  { id: 2, name: "money rains on Dan", s: 3.0, e: 7.45, ...G, cam: { p0: [0.4, 1.78, 2.8], l0: [0.1, 1.45, -1.5], p1: [0.3, 1.75, 2.1], l1: [0.1, 1.45, -1.5], fov: [50, 48] } },
  { id: 3, name: "one button", s: 7.45, e: 11.2, ...G, cam: PHONE_CAM() },
  { id: 4, name: "jail teaser", s: 11.2, e: 13.6, ...G, sunAz: 160, sunEl: 66, cam: { p0: [POLICE + 3.4, 1.6, 2.9], l0: [POLICE + 3.2, 1.45, -3.5], p1: [POLICE + 3.35, 1.6, 2.4], l1: [POLICE + 3.2, 1.45, -3.5], fov: [46, 44], ease: "o" } },
  { id: 5, name: "late shifts", s: 13.6, e: 16.0, ...G, cam: { p0: [-0.3, 1.6, 1.6], l0: [-0.6, 1.5, -3.1], p1: [-0.4, 1.58, 1.0], l1: [-0.6, 1.5, -3.1], fov: [46, 44] } },
  { id: 6, name: "tip jar", s: 16.0, e: 18.9, ...G, cam: { p0: [-1.25, 1.5, -0.2], l0: [-1.35, 1.4, -2.3], p1: [-1.28, 1.48, -0.45], l1: [-1.35, 1.4, -2.3], fov: [46, 44] } },
  { id: 7, name: "2 a.m.", s: 18.9, e: 21.0, ...G, cam: { p0: [4.3, 3.55, -7.9], l0: [4.4, 3.6, -9.92], p1: [4.35, 3.58, -8.2], l1: [4.4, 3.6, -9.92], fov: [42, 40] } },
  { id: 8, name: "tired at the bar", s: 21.0, e: 24.0, ...G, cam: { p0: [0.6, 1.65, 2.6], l0: [0.1, 1.45, -1.5], p1: [0.5, 1.62, 2.1], l1: [0.1, 1.45, -1.5], fov: [46, 44] } },
  { id: 9, name: "error", s: 24.0, e: 27.44, ...G, cam: PHONE_CAM() },
  { id: 10, name: "again and again", s: 27.44, e: 31.9, ...G, cam: { p0: [0.9, 1.65, 2.5], l0: [0.1, 1.45, -1.0], p1: [0.75, 1.62, 2.0], l1: [0.1, 1.45, -1.0], fov: [46, 44] } },
  { id: 11, name: "servers go dark", s: 31.9, e: 34.5, ...G, sunAz: 160, sunEl: 66, cam: { p0: [SERVER - 1.5, 1.6, 2.5], l0: [SERVER - 2.0, 1.4, -6], p1: [SERVER - 1.2, 1.6, 1.4], l1: [SERVER - 2.0, 1.4, -6], fov: [52, 50] } },
  { id: 12, name: "guard asleep", s: 34.5, e: 36.9, ...G, sunAz: 160, sunEl: 66, cam: { p0: [SERVER + 3.9, 1.8, 2.6], l0: [SERVER + 3.9, 1.9, -6], p1: [SERVER + 3.9, 1.75, 1.8], l1: [SERVER + 3.9, 1.85, -6], fov: [52, 50] } },
  { id: 13, name: "what would you do", s: 36.9, e: 38.75, ...G, cam: { p0: [0.25, 1.62, 1.9], l0: [0.2, 1.5, -0.5], p1: [0.25, 1.62, 1.5], l1: [0.2, 1.5, -0.5], fov: [44, 42], ease: "o" } },
  { id: 14, name: "calls his friends", s: 38.75, e: 40.7, ...G, cam: { p0: [0.6, 1.62, 2.4], l0: [0.1, 1.5, -1.5], p1: [0.5, 1.6, 2.0], l1: [0.1, 1.5, -1.5], fov: [46, 44] } },
  { id: 15, name: "friends burst in", s: 40.7, e: 42.8, ...G, cam: { p0: [-1.0, 1.75, 7.0], l0: [-1.7, 1.3, -1.0], p1: [-1.1, 1.75, 6.2], l1: [-1.7, 1.3, -1.0], fov: [54, 52] } },
  { id: 16, name: "private jet", s: 42.8, e: 44.4, light: "day", dof: 0, sunAz: 140, sunEl: 32, cam: { p0: [RX + 3.0, 1.7, 24], l0: [RX + 1.0, 2.6, -6], p1: [RX + 2.5, 1.75, 21], l1: [RX + 1.0, 2.6, -6], fov: [46, 44], ease: "o" } },
  { id: 17, name: "five-star hotel", s: 44.4, e: 45.6, light: "golden", dof: 0, sunAz: 30, sunEl: 12, cam: { p0: [HOTEL_X + 1.5, 1.7, 22], l0: [HOTEL_X, 6.0, -6], p1: [HOTEL_X + 1.2, 1.75, 20], l1: [HOTEL_X, 6.0, -6], fov: [56, 54], ease: "o" } },
  { id: 18, name: "bar party", s: 45.6, e: 50.3, ...G, cam: { p0: [0.2, 1.75, 3.8], l0: [0, 1.4, -2.0], p1: [0.1, 1.7, 2.8], l1: [0, 1.4, -2.0], fov: [54, 52] } },
  { id: 19, name: "five months", s: 50.3, e: 54.7, ...G, sunAz: 160, sunEl: 66, cam: { p0: [SERVER - 2.4, 2.35, -2.0], l0: [SERVER - 5.95, 2.4, -2.0], p1: [SERVER - 2.8, 2.38, -2.0], l1: [SERVER - 5.95, 2.4, -2.0], fov: [46, 44] } },
  { id: 20, name: "money that never existed", s: 54.7, e: 58.4, ...G, cam: PHONE_CAM() },
  { id: 21, name: "can't sleep", s: 58.4, e: 61.0, ...G, sunAz: 160, sunEl: 66, cam: { p0: [BEDROOM + 0.3, 1.5, 2.0], l0: [BEDROOM + 0.2, 1.3, -4.5], p1: [BEDROOM + 0.25, 1.5, 1.2], l1: [BEDROOM + 0.2, 1.3, -4.5], fov: [50, 48] } },
  { id: 22, name: "phone rings", s: 61.0, e: 64.3, ...G, sunAz: 160, sunEl: 66, cam: { p0: [BEDROOM + 2.68, 1.1, -4.95], l0: [BEDROOM + 2.7, 0.88, -5.95], p1: [BEDROOM + 2.69, 1.08, -5.05], l1: [BEDROOM + 2.7, 0.88, -5.95], fov: [46, 44] } },
  { id: 23, name: "walks in", s: 64.3, e: 66.9, light: "golden", dof: 0, sunAz: 30, sunEl: 12, cam: { p0: [COPS_X + 2.5, 1.7, 16], l0: [COPS_X, 3.0, -4], p1: [COPS_X + 2.0, 1.7, 14], l1: [COPS_X, 3.0, -4], fov: [52, 50] } },
  { id: 24, name: "confession", s: 66.9, e: 69.7, ...G, sunAz: 160, sunEl: 66, cam: { p0: [POLICE - 2.0, 1.7, 2.8], l0: [POLICE - 2.9, 1.5, -4], p1: [POLICE - 2.2, 1.7, 2.1], l1: [POLICE - 2.9, 1.5, -4], fov: [50, 48] } },
  { id: 25, name: "prison", s: 69.7, e: 71.9, ...G, sunAz: 160, sunEl: 66, cam: { p0: [POLICE + 3.35, 1.6, 2.3], l0: [POLICE + 3.2, 1.45, -3.5], p1: [POLICE + 3.3, 1.6, 1.8], l1: [POLICE + 3.2, 1.45, -3.5], fov: [46, 44] } },
  { id: 26, name: "dan vs bank", s: 71.9, e: TOTAL / FPS, light: "golden", dof: 0, sunAz: 30, sunEl: 12, cam: { p0: [SX + 4.6, 1.6, 10.5], l0: [SX + 5.4, 3.3, -3], p1: [SX + 4.4, 1.62, 9.5], l1: [SX + 5.4, 3.3, -3], fov: [58, 56] } },
];
export const shotAt = (t: number) => { let i = 0; while (i + 1 < SHOTS.length && t >= SHOTS[i + 1].s) i++; return SHOTS[i]; };

const EASE = { io: (u: number) => u * u * (3 - 2 * u), o: (u: number) => 1 - (1 - u) ** 3, i: (u: number) => u * u * u, lin: (u: number) => u };
const lerp = (a: number, b: number, u: number) => a + (b - a) * u;
const L3 = (a: V3, b: V3, u: number): V3 => [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
export const KICKS: [number, number, number][] = [[RAIN_T, 0.015, 6], [ERR_T, 0.005, 8], [JUMP_T, 0.006, 7], [SLAM1, 0.05, 6], [SLAM2, 0.05, 6], [42.85, 0.05, 6], [45.65, 0.04, 6], [GLITCH_T, 0.006, 6], [72.0, 0.04, 7]];
const hash = (n: number) => { const v = Math.sin(n * 127.1) * 43758.5453; return v - Math.floor(v); };
const noise1 = (x: number, s: number) => { const i = Math.floor(x), f = x - i, w = f * f * (3 - 2 * f); return lerp(hash(i + s * 57), hash(i + 1 + s * 57), w) * 2 - 1; };
export const camAt = (f: number): Cam => {
  const t = f / FPS, s = shotAt(t), u = Math.min(1, Math.max(0, (t - s.s) / (s.e - s.s)));
  const k = s.cam, e = EASE[k.ease ?? "io"](u);
  const fv = typeof k.fov === "number" ? [k.fov, k.fov] : k.fov ?? [40, 40], rl = typeof k.roll === "number" ? [k.roll, k.roll] : k.roll ?? [0, 0];
  const c: Cam = { pos: L3(k.p0, k.p1 ?? k.p0, e), look: L3(k.l0, k.l1 ?? k.l0, e), fov: lerp(fv[0], fv[1], e), roll: lerp(rl[0], rl[1], e) };
  const d = Math.hypot(c.pos[0] - c.look[0], c.pos[1] - c.look[1], c.pos[2] - c.look[2]);
  let sx = 0.003 * d * noise1(t * 0.9, 1), sy = 0.002 * d * noise1(t * 0.8, 2), rr = 0;
  for (const [tk, a, dec] of KICKS) { if (t < tk || t > tk + 1.2) continue; const env = a * Math.exp(-dec * (t - tk)); sx += env * Math.sin((t - tk) * 55); sy += env * Math.cos((t - tk) * 47) * 0.8; rr += env * 0.15 * Math.sin((t - tk) * 40); }
  c.look = [c.look[0] + sx, c.look[1] + sy, c.look[2]]; c.roll += rr;
  return c;
};
