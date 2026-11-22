// "Silver Thursday": shots timed to the ElevenLabs voiceover (seconds). Camera = eased dolly between two poses +
// impact kicks (decaying shake) + a faint handheld drift. Fast cuts: ~1.0-1.9 s per shot.
import { EXCH, RANCH, TOP_Y, EX_STEP_Y, V3 } from "./sets";
import { VO_DUR } from "./vo";

export const FPS = 30;
export const TOTAL = Math.ceil((VO_DUR + 0.25) * FPS);
export type Light = "day" | "golden";
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type Key = { p0: V3; l0: V3; p1?: V3; l1?: V3; fov?: [number, number] | number; roll?: [number, number] | number; ease?: "io" | "o" | "i" | "lin" };
export type Shot = { id: number; name: string; s: number; e: number; light: Light; cam: Key | ((t: number, u: number) => Cam); dof: number; sunAz?: number; sunEl?: number };

const [EX] = EXCH, [RX] = RANCH, TY = TOP_Y;
/** the official's spot on the exchange's top step */
export const OFFICIAL: V3 = [EX, EX_STEP_Y, 4.0];
/** the brothers on top of the silver */
export const BUNKER: V3 = [-0.6, TY, 0.6];
export const HERBERT: V3 = [0.65, TY, 0.3];
/** at the ranch gate */
export const BUNKER_R: V3 = [RX - 1.1, 0.05, 9.2];
export const HERBERT_R: V3 = [RX + 1.2, 0.05, 8.8];
/** rule-book rip time ("rules") */
export const RIP = 5.78;
/** bars start sliding (cut to the mountain) */
export const SLIDE = 6.22;
/** gusher + money ("oil" / "billionaires") */
export const GUSH = 8.62, MONEY = 9.1;

export const SHOTS: Shot[] = [
  // ---- HOOK: "Two brothers almost owned all the silver on Earth." ----
  { id: 1, name: "silver mountain reveal", s: 0, e: 1.9, light: "day", dof: 0, sunAz: 140, sunEl: 48,
    cam: { p0: [5.5, 1.1, 21], l0: [0, 5.2, 0], p1: [2.6, 6.6, 8.8], l1: [0, 7.3, 0.4], fov: [54, 40], roll: [-0.04, 0], ease: "o" } },
  { id: 2, name: "brothers on top", s: 1.9, e: 3.78, light: "day", dof: 8, sunAz: 140, sunEl: 48,
    cam: { p0: [0.9, 7.55, 7.4], l0: [0.0, 7.05, 0.4], p1: [0.6, 7.45, 6.3], l1: [0.0, 7.05, 0.4], fov: [42, 40], ease: "io" } },
  // ---- "Then Wall Street changed the rules." ----
  { id: 3, name: "exchange", s: 3.78, e: 5.2, light: "day", dof: 0, sunAz: 150, sunEl: 40,
    cam: { p0: [EX + 1.9, 0.9, 10.6], l0: [EX + 0.2, 4.4, 2], p1: [EX + 1.3, 1.1, 9.0], l1: [EX + 0.1, 4.1, 2], fov: [72, 68], ease: "io" } },
  { id: 4, name: "rule book rip", s: 5.2, e: SLIDE, light: "day", dof: 10, sunAz: 150, sunEl: 40,
    cam: { p0: [EX + 0.7, EX_STEP_Y + 1.35, 7.9], l0: [EX + 0.05, EX_STEP_Y + 1.25, 4.0], p1: [EX + 0.5, EX_STEP_Y + 1.35, 7.1], l1: [EX + 0.05, EX_STEP_Y + 1.25, 4.0], fov: [40, 36], ease: "o" } },
  { id: 5, name: "silver slides", s: SLIDE, e: 6.95, light: "day", dof: 0, sunAz: 140, sunEl: 48,
    cam: { p0: [6.2, 6.9, 8.2], l0: [0.4, 6.2, 0.6], p1: [5.6, 6.6, 7.4], l1: [0.4, 6.0, 0.6], fov: [46, 44], roll: [0.03, -0.02], ease: "o" } },
  // ---- "Meet the Hunt brothers, Texas oil billionaires." ----
  { id: 6, name: "ranch gate", s: 6.95, e: 8.3, light: "day", dof: 0, sunAz: 120, sunEl: 34,
    cam: { p0: [RX + 1.5, 1.6, 26], l0: [RX - 1, 4.0, 0], p1: [RX + 0.8, 1.5, 21], l1: [RX - 1, 3.6, 0], fov: [54, 50], ease: "io" } },
  { id: 7, name: "oil billionaires", s: 8.3, e: 10.42, light: "day", dof: 0, sunAz: 120, sunEl: 34,
    cam: { p0: [RX + 0.5, 1.5, 15.4], l0: [RX - 2.2, 3.3, -10], p1: [RX + 0.3, 1.45, 14.2], l1: [RX - 2.2, 3.2, -10], fov: [64, 62], ease: "io" } },
  // ---- rest of the film: placeholder hold until those shots are built ----
  { id: 99, name: "tbd", s: 10.42, e: TOTAL / FPS, light: "day", dof: 0,
    cam: { p0: [9, 3, 26], l0: [0, 4, 0], fov: 46 } },
];
export const shotAt = (t: number) => { let i = 0; while (i + 1 < SHOTS.length && t >= SHOTS[i + 1].s) i++; return SHOTS[i]; };

// ---------------- camera ----------------
const EASE = { io: (u: number) => u * u * (3 - 2 * u), o: (u: number) => 1 - (1 - u) ** 3, i: (u: number) => u * u * u, lin: (u: number) => u };
const lerp = (a: number, b: number, u: number) => a + (b - a) * u;
const L3 = (a: V3, b: V3, u: number): V3 => [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
/** impact kicks: time, strength (m of shake at the start), decay (1/s) */
export const KICKS: [number, number, number][] = [
  [0.02, 0.06, 6], [RIP, 0.05, 7], [SLIDE + 0.02, 0.14, 5], [GUSH, 0.08, 5], [MONEY, 0.04, 7],
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
  const d = Math.hypot(c.pos[0] - c.look[0], c.pos[1] - c.look[1], c.pos[2] - c.look[2]);
  let sx = 0.004 * d * noise1(t * 0.9, 1), sy = 0.003 * d * noise1(t * 0.8, 2), rr = 0;
  for (const [tk, a, dec] of KICKS) {
    if (t < tk || t > tk + 1.2) continue;
    const env = a * Math.exp(-dec * (t - tk));
    sx += env * Math.sin((t - tk) * 55); sy += env * Math.cos((t - tk) * 47) * 0.8; rr += env * 0.15 * Math.sin((t - tk) * 40);
  }
  c.look = [c.look[0] + sx, c.look[1] + sy, c.look[2]];
  c.roll += rr;
  return c;
};
