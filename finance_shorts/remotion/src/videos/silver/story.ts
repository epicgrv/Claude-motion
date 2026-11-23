// "Silver Thursday": shots timed to the ElevenLabs voiceover (seconds). Camera = eased dolly between two poses +
// impact kicks (decaying shake) + a faint handheld drift. Fast cuts: ~1.0-1.9 s per shot.
import { EXCH, RANCH, TOP_Y, EX_STEP_Y, V3 } from "./sets";
import { TOWN, OFFICE, FLOOR, COURT, VAULT, ALPS } from "./places";
import { VO_DUR } from "./vo";

export const FPS = 30;
export const TOTAL = Math.ceil((VO_DUR + 0.25) * FPS);
export type Light = "day" | "golden";
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type Key = { p0: V3; l0: V3; p1?: V3; l1?: V3; fov?: [number, number] | number; roll?: [number, number] | number; ease?: "io" | "o" | "i" | "lin" };
export type Shot = { id: number; name: string; s: number; e: number; light: Light; cam: Key | ((t: number, u: number) => Cam); dof: number; sunAz?: number; sunEl?: number };

const [EX] = EXCH, [RX] = RANCH, TY = TOP_Y, [TX, , TZ] = TOWN, OX = OFFICE, FX = FLOOR, CX = COURT, VX = VAULT;
/** cargo plane flight over the Alps (nose +x) */
export const planeAt = (t: number): V3 => [ALPS[0] - 120 + 78 * (t - 20.6), 255 + 3 * Math.sin(t * 0.8), ALPS[2]];
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
  // ---- "It's the 1970s. Inflation is eating cash alive." ----
  { id: 8, name: "70s main street", s: 10.42, e: 12.1, light: "day", dof: 0, sunAz: 130, sunEl: 44,
    cam: { p0: [TX - 5, 1.5, TZ - 4.5], l0: [TX - 1.5, 2.7, TZ + 11], p1: [TX - 3, 1.55, TZ - 2.5], l1: [TX, 2.6, TZ + 11], fov: [56, 52], ease: "io" } },
  { id: 9, name: "grocery prices", s: 12.1, e: 14.4, light: "day", dof: 6, sunAz: 130, sunEl: 44,
    cam: { p0: [TX - 18.8, 1.8, TZ - 1.6], l0: [TX - 19.4, 2.25, TZ + 10.9], p1: [TX - 19.1, 1.75, TZ - 0.3], l1: [TX - 19.5, 2.2, TZ + 10.9], fov: [52, 50], ease: "io" } },
  // ---- "Gold? Banned for Americans. So they bet big on silver. Not a little." ----
  { id: 10, name: "gold banned", s: 14.4, e: 16.55, light: "day", dof: 8, sunAz: 150, sunEl: 62,
    cam: { p0: [OX + 0.3, 1.75, 2.6], l0: [OX - 0.1, 1.3, -2.6], p1: [OX + 0.15, 1.6, 1.6], l1: [OX - 0.15, 1.25, -2.6], fov: [48, 44], ease: "io" } },
  { id: 11, name: "carts of silver", s: 16.55, e: 19.1, light: "day", dof: 0, sunAz: 150, sunEl: 40,
    cam: { p0: [EX + 1.0, 2.6, 21.5], l0: [EX, 1.3, 10.5], p1: [EX + 0.7, 2.5, 19.6], l1: [EX, 1.3, 11], fov: [46, 44], ease: "io" } },
  { id: 12, name: "convoy", s: 19.1, e: 20.6, light: "day", dof: 0, sunAz: 150, sunEl: 40,
    cam: { p0: [EX + 4, 2.6, 25], l0: [EX, 1.6, 8], p1: [EX + 7, 7.5, 31], l1: [EX, 1.0, 6], fov: [50, 52], ease: "o" } },
  // ---- "Planes full of it, flown to Switzerland." ----
  { id: 13, name: "plane over the alps", s: 20.6, e: 22.75, light: "day", dof: 0, sunAz: 120, sunEl: 40,
    cam: (t) => { const p = planeAt(t); return { pos: [p[0] - 34 + 6 * (t - 20.6), p[1] + 9, p[2] + 72], look: [p[0] + 5, p[1] - 9, p[2]], fov: 50, roll: -0.03 }; } },
  // ---- "By 1979, they controlled an estimated third of the world's available silver." ----
  { id: 14, name: "globe wide", s: 22.75, e: 24.9, light: "day", dof: 6, sunAz: 150, sunEl: 62,
    cam: { p0: [OX + 3.3, 1.95, 3.4], l0: [OX + 3.5, 1.55, -4.6], p1: [OX + 3.4, 1.9, 2.4], l1: [OX + 3.55, 1.6, -4.6], fov: [54, 52], ease: "io" } },
  { id: 15, name: "a third turns silver", s: 24.9, e: 27.45, light: "day", dof: 10, sunAz: 150, sunEl: 62,
    cam: { p0: [OX + 3.4, 2.1, 0.2], l0: [OX + 3.6, 2.0, -4.6], p1: [OX + 3.5, 2.05, -0.6], l1: [OX + 3.6, 2.0, -4.6], fov: [46, 44], ease: "io" } },
  // ---- "Silver jumps from $6 an ounce to almost 50." ----
  { id: 16, name: "board climbs", s: 27.45, e: 31.25, light: "day", dof: 4, sunAz: 160, sunEl: 64,
    cam: { p0: [FX + 1.0, 1.9, 5.5], l0: [FX, 2.9, -16], p1: [FX + 0.6, 2.0, 3.5], l1: [FX, 3.0, -16], fov: [62, 58], ease: "io" } },
  // ---- "People are melting grandma's forks for cash." ----
  { id: 17, name: "silver queue", s: 31.25, e: 34.45, light: "day", dof: 6, sunAz: 130, sunEl: 44,
    cam: { p0: [TX + 12.5, 1.6, TZ + 1.6], l0: [TX + 3.5, 1.55, TZ + 8.2], p1: [TX + 9.2, 1.55, TZ + 3.2], l1: [TX + 3.2, 1.5, TZ + 8.0], fov: [46, 42], ease: "io" } },
  // ---- "The brothers up billions on paper." ----
  { id: 18, name: "billions on paper", s: 34.45, e: 37.45, light: "day", dof: 8, sunAz: 150, sunEl: 62,
    cam: { p0: [OX, 1.8, 3.0], l0: [OX, 1.5, -2.6], p1: [OX, 1.7, 2.0], l1: [OX, 1.5, -2.6], fov: [54, 50], ease: "io" } },
  // ---- "Then the exchange changes the rules. No more buying silver with borrowed money." ----
  { id: 19, name: "new rule stamp", s: 37.45, e: 40.0, light: "day", dof: 6, sunAz: 160, sunEl: 64,
    cam: { p0: [FX + 0.9, 2.7, -6.6], l0: [FX, 2.3, -13], p1: [FX + 0.5, 2.6, -8.2], l1: [FX, 2.25, -13], fov: [50, 46], ease: "io" } },
  { id: 20, name: "board: no borrowed money", s: 40.0, e: 42.3, light: "day", dof: 0, sunAz: 160, sunEl: 64,
    cam: { p0: [FX, 4.8, -4.0], l0: [FX, 5.2, -16], p1: [FX, 5.0, -6.0], l1: [FX, 5.3, -16], fov: [54, 52], ease: "io" } },
  // ---- "Soon, traders can basically only sell. And the Hunts borrowed big." ----
  { id: 21, name: "sell only", s: 42.3, e: 45.0, light: "day", dof: 8, sunAz: 160, sunEl: 64,
    cam: { p0: [FX + 4.5, 2.9, 6.6], l0: [FX + 4.5, 1.15, 0.6], p1: [FX + 4.5, 2.7, 5.8], l1: [FX + 4.5, 1.15, 0.6], fov: [50, 48], ease: "io" } },
  { id: 22, name: "borrowed big", s: 45.0, e: 47.25, light: "day", dof: 8, sunAz: 150, sunEl: 62,
    cam: { p0: [OX + 0.2, 1.7, 1.4], l0: [OX, 1.5, -3.2], p1: [OX + 0.1, 1.65, 0.6], l1: [OX, 1.5, -3.2], fov: [48, 46], ease: "io" } },
  // ---- "March 27th, 1980. Silver Thursday. Silver crashes to about $11." ----
  { id: 23, name: "calendar", s: 47.25, e: 49.55, light: "day", dof: 6, sunAz: 160, sunEl: 64,
    cam: { p0: [FX - 9.6, 4.4, -11.6], l0: [FX - 10, 4.6, -16], p1: [FX - 9.8, 4.5, -12.6], l1: [FX - 10, 4.6, -16], fov: [46, 44], ease: "io" } },
  { id: 24, name: "silver thursday", s: 49.55, e: 50.65, light: "day", dof: 0, sunAz: 160, sunEl: 64,
    cam: { p0: [FX + 0.6, 1.9, 4.6], l0: [FX, 3.0, -16], p1: [FX + 0.5, 1.95, 3.6], l1: [FX, 3.1, -16], fov: [62, 60], ease: "o" } },
  { id: 25, name: "crash", s: 50.65, e: 53.15, light: "day", dof: 4, sunAz: 160, sunEl: 64,
    cam: { p0: [FX + 1.0, 1.9, 2.2], l0: [FX, 2.9, -16], p1: [FX + 0.8, 1.85, 0.6], l1: [FX, 2.8, -16], fov: [60, 56], roll: [0.05, -0.04], ease: "o" } },
  // ---- "Their broker wants over $100 million today. They can't pay." ----
  { id: 26, name: "phone", s: 53.15, e: 57.25, light: "day", dof: 8, sunAz: 150, sunEl: 62,
    cam: { p0: [OX + 0.6, 1.65, 1.3], l0: [OX + 0.3, 1.4, -2.8], p1: [OX + 0.4, 1.6, 0.4], l1: [OX + 0.2, 1.45, -2.8], fov: [48, 44], ease: "io" } },
  { id: 27, name: "can't pay", s: 57.25, e: 58.95, light: "day", dof: 10, sunAz: 150, sunEl: 62,
    cam: { p0: [OX - 0.1, 1.75, -0.2], l0: [OX - 0.1, 1.65, -3.3], p1: [OX - 0.1, 1.72, -0.6], l1: [OX - 0.1, 1.65, -3.3], fov: [46, 44], ease: "o" } },
  // ---- "Banks lend them over a billion just to stop a meltdown." ----
  { id: 28, name: "bankers rush", s: 58.95, e: 62.85, light: "day", dof: 0, sunAz: 150, sunEl: 40,
    cam: { p0: [EX + 3.0, 1.5, 25], l0: [EX, 3.2, 6], p1: [EX + 2.0, 1.8, 21], l1: [EX, 3.0, 6], fov: [50, 48], ease: "io" } },
  // ---- "Years later, a jury says they tried to rig the market. Bankrupt. Banned from commodities trading." ----
  { id: 29, name: "jury", s: 62.85, e: 65.95, light: "day", dof: 4, sunAz: 165, sunEl: 64,
    cam: { p0: [CX + 1.4, 1.95, 3.4], l0: [CX + 2.9, 1.35, -3.6], p1: [CX + 1.7, 1.9, 2.4], l1: [CX + 3.0, 1.35, -3.6], fov: [58, 56], ease: "io" } },
  { id: 30, name: "bankrupt", s: 65.95, e: 66.95, light: "day", dof: 8, sunAz: 165, sunEl: 64,
    cam: { p0: [CX - 3.0, 1.65, 2.4], l0: [CX - 3.0, 1.5, -2.2], p1: [CX - 3.0, 1.62, 2.0], l1: [CX - 3.0, 1.5, -2.2], fov: [46, 44], roll: [-0.04, 0.02], ease: "o" } },
  { id: 31, name: "banned", s: 66.95, e: 68.65, light: "day", dof: 0, sunAz: 150, sunEl: 40,
    cam: { p0: [EX + 2.6, 1.4, 17.5], l0: [EX, 2.4, 5], p1: [EX + 2.0, 1.45, 16.2], l1: [EX, 2.4, 5], fov: [52, 50], ease: "io" } },
  // ---- "Bunker's take? A billion dollars isn't what it used to be." ----
  { id: 32, name: "vault", s: 68.65, e: 72.3, light: "day", dof: 8, sunAz: 165, sunEl: 66,
    cam: { p0: [VX + 0.5, 1.7, 2.6], l0: [VX, 1.45, -3.4], p1: [VX + 0.2, 1.65, 0.3], l1: [VX, 1.5, -3.4], fov: [48, 44], ease: "io" } },
  // ---- "So cheaters? Or did Wall Street change the rules because the wrong guys were winning? Comment below." ----
  { id: 33, name: "cheaters?", s: 72.3, e: 73.6, light: "day", dof: 8, sunAz: 140, sunEl: 48,
    cam: { p0: [0.7, 7.45, 6.2], l0: [0.0, 7.05, 0.4], p1: [0.5, 7.4, 5.6], l1: [0.0, 7.05, 0.4], fov: [42, 40], ease: "o" } },
  { id: 34, name: "rigged?", s: 73.6, e: 76.95, light: "day", dof: 10, sunAz: 150, sunEl: 40,
    cam: { p0: [EX + 0.9, EX_STEP_Y + 1.4, 8.6], l0: [EX + 0.05, EX_STEP_Y + 1.2, 4.0], p1: [EX + 0.5, EX_STEP_Y + 1.35, 7.4], l1: [EX + 0.05, EX_STEP_Y + 1.25, 4.0], fov: [42, 38], ease: "io" } },
  { id: 35, name: "comment below", s: 76.95, e: TOTAL / FPS, light: "day", dof: 6, sunAz: 140, sunEl: 48,
    cam: { p0: [0.6, 7.4, 6.0], l0: [0.0, 7.0, 0.4], p1: [1.0, 7.6, 7.2], l1: [0.0, 6.9, 0.4], fov: [40, 44], ease: "io" } },
];
export const shotAt = (t: number) => { let i = 0; while (i + 1 < SHOTS.length && t >= SHOTS[i + 1].s) i++; return SHOTS[i]; };

// ---------------- camera ----------------
const EASE = { io: (u: number) => u * u * (3 - 2 * u), o: (u: number) => 1 - (1 - u) ** 3, i: (u: number) => u * u * u, lin: (u: number) => u };
const lerp = (a: number, b: number, u: number) => a + (b - a) * u;
const L3 = (a: V3, b: V3, u: number): V3 => [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
/** impact kicks: time, strength (m of shake at the start), decay (1/s) */
export const KICKS: [number, number, number][] = [
  [0.02, 0.06, 6], [RIP, 0.05, 7], [SLIDE + 0.02, 0.14, 5], [GUSH, 0.08, 5], [MONEY, 0.04, 7],
  [13.0, 0.05, 7], [15.25, 0.06, 7], [38.6, 0.07, 6], [47.95, 0.05, 7], [49.75, 0.06, 6], [51.0, 0.12, 4], [54.0, 0.04, 9],
  [60.3, 0.05, 7], [66.25, 0.12, 5], [67.3, 0.05, 7], [72.5, 0.04, 8], [74.3, 0.04, 8], [77.1, 0.04, 8],
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
