// "Infinite Money Glitch": shots timed to the ElevenLabs voiceover (tightened take, 79.2 s).
// Step 5 (sample) builds the main parts: hook, ERROR twist, jets + party, final vote. The rest is filled in step 6.
import { RUNWAY, STREET, PHONE, V3 } from "./sets";
import { VO_DUR } from "./vo";

export const FPS = 30;
export const TOTAL = Math.ceil((VO_DUR + 0.25) * FPS);
export type Light = "day" | "golden";
export type Cam = { pos: V3; look: V3; fov: number; roll: number };
type Key = { p0: V3; l0: V3; p1?: V3; l1?: V3; fov?: [number, number] | number; roll?: [number, number] | number; ease?: "io" | "o" | "i" | "lin" };
export type Shot = { id: number; name: string; s: number; e: number; light: Light; cam: Key; dof: number; sunAz?: number; sunEl?: number };

const [RX] = RUNWAY, [SX] = STREET, [PX, PY, PZ] = PHONE;
const SY = PY + 0.19; // phone screen centre height
export const DAN_BAR: V3 = [0, 0, -3.2];
/** moments */
export const ERR_T = 24.8, JUMP_T = 26.2, RAIN_T = 1.6;

export const SHOTS: Shot[] = [
  // ---- HOOK: "A bartender found an infinite money glitch… $1.6 million before anyone noticed." ----
  { id: 1, name: "phone balance explodes", s: 0, e: 3.0, light: "golden", dof: 0, sunAz: 150, sunEl: 70,
    cam: { p0: [PX + 0.05, SY + 0.02, PZ + 0.74], l0: [PX, SY, PZ], p1: [PX + 0.02, SY + 0.01, PZ + 0.62], l1: [PX, SY, PZ], fov: [48, 46], ease: "o" } },
  { id: 2, name: "money rains on Dan", s: 3.0, e: 7.45, light: "golden", dof: 0, sunAz: 150, sunEl: 70,
    cam: { p0: [0.3, 1.65, 1.6], l0: [0, 1.5, -3.2], p1: [0.15, 1.6, 0.9], l1: [0, 1.5, -3.2], fov: [46, 44], ease: "io" } },
  // ---- (step 6) 7.45 – 24.0 ----
  { id: 90, name: "tbd A", s: 7.45, e: 24.0, light: "golden", dof: 0, sunAz: 150, sunEl: 70, cam: { p0: [0, 1.7, 4.5], l0: [0, 1.6, -4], fov: 50 } },
  // ---- TWIST: "The screen says ERROR… but the money shows up anyway. Error. Money arrives. Again. And again." ----
  { id: 3, name: "error popup", s: 24.0, e: 27.44, light: "golden", dof: 0, sunAz: 150, sunEl: 70,
    cam: { p0: [PX + 0.04, SY + 0.02, PZ + 0.7], l0: [PX, SY, PZ], p1: [PX, SY, PZ + 0.6], l1: [PX, SY, PZ], fov: [48, 46], ease: "io" } },
  { id: 4, name: "again and again", s: 27.44, e: 31.9, light: "golden", dof: 0, sunAz: 150, sunEl: 70,
    cam: { p0: [0.9, 1.65, 0.8], l0: [-0.1, 1.55, -3.2], p1: [0.7, 1.62, 0.3], l1: [-0.1, 1.55, -3.2], fov: [46, 44], ease: "io" } },
  { id: 91, name: "tbd B", s: 31.9, e: 42.8, light: "golden", dof: 0, sunAz: 150, sunEl: 70, cam: { p0: [0, 1.7, 4.5], l0: [0, 1.6, -4], fov: 50 } },
  // ---- ESCALATION: "Private jets. Five-star hotels. Parties every weekend. He paid bar tabs for complete strangers…" ----
  { id: 5, name: "private jet", s: 42.8, e: 44.6, light: "day", dof: 0, sunAz: 140, sunEl: 32,
    cam: { p0: [RX + 2.5, 1.6, 26], l0: [RX + 0.5, 2.4, -6], p1: [RX + 2.0, 1.7, 22.5], l1: [RX + 0.5, 2.4, -6], fov: [46, 44], ease: "o" } },
  { id: 6, name: "bar party", s: 44.6, e: 50.3, light: "golden", dof: 0, sunAz: 150, sunEl: 70,
    cam: { p0: [0.2, 1.75, 3.8], l0: [0, 1.4, -2.4], p1: [0.1, 1.7, 2.8], l1: [0, 1.4, -2.4], fov: [54, 52], ease: "io" } },
  { id: 92, name: "tbd C", s: 50.3, e: 71.9, light: "golden", dof: 0, sunAz: 150, sunEl: 70, cam: { p0: [0, 1.7, 4.5], l0: [0, 1.6, -4], fov: 50 } },
  // ---- QUESTION: "So who's really guilty? … Comment 1 for Dan, 2 for the bank." ----
  { id: 7, name: "dan vs bank", s: 71.9, e: TOTAL / FPS, light: "golden", dof: 0, sunAz: 30, sunEl: 12,
    cam: { p0: [SX + 5.6, 1.6, 16], l0: [SX + 6, 3.8, -3], p1: [SX + 5.3, 1.65, 14.5], l1: [SX + 6, 3.8, -3], fov: [58, 56], ease: "io" } },
];
export const shotAt = (t: number) => { let i = 0; while (i + 1 < SHOTS.length && t >= SHOTS[i + 1].s) i++; return SHOTS[i]; };

const EASE = { io: (u: number) => u * u * (3 - 2 * u), o: (u: number) => 1 - (1 - u) ** 3, i: (u: number) => u * u * u, lin: (u: number) => u };
const lerp = (a: number, b: number, u: number) => a + (b - a) * u;
const L3 = (a: V3, b: V3, u: number): V3 => [lerp(a[0], b[0], u), lerp(a[1], b[1], u), lerp(a[2], b[2], u)];
export const KICKS: [number, number, number][] = [[0.02, 0.01, 6], [RAIN_T, 0.02, 6], [ERR_T, 0.006, 8], [JUMP_T, 0.008, 7], [42.85, 0.05, 6], [44.65, 0.04, 6], [72.0, 0.04, 7]];
const hash = (n: number) => { const v = Math.sin(n * 127.1) * 43758.5453; return v - Math.floor(v); };
const noise1 = (x: number, s: number) => { const i = Math.floor(x), f = x - i, w = f * f * (3 - 2 * f); return lerp(hash(i + s * 57), hash(i + 1 + s * 57), w) * 2 - 1; };
export const camAt = (f: number): Cam => {
  const t = f / FPS, s = shotAt(t), u = Math.min(1, Math.max(0, (t - s.s) / (s.e - s.s)));
  const k = s.cam, e = EASE[k.ease ?? "io"](u);
  const fv = typeof k.fov === "number" ? [k.fov, k.fov] : k.fov ?? [40, 40], rl = typeof k.roll === "number" ? [k.roll, k.roll] : k.roll ?? [0, 0];
  const c: Cam = { pos: L3(k.p0, k.p1 ?? k.p0, e), look: L3(k.l0, k.l1 ?? k.l0, e), fov: lerp(fv[0], fv[1], e), roll: lerp(rl[0], rl[1], e) };
  const d = Math.hypot(c.pos[0] - c.look[0], c.pos[1] - c.look[1], c.pos[2] - c.look[2]);
  let sx = 0.004 * d * noise1(t * 0.9, 1), sy = 0.003 * d * noise1(t * 0.8, 2), rr = 0;
  for (const [tk, a, dec] of KICKS) { if (t < tk || t > tk + 1.2) continue; const env = a * Math.exp(-dec * (t - tk)); sx += env * Math.sin((t - tk) * 55); sy += env * Math.cos((t - tk) * 47) * 0.8; rr += env * 0.15 * Math.sin((t - tk) * 40); }
  c.look = [c.look[0] + sx, c.look[1] + sy, c.look[2]]; c.roll += rr;
  return c;
};
