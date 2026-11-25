// Infinite Money Glitch text layer (same system as Silver Thursday v2) + sample caption looks: classic / single / neon / boxed.
//  - captions: ONE clean premium font (Montserrat 900, uppercase), white with a thin dark outline + soft shadow,
//    no tilt, no blur, no curvy italic. Key words turn solid yellow, money gets a green pill, "negative" words a red line.
//  - two modes: "multi" (2-4 words, up to 2 lines) and "single" (one big word at a time).
//  - captions sit in the lower safe zone (default 76 % from the top) and move lower where a shot has important text.
//  - banners (BANKRUPT, $1.1 BILLION LOAN, ...) are screen-space labels in a fixed top zone, always fully inside the frame.
import React from "react";
import { AbsoluteFill } from "remotion";
import { LINES, Word } from "./vo";
import "@fontsource/montserrat/800.css";
import "@fontsource/montserrat/900.css";

const SANS = '"Montserrat", "Arial Black", sans-serif';
const INK = "#140c18";
export type CapMode = "multi" | "single" | "auto";
type Look = "classic" | "neon" | "boxed";
/** sample (step 5): which caption look plays when */
const styleAt = (t: number): { kind: "multi" | "single"; look: Look } => { void t; return { kind: "multi", look: "classic" }; }; // user picked style A

type Kind = "money" | "accent" | "scratch" | "small" | "normal";
const YEAR = /^(19\d\d|\d+(st|nd|rd|th))/i;
const MONEY = /\$|million|billion|^\d{1,3}[.,]?$/i;
const ACCENT = /glitch|infinite|button|error|anyway|again|offline|watching|you|friends|jets|hotels|parties|strangers|months|existed|sleep|police|confessed|prison|guilty|bank/i;
const SCRATCH = /^(error|can't|never)[.,!?]*$/i;
const SMALL = /^(a|an|the|to|of|at|for|and|in|is|he|it|so|but|with|on|we|do|was|his|him|be|by|that's|what|who|this|plus|two)[.,!?…]*$/i;
const kindOf = (w: string): Kind => (YEAR.test(w) ? "normal" : MONEY.test(w) ? "money" : SCRATCH.test(w) ? "scratch" : ACCENT.test(w) ? "accent" : SMALL.test(w) ? "small" : "normal");

/** glue number pieces split by the transcriber ("$700" ",000") */
const glue = (ws: Word[]) => {
  const out: Word[] = [];
  for (const w of ws) { const p = out[out.length - 1]; if (p && /^[,.%-]/.test(w.w)) out[out.length - 1] = { w: p.w + w.w, s: p.s, e: w.e }; else out.push({ ...w }); }
  return out;
};
const WORDS: Word[] = LINES.flatMap((l) => glue(l.words));
type Chunk = { words: Word[]; s: number; e: number };
const CHUNKS: Chunk[] = (() => {
  const out: Chunk[] = [];
  for (const l of LINES) {
    const ws = glue(l.words); let cur: Word[] = [];
    const flush = () => { if (cur.length) out.push({ words: cur, s: cur[0].s, e: cur[cur.length - 1].e }); cur = []; };
    ws.forEach((w, i) => { const prev = ws[i - 1]; if (cur.length && (cur.length >= 3 || (prev && w.s - prev.e > 0.3) || /[.,?!…]$/.test(prev?.w ?? ""))) flush(); cur.push(w); });
    flush();
  }
  out.forEach((c, i) => { const n = out[i + 1]; c.e = n ? Math.min(n.s, c.e + 0.4) : c.e + 0.6; });
  return out;
})();
const clean = (w: string) => w.replace(/[,]$/, "").replace(/^(\d{3}),/, "$$$1,").toUpperCase();
const easeOut = (u: number) => 1 - (1 - Math.min(1, Math.max(0, u))) ** 2;
const backOut = (u: number) => { const x = Math.min(1, Math.max(0, u)), c = 1.6; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2; };

/** caption height (top of the caption block, % of frame) per moment: lower where a shot shows important text */
const LOW: [number, number][] = [[0, 3.0], [7.45, 11.2], [24.0, 27.44], [54.7, 58.4], [18.9, 21.0], [50.3, 54.7], [61.0, 64.3]];
const capTop = (t: number) => (LOW.some(([a, b]) => t >= a && t < b) ? 82 : 76);

const OUTLINE = `0 0 2px ${INK}, 0 0 2px ${INK}, 0 0 3px ${INK}`;
const SHADOW = "0 6px 14px rgba(0,0,0,0.55)";
let LOOK: Look = "classic";
const wordStyle = (k: Kind, size: number, cur: boolean): React.CSSProperties => LOOK === "neon" ? ({
  fontFamily: SANS, fontWeight: 900, fontSize: size, letterSpacing: -1, lineHeight: 1.05, color: k === "accent" ? "#3ef0ff" : k === "money" ? "#5cf5a6" : "#ffffff",
  WebkitTextStroke: `${Math.round(size / 16)}px #1a0f2e`, paintOrder: "stroke fill",
  textShadow: k === "accent" ? "0 0 18px rgba(62,240,255,0.9), 0 0 40px rgba(255,79,216,0.6)" : `0 0 16px rgba(255,79,216,${cur ? 0.9 : 0.5}), ${SHADOW}`,
}) : ({
  fontFamily: SANS, fontWeight: 900, fontSize: size, letterSpacing: -1, lineHeight: 1.05, color: k === "accent" ? "#ffd72e" : "#ffffff",
  WebkitTextStroke: LOOK === "boxed" ? "0px" : `${Math.round(size / 14)}px ${INK}`, paintOrder: "stroke fill", textShadow: LOOK === "boxed" ? "none" : `${SHADOW}${cur ? ", 0 0 22px rgba(255,215,46,0.45)" : ""}`,
});
const WordView: React.FC<{ w: Word; t: number; size: number; cur: boolean; out: number }> = ({ w, t, size, cur, out }) => {
  const k = kindOf(w.w), age = t - (w.s - 0.05);
  const sz = k === "small" ? size * 0.72 : size;
  if (age < 0) return <span style={{ ...wordStyle(k, sz, false), opacity: 0, margin: "0 12px" }}>{clean(w.w)}</span>;
  const sc = 0.7 + 0.3 * backOut(age / 0.22) + (cur ? 0.04 : 0);
  const wrap: React.CSSProperties = { display: "inline-block", position: "relative", whiteSpace: "nowrap", margin: "0 12px", opacity: easeOut(age / 0.12) * (1 - out), transform: `scale(${sc})` };
  if (k === "money") {
    const wipe = easeOut((age - 0.06) / 0.18);
    return (
      <span style={{ ...wrap, padding: "4px 22px" }}>
        <span style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${100 * wipe}%`, background: "#22c36e", borderRadius: 18, border: `5px solid ${INK}`, boxShadow: SHADOW }} />
        <span style={{ ...wordStyle(k, sz, false), position: "relative", color: "#ffffff" }}>{clean(w.w)}</span>
      </span>
    );
  }
  if (k === "scratch") {
    const scr = easeOut((age - 0.2) / 0.18);
    return (
      <span style={wrap}>
        <span style={wordStyle(k, sz, cur)}>{clean(w.w)}</span>
        <span style={{ position: "absolute", left: "-3%", top: "46%", height: Math.round(sz / 7), width: `${106 * scr}%`, background: "#ff3b3b", borderRadius: 8, boxShadow: `0 0 0 4px ${INK}` }} />
      </span>
    );
  }
  return <span style={wrap}><span style={wordStyle(k, sz, cur)}>{clean(w.w)}</span></span>;
};

export const Captions: React.FC<{ t: number; mode?: CapMode }> = ({ t, mode = "auto" }) => {
  const st = mode === "auto" ? styleAt(t) : { kind: mode, look: "classic" as Look };
  LOOK = st.look; mode = st.kind;
  const top = `${capTop(t)}%`;
  if (mode === "single") {
    const i = WORDS.findIndex((w, k) => t >= w.s - 0.05 && t < Math.min((WORDS[k + 1]?.s ?? w.e + 0.5) - 0.05, w.e + 0.5));
    if (i < 0) return null;
    return (
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", top }}>
        <WordView key={i} w={WORDS[i]} t={t} size={124} cur={false} out={0} />
      </AbsoluteFill>
    );
  }
  const c = CHUNKS.find((k) => t >= k.s - 0.06 && t < k.e);
  if (!c) return null;
  const out = Math.min(1, Math.max(0, (t - (c.e - 0.12)) / 0.12));
  const lines: Word[][] = c.words.length <= 2 ? [c.words] : [c.words.slice(0, 2), c.words.slice(2)];
  let idx = 0;
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", top }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", maxWidth: 980 }}>
        {lines.map((ln, li) => (
          <div key={li} style={{ display: "flex", justifyContent: "center", alignItems: "center", margin: LOOK === "boxed" ? "6px 0" : "4px 0",
            ...(LOOK === "boxed" ? { background: "rgba(14,10,20,0.88)", borderRadius: 22, padding: "8px 14px", boxShadow: "0 8px 20px rgba(0,0,0,0.35)" } : {}) }}>
            {ln.map((w) => { const i = idx++; const nxt = c.words[i + 1]; const cur = t >= w.s - 0.05 && (!nxt || t < nxt.s - 0.05); return <WordView key={i} w={w} t={t} size={92} cur={cur} out={out} />; })}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

/** on-screen hook headline, first 3.3 s */
export const HookTitle: React.FC<{ t: number }> = ({ t }) => {
  if (t > 3.3) return null;
  const a = (d: number) => easeOut((t - d) / 0.22), out = t > 3.05 ? Math.min(1, (t - 3.05) / 0.25) : 0;
  const st = (d: number, size: number, color: string): React.CSSProperties => ({
    display: "inline-block", opacity: a(d) * (1 - out), transform: `translateY(${30 * (1 - a(d))}px) scale(${0.85 + 0.15 * a(d)})`,
    fontFamily: SANS, fontWeight: 900, fontSize: size, color, letterSpacing: -1.5, WebkitTextStroke: `${Math.round(size / 13)}px ${INK}`, paintOrder: "stroke fill", textShadow: SHADOW,
  });
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", top: "6%" }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", lineHeight: 1.04 }}>
        <span style={st(0.0, 58, "#ffffff")}>HIS BANK HAD AN</span>
        <span style={st(0.15, 96, "#5cf5a6")}>INFINITE MONEY</span>
        <span style={st(0.45, 84, "#ffd72e")}>GLITCH</span>
      </div>
    </AbsoluteFill>
  );
};

// ---------------- banners (screen space, top safe zone) ----------------
type Banner = { s: number; e: number; text: string; bg: string; fg?: string; sub?: string; y?: number };
export const BANNERS: Banner[] = [
  { s: 7.7, e: 10.1, text: "NO HACKING. NO PASSWORDS.", bg: "#14213f" },
  { s: 47.2, e: 50.3, text: "BAR TAB: PAID BY DAN", bg: "#1f8f4e" },
  { s: 67.4, e: 69.7, text: "HE CONFESSED", bg: "#d62f3a" },
  { s: 72.0, e: 76.5, text: "WHO'S REALLY GUILTY?", bg: "#d62f3a", y: 30 },
  { s: 76.5, e: 79.5, text: "COMMENT 1 OR 2", sub: "1 = DAN • 2 = THE BANK", bg: "#ffd72e", fg: INK, y: 30 },
];
export const Banners: React.FC<{ t: number }> = ({ t }) => {
  const b = BANNERS.find((k) => t >= k.s && t < k.e);
  if (!b) return null;
  const age = t - b.s, sc = 0.6 + 0.4 * backOut(age / 0.2), op = easeOut(age / 0.1) * (1 - Math.min(1, Math.max(0, (t - (b.e - 0.12)) / 0.12)));
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", top: `${b.y ?? 10}%` }}>
      <div style={{ transform: `scale(${sc})`, opacity: op, background: b.bg, border: `6px solid ${INK}`, borderRadius: 26, padding: b.sub ? "16px 40px 20px" : "14px 40px",
        boxShadow: "0 10px 0 rgba(20,12,24,0.9), 0 18px 30px rgba(0,0,0,0.35)", maxWidth: 940, textAlign: "center" }}>
        <div style={{ fontFamily: SANS, fontWeight: 900, fontSize: b.text.length > 16 ? 60 : 80, lineHeight: 1.05, color: b.fg ?? "#ffffff", letterSpacing: -1 }}>{b.text}</div>
        {b.sub ? <div style={{ display: "flex", justifyContent: "center", gap: 18, marginTop: 10 }}>{b.sub.split("•").map((x, i) => <span key={i} style={{ fontFamily: SANS, fontWeight: 900, fontSize: 44, lineHeight: 1, color: "#ffffff", background: i ? "#1d3f8a" : "#d62f3a", borderRadius: 14, padding: "8px 18px", whiteSpace: "nowrap" }}>{x.trim()}</span>)}</div> : null}
      </div>
    </AbsoluteFill>
  );
};
