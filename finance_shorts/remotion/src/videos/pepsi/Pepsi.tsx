// "The Kid Who Tried to Buy a Jet With Soda Points": flat 2D cast in a real three.js toon world (claude-animated-shorts
// look engine: ink pass -> lens blur -> bloom -> neutral tone map -> grade), hard cuts, word-by-word captions.
import React, { useEffect, useMemo } from "react";
import * as THREE from "three";
import { AbsoluteFill, getInputProps, useCurrentFrame } from "remotion";
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
const clean = (w: string) => w.replace(/^(\d{3}),/, "$$$1,").replace(/\.$/, (m) => m);
const HOT = /(\d|jet|million|grand|free|sued|lost|kidding|arbitrage|insanity|criminal|school|forever|discount|inflation)/i;

const Captions: React.FC<{ t: number }> = ({ t }) => {
  const c = CHUNKS.find((k) => t >= k.s - 0.03 && t < k.e);
  if (!c) return null;
  const pop = Math.min(1, (t - c.s + 0.03) / 0.09);
  const sc = 0.82 + 0.18 * pop + 0.04 * Math.sin(Math.min(1, pop) * Math.PI);
  return (
    <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", top: "63%" }}>
      <div style={{ transform: `scale(${sc})`, display: "flex", flexWrap: "wrap", justifyContent: "center", gap: "0 22px", maxWidth: 940, textAlign: "center" }}>
        {c.words.map((w, i) => {
          const live = t >= w.s - 0.03;
          const cur = live && (i === c.words.length - 1 || t < c.words[i + 1].s - 0.03);
          const txt = w.w.startsWith("$") || w.w.startsWith(",") || w.w.startsWith(".") ? w.w : w.w;
          const hot = HOT.test(txt);
          return (
            <span key={i} style={{
              fontFamily: '"Arial Black", "Helvetica Neue", Arial, sans-serif', fontWeight: 900, fontSize: 92, lineHeight: 1.08, letterSpacing: -1,
              color: cur ? (hot ? "#ffe14a" : "#ffffff") : hot ? "#ffe14a" : "#ffffff", opacity: live ? 1 : 0,
              WebkitTextStroke: "14px #1b1220", paintOrder: "stroke fill", textTransform: "uppercase",
              textShadow: "0 8px 0 rgba(27,18,32,0.55)", display: "inline-block", transform: cur ? "translateY(-6px) scale(1.06)" : "none",
            }}>{clean(txt)}</span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const dprOverride = () => (getInputProps() as { post?: { dpr?: number } }).post?.dpr;
export const PepsiShort: React.FC = () => {
  const f = useCurrentFrame();
  const on = toggles();
  return (
    <AbsoluteFill style={{ background: "#cfe3f2" }}>
      <ThreeCanvas width={1080} height={1920} {...(dprOverride() ? { dpr: dprOverride() } : {})} shadows gl={{ antialias: false, stencil: false, powerPreference: "high-performance", toneMappingExposure: 1.0 }}
        camera={{ fov: 40, near: 0.05, far: 1500 }}>
        <Inner />
      </ThreeCanvas>
      {on.captions ? <Captions t={f / FPS} /> : null}
    </AbsoluteFill>
  );
};
