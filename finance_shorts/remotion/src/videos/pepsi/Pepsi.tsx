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
import { Captions, HookTitle } from "./captions";

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
  // depth of field only on shots that use it (it is ~40 % of the frame cost)
  const useLens = on.lens && shotAt(f / FPS).dof > 0;
  const post = useMemo(() => (
    <EffectComposer multisampling={4}>
      {on.ink ? <primitive object={fx.ink} dispose={null} /> : null}
      {useLens ? <primitive object={fx.lens.pre} dispose={null} /> : null}
      {useLens ? <primitive object={fx.lens.main} dispose={null} /> : null}
      {on.bloom ? <primitive object={fx.bloom} dispose={null} /> : null}
      <primitive object={fx.tone} dispose={null} />
      {on.grade ? <primitive object={fx.grade} dispose={null} /> : null}
    </EffectComposer>
  ), [fx, on, useLens]);
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

const dprOverride = () => (getInputProps() as { post?: { dpr?: number } }).post?.dpr;
export const PepsiShort: React.FC = () => {
  const f = useCurrentFrame();
  const [fh] = useState(() => delayRender("fonts"));
  useEffect(() => { Promise.all([document.fonts.load('900 96px "Montserrat"'), document.fonts.load('italic 900 96px "Playfair Display"')]).finally(() => continueRender(fh)); }, [fh]);
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

/** captions + hook headline only, on a transparent background (composited over the 3D render with ffmpeg) */
export const PepsiCaptions: React.FC = () => {
  const f = useCurrentFrame();
  const [fh] = useState(() => delayRender("fonts"));
  useEffect(() => { Promise.all([document.fonts.load('900 96px "Montserrat"'), document.fonts.load('italic 900 96px "Playfair Display"')]).finally(() => continueRender(fh)); }, [fh]);
  return (<AbsoluteFill><Captions t={f / FPS} /><HookTitle t={f / FPS} /></AbsoluteFill>);
};
