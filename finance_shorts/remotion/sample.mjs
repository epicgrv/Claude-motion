// node sample.mjs <outDir> <ranges "a-b:mode,a-b:mode,...">  - renders 3D clips (no captions) + caption layers per range, one bundle
import path from "node:path";
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
const [outDir, spec] = process.argv.slice(2);
const browserExecutable = process.env.CHROME || "/opt/pw-browsers/chromium_headless_shell";
const chromiumOptions = { gl: "swangle" };
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.tsx"), publicDir: path.resolve("public") });
const ranges = spec.split(",").map((r) => { const [ab, mode] = r.split(":"); const [a, b] = ab.split("-").map(Number); return { a, b, mode }; });
const t0 = Date.now();
for (const [i, r] of ranges.entries()) {
  const p3 = { post: { captions: false } };
  const c3 = await selectComposition({ serveUrl, id: "SilverShort", browserExecutable, chromiumOptions, inputProps: p3 });
  await renderMedia({ composition: c3, serveUrl, codec: "h264", crf: 16, inputProps: p3, outputLocation: `${outDir}/clip${i}.mp4`, frameRange: [r.a, r.b], concurrency: 2, browserExecutable, chromiumOptions, timeoutInMilliseconds: 600000 });
  const pc = { capMode: r.mode };
  const cc = await selectComposition({ serveUrl, id: "SilverCaptions", browserExecutable, inputProps: pc });
  await renderMedia({ composition: cc, serveUrl, codec: "prores", proResProfile: "4444", imageFormat: "png", pixelFormat: "yuva444p10le", inputProps: pc,
    outputLocation: `${outDir}/cap${i}.mov`, frameRange: [r.a, r.b], concurrency: 2, browserExecutable, timeoutInMilliseconds: 120000 });
  console.log("clip", i, r.a, r.b, r.mode, ((Date.now() - t0) / 1000).toFixed(0) + "s");
}
console.log("ALLDONE");
