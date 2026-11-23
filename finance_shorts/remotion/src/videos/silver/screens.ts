// Animated canvases (trading board, wall calendar, BUY/SELL console, trader CRTs, grocery prices) and the cart paths.
import { DynTex } from "./places";
import { EXCH, V3 } from "./sets";

const clamp01 = (x: number) => Math.min(1, Math.max(0, x));
const ease = (u: number) => { const x = clamp01(u); return x * x * (3 - 2 * x); };
const INK = "#241726";

/** silver price on the board (dollars per ounce) */
export const priceAt = (t: number) => {
  if (t < 50.85) return 6 + (49.45 - 6) * ease((t - 27.9) / 2.7);
  return 49.45 + (10.8 - 49.45) * ease((t - 50.85) / 1.75);
};
const money = (v: number) => "$" + v.toFixed(2);

export const drawBoard = (d: DynTex, t: number, id: number) => {
  const blink = Math.floor(t * 4) % 2;
  if (id === 20) return d.set("rule", (g, w, h) => {
    g.fillStyle = "#14101a"; g.fillRect(0, 0, w, h);
    g.fillStyle = "#e2453c"; g.fillRect(w / 2 - 360, 40, 720, 150);
    g.fillStyle = "#ffffff"; g.font = '900 110px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("NEW RULE", w / 2, 118);
    g.fillStyle = "#fff36b"; g.font = '900 92px "Arial Black", Arial'; g.fillText("NO BUYING", w / 2, 300); g.fillText("WITH", w / 2, 420);
    g.fillText("BORROWED", w / 2, 540); g.fillText("MONEY", w / 2, 650);
    g.strokeStyle = "#e2453c"; g.lineWidth = 26; for (const x of [w / 2 - 420, w / 2 + 420]) { g.beginPath(); g.arc(x, 480, 80, 0, 7); g.stroke(); g.beginPath(); g.moveTo(x - 56, 424); g.lineTo(x + 56, 536); g.stroke(); }
  });
  if (id === 24) return d.set("thu" + blink, (g, w, h) => {
    g.fillStyle = blink ? "#e2453c" : "#14101a"; g.fillRect(0, 0, w, h);
    g.fillStyle = blink ? "#fff36b" : "#e2453c"; g.font = '900 210px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle";
    g.fillText("SILVER", w / 2, 230); g.fillText("THURSDAY", w / 2, 480);
  });
  const p = priceAt(t), falling = t > 50.85, crash = t > 51.4 && t < 53.2 && blink;
  const key = "p" + p.toFixed(2) + (falling ? "f" : "u") + (crash ? "c" : "");
  d.set(key, (g, w, h) => {
    g.fillStyle = "#14101a"; g.fillRect(0, 0, w, h);
    g.fillStyle = "rgba(255,255,255,.05)"; for (let y = 0; y < h; y += 6) g.fillRect(0, y, w, 3);
    g.fillStyle = "#fff36b"; g.font = '900 86px "Arial Black", Arial'; g.textAlign = "left"; g.textBaseline = "middle"; g.fillText("SILVER  Ag", 60, 90);
    g.textAlign = "right"; g.fillStyle = "#9aa6b5"; g.font = '700 60px Arial'; g.fillText("PER OUNCE", w - 60, 92);
    const c = falling ? "#ff4a4a" : "#41f08f";
    g.fillStyle = c; g.font = '900 230px "Courier New", monospace'; g.textAlign = "center"; g.fillText(money(p), w / 2, 330);
    // arrow
    g.save(); g.translate(w / 2 + 520, 330); g.scale(0.7, 0.7); if (falling) g.rotate(Math.PI); g.fillStyle = c; g.beginPath(); g.moveTo(0, -110); g.lineTo(95, 30); g.lineTo(-95, 30); g.closePath(); g.fill(); g.restore();
    // sparkline (history up to now)
    g.strokeStyle = c; g.lineWidth = 12; g.lineJoin = "round"; g.beginPath();
    const t0 = falling ? 48 : 27.6, t1 = Math.max(t0 + 0.1, t);
    for (let k = 0; k <= 60; k++) { const tt = t0 + ((t1 - t0) * k) / 60, x = 80 + ((w - 160) * k) / 60, y = h - 60 - (priceAt(tt) / 52) * 200; if (k) g.lineTo(x, y); else g.moveTo(x, y); }
    g.stroke();
    if (crash) { g.fillStyle = "#e2453c"; g.fillRect(w / 2 - 330, 470, 660, 120); g.fillStyle = "#ffffff"; g.font = '900 100px "Arial Black", Arial'; g.textAlign = "center"; g.fillText("CRASH!", w / 2, 534); }
  });
};

export const drawCal = (d: DynTex, t: number) => {
  const day = t < 47.95 ? 26 : 27;
  d.set("cal" + day, (g, w, h) => {
    g.fillStyle = "#f4f1ea"; g.fillRect(0, 0, w, h);
    g.fillStyle = "#c0262f"; g.fillRect(0, 0, w, 150);
    g.fillStyle = "#ffffff"; g.font = '900 96px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("MARCH", w / 2, 80);
    g.fillStyle = INK; g.font = '900 300px "Arial Black", Arial'; g.fillText(String(day), w / 2, 350);
    g.fillStyle = day === 27 ? "#c0262f" : "#5a6478"; g.font = '900 60px "Arial Black", Arial'; g.fillText(day === 27 ? "THURSDAY" : "WEDNESDAY", w / 2, 530);
    g.fillStyle = "#5a6478"; g.font = '900 54px Arial'; g.fillText("1980", w / 2, 600);
    g.strokeStyle = INK; g.lineWidth = 12; g.strokeRect(6, 6, w - 12, h - 12);
    for (let x = 90; x < w; x += 110) { g.fillStyle = "#9aa6b5"; g.beginPath(); g.arc(x, 20, 14, 0, 7); g.fill(); }
  });
};

export const drawConsole = (d: DynTex, t: number) => {
  const on = Math.floor(t * 5) % 2;
  d.set("con" + on, (g, w, h) => {
    g.fillStyle = "#3a3d4a"; g.fillRect(0, 0, w, h);
    const btn = (x: number, fill: string, label: string, glow: boolean) => {
      if (glow) { const gr = g.createRadialGradient(x, 250, 60, x, 250, 230); gr.addColorStop(0, "rgba(255,80,80,.8)"); gr.addColorStop(1, "rgba(255,80,80,0)"); g.fillStyle = gr; g.fillRect(x - 240, 20, 480, 470); }
      g.fillStyle = fill; g.strokeStyle = INK; g.lineWidth = 16; g.beginPath(); g.arc(x, 250, 170, 0, 7); g.fill(); g.stroke();
      g.fillStyle = "rgba(255,255,255,.35)"; g.beginPath(); g.ellipse(x - 50, 190, 70, 34, -0.5, 0, 7); g.fill();
      g.fillStyle = "#ffffff"; g.font = '900 110px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(label, x, 258);
    };
    btn(260, "#7a7f8c", "BUY", false);
    // padlock over BUY
    g.fillStyle = "#e8c45a"; g.strokeStyle = INK; g.lineWidth = 12; g.beginPath(); g.roundRect(190, 300, 140, 110, 14); g.fill(); g.stroke();
    g.beginPath(); g.arc(260, 300, 46, Math.PI, 0); g.stroke();
    btn(w - 260, on ? "#ff3b3b" : "#c0262f", "SELL", !!on);
  });
};

export const drawScreen = (d: DynTex, t: number) => {
  const p = priceAt(t), f = t > 50.85;
  d.set("scr" + p.toFixed(1) + (f ? "f" : "u") + (Math.floor(t * 3) % 2), (g, w, h) => {
    g.fillStyle = "#0e1a12"; g.fillRect(0, 0, w, h);
    g.fillStyle = f ? "#ff5a5a" : "#46f08f"; g.font = '700 34px "Courier New", monospace'; g.textAlign = "left"; g.textBaseline = "middle";
    g.fillText("Ag " + p.toFixed(2) + (f ? " ▼" : " ▲"), 14, 40);
    for (let k = 0; k < 4; k++) g.fillText(["Au", "Cu", "Pt", "Pd"][k] + " " + (100 + ((k * 37 + Math.floor(t * 3)) % 90)).toFixed(0), 14, 86 + k * 26);
  });
};

export const drawPrices = (d: DynTex, t: number) => {
  const k = 1 + 1.7 * ease((t - 12.5) / 1.6), q = Math.round(k * 20) / 20;
  d.set("pr" + q, (g, w, h) => {
    g.fillStyle = "#1c2f22"; g.fillRect(0, 0, w, h);
    g.fillStyle = "#e2453c"; g.fillRect(0, 0, w, 96);
    g.fillStyle = "#ffffff"; g.font = '900 60px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(q > 1.05 ? "PRICES UP!" : "TODAY", w / 2, 50);
    g.textAlign = "left"; g.fillStyle = "#f4f1ea"; g.font = '900 64px "Arial Black", Arial';
    [["MILK", 0.39], ["BREAD", 0.29], ["EGGS", 0.59]].forEach(([n, v], i) => {
      g.fillStyle = "#f4f1ea"; g.fillText(String(n), 30, 170 + i * 120);
      g.fillStyle = q > 1.05 ? "#fff36b" : "#f4f1ea"; g.textAlign = "right"; g.fillText("$" + (Number(v) * q).toFixed(2), w - 30, 170 + i * 120); g.textAlign = "left";
    });
    g.strokeStyle = "#f4f1ea"; g.lineWidth = 10; g.strokeRect(5, 5, w - 10, h - 10);
  });
};

/** cart i on the exchange plaza (null = hidden). Carts 0/1 are the brothers', 2..9 the convoy. */
export const cartPath = (i: number, t: number, id: number): V3 | null => {
  const EX = EXCH[0];
  if (id !== 11 && id !== 12) return null;
  const z0 = 11.0 + 3.0 * clamp01((t - 16.55) / 2.55) + 1.2 * clamp01((t - 19.1) / 1.5);
  if (i < 2) return [EX + (i ? 1.05 : -1.05), 0, z0 + 0.95];
  if (id !== 12) return null;
  const k = i - 2, c = k % 4, r = Math.floor(k / 4);
  return [EX - 4.8 + c * 3.2, 0, z0 - 1.8 - r * 2.4 + 0.95];
};
