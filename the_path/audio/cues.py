"""SFX cue sheet: places library sounds on the timeline from the picture's own sync events (events.json)
plus a handful of hand-placed beats. This is the single place that decides *what is heard when*.
"""
from __future__ import annotations

import json
import math

import numpy as np

from ..config import A, OUT, TOTAL
from . import dsp, sfx
from .dsp import Track

AUDIO = OUT / "audio"


def build(events_path=None, fmt="h"):
    lib = sfx.library()
    events = json.loads((events_path or AUDIO / f"events_{fmt}.json").read_text())
    tr = Track(TOTAL + 1.0)
    prot = Track(TOTAL + 1.0)      # brand sounds: never ducked under the narration
    log = []

    def put(name, t, db=-10.0, pan=0.0, rate=1.0, rev=False, protect=False, dur=None):
        x = lib[name]
        if rate != 1.0:
            x = dsp.vary_rate(x, rate)
        if rev:
            x = x[::-1].copy()
        if dur and x.shape[0] > dsp.n_of(dur):
            x = dsp.fade(x[: dsp.n_of(dur)], 0.002, 0.03)
        (prot if protect else tr).add(x, t, dsp.db(db), p=pan)
        log.append(dict(t=round(float(t), 3), name=name, db=db, pan=pan, rate=rate, rev=rev))

    ev = lambda kind: [e for e in events if e["kind"] == kind]
    rng = np.random.default_rng(5)

    # ---------------- S01 - the impact
    put("en_pulse_01", A["spark_on"], -20)
    put("en_light_03", A["spark_on"] + 0.05, -22, rate=0.8)
    for k, t in enumerate(np.linspace(0.30, 0.90, 9)):
        put(f"mv_whoosh_s_{k % 3 + 1:02d}", float(t), -17 + 0.4 * k, pan=float(rng.uniform(-0.8, 0.8)), rate=float(rng.uniform(0.85, 1.25)))
    put("mv_pass_01", 0.40, -16, pan=0.0)
    put("mv_pass_02", 0.62, -17)
    put("mv_whoosh_rev_01", A["duo_launch"] - 0.05, -9)
    put("mv_accel_01", A["duo_launch"], -14)
    t_imp = A["impact"]
    put("im_boom_01", t_imp, -2, protect=True)
    put("im_crack_01", t_imp, -6, protect=True)
    put("im_glass_01", t_imp + 0.01, -10)
    put("mt_muffled_01", t_imp + 0.02, -8)
    for k in range(5):
        put(f"im_sparkle_{k % 4 + 1:02d}", t_imp + 0.04 + 0.07 * k, -22 - k, pan=float(rng.uniform(-0.9, 0.9)))
    put("im_tick_03", A["blink"], -26)
    put("mt_contact_01", 1.43, -14)
    put("ch_jump_01", A["duo_leaves"], -10)
    put("mv_whoosh_s_02", A["duo_leaves"] + 0.01, -11, pan=-0.5)
    put("mv_whoosh_m_01", A["retreat"], -15)
    for e in ev("letter"):
        put(f"br_ladder_{(e['i'] % 8) + 1:02d}", e["t"], -17, pan=(e["i"] - 3.5) / 5)
    # ---------------- S02 - the learning universe
    for e in ev("node"):
        i = e["i"]
        put("en_light_01" if i % 2 == 0 else "en_light_02", e["t"], -17, pan=float(math.sin(i * 0.9) * 0.6), rate=0.9 + 0.045 * i)
        put(f"mt_button_{i % 4 + 1:02d}", e["t"] + 0.004, -24)
    put("mv_whoosh_l_01", 1.72, -17)
    put("mv_whoosh_m_02", 2.2, -18)
    put("mv_decel_01", 2.32, -16)
    tp = A["press"]
    put("mt_button_01", tp, -7, protect=True)
    put("im_boom_02", tp, -5, protect=True)
    put("en_propagate_01", tp + 0.02, -12)
    put("en_pulse_02", tp + 0.0, -8)
    put("mt_clack_01", A["press"] + 0.10, -10)
    put("mt_slide_01", A["press"] + 0.12, -14)
    put("mv_accel_02", A["phone_rise"], -13)
    put("mt_slide_02", A["phone_rise"] + 0.02, -14)
    put("mv_whoosh_l_02", A["phone_rise"] + 0.06, -14, rate=1.1)
    put("mt_clack_03", A["phone_rise"] + 0.24, -12)
    put("mv_whoosh_m_02", A["enter_screen"] - 0.12, -12)
    put("en_light_05", A["enter_screen"], -15)
    # ---------------- S03 - the satisfaction of learning
    for k, t in enumerate((2.90, 2.94, 2.98, 3.02, 3.06, 3.10)):
        put(f"mv_whoosh_s_{k % 3 + 1:02d}", t, -19, pan=float(rng.uniform(-0.7, 0.7)), rate=float(rng.uniform(1.0, 1.4)))
    for e in ev("tile_lock"):
        i = e["i"]
        put(f"br_ladder_{i + 2:02d}", e["t"], -9, pan=-0.4 + 0.2 * i, protect=True)
        put(f"mt_contact_{i % 4 + 1:02d}", e["t"], -14, pan=-0.4 + 0.2 * i)
    put("br_check_on", A["check_on"], -10, protect=True)
    put("mt_button_02", 4.18, -9, protect=True)
    put("br_correct_01", A["correct1"], -3, protect=True)
    put("im_sparkle_02", A["correct1"] + 0.02, -15, protect=True)
    put("im_sparkle_03", A["correct1"] + 0.10, -17, pan=0.4)
    put("en_propagate_02", 4.40, -12, dur=0.45)
    put("mv_whoosh_m_03", 4.62, -13)
    # ---------------- S04 - 365 days
    put("mv_whoosh_l_02", 4.82, -13, dur=0.5)
    put("en_ignite_01", A["ignition"], -4, protect=True)
    put("im_boom_03", A["ignition"], -7, protect=True)
    put("en_propagate_03", A["ignition"] + 0.02, -12)
    put("im_sparkle_01", A["ignition"] + 0.03, -18)
    for e in ev("odo_tick"):
        put(f"mt_clack_{e['i'] % 4 + 1:02d}", e["t"], -9, pan=0.0)
        put("mt_button_03", e["t"], -17)
    put("mt_slide_03", 6.20, -13)
    put("mt_clack_04", 6.34, -11)
    for e in ev("day_on"):
        put(f"br_ladder_{e['i'] + 1:02d}", e["t"], -17, pan=-0.6 + 0.2 * e["i"], rate=0.5)
    put("mv_whoosh_m_01", A["energy_leaves"] if "energy_leaves" in A else 6.95, -13)
    put("mv_whoosh_l_03", 7.10, -15)
    # ---------------- S05 - the ascent
    put("en_light_02", 7.78, -10)
    put("mt_slide_01", 7.88, -12)
    for k, e in enumerate(ev("rank_pass")):
        put(f"mt_button_{k % 4 + 1:02d}", e["t"], -11, pan=0.0)
        put("mv_whoosh_s_01", e["t"] - 0.02, -16, rate=1.0 + 0.08 * k)
        put(f"br_ladder_{k + 1:02d}", e["t"], -16)
    put("br_correct_02", A["rank1"], -3, protect=True)
    put("im_boom_02", A["rank1"], -7, protect=True)
    put("mv_whoosh_l_01", A["rank1"] + 0.04, -9)
    put("en_propagate_01", A["rank1"] + 0.06, -12)
    # ---------------- S06 - the human moment
    put("mv_whoosh_m_02", 9.30, -12)
    put("mv_whoosh_m_03", A["call_open"] if "call_open" in A else 9.50, -14, pan=0.2)
    put("mt_clack_02", 9.58, -10)
    put("ch_jump_02", 9.66, -11)
    put("ch_chirp_01", 9.76, -18)
    put("im_sparkle_04", 10.30, -18)
    put("en_propagate_02", 10.30, -15, dur=0.5)
    put("ch_chirp_03", 11.60, -14)
    put("ch_wing_02", 11.65, -16)
    # ---------------- S07 - four universes
    put("en_pulse_03", 11.55, -12)
    for k, name in enumerate(("lang", "math", "music", "chess")):
        t0 = dict(lang=11.64, math=12.20, music=12.74, chess=13.45)[name]
        put("mv_whoosh_m_01", t0, -13, pan=(-0.7, -0.3, 0.3, 0.7)[k], rate=1.0 + 0.1 * k)
    put("mv_whoosh_l_01", 11.45, -13, rev=True)
    for e in ev("flag_on"):
        put(f"br_ladder_{e['i'] % 8 + 1:02d}", e["t"], -16, pan=float(rng.uniform(-0.6, 0.6)))
    for e in ev("math_click"):
        put(f"mt_clack_{e['i'] % 4 + 1:02d}", e["t"], -10, pan=0.0)
    put("en_light_04", A["music"], -12)
    for e in ev("key_hit"):
        put("mt_contact_02", e["t"], -17, rate=1.4)
    put("mt_vibe_01", A["chess"] + 0.10, -17)
    put("ch_jump_03", A["chess"] + 0.20, -13)
    put("mv_whoosh_s_03", A["chess"] + 0.22, -14)
    put("ch_land_01", ev("knight_land")[0]["t"], -9)
    put("im_boom_03", ev("knight_land")[0]["t"], -13)
    put("en_propagate_03", ev("knight_land")[0]["t"], -15)
    # ---------------- S08 - the big idea
    put("mv_whoosh_l_01", 14.62, -12, rev=True)
    put("mv_whoosh_l_03", 14.76, -14)
    put("im_boom_03", A["msg1"], -8)
    put("en_light_01", A["msg1"] + 0.02, -12)
    for k, e in enumerate(ev("letter8")):
        if k % 2 == 0:
            put(f"im_tick_{k % 6 + 1:02d}", e["t"], -27)
    put("en_light_02", A["msg2"], -14)
    put("en_transform_01", 16.02, -14)
    put("im_sparkle_01", 16.04, -18)
    # ---------------- S09 - the perfect close
    put("im_glass_02", A["music_pause"], -10)
    put("im_sparkle_02", A["music_pause"] + 0.05, -20)
    put("im_riser_01", A["music_pause"], -9, dur=A["landing"] - A["music_pause"])
    put("im_boom_01", A["landing"], 0, protect=True)
    put("ch_land_02", A["landing"], -6, protect=True)
    put("mt_bounce_01", A["landing"] + 0.05, -14)
    put("en_propagate_01", A["landing"] + 0.03, -10)
    put("mv_whoosh_m_03", A["landing"] + 0.20, -14)
    put("mv_whoosh_m_02", 17.00, -13)
    for k, e in enumerate(ev("logo_letter")):
        put(f"br_ladder_{k + 1:02d}", e["t"], -12, pan=(k - 3.5) / 5)
    for k in range(3):
        put(f"ch_wing_{k + 1:02d}", A["fanfare"] + 0.03 + 0.16 * k, -12, pan=-0.2 + 0.2 * k)
    put("im_sparkle_03", A["fanfare"] + 0.05, -14)
    # ---------------- S10 - signature
    put("br_signature_on", A["signature"] + 0.40, -14, protect=True)
    put("im_tick_02", A["signature"] + 0.45, -24)
    log.sort(key=lambda d: d["t"])
    (AUDIO / "sfx_cues.json").write_text(json.dumps(log, indent=1))
    dsp.write_wav(AUDIO / "sfx.wav", tr.buf)
    dsp.write_wav(AUDIO / "sfx_protected.wav", prot.buf)
    print(f"[cues] {len(log)} placements using {len(set(l['name'] for l in log))} distinct effects")
    return tr.buf, prot.buf


if __name__ == "__main__":
    build()
