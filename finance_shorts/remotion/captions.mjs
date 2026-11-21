// node captions.mjs <out.mov>  - transparent ProRes 4444 caption layer for PepsiCaptions
import path from "node:path";
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
const [out] = process.argv.slice(2);
const browserExecutable = process.env.CHROME || "/opt/pw-browsers/chromium_headless_shell";
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.tsx"), publicDir: path.resolve("public") });
const composition = await selectComposition({ serveUrl, id: "PepsiCaptions", browserExecutable });
const t0 = Date.now();
await renderMedia({ composition, serveUrl, codec: "prores", proResProfile: "4444", imageFormat: "png", pixelFormat: "yuva444p10le",
  outputLocation: out, concurrency: 2, browserExecutable, timeoutInMilliseconds: 120000 });
console.log("done", ((Date.now() - t0) / 1000).toFixed(1) + "s");
