// The GOLDLEAF BANK app on Dan's phone (made-up bank) and the bar's wall clock.
import { DynTex } from "../silver/places";
import { ERR_T, JUMP_T } from "./story";

const clamp01 = (x: number) => Math.min(1, Math.max(0, x));
const ease = (u: number) => { const x = clamp01(u); return x * x * (3 - 2 * x); };
const money = (v: number) => "$" + v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

/** balance shown on the app */
export const balanceAt = (t: number) => {
  if (t < 7.45) return 312.4 + (1_600_000 - 312.4) * ease((t - 0.35) / 2.3) ** 1.6;
  if (t < JUMP_T) return 312.4;
  const taps = [JUMP_T, 28.3, 29.6, 30.9].filter((x) => t >= x).length;
  return 312.4 + 1000 * taps;
};
export const drawPhone = (d: DynTex, t: number) => {
  const err = t >= ERR_T && t < JUMP_T + 0.25 && t > 20, b = balanceAt(t), flash = t > 20 && [JUMP_T, 28.3, 29.6, 30.9].some((x) => t >= x && t < x + 0.35);
  const key = `ph${b.toFixed(0)}${err ? "e" : ""}${flash ? "f" : ""}${t < 7.45 && t > 0.4 && t < 3 ? "c" : ""}`;
  d.set(key, (g, w, h) => {
    const bg = g.createLinearGradient(0, 0, 0, h); bg.addColorStop(0, "#14213f"); bg.addColorStop(1, "#0b1226"); g.fillStyle = bg; g.fillRect(0, 0, w, h);
    g.fillStyle = "#c9d3e6"; g.font = "700 30px Arial"; g.textAlign = "left"; g.textBaseline = "middle"; g.fillText("2:07 AM", 30, 40); g.textAlign = "right"; g.fillText("▮▮▮ 76%", w - 30, 40);
    g.fillStyle = "#e8c45a"; g.font = '900 54px "Arial Black", Arial'; g.textAlign = "center"; g.fillText("GOLDLEAF BANK", w / 2, 130);
    g.fillStyle = "#1d2b52"; g.beginPath(); g.roundRect(30, 200, w - 60, 330, 30); g.fill();
    g.fillStyle = "#9fb0d0"; g.font = "800 34px Arial"; g.fillText("SAVINGS BALANCE", w / 2, 255);
    g.fillStyle = flash ? "#5cf5a6" : "#ffffff"; const txt = money(b); g.font = `900 ${txt.length > 11 ? 66 : 80}px "Arial Black", Arial`; g.fillText(txt, w / 2, 360);
    if (flash) { g.fillStyle = "#5cf5a6"; g.font = '900 44px "Arial Black", Arial'; g.fillText("+ $1,000.00", w / 2, 450); }
    else { g.fillStyle = "#9fb0d0"; g.font = "700 30px Arial"; g.fillText("Available now", w / 2, 450); }
    g.fillStyle = "#e8c45a"; g.beginPath(); g.roundRect(60, 600, w - 120, 110, 55); g.fill();
    g.fillStyle = "#14213f"; g.font = '900 44px "Arial Black", Arial'; g.fillText("TRANSFER", w / 2, 657);
    for (let i = 0; i < 3; i++) { g.fillStyle = "#1d2b52"; g.beginPath(); g.roundRect(30, 760 + i * 95, w - 60, 80, 20); g.fill(); g.fillStyle = "#c9d3e6"; g.font = "700 30px Arial"; g.textAlign = "left"; g.fillText(["Transfer to Savings", "Transfer to Savings", "Transfer to Savings"][i], 60, 800 + i * 95); g.textAlign = "right"; g.fillStyle = "#5cf5a6"; g.fillText("+$1,000", w - 60, 800 + i * 95); g.textAlign = "center"; }
    if (err) {
      g.fillStyle = "rgba(0,0,0,.55)"; g.fillRect(0, 0, w, h);
      g.fillStyle = "#ffffff"; g.beginPath(); g.roundRect(50, 330, w - 100, 380, 36); g.fill();
      g.fillStyle = "#e2333c"; g.beginPath(); g.arc(w / 2, 420, 56, 0, 7); g.fill(); g.fillStyle = "#ffffff"; g.font = '900 80px "Arial Black", Arial'; g.fillText("!", w / 2, 425);
      g.fillStyle = "#e2333c"; g.font = '900 66px "Arial Black", Arial'; g.fillText("ERROR", w / 2, 530);
      g.fillStyle = "#3a3d47"; g.font = "700 30px Arial"; g.fillText("Transfer could not", w / 2, 590); g.fillText("be completed", w / 2, 628);
    }
  });
};
export const drawClock = (d: DynTex, t: number) => {
  const m = Math.floor(t / 10) % 60;
  d.set("clk" + m, (g, w, h) => {
    g.fillStyle = "#f4f1ea"; g.beginPath(); g.arc(w / 2, h / 2, w / 2 - 6, 0, 7); g.fill(); g.strokeStyle = "#241726"; g.lineWidth = 12; g.stroke();
    for (let i = 0; i < 12; i++) { const a = (i / 12) * Math.PI * 2; g.lineWidth = 6; g.beginPath(); g.moveTo(w / 2 + Math.sin(a) * 96, h / 2 - Math.cos(a) * 96); g.lineTo(w / 2 + Math.sin(a) * 110, h / 2 - Math.cos(a) * 110); g.stroke(); }
    const hA = ((2 + m / 60) / 12) * Math.PI * 2, mA = (m / 60) * Math.PI * 2;
    g.lineWidth = 12; g.beginPath(); g.moveTo(w / 2, h / 2); g.lineTo(w / 2 + Math.sin(hA) * 60, h / 2 - Math.cos(hA) * 60); g.stroke();
    g.lineWidth = 7; g.beginPath(); g.moveTo(w / 2, h / 2); g.lineTo(w / 2 + Math.sin(mA) * 92, h / 2 - Math.cos(mA) * 92); g.stroke();
  });
};
