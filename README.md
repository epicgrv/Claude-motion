# THE PATH — Duolingo concept spot (21.2 s, 60 fps, 16:9 + 9:16)

*Un solo camino. Todas las habilidades.*

A fully programmatic, reproducible production: **Python orchestrates Blender 5.2 / Cycles (real 3-D, PBR, motion
blur, DOF, OIDN denoising)**; compositing/finishing is numpy/OpenCV in scene-linear float; all sound is synthesised.
One continuous camera trajectory per master, no editorial cuts. Authored from `Prompt_video_Duolingo.pdf`.

```
the_path/            config.py (timeline, anchors, palette)  easing.py (springs/splines)  camera.py  anim.py
                     geo.py (analytic-normal slabs/bezels/…)  duo.py (rig)  thread.py (the light line)  ui.py
                     scenes/s01_impact … s10_signature.py   env.py  post.py  produce.py  render_worker.py  build.py
                     audio/ dsp voice music sfx cues mix      qc/validate.py
tools/               pv.sh (preview through the real finishing)  render_all.sh  contact.py
assets/fonts/        Nunito (OFL) - the only external asset
```

## Reproduce

```bash
pip install -r requirements.txt                     # bpy (Blender 5.2 module), numpy, scipy, pillow, OpenCV, OpenEXR
apt-get install espeak-ng mbrola mbrola-es3 mbrola-mx1 mbrola-mx2 sox ffmpeg   # scratch voice + encoding
python -m the_path.audio.voice                      # voice (backend: elevenlabs | assets/voice/*.wav | scratch) + envelopes
python -m the_path.render_worker --fmt h --events out/audio/events_h.json
python -m the_path.audio.music; python -m the_path.audio.sfx; python -m the_path.audio.cues; python -m the_path.audio.mix
tools/render_all.sh h 2 6 67                        # frames -> out/exr/h   (fmt, workers, spp, scale%)
tools/render_all.sh v 2 6 67
python -m the_path.produce --fmt h                  # grade/bloom/grain + ffmpeg mux -> out/final/*.mp4
python -m the_path.qc.validate --fmt h
```

`PATH_SPP`, scale and workers are the only quality knobs: on a GPU box or a bigger CPU use `tools/render_all.sh h 1 32 100`
for a native-resolution, low-noise render of exactly the same scene.

## Decisions & interpretations (read these)

* **Timecodes** in the brief are `SS:CC` (seconds:hundredths): `19:20` = 19.20 s.
* **"0:17 — IMPACTO HEROICO"** is read as **1:17** (1.17 s): scene 1 ends at 1:67 and must still contain the blink, the
  camera retreat, the logo reveal and Duo's exit. Everything else uses the brief's numbers verbatim (`config.A`).
* **Exercise tiles** are the five Spanish words *Quiero · un · café, · por · favor* (exactly five), with a small English
  source line in Duo's bubble ("I want a coffee, please") so *Traduce esta oración* makes sense; consistent with the user later
  saying "Pedí un café en español".
* **Tempo grid**: the brief's anchors (2.40, 4.80, 7.20, 16.80, 19.20…) sit on a 100 BPM grid; the score follows it.
* The ring of the four skill worlds, the camera orbit around the hub and the vertical-specific layouts are my own
  directorial choices inside the brief's beats.

## Limitations — what this build is *not*

* **Voice is a scratch/guide track.** ElevenLabs (and every other neural TTS host) is blocked by the build sandbox's network
  policy, so the narration and the three on-screen lines were produced with offline **espeak-ng/MBROLA**: timing is exact and
  intelligible, but it is **robotic and Castilian, not the natural young Latin-American voice the brief asks for**. The ElevenLabs
  backend (`audio/voice.py`) is written (single continuous take + character timestamps) but **has not been run**. To finish:
  set `ELEVENLABS_API_KEY` / `ELEVENLABS_VOICE_ID` (and allow `api.elevenlabs.io`), or drop `narr0..5.wav`, `duo_line.wav`,
  `duo_hi.wav`, `user_line.wav` in `assets/voice/`, then re-run the audio chain and **re-render S03 and S06** (the jaw and the 3-D
  waveform are driven by the real voice envelope in `voice_env.json`).
* **No official Duolingo assets were available.** Duo and the wordmark are rebuilt procedurally (Duo from analytic primitives, the
  wordmark in Nunito Black). The brief says to use official files when available *and permitted*; the pipeline has a single
  place to swap them (`duo.py`, `logo.py`). Flags are drawn procedurally. Official sounds can override any SFX via `assets/sfx/<name>.wav`.
  The "correct" chime and fanfare are original compositions, not copies of Duolingo's.
* **Render budget.** The sandbox has 4 CPU cores and no GPU; a full-frame Cycles sample costs ~2 s here. The delivered masters are
  rendered at **1280×720 / 720×1280 (6 spp + OIDN) and upscaled to 1920×1080 / 1080×1920** with Lanczos + light sharpening, so they are
  softer than a native render and the finest UI text is the first thing to suffer. Same scene, same code — re-render at scale 100 for the real thing.
* Fine details inside the three seconds of S02 (node cascade) and S07 are fast by design; they are legible but not studied frame by frame.
* There is no DaVinci Resolve project (the brief lists it as optional "when requested").
* Scene scoring (brief §14) and the defects found are in `QC_REPORT.md`.
