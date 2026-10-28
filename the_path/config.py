"""THE PATH - global configuration: formats, timeline, palette, sync anchors.

All times in the brief are written SS:CC (seconds:hundredths), e.g. ``19:20`` is 19.20 s.
Everything here is plain Python (no bpy) so audio, render and QC share one source of truth.
"""
from __future__ import annotations

import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get("PATH_OUT", ROOT / "out"))
ASSETS = ROOT / "assets"
FONT_BLACK = str(ASSETS / "fonts" / "Nunito-900.ttf")
FONT_BOLD = str(ASSETS / "fonts" / "Nunito-800.ttf")

# ---------------------------------------------------------------- formats
FPS = 60
AD_DURATION = 19.2
END_DURATION = 2.0
TOTAL = AD_DURATION + END_DURATION          # 21.2 s
N_FRAMES = round(TOTAL * FPS)               # 1272
FORMATS = {
    "h": dict(name="horizontal", w=1920, h=1080),
    "v": dict(name="vertical", w=1080, h=1920),
}


def frame_of(t: float) -> int:
    """Time (s) -> 0-based frame index."""
    return int(round(t * FPS))


def time_of(frame: int) -> float:
    return frame / FPS


# ---------------------------------------------------------------- scenes
SCENES = [
    # id, name, t0, t1
    ("s01", "EL IMPACTO", 0.00, 1.67),
    ("s02", "EL UNIVERSO DEL APRENDIZAJE", 1.67, 2.93),
    ("s03", "LA SATISFACCION DE APRENDER", 2.93, 4.80),
    ("s04", "365 DIAS", 4.80, 7.20),
    ("s05", "EL ASCENSO", 7.20, 9.33),
    ("s06", "EL MOMENTO HUMANO", 9.33, 11.40),
    ("s07", "CUATRO UNIVERSOS, UN CAMINO", 11.40, 14.67),
    ("s08", "LA GRAN IDEA", 14.67, 16.50),
    ("s09", "EL CIERRE PERFECTO", 16.50, 19.20),
    ("s10", "FIRMA", 19.20, 21.20),
]
SCENE_T = {s[0]: (s[2], s[3]) for s in SCENES}


def scene_at(t: float) -> str:
    for sid, _, t0, t1 in SCENES:
        if t0 <= t < t1:
            return sid
    return SCENES[-1][0]


# ---------------------------------------------------------------- anchors
# Every timestamp that audio and picture must agree on. The brief's own numbers are used
# verbatim; extra beats (marked "mine") are choreography decisions between them.
A = dict(
    # scene 01
    spark_on=0.12,                   # mine
    fibers_in=0.30, fibers_out=0.95,  # mine
    duo_launch=0.86,                 # mine: Duo leaves the far distance
    impact=1.17,                     # brief "0:17" read as 1:17 (see README "interpretation")
    blink=1.30, retreat=1.33, logo_reveal=1.38, duo_leaves=1.50,
    # scene 02
    node_first=1.72, press=2.40, phone_rise=2.52, enter_screen=2.80,
    # scene 03
    voice_duo=3.10, tiles_assemble=3.55, check_on=4.05, correct1=4.23, bar_fill=4.40,
    # scene 04
    ignition=5.00, counter_start=5.10, counter_end=6.25, week_lights=6.35,
    # scene 05
    league_enter=7.35, rank_start=7.85, rank1=8.70,
    # scene 06
    call_open=9.50, duo_hi=9.80, user_wave=10.30,
    # scene 07
    langs=11.67, math_=12.42, music=12.98, chess=13.70,
    # scene 08
    converge=14.67, msg1=15.05, msg2=15.85,
    # scene 09
    music_pause=16.50, landing=16.80, voice_duolingo=17.33, fanfare=18.07,
    # scene 10
    signature=19.20,
)

# Voice sync targets (brief section 9) - validated against the final take.
VOICE_SYNC = [
    (0.50, "comienza la narración"),
    (2.95, "Una palabra"),
    (4.60, "Una racha"),
    (9.05, "Y, de repente"),
    (11.67, "Idiomas"),
    (14.93, "Un solo camino"),
    (17.33, "Duolingo"),
]
VOICE_SCRIPT = [
    "Cinco minutos al día. Eso es todo lo que necesitás.",
    "Una palabra a la vez. Una racha que no vas a querer perder. Una liga que vas a querer ganar.",
    "Y, de repente, un día… simplemente hablás.",
    "Idiomas, matemáticas, música… hasta ajedrez.",
    "Un solo camino. Todas las habilidades.",
    "Duolingo.",
]
# (phrase index, start time) the narration is placed at (seconds)
VOICE_CUES = [(0, 0.50), (1, 2.95), (2, 9.05), (3, 11.67), (4, 14.93), (5, 17.33)]

# ---------------------------------------------------------------- music
BPM = 100
BEAT = 60.0 / BPM            # 0.6 s
BAR = 4 * BEAT               # 2.4 s
KEY_ROOT = "D"               # D major

# ---------------------------------------------------------------- palette (sRGB hex)
PAL = dict(
    bg="#060A0C",
    feather="#58CC02", mask="#89E219", feather_dark="#46A302", feather_deep="#2F7A00",
    snow="#F4F8FA", eel="#4B4B4B",
    surf0="#0B1216", surf1="#16222A", surf2="#1F2F39", edge="#2C4150", slate="#37464F",
    macaw="#1CB0F6", humpback="#2B70C9", math_deep="#1A5FA8",
    beetle="#CE82FF", beetle_deep="#8E45CC",
    bee="#FFC800", bee_deep="#C79600",
    fox="#FF9600", fox_deep="#C96E00",
    cardinal="#FF4B4B",
    beak="#FF9600", beak_deep="#D97A00",
    # skill identities (scene 07)
    sk_lang="#58CC02", sk_math="#1CB0F6", sk_music="#CE82FF", sk_chess="#FFC800",
)


def hex2rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def srgb2lin(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def lin(h: str, gain: float = 1.0):
    """sRGB hex -> scene-linear RGB tuple (optionally multiplied)."""
    return tuple(srgb2lin(c) * gain for c in hex2rgb(PAL.get(h, h)))


# ---------------------------------------------------------------- render quality
RENDER = dict(
    samples_max=int(os.environ.get("PATH_SPP", 20)),
    samples_min=4,
    noise_threshold=0.04,
    max_bounces=4, diffuse_bounces=2, glossy_bounces=3,
    clamp_indirect=1.2, clamp_direct=0.0,
    filter_width=1.4,
    motion_shutter=0.45,           # ~160 degree shutter
    denoise_quality="HIGH", denoise_prefilter="FAST",
)

if __name__ == "__main__":  # quick sanity
    print(N_FRAMES, lin("bg"), lin("feather"))
    assert abs(N_FRAMES - 1272) == 0
    assert math.isclose(SCENES[-1][3], TOTAL)
