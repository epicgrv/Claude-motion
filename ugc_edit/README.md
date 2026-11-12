# UGC edit — dishwasher detergent

`UGC_dishwasher_final.mp4` — 1080x1920, 24 fps, 13.42 s, −14.7 LUFS.

Pipeline (assets from the editing pack on Drive go in `a/` and `sfx/`, not committed — fonts are licensed):
- `edit.json` — cut points, zoom drift/punch-ins, film-burn placements, word-timed captions (Whisper small.en).
- `render.py` — zoom-out hook, shutter flash, film burns (screen blend), whip transitions, TailorMade LUT @50 %, vignette, grain, captions (Sequel Sans + Adobe Garamond Pro Bold Italic).
- `mix.py` — SFX bed from the pack's trending SFX + synthesized shutter.
