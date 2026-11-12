# Busy Co. body wipes — UGC edit

`BusyCo_body_wipes_final.mp4` — 1080x1920, 30 fps, 26.6 s, −13.7 LUFS.

Brand system (from getbusy.co CSS): Pangram Bold (captions, hook, price), Supply Bold (unused now);
ink #241F21, cream #F2EDEB, mauve #C980A3, blush #FAC2D9, orange #EB7045, yellow #F0DE36.
Fonts are not committed (brand-licensed); put them in `a/` to re-render.

- Source upscaled 478x850 -> 1080x1920 (denoise + lanczos + unsharp); 3 s silent gap (orig 21.15–24.13) cut.
- `edit.json` — cuts, zooms/punches, shutter + impact hook, film burns, stacked keyword captions (small white top / big orange-yellow Pangram keyword / cream bottom), placed below the face.
- `render_busy.py` — render; `mix_busy.py` — SFX bed from the Drive pack.
