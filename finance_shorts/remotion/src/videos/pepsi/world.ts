// Poses the whole Pepsi-points world for frame f: camera, camera-relative sun (frozen per shot), sky/fog, the jet,
// the price board, TV / calculator screens, cheques, coin, gavel, bus, inflation arrow, and the cast cards.
import * as THREE from "three";
import { TONE, CHAR, untone } from "../bridge/shade";
import { LIGHTS, LOOK } from "../bridge/lights";
import { NOINK } from "../bridge/ink";
import { cloudHD } from "../bridge/paint";
import { Pool, Actor, Fx } from "../bridge/cast";
import { Sets, ROOM, A, drawPrice } from "./sets";
import { FPS, SHOTS, Shot, camAt, shotAt, BOARD, jetPass, arrowH, ARROW } from "./story";
import { stage } from "./cast";

const V = (x: number, y: number, z: number) => new THREE.Vector3(x, y, z);
const clamp01 = (x: number) => Math.min(1, Math.max(0, x));
const smooth = (x: number) => { const u = clamp01(x); return u * u * (3 - 2 * u); };
const bounceIn = (u: number) => { // drop with two bounces, 0 -> 1
  if (u < 0.55) return (u / 0.55) ** 2;
  if (u < 0.8) { const k = (u - 0.675) / 0.125; return 1 - 0.12 * (1 - k * k); }
  const k = (u - 0.9) / 0.1; return 1 - 0.03 * (1 - k * k);
};

export class World {
  root = new THREE.Group();
  sets = new Sets();
  private pool = new Pool();
  private actors: Actor[] = [];
  private fxs: Fx[] = [];
  private sun: THREE.DirectionalLight; private hemi: THREE.HemisphereLight;
  private sky: THREE.Mesh; private skyMat: THREE.ShaderMaterial;
  private fog = new THREE.Fog("#bccbec", 25, 420);
  private sunCache = new Map<number, THREE.Vector3>();
  private clouds: THREE.Mesh[] = [];
  private cloudMaps: Record<"day" | "golden", THREE.Texture[]>;
  private frustum = new THREE.Frustum(); private m4 = new THREE.Matrix4(); private v = new THREE.Vector3(); private sph = new THREE.Sphere();

  constructor() {
    const R = this.root;
    R.add(this.sets.root);
    this.skyMat = new THREE.ShaderMaterial({
      uniforms: { c0: { value: new THREE.Color() }, c1: { value: new THREE.Color() }, c2: { value: new THREE.Color() }, c3: { value: new THREE.Color() }, c4: { value: new THREE.Color() }, e: { value: new THREE.Vector4() } },
      vertexShader: "varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
      fragmentShader: `uniform vec3 c0, c1, c2, c3, c4; uniform vec4 e; varying vec3 vP;
        void main(){ float el = asin(clamp(normalize(vP).y, -1.0, 1.0));
          vec3 c = mix(c0, c1, smoothstep(0.0, e.x, el)); c = mix(c, c2, smoothstep(e.x, e.y, el));
          c = mix(c, c3, smoothstep(e.y, e.z, el)); c = mix(c, c4, smoothstep(e.z, e.w, el)); gl_FragColor = vec4(c, 1.0); }`,
      side: THREE.BackSide, depthWrite: false, fog: false,
    });
    this.sky = new THREE.Mesh(new THREE.SphereGeometry(1100, 48, 24), this.skyMat);
    this.sky.renderOrder = -1; this.sky.frustumCulled = false; this.sky.layers.set(NOINK); R.add(this.sky);
    this.hemi = new THREE.HemisphereLight("#cfe6ff", "#6c5c8c", 0.5);
    this.sun = new THREE.DirectionalLight("#fff0d6", 2.6);
    this.sun.castShadow = true; this.sun.shadow.mapSize.set(2048, 2048);
    R.add(this.hemi, this.sun, this.sun.target);
    this.cloudMaps = { day: [0, 1, 2, 3].map((k) => cloudHD(k, LOOK.day.cloud)), golden: [0, 1, 2, 3].map((k) => cloudHD(k, LOOK.golden.cloud)) };
    for (let i = 0; i < 10; i++) {
      const a = (i / 10) * Math.PI * 2 + 0.3, d = 560 + (i % 3) * 70, w = 130 + (i % 4) * 30;
      const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: this.cloudMaps.day[i % 4], color: new THREE.Color(1.1, 1.1, 1.1), transparent: true, depthWrite: false, fog: false }));
      m.position.set(Math.cos(a) * d, 110 + (i % 4) * 40, Math.sin(a) * d); m.scale.set(w, w / 2, 1); m.layers.set(NOINK);
      this.clouds.push(m); R.add(m);
    }
  }

  /** camera-relative sun frozen per shot: mean view direction turned by az toward screen right, lifted by el */
  private shotSun(s: Shot) {
    let v = this.sunCache.get(s.id);
    if (v) return v;
    let fx = 0, fz = 0;
    for (let f = Math.ceil(s.s * FPS); f < s.e * FPS; f += 3) {
      const c = camAt(f), x = c.look[0] - c.pos[0], z = c.look[2] - c.pos[2], n = Math.hypot(x, z) || 1;
      fx += x / n; fz += z / n;
    }
    const n = Math.hypot(fx, fz) || 1; fx /= n; fz /= n;
    const L = LIGHTS[s.light];
    const az = THREE.MathUtils.degToRad(s.sunAz ?? (s.light === "golden" ? 35 : 125)), el = THREE.MathUtils.degToRad(s.sunEl ?? (s.light === "golden" ? 14 : L.el));
    const hx = fx * Math.cos(az) - fz * Math.sin(az), hz = fz * Math.cos(az) + fx * Math.sin(az);
    v = new THREE.Vector3(hx * Math.cos(el), Math.sin(el), hz * Math.cos(el)).normalize();
    this.sunCache.set(s.id, v);
    return v;
  }
  private actor(i: number) { while (this.actors.length <= i) this.actors.push(new Actor(this.root)); return this.actors[i]; }
  private fx(i: number) { while (this.fxs.length <= i) this.fxs.push(new Fx(this.root)); return this.fxs[i]; }

  update(f: number, cam: THREE.PerspectiveCamera, scene: THREE.Scene) {
    const t = f / FPS, s = shotAt(t), L = LIGHTS[s.light], K = LOOK[s.light];
    const c = camAt(f);
    cam.position.set(...c.pos); cam.up.set(0, 1, 0); cam.lookAt(...c.look); cam.rotateZ(c.roll);
    cam.fov = c.fov; cam.near = 0.05; cam.far = 1500; cam.updateProjectionMatrix(); cam.updateMatrixWorld();
    cam.layers.enable(NOINK);
    const focus = V(...c.look), dist = cam.position.distanceTo(focus);
    // ---- light rig ----
    const sunDir = this.shotSun(s);
    this.hemi.color.set(L.sky); this.hemi.groundColor.set(L.ground); this.hemi.intensity = L.hemiI;
    this.sun.color.set(L.sunCol); this.sun.intensity = L.sunI;
    const Rr = THREE.MathUtils.clamp(dist * 1.2 + 6, 8, s.id === 30 || s.id === 19 ? 120 : 60);
    this.sun.position.copy(focus).addScaledVector(sunDir, 220); this.sun.target.position.copy(focus);
    const sc = this.sun.shadow.camera;
    sc.left = -Rr; sc.right = Rr; sc.top = Rr; sc.bottom = -Rr; sc.near = 20; sc.far = 480; sc.updateProjectionMatrix();
    this.sun.shadow.bias = L.bias; this.sun.shadow.normalBias = L.normalBias * (Rr / 12);
    TONE.uLitCol.value.set(...L.lit); TONE.uShadeCol.value.set(...L.shade); TONE.uShadeLift.value.set(...L.lift);
    TONE.uLambert.value = L.lambert; TONE.uSideK.value = L.sideK; TONE.uTerm.value = L.term; TONE.uBounce.value.set(...K.bounce); TONE.uSat.value = K.sat;
    CHAR.uCharTint.value.set(...L.charTint); CHAR.uCharShade.value = L.charShade; CHAR.uGrad.value = L.charGrad;
    CHAR.uBodyGrad.value = L.bodyGrad; CHAR.uSideTint.value.set(...L.sideTint);
    const su = this.skyMat.uniforms;
    K.sky.c.forEach((h, i) => untone(h, su["c" + i].value));
    const e = K.sky.e.map((deg) => THREE.MathUtils.degToRad(deg));
    su.e.value.set(e[1], e[2], e[3], e[4]);
    this.sky.position.copy(cam.position);
    untone(L.fog, this.fog.color); this.fog.near = L.fogNear + 20; this.fog.far = L.fogFar + 120;
    scene.fog = this.fog; scene.background = null;
    for (let i = 0; i < this.clouds.length; i++) {
      const m = this.clouds[i]; m.lookAt(cam.position.x, m.position.y, cam.position.z);
      (m.material as THREE.MeshBasicMaterial).map = this.cloudMaps[s.light][i % 4];
    }
    // ---- props ----
    this.poseProps(s.id, t);
    // ---- cast ----
    const right = V(0, 0, 0).setFromMatrixColumn(cam.matrixWorld, 0);
    const st = stage(s.id, t, s.light, { pos: cam.position, right, sun: sunDir });
    this.frustum.setFromProjectionMatrix(this.m4.multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse));
    let ai = 0;
    const used: Actor[] = [];
    for (const p of st.places) {
      const sc2 = p.scale ?? 1;
      if (!this.frustum.intersectsSphere(this.sph.set(this.v.set(p.x, p.y + 1.1 * sc2, p.z), 3.5))) continue;
      const a = this.actor(ai++);
      const [w, h, k] = p.size ?? [300, 500, 0.5];
      a.r = this.pool.req(p.key, w, h, k, p.draw);
      a.mesh.visible = true; a.mesh.position.set(p.x, p.y, p.z);
      a.mesh.rotation.set(0, Math.atan2(cam.position.x - p.x, cam.position.z - p.z), 0);
      a.mesh.scale.set(sc2, sc2, sc2);
      a.mesh.castShadow = L.actorShadow;
      used.push(a);
    }
    for (let i = ai; i < this.actors.length; i++) this.actors[i].mesh.visible = false;
    let fi = 0;
    const fused: Fx[] = [];
    for (const p of st.fx) {
      if (!this.frustum.intersectsSphere(this.sph.set(this.v.set(p.x, p.y, p.z), Math.max(p.w, p.h)))) continue;
      const e2 = this.fx(fi++);
      e2.r = this.pool.req(p.key, p.cw, p.ch, 1, p.draw);
      e2.use(!!p.soft); e2.mesh.visible = true; e2.mesh.position.set(p.x, p.y, p.z);
      if (p.flat) e2.mesh.rotation.set(-Math.PI / 2, 0, p.rot ?? 0);
      else { e2.mesh.quaternion.copy(cam.quaternion); e2.mesh.rotateZ(p.rot ?? 0); }
      e2.mesh.scale.set(p.w, p.h, 1);
      e2.mesh.renderOrder = p.flat ? 0.5 : 2;
      fused.push(e2);
    }
    for (let i = fi; i < this.fxs.length; i++) this.fxs[i].mesh.visible = false;
    this.pool.flush();
    for (const a of used) a.bind();
    for (const e2 of fused) e2.bind();
    return focus;
  }

  private poseProps(id: number, t: number) {
    const S = this.sets, J = S.jet;
    const hide = (...o: THREE.Object3D[]) => o.forEach((x) => (x.visible = false));
    hide(J.group, S.price, S.chequeBig, S.chequeB, S.letter, S.coin, S.gavel, S.arrow, S.dust);
    S.bus.visible = true;
    // bus: parked by the school unless driving in shot 27
    S.bus.position.set(id === 27 ? 62.5 : 96, 0, 2.2); S.bus.rotation.y = 0;
    S.mailFlag.rotation.z = 0;
    // ---- jet ----
    const [jx, , jz] = A.jetLawn;
    const noz = (a: number) => J.nozzles.forEach((n) => (n.rotation.x = a));
    if (id === 2) {
      const p = jetPass(t);
      J.group.visible = true; J.group.position.set(...p); J.group.rotation.set(0.04, -Math.PI / 2, 0.25 * Math.sin(t * 1.3)); J.gear.visible = false; noz(-1.2);
    } else if ([3, 4, 5, 10, 29, 31].includes(id)) {
      J.group.visible = true; J.gear.visible = true;
      let y = 0.1;
      if (id === 3) { const u = clamp01((t - 5.8) / 2.8); y = 0.1 + 13 * (1 - smooth(u)) + 0.08 * Math.sin(t * 9) * (1 - u); }
      J.group.position.set(jx, y, jz); J.group.rotation.set(0, Math.PI / 2, id === 3 ? 0.04 * Math.sin(t * 2.3) : 0); noz(0);
      if (id === 3 && t > 7.2) { S.dust.visible = true; const u = clamp01((t - 7.2) / 2.2); S.dust.position.set(jx, 0.16, jz); S.dust.scale.setScalar(2 + 9 * u); (S.dust.material as THREE.MeshBasicMaterial).opacity = 0.55 * (1 - u); }
    }
    // ---- price board ----
    if ([5, 10, 29, 31].includes(id)) {
      S.price.visible = true;
      let dy = 0;
      if (id === 5) dy = 22 * (1 - bounceIn(clamp01((t - 10.75) / 0.5)));
      S.price.position.set(BOARD[0], BOARD[1] + dy, BOARD[2]); S.price.rotation.set(0, 0.0, 0);
      if (id === 10) S.priceTex.set("worth", (g, w, h) => drawPrice(g, w, h, "$20,000,000+", "REAL VALUE", "", { bg: "#c9f2c0", fg: "#2f7a3a" }));
      else if (id === 29 && t < 69.3) S.priceTex.set("7m", (g, w, h) => drawPrice(g, w, h, "7,000,000", "POINTS", ""));
      else if (id === 29 || id === 31) {
        const big = id === 31 && t > 77.2;
        S.priceTex.set(big ? "700m-jk" : "700m", (g, w, h) => {
          drawPrice(g, w, h, "700,000,000", "POINTS", big ? "" : "just kidding");
          if (big) { g.save(); g.translate(w * 0.72, h * 0.88); g.rotate(-0.08); g.fillStyle = "#241726"; g.beginPath(); g.roundRect(-250, -62, 500, 124, 30); g.fill(); g.fillStyle = "#fff36b"; g.font = '900 78px "Arial Black", Arial'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText("JUST KIDDING", 0, 6); g.restore(); }
        });
      } else S.priceTex.set("7m", (g, w, h) => drawPrice(g, w, h, "7,000,000", "POINTS", ""));
      if (id === 29) { const k = t > 69.3 && t < 69.5 ? 1 - Math.abs(t - 69.4) * 10 : 0; S.price.rotation.x = -0.25 * k; }
    }
    // ---- mailbox cheques ----
    if (id === 1) {
      S.chequeBig.visible = true;
      const u = clamp01((t - 0.3) / 2.1), e = smooth(u);
      S.chequeBig.position.set(2.75 + 0.75 * e, 1.18 + 0.02 * Math.sin(t * 20) * (u > 0.4 ? 1 : 0), -6.2 - 0.85 * e);
      S.chequeBig.rotation.set(-0.15, 0.95 - 0.4 * e, 0.05 * Math.sin(Math.floor(t * 12) * 2.1) * (u > 0.5 ? 1 : 0));
      S.chequeBig.scale.set(1 - 0.1 * e, 1, 1);
    }
    if (id === 18) {
      S.chequeB.visible = true;
      const u = clamp01((t - 39.9) / 0.6);
      S.chequeB.position.set(3.05 + 0.35 * u, 1.16, -6.45 - 0.7 * u); S.chequeB.rotation.set(-0.1, 0.75, 0); S.chequeB.scale.setScalar(0.7);
      if (t > 40.3) S.mailFlag.rotation.z = -Math.min(1.45, (t - 40.3) * 14) + 0.12 * Math.sin((t - 40.3) * 30) * Math.exp(-(t - 40.3) * 5);
    }
    if (id === 19) { // the envelope flying into the tower
      S.letter.visible = true; const u = clamp01((t - 41.7) / 2.4);
      S.letter.position.set(-118 - 12 * u, 2.0 + 30 * u * u, -10 - 20 * u); S.letter.rotation.set(0.3, t * 4, 0.2); S.letter.scale.setScalar(4);
    }
    if (id === 20 || id === 21) { // the cheque in the CEO's hand
      S.chequeB.visible = true;
      S.chequeB.position.set(ROOM.office + 0.55, 1.42 + 0.03 * Math.sin(Math.floor(t * 12) * 1.7), -2.75); S.chequeB.rotation.set(0, 0, 0.12); S.chequeB.scale.setScalar(0.42);
    }
    if (id === 22) {
      S.letter.visible = t < 50; S.letter.position.set(0.1, 1.0, -7.6); S.letter.rotation.set(0, 0, 0.2); S.letter.scale.setScalar(1);
      S.chequeB.visible = t > 49.2; S.chequeB.position.set(-0.55, 1.05, -7.55); S.chequeB.rotation.set(0, 0.1, -0.25); S.chequeB.scale.setScalar(0.4);
    }
    // ---- coin (shot 8) ----
    if (id === 8) {
      S.coin.visible = t > 18.2;
      const u = clamp01((t - 18.2) / 0.5);
      S.coin.position.set(ROOM.dorm + 3.05, 1.02 + 0.32 * (1 - (1 - u) ** 3), -3.5); S.coin.rotation.set(-0.5, (t - 18.2) * 9, 0); S.coin.scale.setScalar(0.11 * (0.4 + 0.6 * smooth(u)));
    }
    // ---- calculator display ----
    const calc = id === 9 ? (t < 20.4 ? "7000000" : t < 21.0 ? "7000000×" : t < 21.55 ? "×0.10" : "700,000.") : "0.";
    S.calcTex.set(calc, (g, w, h) => {
      g.fillStyle = "#b8c9a0"; g.fillRect(0, 0, w, h);
      g.fillStyle = "rgba(0,0,0,.06)"; g.fillRect(0, 0, w, 14);
      g.fillStyle = "#1c2418"; g.font = '700 120px "Courier New", monospace'; g.textAlign = "right"; g.textBaseline = "middle"; g.fillText(calc, w - 20, h / 2 + 6);
    });
    // ---- TV ----
    const tvKey = id === 28 ? `re${Math.floor(t * 6) % 2}` : "ad";
    S.tvTex.set(tvKey, (g, w, h) => drawAd(g, w, h, id === 28, Math.floor(t * 6) % 2));
    // ---- gavel ----
    if (id === 26) {
      S.gavel.visible = true;
      const strike = t < 61.98 ? 0 : clamp01((t - 61.98) / 0.07);
      const raise = t < 61.98 ? smooth((t - 61.8) / 0.18) : 1 - strike;
      S.gavel.position.set(ROOM.court - 0.65, 1.95 + 0.55 * raise, -4.3); S.gavel.rotation.set(0, 0.3, -0.9 * raise);
    }
    // ---- inflation arrow ----
    if (id === 30) {
      S.arrow.visible = true;
      const h = arrowH(t);
      S.arrow.position.set(ARROW[0], 0, ARROW[2]);
      S.arrowBody.scale.set(1, Math.max(0.01, h - 3), 1);
      S.arrowHead.position.set(0, Math.max(1.7, h - 3 + 1.7), 0);
      S.arrow.rotation.z = -0.08;
    }
  }
}

/** the TV ad (2D, unlit screen): sky, a cartoon jet, the price in points; re-air adds "NEW PRICE" */
const drawAd = (g: CanvasRenderingContext2D, w: number, h: number, re: boolean, blink: number) => {
  const gr = g.createLinearGradient(0, 0, 0, h); gr.addColorStop(0, "#5aa0e8"); gr.addColorStop(1, "#cfe6ff");
  g.fillStyle = gr; g.fillRect(0, 0, w, h);
  g.fillStyle = "#6fb24f"; g.fillRect(0, h * 0.78, w, h * 0.22);
  g.save(); g.translate(w * 0.38, h * 0.48); g.rotate(-0.12);
  g.fillStyle = "#9aa6b5"; g.strokeStyle = "#241726"; g.lineWidth = 8;
  g.beginPath(); g.moveTo(-170, 0); g.quadraticCurveTo(-60, -40, 150, -12); g.lineTo(190, 0); g.lineTo(150, 14); g.quadraticCurveTo(-60, 36, -170, 12); g.closePath(); g.fill(); g.stroke();
  g.beginPath(); g.moveTo(-20, 0); g.lineTo(-90, 80); g.lineTo(-40, 80); g.lineTo(40, 6); g.closePath(); g.fill(); g.stroke();
  g.beginPath(); g.moveTo(-150, -4); g.lineTo(-185, -70); g.lineTo(-150, -70); g.lineTo(-115, -6); g.closePath(); g.fill(); g.stroke();
  g.fillStyle = "#3b5f9e"; g.beginPath(); g.ellipse(90, -18, 40, 18, 0, Math.PI, 0); g.fill(); g.stroke();
  g.restore();
  g.fillStyle = "#fff36b"; g.strokeStyle = "#241726"; g.lineWidth = 8; g.beginPath(); g.roundRect(w * 0.52, h * 0.06, w * 0.45, h * 0.3, 18); g.fill(); g.stroke();
  g.fillStyle = "#e2453c"; g.font = `900 ${re ? 46 : 54}px "Arial Black", Arial`; g.textAlign = "center"; g.textBaseline = "middle";
  g.fillText(re ? "700,000,000" : "7,000,000", w * 0.745, h * 0.17);
  g.fillStyle = "#241726"; g.font = '900 30px "Arial Black", Arial'; g.fillText("POINTS", w * 0.745, h * 0.28);
  if (re && blink) { g.fillStyle = "#e2453c"; g.beginPath(); g.roundRect(w * 0.05, h * 0.06, w * 0.36, h * 0.16, 12); g.fill(); g.fillStyle = "#fff"; g.font = '900 34px "Arial Black", Arial'; g.fillText("NEW PRICE!", w * 0.23, h * 0.14); }
  // scanlines
  g.fillStyle = "rgba(0,0,0,.07)"; for (let y = 0; y < h; y += 4) g.fillRect(0, y, w, 2);
};
