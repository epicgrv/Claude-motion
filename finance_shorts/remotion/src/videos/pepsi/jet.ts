// A stylised jump-jet (our own toy-like design inspired by the Harrier silhouette): lathed fuselage, bubble canopy,
// shoulder wings with droop, big cheek intakes, four swivel nozzles, tall fin, outrigger wheels. Origin = ground under
// the centre of mass, nose toward +z. All parts use the world two-tone materials so the ink pass outlines them.
import * as THREE from "three";
import { lam } from "../bridge/build";
import { twoTone } from "../bridge/shade";
import { ctex } from "../bridge/paint";

const V2 = (x: number, y: number) => new THREE.Vector2(x, y);
const skinTex = () => ctex("jetSkin", 1024, 512, (g, r) => {
  g.fillStyle = "#9aa6b5"; g.fillRect(0, 0, 1024, 512);
  // soft camo blotches
  for (let i = 0; i < 26; i++) {
    g.fillStyle = r() < 0.5 ? "rgba(110,124,140,.55)" : "rgba(170,180,192,.5)";
    g.beginPath(); const x = r() * 1024, y = r() * 512; g.ellipse(x, y, 50 + r() * 90, 30 + r() * 50, r() * 3, 0, 7); g.fill();
  }
  // panel lines + rivets
  g.strokeStyle = "rgba(40,40,60,.35)"; g.lineWidth = 3;
  for (let x = 0; x < 1024; x += 128) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, 512); g.stroke(); }
  for (let y = 64; y < 512; y += 128) { g.beginPath(); g.moveTo(0, y); g.lineTo(1024, y); g.stroke(); }
  g.fillStyle = "rgba(40,40,60,.35)"; for (let x = 8; x < 1024; x += 16) for (const y of [70, 198, 326, 454]) g.fillRect(x, y, 3, 3);
});
const wingTex = () => ctex("jetWing", 512, 512, (g) => {
  g.fillStyle = "#93a0b0"; g.fillRect(0, 0, 512, 512);
  g.strokeStyle = "rgba(40,40,60,.35)"; g.lineWidth = 3;
  for (let x = 0; x < 512; x += 96) { g.beginPath(); g.moveTo(x, 0); g.lineTo(x, 512); g.stroke(); }
  g.fillStyle = "#d8323c"; g.fillRect(380, 0, 132, 512); // red tips
  g.fillStyle = "#f4f1ea"; g.beginPath(); g.arc(250, 256, 70, 0, 7); g.fill();
  g.fillStyle = "#1d4fb8"; g.beginPath(); g.arc(250, 256, 44, 0, 7); g.fill();
});
const finTex = () => ctex("jetFin", 512, 512, (g) => {
  g.fillStyle = "#93a0b0"; g.fillRect(0, 0, 512, 512);
  g.fillStyle = "#1d4fb8"; g.fillRect(0, 300, 512, 70); g.fillStyle = "#f4f1ea"; g.fillRect(0, 370, 512, 30); g.fillStyle = "#d8323c"; g.fillRect(0, 400, 512, 70);
  g.fillStyle = "#241726"; g.font = '900 90px "Arial Black", Arial'; g.textAlign = "center"; g.fillText("PTS", 256, 200);
});

const mSkin = () => lam("jetSkinM", () => ({ map: skinTex() }));
const mWing = () => lam("jetWingM", () => ({ map: wingTex(), side: THREE.DoubleSide }));
const mFin = () => lam("jetFinM", () => ({ map: finTex(), side: THREE.DoubleSide }));
const mDark = () => lam("jetDark", () => ({ color: "#3a3f4e" }));
const mIntake = () => lam("jetIntake", () => ({ color: "#20222c" }));
const mTyre = () => lam("jetTyre", () => ({ color: "#2a2a30" }));
const mHub = () => lam("jetHub", () => ({ color: "#d7d9de" }));
const mRed = () => lam("jetRed", () => ({ color: "#d8323c" }));
let canopyM: THREE.Material | null = null;
const mCanopy = () => (canopyM ??= twoTone(new THREE.MeshPhongMaterial({ color: "#3b5f9e", specular: "#ffffff", shininess: 90 })));

/** thin wing panel from a 2D planform (x span, y chord) extruded thin, laid flat in xz */
const panel = (pts: [number, number][], thick: number, mat: THREE.Material) => {
  const s = new THREE.Shape(pts.map(([x, y]) => V2(x, y)));
  const g = new THREE.ExtrudeGeometry(s, { depth: thick, bevelEnabled: true, bevelThickness: thick * 0.4, bevelSize: thick * 0.6, bevelSegments: 2 });
  g.translate(0, 0, -thick / 2);
  g.rotateX(Math.PI / 2); // shape y -> -z (chord toward the tail)
  const m = new THREE.Mesh(g, mat); m.castShadow = m.receiveShadow = true;
  return m;
};

export type Jet = { group: THREE.Group; gear: THREE.Group; nozzles: THREE.Object3D[]; pilot: THREE.Vector3 };
export const buildJet = (): Jet => {
  const G = new THREE.Group();
  const add = (o: THREE.Object3D) => { o.traverse((c) => { const m = c as THREE.Mesh; if (m.isMesh) { m.castShadow = true; m.receiveShadow = true; } }); G.add(o); return o; };
  const Y = 2.05; // fuselage axis height
  // fuselage: lathe profile r(z) from nose (+7) to tail (-7)
  const prof: [number, number][] = [[0.0, 7.4], [0.22, 7.1], [0.48, 6.4], [0.72, 5.4], [0.86, 4.3], [0.95, 2.8], [1.0, 1.0], [0.98, -1.5], [0.86, -3.5], [0.66, -5.2], [0.48, -6.4], [0.36, -7.0], [0.0, -7.05]];
  const lathe = new THREE.LatheGeometry(prof.slice().reverse().map(([r, z]) => V2(r, z)), 28);
  lathe.rotateX(Math.PI / 2); // lathe y -> world z
  lathe.scale(1, 1.08, 1);
  const fus = new THREE.Mesh(lathe, mSkin()); fus.position.y = Y; add(fus);
  // nose tip + pitot
  const tip = new THREE.Mesh(new THREE.ConeGeometry(0.07, 0.9, 10), mDark()); tip.rotation.x = Math.PI / 2; tip.position.set(0, Y, 7.75); add(tip);
  // canopy bubble
  const can = new THREE.Mesh(new THREE.SphereGeometry(1, 28, 18, 0, Math.PI * 2, 0, Math.PI / 2), mCanopy());
  can.scale.set(0.62, 0.62, 1.55); can.position.set(0, Y + 0.62, 3.6); add(can);
  const frame = new THREE.Mesh(new THREE.TorusGeometry(0.62, 0.045, 6, 24, Math.PI), mDark()); frame.position.set(0, Y + 0.62, 3.0); add(frame);
  // dorsal spine
  const spine = new THREE.Mesh(new THREE.CapsuleGeometry(0.42, 4.5, 6, 12), mSkin()); spine.rotation.x = Math.PI / 2; spine.position.set(0, Y + 0.72, -1.2); spine.scale.set(1, 1, 0.6); add(spine);
  // cheek intakes (half pipes either side) + dark mouths
  for (const s of [-1, 1]) {
    const it = new THREE.Mesh(new THREE.CylinderGeometry(0.62, 0.7, 3.4, 18, 1, true), mSkin()); it.material = mSkin();
    it.rotation.x = Math.PI / 2; it.position.set(s * 1.05, Y - 0.05, 1.3); add(it);
    const lip = new THREE.Mesh(new THREE.TorusGeometry(0.62, 0.09, 8, 22), mDark()); lip.position.set(s * 1.05, Y - 0.05, 3.0); add(lip);
    const mouth = new THREE.Mesh(new THREE.CircleGeometry(0.6, 22), mIntake()); mouth.position.set(s * 1.05, Y - 0.05, 2.98); add(mouth);
  }
  // wings: shoulder mounted, swept, drooping (anhedral) - built per side
  for (const s of [-1, 1]) {
    const w = panel([[0, 0], [3.9, -1.9], [3.9, -2.9], [0, -4.6]], 0.16, mWing());
    w.scale.x = s; w.position.set(s * 0.6, Y + 0.6, 0.6); w.rotation.z = s * -0.2; add(w);
    // outrigger wheel at the tip
    const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 1.2, 8), mDark()); leg.position.set(s * 3.9, 0.9, -2.0); add(leg);
    const wh = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.28, 0.18, 14), mTyre()); wh.rotation.z = Math.PI / 2; wh.position.set(s * 3.9, 0.28, -2.0); add(wh);
    // tailplanes (anhedral)
    const tp = panel([[0, 0], [2.3, -1.3], [2.3, -1.9], [0, -2.5]], 0.12, mWing());
    tp.scale.x = s; tp.position.set(s * 0.3, Y + 0.25, -4.6); tp.rotation.z = s * -0.3; add(tp);
    // missiles / pods under the wings
    const pod = new THREE.Mesh(new THREE.CapsuleGeometry(0.17, 1.9, 4, 12), mRed()); pod.rotation.x = Math.PI / 2; pod.position.set(s * 2.4, Y - 0.2, -0.8); add(pod);
    const py = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.5, 0.8), mDark()); py.position.set(s * 2.4, Y + 0.12, -0.8); add(py);
  }
  // fin
  const fin = panel([[0, 0], [1.2, -0.9], [2.6, -1.6], [2.6, -2.5], [0, -2.9]], 0.12, mFin());
  const finG = new THREE.Group(); finG.add(fin); fin.position.set(0, 0, 0); fin.rotation.set(0, 0, Math.PI / 2); finG.position.set(0, Y + 0.6, -3.9); add(finG);
  // four nozzles (two per side), swivel about x
  const nozzles: THREE.Object3D[] = [];
  for (const s of [-1, 1]) for (const z of [0.9, -1.2]) {
    const piv = new THREE.Group(); piv.position.set(s * 1.25, Y - 0.35, z);
    const nz = new THREE.Mesh(new THREE.CylinderGeometry(0.32, 0.4, 0.95, 16), mDark()); nz.position.y = -0.4; piv.add(nz);
    const ring = new THREE.Mesh(new THREE.TorusGeometry(0.36, 0.06, 8, 18), mRed()); ring.rotation.x = Math.PI / 2; ring.position.y = -0.85; piv.add(ring);
    add(piv); nozzles.push(piv);
  }
  // main gear (tandem bicycle gear under the belly)
  const gear = new THREE.Group();
  for (const z of [2.6, -2.2]) {
    const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 1.2, 8), mDark()); leg.position.set(0, 0.9, z); gear.add(leg);
    for (const x of [-0.18, 0.18]) {
      const wh = new THREE.Mesh(new THREE.CylinderGeometry(0.36, 0.36, 0.22, 16), mTyre()); wh.rotation.z = Math.PI / 2; wh.position.set(x, 0.36, z); gear.add(wh);
      const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 0.24, 12), mHub()); hub.rotation.z = Math.PI / 2; hub.position.set(x, 0.36, z); gear.add(hub);
    }
  }
  add(gear);
  // ladder hooked on the cockpit side (for the "beats the bus" pose)
  return { group: G, gear, nozzles, pilot: new THREE.Vector3(0, Y + 0.55, 3.75) };
};
