// Painted canvas textures for the Pepsi-points world (our own designs; no real logos). Every texture is cached by key.
import * as THREE from "three";
import { ctex, jit } from "../bridge/paint";

const INKL = "rgba(36,23,38,0.9)";
const U = (r: () => number, a: number, b: number) => a + (b - a) * r();
const blot = (g: CanvasRenderingContext2D, x: number, y: number, rad: number, rgb: string, a: number) => {
  const gr = g.createRadialGradient(x, y, 0, x, y, rad);
  gr.addColorStop(0, `rgba(${rgb},${a})`); gr.addColorStop(1, `rgba(${rgb},0)`);
  g.fillStyle = gr; g.fillRect(x - rad, y - rad, rad * 2, rad * 2);
};

/** asphalt with painted speckle, soft tyre wear and a dashed yellow centre line (u along the road, 1 tile = 8 m) */
export const asphalt = () => ctex("asphalt", 1024, 1024, (g, r) => {
  g.fillStyle = "#5d5f6e"; g.fillRect(0, 0, 1024, 1024);
  for (let i = 0; i < 26; i++) blot(g, U(r, 0, 1024), U(r, 0, 1024), U(r, 60, 200), r() < 0.5 ? "40,40,52" : "120,122,138", U(r, 0.06, 0.14));
  for (let i = 0; i < 2600; i++) { g.fillStyle = r() < 0.5 ? "rgba(30,30,40,.35)" : "rgba(170,170,185,.3)"; g.fillRect(U(r, 0, 1024), U(r, 0, 1024), 3, 3); }
  // tyre wear bands
  for (const y of [300, 380, 640, 720]) { g.fillStyle = "rgba(40,40,52,.12)"; g.fillRect(0, y, 1024, 46); }
  // centre dashes
  g.fillStyle = "#f2c94c"; for (let x = 0; x < 1024; x += 256) g.fillRect(x + 20, 500, 150, 24);
  g.strokeStyle = "rgba(255,255,255,.75)"; g.lineWidth = 14; g.beginPath(); g.moveTo(0, 60); g.lineTo(1024, 60); g.moveTo(0, 964); g.lineTo(1024, 964); g.stroke();
  // cracks
  g.strokeStyle = "rgba(30,28,40,.45)"; g.lineWidth = 3;
  for (let i = 0; i < 9; i++) { let x = U(r, 0, 1024), y = U(r, 0, 1024); g.beginPath(); g.moveTo(x, y); for (let k = 0; k < 6; k++) { x += U(r, -40, 40); y += U(r, -40, 40); g.lineTo(x, y); } g.stroke(); }
});
/** concrete sidewalk slabs 1.5 m */
export const slabs = () => ctex("slabs", 512, 512, (g, r) => {
  g.fillStyle = "#cfc8bb"; g.fillRect(0, 0, 512, 512);
  for (let y = 0; y < 512; y += 128) for (let x = 0; x < 512; x += 128) { g.fillStyle = jit(r, "#d6cfc2", 0.05); g.fillRect(x + 3, y + 3, 122, 122); }
  for (let i = 0; i < 30; i++) blot(g, U(r, 0, 512), U(r, 0, 512), U(r, 20, 60), "120,110,100", 0.08);
});
export const lawn = () => ctex("lawnP", 1024, 1024, (g, r) => {
  g.fillStyle = "#6fb24f"; g.fillRect(0, 0, 1024, 1024);
  for (let i = 0; i < 40; i++) blot(g, U(r, 0, 1024), U(r, 0, 1024), U(r, 60, 180), r() < 0.5 ? "70,140,60" : "150,200,90", U(r, 0.12, 0.25));
  for (let i = 0; i < 3500; i++) {
    const x = U(r, 0, 1024), y = U(r, 0, 1024);
    g.strokeStyle = r() < 0.5 ? "rgba(60,120,50,.5)" : "rgba(170,215,110,.45)"; g.lineWidth = 2;
    g.beginPath(); g.moveTo(x, y); g.lineTo(x + U(r, -4, 4), y - U(r, 6, 14)); g.stroke();
  }
});
export const woodFloor = (key = "wfloor", base = "#b07a4c") => ctex(key, 1024, 1024, (g, r) => {
  g.fillStyle = base; g.fillRect(0, 0, 1024, 1024);
  for (let y = 0; y < 1024; y += 64) {
    let x = -U(r, 0, 300);
    while (x < 1024) {
      const w = U(r, 220, 420);
      g.fillStyle = jit(r, base, 0.1, 4); g.fillRect(x + 2, y + 2, w - 4, 60);
      g.strokeStyle = "rgba(60,30,15,.18)"; g.lineWidth = 2;
      for (let k = 0; k < 3; k++) { const yy = y + U(r, 10, 54); g.beginPath(); g.moveTo(x + 6, yy); g.bezierCurveTo(x + w * 0.3, yy + U(r, -6, 6), x + w * 0.6, yy + U(r, -6, 6), x + w - 6, yy); g.stroke(); }
      g.fillStyle = "rgba(255,240,210,.12)"; g.fillRect(x + 2, y + 2, w - 4, 6);
      x += w;
    }
  }
});
export const carpet = (key: string, base: string) => ctex(key, 512, 512, (g, r) => {
  g.fillStyle = base; g.fillRect(0, 0, 512, 512);
  for (let i = 0; i < 5000; i++) { g.fillStyle = r() < 0.5 ? "rgba(0,0,0,.08)" : "rgba(255,255,255,.07)"; g.fillRect(U(r, 0, 512), U(r, 0, 512), 2, 2); }
  for (let i = 0; i < 16; i++) blot(g, U(r, 0, 512), U(r, 0, 512), U(r, 40, 120), "0,0,0", 0.05);
});
/** interior wall: paint with soft wainscot band + skirting */
export const wallPaint = (key: string, top: string, low: string, stripe = false) => ctex(key, 1024, 512, (g, r) => {
  g.fillStyle = top; g.fillRect(0, 0, 1024, 512);
  if (stripe) for (let x = 0; x < 1024; x += 64) { g.fillStyle = "rgba(255,255,255,.07)"; g.fillRect(x, 0, 30, 330); }
  for (let i = 0; i < 18; i++) blot(g, U(r, 0, 1024), U(r, 0, 330), U(r, 50, 160), "0,0,0", 0.035);
  g.fillStyle = low; g.fillRect(0, 330, 1024, 182);
  for (let x = 0; x < 1024; x += 128) { g.strokeStyle = "rgba(0,0,0,.18)"; g.lineWidth = 3; g.strokeRect(x + 14, 352, 100, 120); }
  g.fillStyle = "rgba(255,255,255,.35)"; g.fillRect(0, 326, 1024, 8);
  g.fillStyle = "#3a2a2a"; g.fillRect(0, 490, 1024, 22);
});
export const woodPanel = () => ctex("woodPanel", 1024, 512, (g, r) => {
  g.fillStyle = "#7a4a2c"; g.fillRect(0, 0, 1024, 512);
  for (let x = 0; x < 1024; x += 170) {
    g.fillStyle = jit(r, "#8a5634", 0.06); g.fillRect(x + 10, 20, 150, 472);
    g.strokeStyle = "rgba(30,15,8,.5)"; g.lineWidth = 4; g.strokeRect(x + 22, 34, 126, 444);
    g.fillStyle = "rgba(255,220,170,.10)"; g.fillRect(x + 26, 38, 118, 10);
    g.strokeStyle = "rgba(40,20,10,.15)"; g.lineWidth = 2;
    for (let k = 0; k < 8; k++) { const xx = x + U(r, 30, 140); g.beginPath(); g.moveTo(xx, 40); g.bezierCurveTo(xx + U(r, -8, 8), 200, xx + U(r, -8, 8), 330, xx, 470); g.stroke(); }
  }
});
export const marble = () => ctex("marble", 512, 512, (g, r) => {
  g.fillStyle = "#ece6da"; g.fillRect(0, 0, 512, 512);
  g.strokeStyle = "rgba(150,140,130,.35)";
  for (let i = 0; i < 14; i++) { g.lineWidth = U(r, 1, 3); let x = U(r, 0, 512), y = 0; g.beginPath(); g.moveTo(x, y); while (y < 512) { x += U(r, -30, 30); y += U(r, 20, 50); g.lineTo(x, y); } g.stroke(); }
  for (let y = 0; y < 512; y += 128) { g.fillStyle = "rgba(0,0,0,.08)"; g.fillRect(0, y, 512, 3); }
});
/** glass curtain wall for the HQ tower: blue panes, sky reflections, mullions */
export const glassTower = () => ctex("glassTower", 512, 1024, (g, r) => {
  const gr = g.createLinearGradient(0, 0, 512, 1024); gr.addColorStop(0, "#9cc9f0"); gr.addColorStop(0.5, "#4f86c9"); gr.addColorStop(1, "#2e5a9a");
  g.fillStyle = gr; g.fillRect(0, 0, 512, 1024);
  for (let y = 0; y < 1024; y += 64) for (let x = 0; x < 512; x += 64) {
    g.fillStyle = `rgba(255,255,255,${U(r, 0, 0.18)})`; g.fillRect(x + 4, y + 4, 56, 56);
    if (r() < 0.12) { g.fillStyle = "rgba(255,240,190,.35)"; g.fillRect(x + 4, y + 4, 56, 56); }
  }
  g.strokeStyle = "rgba(255,255,255,.35)"; g.lineWidth = 18; g.beginPath(); g.moveTo(-40, 700); g.lineTo(560, 200); g.stroke();
  g.fillStyle = "#1f3354"; for (let y = 0; y < 1024; y += 64) g.fillRect(0, y, 512, 5); for (let x = 0; x < 512; x += 64) g.fillRect(x, 0, 5, 1024);
});
export const schoolBrick = () => ctex("schoolBrick", 1024, 1024, (g, r) => {
  g.fillStyle = "#e8d2b4"; g.fillRect(0, 0, 1024, 1024);
  const bw = 64, bh = 22;
  for (let y = 0, row = 0; y < 1024; y += bh, row++) for (let x = -(row % 2) * bw / 2; x < 1024; x += bw) { g.fillStyle = jit(r, "#c4583a", 0.12, 6); g.fillRect(x + 2, y + 2, bw - 4, bh - 4); }
  for (let i = 0; i < 10; i++) blot(g, U(r, 0, 1024), U(r, 0, 1024), U(r, 80, 200), "60,30,20", 0.07);
});
export const chalkboard = (lines: string[], key = "chalk") => ctex(key, 1600, 800, (g, r) => {
  g.fillStyle = "#2f4a3c"; g.fillRect(0, 0, 1600, 800);
  for (let i = 0; i < 40; i++) blot(g, U(r, 0, 1600), U(r, 0, 800), U(r, 60, 200), "230,240,230", U(r, 0.02, 0.06));
  g.fillStyle = "#f4f1e6"; g.textAlign = "center"; g.textBaseline = "middle";
  lines.forEach((l, i) => {
    const big = i === 0;
    g.font = `${big ? 900 : 700} ${big ? 150 : 84}px "Comic Sans MS", "Chalkboard", "Marker Felt", sans-serif`;
    g.fillStyle = i === 0 ? "#fff6c9" : "#f4f1e6";
    g.fillText(l, 800, big ? 150 : 330 + (i - 1) * 130);
  });
  g.strokeStyle = "#f4f1e6"; g.lineWidth = 8; g.beginPath(); g.moveTo(330, 240); g.lineTo(1270, 240); g.stroke();
  g.fillStyle = "#6a4a2c"; g.fillRect(0, 0, 1600, 26); g.fillRect(0, 774, 1600, 26); g.fillRect(0, 0, 26, 800); g.fillRect(1574, 0, 26, 800);
});

/** generic sign / label: rounded panel, ink border, centred multi-line text */
export type SignOpts = { bg: string; fg: string; border?: string; font?: string; sizes?: number[]; w?: number; h?: number; stripe?: string; radius?: number; shadow?: boolean };
export const signTex = (key: string, lines: string[], o: SignOpts) => {
  const W = o.w ?? 1024, H = o.h ?? 512;
  return ctex("sign_" + key, W, H, (g) => drawSign(g, W, H, lines, o));
};
export const drawSign = (g: CanvasRenderingContext2D, W: number, H: number, lines: string[], o: SignOpts) => {
  g.clearRect(0, 0, W, H);
  const rr = o.radius ?? H * 0.08, bw = Math.max(8, H * 0.03);
  g.fillStyle = o.bg; rrect(g, bw / 2, bw / 2, W - bw, H - bw, rr); g.fill();
  if (o.stripe) { g.save(); rrect(g, bw / 2, bw / 2, W - bw, H - bw, rr); g.clip(); g.fillStyle = o.stripe; g.fillRect(0, H * 0.78, W, H * 0.22); g.restore(); }
  g.lineWidth = bw; g.strokeStyle = o.border ?? INKL; rrect(g, bw / 2, bw / 2, W - bw, H - bw, rr); g.stroke();
  g.textAlign = "center"; g.textBaseline = "middle";
  const sizes = o.sizes ?? lines.map((_, i) => (i === 0 ? H * 0.32 : H * 0.16));
  const total = sizes.reduce((a, b) => a + b * 1.12, 0);
  let y = H / 2 - total / 2;
  lines.forEach((l, i) => {
    const s = sizes[i] ?? H * 0.16;
    g.font = `900 ${s}px ${o.font ?? '"Arial Black", "Helvetica Neue", Arial, sans-serif'}`;
    let sc = 1; const mw = g.measureText(l).width; if (mw > W * 0.9) sc = (W * 0.9) / mw;
    g.save(); g.translate(W / 2, y + (s * 1.12) / 2); g.scale(sc, 1);
    if (o.shadow !== false) { g.fillStyle = "rgba(36,23,38,.35)"; g.fillText(l, s * 0.04, s * 0.05); }
    g.fillStyle = o.fg; g.fillText(l, 0, 0);
    g.restore();
    y += s * 1.12;
  });
};
export const rrect = (g: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) => {
  g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath();
};

/** our fictional soda can label (blue body, red/white wave, "POP" wordmark) wrapped around a cylinder */
export const canLabel = () => ctex("canLabel", 1024, 512, (g) => {
  g.fillStyle = "#1d4fb8"; g.fillRect(0, 0, 1024, 512);
  const gr = g.createLinearGradient(0, 0, 1024, 0);
  for (let i = 0; i <= 8; i++) gr.addColorStop(i / 8, i % 2 ? "rgba(255,255,255,0.0)" : "rgba(255,255,255,0.10)");
  g.fillStyle = gr; g.fillRect(0, 0, 1024, 512);
  g.fillStyle = "#f4f1ea"; g.beginPath(); g.moveTo(0, 230); g.bezierCurveTo(300, 160, 700, 330, 1024, 230); g.lineTo(1024, 300); g.bezierCurveTo(700, 400, 300, 230, 0, 300); g.fill();
  g.fillStyle = "#d8323c"; g.beginPath(); g.moveTo(0, 300); g.bezierCurveTo(300, 230, 700, 400, 1024, 300); g.lineTo(1024, 350); g.bezierCurveTo(700, 450, 300, 280, 0, 350); g.fill();
  g.fillStyle = "#ffffff"; g.font = '900 120px "Arial Black", Arial, sans-serif'; g.textAlign = "center"; g.textBaseline = "middle";
  for (const x of [256, 768]) { g.save(); g.translate(x, 130); g.rotate(-0.06); g.fillText("POP!", 0, 0); g.restore(); g.font = '700 46px Arial, sans-serif'; g.fillText("+10 PTS", x, 440); g.font = '900 120px "Arial Black", Arial, sans-serif'; }
  g.fillStyle = "rgba(255,255,255,.35)"; g.fillRect(0, 0, 1024, 16); g.fillRect(0, 496, 1024, 16);
});
export const canTop = () => ctex("canTop", 256, 256, (g) => {
  g.fillStyle = "#c9ccd6"; g.fillRect(0, 0, 256, 256);
  g.strokeStyle = "#8e93a3"; g.lineWidth = 10; g.beginPath(); g.arc(128, 128, 112, 0, 7); g.stroke();
  g.fillStyle = "#a7abb9"; g.beginPath(); g.ellipse(128, 92, 34, 46, 0, 0, 7); g.fill();
  g.fillStyle = "#3a3d4a"; g.beginPath(); g.ellipse(128, 72, 20, 16, 0, 0, 7); g.fill();
});

/** the cheque face, filled with an amount */
export const chequeTex = (amount: string, words: string) => ctex("cheque" + amount, 1400, 620, (g, r) => {
  g.fillStyle = "#e9f3e6"; g.fillRect(0, 0, 1400, 620);
  g.strokeStyle = "rgba(90,140,110,.18)"; g.lineWidth = 2;
  for (let i = 0; i < 70; i++) { g.beginPath(); g.moveTo(0, i * 12); g.bezierCurveTo(400, i * 12 - 40, 900, i * 12 + 40, 1400, i * 12); g.stroke(); }
  g.fillStyle = "#3b6b52"; g.fillRect(0, 0, 1400, 70);
  g.fillStyle = "#f4f1ea"; g.font = '900 44px "Arial Black", Arial'; g.textBaseline = "middle"; g.fillText("FIRST COLLEGE BANK", 40, 36);
  g.fillStyle = "#241726"; g.font = '700 40px "Courier New", monospace'; g.fillText("No. 1996", 1150, 36 + 70);
  g.font = '700 42px Arial'; g.fillText("PAY TO THE ORDER OF", 40, 190);
  g.font = 'italic 700 64px "Brush Script MT", "Comic Sans MS", cursive'; g.fillStyle = "#1c2f7a"; g.fillText("THE SODA COMPANY", 520, 186);
  g.strokeStyle = "#241726"; g.lineWidth = 3; g.beginPath(); g.moveTo(500, 226); g.lineTo(1020, 226); g.stroke();
  g.fillStyle = "#fff"; g.strokeStyle = "#241726"; g.lineWidth = 6; g.fillRect(1050, 140, 320, 100); g.strokeRect(1050, 140, 320, 100);
  g.fillStyle = "#c0262f"; g.font = '900 60px "Arial Black", Arial'; g.textAlign = "center"; g.fillText(amount, 1210, 192); g.textAlign = "left";
  g.fillStyle = "#1c2f7a"; g.font = 'italic 700 52px "Comic Sans MS", cursive'; g.fillText(words, 60, 330);
  g.strokeStyle = "#241726"; g.lineWidth = 3; g.beginPath(); g.moveTo(40, 366); g.lineTo(1360, 366); g.stroke();
  g.fillStyle = "#241726"; g.font = '700 38px Arial'; g.fillText("FOR:", 40, 470);
  g.fillStyle = "#1c2f7a"; g.font = 'italic 700 54px "Comic Sans MS", cursive'; g.fillText("1 Harrier Jet, pls", 150, 466);
  g.font = 'italic 700 60px "Brush Script MT", cursive'; g.fillText("John L.", 1000, 466);
  g.strokeStyle = "#241726"; g.beginPath(); g.moveTo(950, 500); g.lineTo(1360, 500); g.stroke();
  g.fillStyle = "#241726"; g.font = '700 36px "Courier New", monospace'; g.fillText("⑆0700000⑆ 1996⑈ 008", 40, 580);
});
/** a coupon "FREE SODA" */
export const couponTex = () => ctex("coupon", 640, 320, (g) => {
  g.fillStyle = "#fff4c2"; g.fillRect(0, 0, 640, 320);
  g.setLineDash([16, 12]); g.strokeStyle = "#241726"; g.lineWidth = 8; g.strokeRect(14, 14, 612, 292); g.setLineDash([]);
  g.fillStyle = "#d8323c"; g.font = '900 104px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("FREE", 320, 110);
  g.fillStyle = "#1d4fb8"; g.font = '900 64px "Arial Black", Arial'; g.fillText("SODA!", 320, 200);
  g.fillStyle = "#241726"; g.font = '700 30px Arial'; g.fillText("(no jets)", 320, 266);
});
/** the catalogue page with the fine print */
export const catalogTex = () => ctex("catalog", 1024, 1400, (g, r) => {
  g.fillStyle = "#fbf7ee"; g.fillRect(0, 0, 1024, 1400);
  g.fillStyle = "#1d4fb8"; g.fillRect(0, 0, 1024, 170);
  g.fillStyle = "#fff"; g.font = '900 86px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("POINTS CATALOG", 512, 88);
  const items: [string, string][] = [["T-SHIRT", "75 PTS"], ["SHADES", "175 PTS"], ["JACKET", "1,450 PTS"], ["HARRIER JET", "7,000,000 PTS"]];
  items.forEach(([n, p], i) => {
    const y = 230 + i * 210;
    g.fillStyle = i === 3 ? "#ffe9a8" : "#eef2fb"; g.fillRect(60, y, 904, 180);
    g.strokeStyle = "#241726"; g.lineWidth = 5; g.strokeRect(60, y, 904, 180);
    g.fillStyle = "#241726"; g.textAlign = "left"; g.font = '900 64px "Arial Black", Arial'; g.fillText(n, 100, y + 90);
    g.textAlign = "right"; g.fillStyle = "#d8323c"; g.font = '900 58px "Arial Black", Arial'; g.fillText(p, 924, y + 90);
  });
  g.textAlign = "left"; g.fillStyle = "#6a6070"; g.font = '400 22px Arial';
  for (let i = 0; i < 9; i++) g.fillText("Offer good while supplies last. Void where prohibited. Points have no cash value. Allow 4-6 weeks.".slice(0, 60 + (i % 3) * 10), 60, 1100 + i * 26);
  // THE line
  g.fillStyle = "#fff36b"; g.fillRect(52, 1338, 920, 44);
  g.fillStyle = "#241726"; g.font = '700 30px Arial'; g.fillText("* Need more? Buy extra points for 10¢ each.", 64, 1360);
});
