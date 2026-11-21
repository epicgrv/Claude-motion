// node media.mjs <entry> <compId> <out.mp4> <from> <to> [scale] [concurrency]
import path from "node:path";
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
const [entry, id, out, from, to, scale = "1", conc = "2"] = process.argv.slice(2);
const browserExecutable = process.env.CHROME || "/opt/pw-browsers/chromium_headless_shell";
const chromiumOptions = { gl: process.env.GL || "swangle" };
const serveUrl = await bundle({ entryPoint: path.resolve(entry), publicDir: path.resolve("public") });
const composition = await selectComposition({ serveUrl, id, browserExecutable, chromiumOptions, inputProps: process.env.PROPS ? JSON.parse(process.env.PROPS) : {} });
const t0 = Date.now();
let last = 0;
const inputProps = process.env.PROPS ? JSON.parse(process.env.PROPS) : {};
await renderMedia({ composition, serveUrl, codec: "h264", crf: 16, inputProps, outputLocation: out, scale: Number(scale),
  frameRange: [Number(from), Number(to)], concurrency: Number(conc), browserExecutable, chromiumOptions,
  timeoutInMilliseconds: 600000,
  onProgress: ({ renderedFrames }) => { if (renderedFrames - last >= 10) { last = renderedFrames; console.log("frames", renderedFrames, ((Date.now() - t0) / 1000).toFixed(0) + "s"); } } });
console.log("done", ((Date.now() - t0) / 1000).toFixed(1) + "s");
