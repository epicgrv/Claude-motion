// Animated screens: the GOLDLEAF BANK app (made-up bank), the wall clock, the bank's server status screen,
// the "unnoticed for" calendar and the 4 a.m. incoming call.
import { DynTex } from "../silver/places";
import { ERR_T, JUMP_T, TAPS, TAP_T, GLITCH_T, OFF_T, RING_T } from "./story";

const clamp01 = (x: number) => Math.min(1, Math.max(0, x));
const ease = (u: number) => { const x = clamp01(u); return x * x * (3 - 2 * x); };
const money = (v: number) => "$" + v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const hh = (i: number, s = 0) => { const v = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return v - Math.floor(v); };

/** balance shown on the app */
export const balanceAt = (t: number) => {
  if (t < 7.45) return 312.4 + (1_600_000 - 312.4) * ease((t - 0.35) / 2.3) ** 1.6;
  if (t < JUMP_T) return 312.4;
  if (t < 50) return 312.4 + 1000 * [JUMP_T, ...TAPS].filter((x) => t >= x).length;
  return 1_600_000;
};
export const drawPhone = (d: DynTex, t: number) => {
  const err = t >= ERR_T && t < JUMP_T + 0.2 && t < 30, b = balanceAt(t);
  const flash = t > 20 && t < 40 && [JUMP_T, ...TAPS].some((x) => t >= x && t < x + 0.4);
  const press = t > TAP_T - 0.05 && t < TAP_T + 0.6 && t < 20;
  const gl = t >= GLITCH_T && t < 60 ? Math.floor((t - GLITCH_T) * 12) : -1, gone = t >= GLITCH_T + 0.8 && t < 60;
  const key = `ph${b.toFixed(0)}${err ? "e" : ""}${flash ? "f" : ""}${press ? "p" : ""}${gone ? "g" : gl >= 0 ? "x" + gl : ""}`;
  d.set(key, (g, w, h) => {
    const bg = g.createLinearGradient(0, 0, 0, h); bg.addColorStop(0, "#14213f"); bg.addColorStop(1, "#0b1226"); g.fillStyle = bg; g.fillRect(0, 0, w, h);
    g.fillStyle = "#c9d3e6"; g.font = "700 30px Arial"; g.textAlign = "left"; g.textBaseline = "middle"; g.fillText("2:07 AM", 30, 40); g.textAlign = "right"; g.fillText("76%", w - 30, 40);
    g.fillStyle = "#e8c45a"; g.font = '900 54px "Arial Black", Arial'; g.textAlign = "center"; g.fillText("GOLDLEAF BANK", w / 2, 130);
    g.fillStyle = "#1d2b52"; g.beginPath(); g.roundRect(30, 200, w - 60, 330, 30); g.fill();
    g.fillStyle = "#9fb0d0"; g.font = "800 34px Arial"; g.fillText("SAVINGS BALANCE", w / 2, 255);
    if (gone) { g.fillStyle = "#ff4a4a"; g.font = '900 46px "Arial Black", Arial'; g.fillText("BALANCE", w / 2, 340); g.fillText("NOT FOUND", w / 2, 400); }
    else { g.fillStyle = flash ? "#5cf5a6" : "#ffffff"; const txt = money(b); g.font = `900 ${txt.length > 11 ? 66 : 80}px "Arial Black", Arial`; g.fillText(txt, w / 2, 360); }
    if (flash) { g.fillStyle = "#5cf5a6"; g.font = '900 44px "Arial Black", Arial'; g.fillText("+ $1,000.00", w / 2, 450); }
    else if (!gone) { g.fillStyle = "#9fb0d0"; g.font = "700 30px Arial"; g.fillText("Available now", w / 2, 450); }
    g.fillStyle = press ? "#fff2a8" : "#e8c45a"; g.beginPath(); g.roundRect(60, 600, w - 120, 110, 55); g.fill();
    if (press) { g.strokeStyle = "rgba(255,242,168,.6)"; g.lineWidth = 14; g.beginPath(); g.roundRect(44, 584, w - 88, 142, 70); g.stroke(); }
    g.fillStyle = "#14213f"; g.font = '900 44px "Arial Black", Arial'; g.fillText("TRANSFER", w / 2, 657);
    for (let i = 0; i < 3; i++) { g.fillStyle = "#1d2b52"; g.beginPath(); g.roundRect(30, 760 + i * 95, w - 60, 80, 20); g.fill(); g.fillStyle = "#c9d3e6"; g.font = "700 30px Arial"; g.textAlign = "left"; g.fillText("Checking → Savings", 60, 800 + i * 95); g.textAlign = "right"; g.fillStyle = "#5cf5a6"; g.fillText("$1,000", w - 60, 800 + i * 95); g.textAlign = "center"; }
    if (err) {
      g.fillStyle = "rgba(0,0,0,.55)"; g.fillRect(0, 0, w, h);
      g.fillStyle = "#ffffff"; g.beginPath(); g.roundRect(50, 330, w - 100, 380, 36); g.fill();
      g.fillStyle = "#e2333c"; g.beginPath(); g.arc(w / 2, 420, 56, 0, 7); g.fill(); g.fillStyle = "#ffffff"; g.font = '900 80px "Arial Black", Arial'; g.fillText("!", w / 2, 425);
      g.fillStyle = "#e2333c"; g.font = '900 66px "Arial Black", Arial'; g.fillText("ERROR", w / 2, 530);
      g.fillStyle = "#3a3d47"; g.font = "700 30px Arial"; g.fillText("Transfer could not", w / 2, 590); g.fillText("be completed", w / 2, 628);
    }
    if (gl >= 0 && !gone) { // digital glitch: shifted slices + colour split
      const img = g.getImageData(0, 0, w, h);
      for (let k = 0; k < 9; k++) { const y = Math.floor(hh(k, gl) * h), hgt = 20 + Math.floor(hh(k, gl + 3) * 60), dx = Math.floor((hh(k, gl + 7) - 0.5) * 120); g.putImageData(img, dx, 0, 0, y, w, hgt); }
      g.fillStyle = "rgba(255,40,80,.18)"; g.fillRect(0, 0, w, h);
    }
  });
};
export const drawClock = (d: DynTex, t: number, hour: number) => {
  const m = Math.floor((t % 60) / 6);
  d.set(`clk${hour}_${m}`, (g, w, h) => {
    g.fillStyle = "#f4f1ea"; g.beginPath(); g.arc(w / 2, h / 2, w / 2 - 6, 0, 7); g.fill(); g.strokeStyle = "#241726"; g.lineWidth = 12; g.stroke();
    for (let i = 0; i < 12; i++) { const a = (i / 12) * Math.PI * 2; g.lineWidth = 6; g.beginPath(); g.moveTo(w / 2 + Math.sin(a) * 96, h / 2 - Math.cos(a) * 96); g.lineTo(w / 2 + Math.sin(a) * 110, h / 2 - Math.cos(a) * 110); g.stroke(); }
    const hA = ((hour + m / 60) / 12) * Math.PI * 2, mA = (m / 60) * Math.PI * 2;
    g.lineWidth = 12; g.beginPath(); g.moveTo(w / 2, h / 2); g.lineTo(w / 2 + Math.sin(hA) * 60, h / 2 - Math.cos(hA) * 60); g.stroke();
    g.lineWidth = 7; g.beginPath(); g.moveTo(w / 2, h / 2); g.lineTo(w / 2 + Math.sin(mA) * 92, h / 2 - Math.cos(mA) * 92); g.stroke();
  });
};
export const drawServer = (d: DynTex, t: number) => {
  const off = t >= OFF_T, blink = Math.floor(t * 2) % 2;
  d.set("srv" + (off ? "off" + blink : "on"), (g, w, h) => {
    g.fillStyle = "#0b0f18"; g.fillRect(0, 0, w, h);
    g.fillStyle = off ? (blink ? "#ff4a4a" : "#c0262f") : "#2fbf71"; g.fillRect(0, 0, w, 90);
    g.fillStyle = "#ffffff"; g.font = '900 56px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(off ? "SYSTEM OFFLINE" : "SYSTEM ONLINE", w / 2, 48);
    g.fillStyle = "#c9d3e6"; g.font = "800 40px Arial"; g.fillText(off ? "2:00 AM – 5:00 AM" : "All checks running", w / 2, 170);
    g.fillStyle = off ? "#ff8a8a" : "#5cf5a6"; g.font = "800 36px Arial"; g.fillText(off ? "TRANSFER CHECKS: PAUSED" : "TRANSFER CHECKS: ON", w / 2, 250);
    g.fillStyle = "#9fb0d0"; g.font = "700 30px Arial"; g.fillText("GOLDLEAF BANK • CORE SYSTEM", w / 2, 380);
  });
};
export const drawCal = (d: DynTex, t: number) => {
  const v = t < 51.95 ? ["1", "DAY"] : t < 53.3 ? ["1", "WEEK"] : ["5", "MONTHS"];
  d.set("cal" + v[1], (g, w, h) => {
    g.fillStyle = "#f4f1ea"; g.fillRect(0, 0, w, h); g.fillStyle = "#c0262f"; g.fillRect(0, 0, w, 120);
    g.fillStyle = "#ffffff"; g.font = '900 52px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("UNNOTICED FOR", w / 2, 62);
    g.fillStyle = "#241726"; g.font = '900 220px "Arial Black", Arial'; g.fillText(v[0], w / 2, 280);
    g.fillStyle = "#c0262f"; g.font = '900 72px "Arial Black", Arial'; g.fillText(v[1], w / 2, 440);
    g.strokeStyle = "#241726"; g.lineWidth = 12; g.strokeRect(6, 6, w - 12, h - 12);
  });
};
export const drawNightPhone = (d: DynTex, t: number) => {
  const ring = t >= RING_T, pulse = ring ? Math.floor(t * 4) % 2 : 0;
  d.set("np" + (ring ? "r" + pulse : "o"), (g, w, h) => {
    g.fillStyle = ring ? "#0f1a2e" : "#05070c"; g.fillRect(0, 0, w, h);
    if (!ring) return;
    g.fillStyle = "#c9d3e6"; g.font = "700 22px Arial"; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("INCOMING CALL", w / 2, 70);
    g.fillStyle = "#ffffff"; g.font = '900 34px "Arial Black", Arial'; g.fillText("UNKNOWN", w / 2, 150); g.fillText("NUMBER", w / 2, 192);
    g.fillStyle = pulse ? "#ff5a5a" : "#c0262f"; g.beginPath(); g.arc(70, 440, 38, 0, 7); g.fill();
    g.fillStyle = pulse ? "#5cf5a6" : "#2fbf71"; g.beginPath(); g.arc(w - 70, 440, 38, 0, 7); g.fill();
  });
};
