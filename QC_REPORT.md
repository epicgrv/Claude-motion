# QC REPORT — THE PATH (Duolingo concept spot)

Honest status of the two masters in `out/final/`. Everything under "Automated" was measured by
`the_path/qc/validate.py` (`out/final/qc_h.json`, `qc_v.json`). Everything under "Visual" is my own reading
of **real decoded frames**, but of a limited sample (see "What was NOT inspected").

## 1. Automated results (both masters)

| Check | Horizontal 1920×1080 | Vertical 1080×1920 |
|---|---|---|
| Duration 21.200 s | OK | OK |
| 60 fps, 1272 frames | OK | OK |
| h264 yuv420p + AAC 48 kHz stereo, stream integrity | OK | OK |
| Black frames (luma < 2/255) | 0 | 0 |
| Camera path continuous (solved from scene) | max 2.38 m/frame, 7.6°/frame | max 2.30 m/frame, 7.6°/frame |
| Integrated loudness (target −14 LUFS) | −14.2 LUFS | −14.2 LUFS |
| True peak (limit −1.25 dBTP) | −1.4 dBTP | −1.4 dBTP |
| Impact audio↔picture sync (1.17 s) | −4 ms | −4 ms |

Audio report: L/R correlation ≈ 0.94, no clipped samples, ~51 % of energy < 120 Hz, ~19 % < 80 Hz.
"Big luma jump" frames flagged (70, 141–143, 164–172, 303/306 H; plus 153–161, 184 V) coincide with designed events
(impact flash, ignition, light-thread bursts). They were spot-checked, not all individually reviewed.

## 2. Defects found and what was done

| # | Defect | Status |
|---|---|---|
| 1 | Camera whip (≈70°/frame) at the S06→S07 handover | **Fixed** (ring rotated, S08 rotated, frames ≥636 re-rendered in both formats); now ≤7.6°/frame |
| 2 | True-peak overshoot after AAC encode | **Fixed** (limiter 0.835, audio remux) |
| 3 | Black frames from a look-at target overshooting the lens | **Fixed** |
| 4 | Shared meshes taking the last material; head/hub radius overridden by scale keys | **Fixed** |
| 5 | Speckled/“fireflies” edges on Duo at ~1.17 s (frame 70) | **Open** — low-spp noise survives denoise on one frame |
| 6 | Faint wordmark ghost around 20 s (end card) and an overlapping duplicate wordmark/text reflection near 16.8 s in the vertical master | **Open** |
| 7 | Whole film is a 1280×720 / 720×1280 render, 6 spp + OIDN, Lanczos-upscaled | **Open by design** (CPU-only sandbox); finest UI text is soft |
| 8 | Vertical 13.35 s (skill ring, seen from far) reads small and sparse in the 9:16 frame | **Open** |

## 3. Scene scoring (brief §14, 1–10)

Scores are my own judgement from the key frames listed below — not a panel review, and deliberately conservative.
C = composition, M = movement, L = lighting, N = narrative clarity, S = satisfaction/“wow”.

| Scene | Time | C | M | L | N | S | Notes |
|---|---|---|---|---|---|---|---|
| S01 El impacto | 0.00–1.67 | 7 | 7 | 7 | 7 | 6 | Impact, logo reveal in sync (−4 ms). Speckle on frame 70 hurts the hero shot. |
| S02 Universo | 1.67–2.93 | 7 | 7 | 7 | 7 | 7 | Fast by design; the star/node cascade reads, details not frame-studied. |
| S03 Interfaz | 2.93–4.80 | 8 | 7 | 7 | 8 | 7 | Exercise, tiles, “Comprobar” legible; Duo bubble + five tiles clear in both formats. |
| S04 365 días | 4.80–7.20 | 8 | 7 | 8 | 8 | 7 | Ignition flame and counter work; streak counter is the strongest vertical frame. |
| S05 El ascenso | 7.20–9.33 | 8 | 7 | 7 | 8 | 7 | League board readable; small text soft after upscale. |
| S06 Momento humano | 9.33–11.40 | 7 | 7 | 7 | 7 | 6 | Call framing OK; Duo’s face is procedural, lip-sync driven by a robotic scratch voice. |
| S07 Cuatro universos | 11.40–14.67 | 6 | 7 | 6 | 6 | 6 | Worlds are small/dark at distance; the thread reads, the four skills less so. |
| S08 La gran idea | 14.67–16.50 | 7 | 7 | 7 | 7 | 7 | “UN SOLO CAMINO.” clear; flags small. |
| S09 Cierre | 16.50–19.20 | 7 | 7 | 7 | 7 | 7 | Landing + “duolingo” fanfare land on the beats; wordmark ghost on reflection. |
| S10 Firma | 19.20–21.20 | 6 | 7 | 6 | 7 | 5 | Placeholder “[TU FIRMA]” is correct but visually sparse; faint ghost. |

Overall, honest verdict: **a complete, coherent, technically clean concept render — not a final-quality commercial.**
Its main weaknesses are the voice, procedural Duo/wordmark and the upscaled resolution.

## 4. What was NOT inspected

* I viewed **13 (V) and ~32 (H) key frames** on contact sheets (down-scaled to 200 px wide for the vertical sheet),
  not all 1272 frames of either master. Motion quality is judged from the solved camera path, event timings and sample frames, not from watching the film in real time.
* The vertical master was inspected only at contact-sheet scale; no full-resolution pass.
* No A/B listening on real playback hardware; the mix was verified with measurements only.
* No audience or brand-owner review.

## 5. Limitations (unflattering list)

1. **Voice is a robotic espeak-ng/MBROLA scratch track**, Castilian-sounding, not the requested natural young Latin-American voice. ElevenLabs backend is written but **never run** (host blocked).
2. **No official Duolingo assets.** Duo, flags and the wordmark are procedural look-alikes; a brand-compliance review would likely reject them.
3. **Resolution:** internal 1280×720 / 720×1280, 6 spp, upscaled. A native 1080p render would be sharper and cleaner.
4. Music and ~106 SFX are synthesised (numpy), original; they are functional but do not match the polish of a human-composed score.
5. Brief “0:17” interpreted as 1:17 s; five Spanish tiles with an English source line — my interpretations, flagged in README.
6. Open visual defects #5, #6, #8 above.
7. No Resolve project; no stems for the sound; no subtitles/captions file.
