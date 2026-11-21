// v5 captions, mastered from the caption tutorials the user sent:
//  - two fonts: Montserrat 900 (context, uppercase, tight tracking) + Playfair Display 900 italic (accent / power words)
//  - every word enters on its own spoken time with one of three master movements (slide up / from left / from right),
//    fade + blur in, quad ease-out (fast then slow), ~0.26 s
//  - size hierarchy: power words big on their own line, filler words small
//  - power words change colour after landing; money words get an animated highlighter box + shine sweep;
//    "negative" words get a red scratch line drawn through them
//  - thin stroke + soft shadow; phrase fades / blurs out; placed just below the middle (above the chin line)
import React from "react";
import { AbsoluteFill } from "remotion";
import { LINES, Word } from "./vo";
import "@fontsource/montserrat/900.css";
import "@fontsource/playfair-display/900-italic.css";

const SANS = '"Montserrat", "Arial Black", sans-serif';
const SERIF = '"Playfair Display", Georgia, serif';
const INK = "#140c18";

type Kind = "money" | "accent" | "scratch" | "small" | "normal";
const MONEY = /\d|\$|million|grand|cents|%/i;
const ACCENT = /jet|loophole|forever|fine|print|arbitrage|insanity|investors|school|criminal|commercial|coupons|free|sued|judge|unreasonable|relief|aired|inflation|history|kidding|cans|discount|friday|cheap|worth|bus|points|pepsi|park/i;
const SCRATCH = /^(joke|lost|back)[.,!?]*$/i;
const SMALL = /^(a|an|the|to|of|at|for|and|in|is|he|it|so|but|with|on|we|do|was|his|him|be|by|that's|what|who|this|plus|two)[.,!?…]*$/i;
const kindOf = (w: string): Kind => (MONEY.test(w) ? "money" : SCRATCH.test(w) ? "scratch" : ACCENT.test(w) ? "accent" : SMALL.test(w) ? "small" : "normal");

/** glue number pieces split by the transcriber ("$700" ",000", "9" ",900" "%", "re" "-aired") */
const glue = (ws: Word[]) => {
  const out: Word[] = [];
  for (const w of ws) {
    const p = out[out.length - 1];
    if (p && /^[,.%-]/.test(w.w)) out[out.length - 1] = { w: p.w + w.w, s: p.s, e: w.e };
    else out.push({ ...w });
  }
  return out;
};
type Chunk = { words: Word[]; s: number; e: number };
export const CHUNKS: Chunk[] = (() => {
  const out: Chunk[] = [];
  for (const l of LINES) {
    const ws = glue(l.words);
    let cur: Word[] = [];
    const flush = () => { if (cur.length) out.push({ words: cur, s: cur[0].s, e: cur[cur.length - 1].e }); cur = []; };
    ws.forEach((w, i) => {
      const prev = ws[i - 1];
      if (cur.length && (cur.length >= 4 || (prev && w.s - prev.e > 0.3) || /[.,?!…]$/.test(prev?.w ?? ""))) flush();
      cur.push(w);
    });
    flush();
  }
  out.forEach((c, i) => { const n = out[i + 1]; c.e = n ? Math.min(n.s, c.e + 0.45) : c.e + 0.6; });
  return out;
})();
/** lines: big words alone, others up to 2 per line */
const layout = (ws: Word[]) => {
  const lines: Word[][] = [];
  let cur: Word[] = [];
  for (const w of ws) {
    const k = kindOf(w.w), big = k === "money" || k === "accent";
    if (big) { if (cur.length) lines.push(cur); lines.push([w]); cur = []; continue; }
    cur.push(w);
    if (cur.length >= 2) { lines.push(cur); cur = []; }
  }
  if (cur.length) lines.push(cur);
  return lines;
};
const clean = (w: string) => w.replace(/[,]$/, "").replace(/^(\d{3}),/, "$$$1,");
const easeOut = (u: number) => 1 - (1 - Math.min(1, Math.max(0, u))) ** 2;
const titleCase = (w: string) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase();

const backOut = (u: number) => { const x = Math.min(1, Math.max(0, u)), c = 1.9; return 1 + (c + 1) * (x - 1) ** 3 + c * (x - 1) ** 2; };
/** chunky 3D extrusion + soft drop */
const EXTRUDE = [1, 2, 3, 4, 5, 6, 7].map((k) => `0 ${k * 1.6}px 0 ${INK}`).join(", ") + ", 0 16px 26px rgba(0,0,0,0.5)";
/** text with stroke + extrusion underneath and an optional gradient-filled copy on top */
const GText: React.FC<{ text: string; style: React.CSSProperties; grad?: string }> = ({ text, style, grad }) => (
  <span style={{ position: "relative", display: "inline-block" }}>
    <span style={{ ...style, WebkitTextStroke: `7px ${INK}`, paintOrder: "stroke fill", textShadow: EXTRUDE }}>{text}</span>
    {grad ? <span style={{ ...style, position: "absolute", left: 0, top: 0, backgroundImage: grad, WebkitBackgroundClip: "text", backgroundClip: "text", color: "transparent", textShadow: "none" }}>{text}</span> : null}
  </span>
);

const WordView: React.FC<{ w: Word; i: number; t: number; out: number; cur: boolean }> = ({ w, i, t, out, cur }) => {
  const k = kindOf(w.w), age = t - (w.s - 0.05);
  if (age < 0) return <span style={{ display: "inline-block", opacity: 0, fontFamily: SANS, fontWeight: 900, fontSize: 92, margin: "0 12px" }}>{clean(w.w)}</span>;
  const u = Math.min(1, age / 0.24), e = 1 - (1 - u) ** 2, mv = i % 3; // 0 up, 1 from left, 2 from right
  const dx = mv === 1 ? -120 * (1 - e) : mv === 2 ? 120 * (1 - e) : 0, dy = mv === 0 ? 80 * (1 - e) : 0;
  const sc = 0.45 + 0.55 * backOut(age / 0.3) + (cur ? 0.06 : 0);
  const blur = 10 * (1 - e) + out * 8;
  const land = easeOut((age - 0.18) / 0.18);
  const wrap: React.CSSProperties = {
    display: "inline-block", position: "relative", whiteSpace: "nowrap", opacity: e * (1 - out), margin: "0 16px", lineHeight: 1.0,
    transform: `translate(${dx}px, ${dy - out * 26}px) scale(${sc})`, filter: (blur > 0.3 ? `blur(${blur.toFixed(1)}px) ` : "") + (cur ? "drop-shadow(0 0 18px rgba(255,217,26,0.55))" : ""),
  };
  if (k === "accent") {
    const grad = land > 0.05 ? `linear-gradient(180deg, #fff6b0 0%, #ffd91a ${45 - 20 * (1 - land)}%, #ff9a1f 100%)` : undefined;
    return <span style={wrap}><GText text={titleCase(clean(w.w))} grad={grad} style={{ fontFamily: SERIF, fontStyle: "italic", fontWeight: 900, fontSize: 132, color: "#ffffff", letterSpacing: -1, padding: "0 6px" }} /></span>;
  }
  if (k === "money") {
    const wipe = easeOut((age - 0.1) / 0.22), shine = (age - 0.3) / 0.5;
    return (
      <span style={{ ...wrap, padding: "0 20px" }}>
        <span style={{ position: "absolute", left: 0, top: "4%", height: "92%", width: `${100 * wipe}%`, background: "linear-gradient(180deg,#5cf5a6,#18c46e)", borderRadius: 22, border: `6px solid ${INK}`, boxShadow: `0 10px 0 ${INK}`, transform: "rotate(-2deg)" }} />
        <span style={{ position: "relative", fontFamily: SANS, fontWeight: 900, fontSize: 112, letterSpacing: -3, color: wipe > 0.55 ? INK : "#ffffff",
          WebkitTextStroke: wipe > 0.55 ? "0px" : `7px ${INK}`, paintOrder: "stroke fill", textShadow: wipe > 0.55 ? "0 3px 0 rgba(255,255,255,0.35)" : EXTRUDE }}>{clean(w.w).toUpperCase()}</span>
        {shine > 0 && shine < 1 ? <span style={{ position: "absolute", inset: 0, borderRadius: 18, mixBlendMode: "screen",
          background: `linear-gradient(105deg, transparent ${shine * 140 - 30}%, rgba(255,255,255,0.9) ${shine * 140 - 15}%, transparent ${shine * 140}%)` }} /> : null}
      </span>
    );
  }
  if (k === "scratch") {
    const scr = easeOut((age - 0.25) / 0.2);
    return (
      <span style={wrap}>
        <GText text={clean(w.w).toUpperCase()} style={{ fontFamily: SANS, fontWeight: 900, fontSize: 108, letterSpacing: -2, color: "#ffffff" }} />
        <span style={{ position: "absolute", left: "-4%", top: "44%", height: 18, width: `${108 * scr}%`, background: "#ff3b3b", borderRadius: 9, transform: "rotate(-7deg)", boxShadow: `0 0 0 5px ${INK}` }} />
      </span>
    );
  }
  return <span style={wrap}><GText text={clean(w.w).toUpperCase()} style={{ fontFamily: SANS, fontWeight: 900, fontSize: k === "small" ? 66 : 92, letterSpacing: -2, color: cur ? "#fffbe6" : "#ffffff" }} /></span>;
};

export const Captions: React.FC<{ t: number }> = ({ t }) => {
  const c = CHUNKS.find((k) => t >= k.s - 0.06 && t < k.e);
  if (!c) return null;
  const out = Math.min(1, Math.max(0, (t - (c.e - 0.14)) / 0.14));
  let idx = 0;
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", top: "64%" }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", maxWidth: 1000 }}>
        {layout(c.words).map((ln, li) => (
          <div key={li} style={{ display: "flex", justifyContent: "center", alignItems: "baseline", transform: `rotate(${li % 2 ? 2.2 : -2.2}deg)`, margin: "8px 0" }}>
            {ln.map((w) => { const i = idx++; const nxt = c.words[i + 1]; const cur = t >= w.s - 0.05 && (!nxt || t < nxt.s - 0.05); return <WordView key={i} w={w} i={i} t={t} out={out} cur={cur} />; })}
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

/** on-screen hook (topic + contrast) in the same caption language, top of frame, first 3 s */
export const HookTitle: React.FC<{ t: number }> = ({ t }) => {
  if (t > 3.3) return null;
  const a = (d: number) => easeOut((t - d) / 0.26), out = t > 3.05 ? Math.min(1, (t - 3.05) / 0.25) : 0;
  const st = (d: number, dx: number, dy: number): React.CSSProperties => ({
    display: "inline-block", opacity: a(d) * (1 - out), transform: `translate(${dx * (1 - a(d))}px, ${dy * (1 - a(d)) - out * 20}px)`,
    filter: `blur(${(10 * (1 - a(d)) + 8 * out).toFixed(1)}px)`, WebkitTextStroke: `6px ${INK}`, paintOrder: "stroke fill",
    textShadow: "0 7px 16px rgba(0,0,0,0.45), 0 3px 0 rgba(20,12,24,0.55)",
  });
  const wipe = easeOut((t - 0.75) / 0.25);
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", top: "7%" }}>
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", lineHeight: 1.02 }}>
        <span style={{ ...st(0.0, 0, 60), fontFamily: SANS, fontWeight: 900, fontSize: 58, color: "#fff", letterSpacing: -2 }}>HE TRIED TO BUY A</span>
        <span style={{ ...st(0.15, -110, 0), fontFamily: SERIF, fontStyle: "italic", fontWeight: 900, fontSize: 112, color: "#ffd91a" }}>$20M Fighter Jet</span>
        <span style={{ ...st(0.5, 110, 0), fontFamily: SANS, fontWeight: 900, fontSize: 64, color: wipe > 0.6 ? INK : "#fff", letterSpacing: -2, position: "relative", padding: "0 16px",
          WebkitTextStroke: wipe > 0.6 ? "0px" : `6px ${INK}`, textShadow: wipe > 0.6 ? "none" : undefined }}>
          <span style={{ position: "absolute", left: 0, top: "6%", height: "90%", width: `${100 * wipe}%`, background: "#2ee68a", borderRadius: 16, zIndex: -1 }} />
          FOR $700K?!
        </span>
      </div>
    </AbsoluteFill>
  );
};
