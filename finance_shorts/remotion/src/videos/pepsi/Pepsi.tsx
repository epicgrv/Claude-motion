// "The Kid Who Tried to Buy a Jet With Soda Points": flat 2D cast in a real three.js toon world (claude-animated-shorts
// look engine: ink pass -> lens blur -> bloom -> neutral tone map -> grade), hard cuts, word-by-word captions.
import React, { useEffect, useMemo, useState } from "react";
import * as THREE from "three";
import { AbsoluteFill, continueRender, delayRender, getInputProps, useCurrentFrame } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import { EffectComposer } from "@react-three/postprocessing";
import { BlendFunction, BloomEffect, ToneMappingEffect, ToneMappingMode } from "postprocessing";
import { InkPass, noInkFallback } from "../bridge/ink";
import { LensBlur } from "../bridge/lensblur";
import { GradeEffect, GRADES, GRADE_STRENGTH, gradeFor } from "../bridge/grade";
import { World } from "./world";
import { TOTAL, FPS, shotAt } from "./story";
import { LINES, Word } from "./vo";
import "@fontsource/montserrat/900.css";

export const PEPSI_FRAMES = TOTAL;

const makeBloom = () => {
  const b = new BloomEffect({ blendFunction: BlendFunction.ADD, intensity: 0.5, luminanceThreshold: 1.0, luminanceSmoothing: 0.2, mipmapBlur: true, levels: 6, radius: 0.6 });
  const mip = b.mipmapBlurPass, setSize = mip.setSize.bind(mip);
  mip.setSize = (w: number, h: number) => setSize(Math.round((1920 * w) / Math.max(h, 1)), 1920);
  return b;
};
const fwd = new THREE.Vector3(), fpt = new THREE.Vector3();
type PostToggles = { ink: boolean; lens: boolean; bloom: boolean; grade: boolean; captions: boolean };
const toggles = (): PostToggles => ({ ink: true, lens: true, bloom: true, grade: true, captions: true, ...((getInputProps() as { post?: Partial<PostToggles> }).post ?? {}) });

const Inner: React.FC = () => {
  const f = useCurrentFrame();
  const { camera, scene } = useThree();
  const world = useMemo(() => new World(), []);
  const on = useMemo(toggles, []);
  const fx = useMemo(() => ({
    ink: new InkPass(scene, camera as THREE.PerspectiveCamera),
    lens: new LensBlur({ maxCoC: 22, nearScale: 1.2 }),
    bloom: makeBloom(),
    tone: new ToneMappingEffect({ mode: ToneMappingMode.NEUTRAL }),
    grade: new GradeEffect(GRADES.day, GRADE_STRENGTH.day),
  }), [camera, scene]);
  useEffect(() => () => fx.ink.dispose(), [fx]);
  const post = useMemo(() => (
    <EffectComposer multisampling={4}>
      {on.ink ? <primitive object={fx.ink} dispose={null} /> : null}
      {on.lens ? <primitive object={fx.lens.pre} dispose={null} /> : null}
      {on.lens ? <primitive object={fx.lens.main} dispose={null} /> : null}
      {on.bloom ? <primitive object={fx.bloom} dispose={null} /> : null}
      <primitive object={fx.tone} dispose={null} />
      {on.grade ? <primitive object={fx.grade} dispose={null} /> : null}
    </EffectComposer>
  ), [fx, on]);
  const cam = camera as THREE.PerspectiveCamera;
  const target = world.update(f, cam, scene);
  noInkFallback(world.root);
  const s = shotAt(f / FPS);
  cam.getWorldDirection(fwd);
  fpt.copy(target);
  fx.lens.focus = Math.max(0.3, fpt.sub(cam.position).dot(fwd));
  fx.lens.cInf = s.dof;
  gradeFor(fx.grade, s.light);
  return (<><primitive object={world.root} dispose={null} />{post}</>);
};

// ---------------- captions ----------------
type Chunk = { words: Word[]; s: number; e: number };
const CHUNKS: Chunk[] = (() => {
  const out: Chunk[] = [];
  for (const l0 of LINES) {
    // glue number pieces the transcriber split ("$700" ",000" / "9" ",900" "%" / "re" "-aired")
    const ws: Word[] = [];
    for (const w of l0.words) {
      const p = ws[ws.length - 1];
      if (p && /^[,.%-]/.test(w.w) && !/^\.\.\./.test(w.w)) ws[ws.length - 1] = { w: p.w + w.w, s: p.s, e: w.e };
      else ws.push({ ...w });
    }
    const l = { ...l0, words: ws };
    let cur: Word[] = [];
    const flush = () => { if (cur.length) out.push({ words: cur, s: cur[0].s, e: cur[cur.length - 1].e }); cur = []; };
    l.words.forEach((w, i) => {
      const prev = l.words[i - 1];
      if (cur.length && (cur.length >= 3 || (prev && w.s - prev.e > 0.3) || /[.,?!…]$/.test(prev?.w ?? ""))) flush();
      cur.push(w);
    });
    flush();
  }
  // each chunk stays until the next starts (max +0.5 s)
  out.forEach((c, i) => { const n = out[i + 1]; c.e = n ? Math.min(n.s, c.e + 0.5) : c.e + 0.6; });
  return out;
})();
const clean = (w: string) => w.replace(/^(\d{3}),/, "$$$1,");
const HOT = /(\d|\$|jet|million|grand|free|sued|lost|kidding|arbitrage|insanity|criminal|school|forever|discount|inflation|loophole|fine|cheap|joke|cans|judge|points)/i;
const EMOJI: [RegExp, string][] = [
  [/loophole/i, "🔍"], [/fine/i, "🔍"], [/jet/i, "✈️"], [/million|grand|\$/i, "💰"], [/cents/i, "🪙"], [/forever/i, "😵"], [/friday|discount/i, "🛍️"],
  [/arbitrage/i, "🧠"], [/insanity/i, "🤯"], [/investors/i, "🤝"], [/school/i, "🏫"], [/criminal/i, "🚨"], [/joke|commercial/i, "😂"],
  [/coupons/i, "🎟️"], [/sued|judge/i, "⚖️"], [/lost/i, "❌"], [/relief/i, "😮‍💨"], [/inflation|hike/i, "📈"], [/kidding/i, "🤡"], [/cans/i, "🥤"], [/bus/i, "🚌"],
];
const FONT = '"Montserrat", "Arial Black", "Noto Color Emoji", sans-serif';

const Captions: React.FC<{ t: number }> = ({ t }) => {
  const c = CHUNKS.find((k) => t >= k.s - 0.03 && t < k.e);
  if (!c) return null;
  const age = t - c.s + 0.03, pop = Math.min(1, age / 0.1);
  const sc = 0.72 + 0.28 * pop + 0.07 * Math.sin(Math.min(1, age / 0.16) * Math.PI);
  let emo = "";
  for (const w of c.words) if (t >= w.s - 0.03) for (const [re, e] of EMOJI) if (re.test(w.w)) { emo = e; break; }
  const eAge = (() => { const w = c.words.find((w) => EMOJI.some(([re]) => re.test(w.w))); return w ? t - w.s : 0; })();
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", top: "61%" }}>
      {emo ? <div style={{ fontFamily: '"Noto Color Emoji"', fontSize: 118, lineHeight: 1, marginBottom: 6,
        transform: `scale(${0.4 + 0.6 * Math.min(1, eAge / 0.12) + 0.12 * Math.sin(Math.min(1, eAge / 0.2) * Math.PI)}) rotate(${-8 + 16 * Math.sin(eAge * 3)}deg)`,
        filter: "drop-shadow(0 6px 0 rgba(20,12,24,.55))" }}>{emo}</div> : null}
      <div style={{ transform: `scale(${sc})`, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 20px", maxWidth: 960, textAlign: "center" }}>
        {c.words.map((w, i) => {
          const live = t >= w.s - 0.03;
          const cur = live && (i === c.words.length - 1 || t < c.words[i + 1].s - 0.03);
          const hot = HOT.test(w.w);
          const bg = cur ? (hot ? "#ffd91a" : "#26d07c") : "transparent";
          return (
            <span key={i} style={{
              fontFamily: FONT, fontWeight: 900, fontSize: 96, lineHeight: 1.12, letterSpacing: -1.5, textTransform: "uppercase",
              color: cur ? "#140c18" : hot ? "#ffd91a" : "#ffffff", opacity: live ? 1 : 0,
              WebkitTextStroke: cur ? "0px" : "13px #140c18", paintOrder: "stroke fill",
              background: bg, borderRadius: 22, padding: cur ? "0 16px" : "0 2px", boxShadow: cur ? "0 8px 0 rgba(20,12,24,0.6)" : "none",
              textShadow: cur ? "none" : "0 8px 0 rgba(20,12,24,0.6)", display: "inline-block",
              transform: cur ? `rotate(${i % 2 ? 2 : -2}deg) scale(1.08)` : "none",
            }}>{clean(w.w)}</span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

/** on-screen hook headline for the first seconds (topic clarity + contrast) */
const HookTitle: React.FC<{ t: number }> = ({ t }) => {
  if (t > 3.3) return null;
  const k = Math.min(1, t / 0.18), out = t > 3.05 ? 1 - (t - 3.05) / 0.25 : 1;
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", top: "9%" }}>
      <div style={{ transform: `scale(${0.6 + 0.4 * k}) rotate(-2deg)`, opacity: out, fontFamily: FONT, fontWeight: 900, fontSize: 66, lineHeight: 1.08,
        textTransform: "uppercase", textAlign: "center", color: "#fff", background: "#e2453c", padding: "18px 30px", borderRadius: 26,
        border: "8px solid #140c18", boxShadow: "0 12px 0 rgba(20,12,24,.6)", maxWidth: 920 }}>
        $20M fighter jet<br /><span style={{ color: "#ffd91a" }}>for $700K?!</span> ✈️
      </div>
    </AbsoluteFill>
  );
};

const dprOverride = () => (getInputProps() as { post?: { dpr?: number } }).post?.dpr;
export const PepsiShort: React.FC = () => {
  const f = useCurrentFrame();
  const [fh] = useState(() => delayRender("fonts"));
  useEffect(() => { Promise.all([document.fonts.load('900 96px "Montserrat"'), document.fonts.load('96px "Noto Color Emoji"', "✈️")]).finally(() => continueRender(fh)); }, [fh]);
  const on = toggles();
  return (
    <AbsoluteFill style={{ background: "#cfe3f2" }}>
      <ThreeCanvas width={1080} height={1920} {...(dprOverride() ? { dpr: dprOverride() } : {})} shadows gl={{ antialias: false, stencil: false, powerPreference: "high-performance", toneMappingExposure: 1.0 }}
        camera={{ fov: 40, near: 0.05, far: 1500 }}>
        <Inner />
      </ThreeCanvas>
      {on.captions ? <Captions t={f / FPS} /> : null}
      {on.captions ? <HookTitle t={f / FPS} /> : null}
    </AbsoluteFill>
  );
};
