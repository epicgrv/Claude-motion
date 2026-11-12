# Busy Co. body wipes — UGC edit

`BusyCo_body_wipes_final.mp4` — 1080x1920, 30 fps, 26.6 s, −13.7 LUFS.

Brand system (from getbusy.co CSS — site is all lowercase, mauve is the primary accent, orange is packaging only): Pangram Bold (captions, hook, price), Supply Bold (unused now);
ink #241F21, cream #F2EDEB, mauve #C980A3, blush #FAC2D9, orange #EB7045, yellow #F0DE36.
Fonts are not committed (brand-licensed); put them in `a/` to re-render.

- Source upscaled 478x850 -> 1080x1920 (denoise + lanczos + unsharp); 3 s silent gap (orig 21.15–24.13) cut.
- `edit.json` — cuts, zooms/punches, impact hook (no opening transition), film burns on cuts, lowercase stacked captions (white top / blush-yellow-blue Pangram keyword with mauve glow / cream bottom), each placed below the face and off the product.
- `render_busy.py` — render; `mix_busy.py` — SFX bed from the Drive pack.
