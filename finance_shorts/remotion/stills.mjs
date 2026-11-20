// node stills.mjs <entry> <compId> <outPrefix> <frames> [scale]   (software WebGL via SwiftShader/ANGLE)
import fs from "node:fs";
import path from "node:path";
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
const [entry, id, prefix, frames, scale = "0.5"] = process.argv.slice(2);
const browserExecutable = process.env.CHROME || "/opt/pw-browsers/chromium/chrome-linux/chrome";
const chromiumOptions = { gl: process.env.GL || "swangle" };
const t0 = Date.now();
const serveUrl = await bundle({ entryPoint: path.resolve(entry), publicDir: path.resolve("public") });
console.log("bundle", ((Date.now() - t0) / 1000).toFixed(1) + "s");
const composition = await selectComposition({ serveUrl, id, browserExecutable, chromiumOptions });
const onBrowserLog = (l) => { if (l.type === "error") console.log(`[${l.type}]`, l.text.slice(0, 300)); };
for (const f of frames.split(",").map(Number)) {
  const t1 = Date.now();
  await renderStill({ composition, serveUrl, frame: f, output: `${prefix}${f}.jpg`, imageFormat: "jpeg", jpegQuality: 88, scale: Number(scale),
    browserExecutable, chromiumOptions, timeoutInMilliseconds: 600000, onBrowserLog });
  console.log("still", f, ((Date.now() - t1) / 1000).toFixed(1) + "s");
}
