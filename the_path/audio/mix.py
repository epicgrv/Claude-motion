"""Mix and master: voice always intelligible, music >= 12 dB under the voice while it speaks, integrated
-14 LUFS, true peak <= -1.25 dBTP (ffmpeg loudnorm, two-pass, linear), mono-compatibility and phone-speaker checks.
"""
from __future__ import annotations

import json
import re
import subprocess

import numpy as np
from scipy import signal

from ..config import OUT, TOTAL
from . import dsp

AUDIO = OUT / "audio"
N_TOTAL = dsp.n_of(TOTAL)


def _load(name):
    x, sr = dsp.read_wav(AUDIO / name)
    x = dsp.resample(x, sr)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    return dsp.fit(x, N_TOTAL)


def follower(x, attack=0.03, release=0.30, thr_db=-48.0, win=0.010):
    """Speech-activity envelope in [0,1] from a mono signal (RMS -> threshold -> attack/release smoothing)."""
    hop = dsp.n_of(win)
    n = len(x) // hop
    r = np.sqrt(np.mean(x[: n * hop].reshape(n, hop) ** 2, axis=1) + 1e-12)
    act = (20 * np.log10(r) > thr_db).astype(float)
    # close short gaps (breaths between words are still "speech")
    k = int(0.18 / win)
    act = np.convolve(act, np.ones(k), mode="same") > 0
    out = np.zeros(n)
    a, rel = np.exp(-win / attack), np.exp(-win / release)
    s = 0.0
    for i in range(n):
        s = a * s + (1 - a) * 1.0 if act[i] else rel * s
        out[i] = s
    env = np.interp(np.arange(len(x)) / hop, np.arange(n), out)
    return np.clip(env, 0, 1)


def rms_db(x):
    return 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)


def mix():
    music = _load("music.wav")
    sfx = _load("sfx.wav")
    sfxp = _load("sfx_protected.wav")
    vn = _load("voice_narration.wav")
    vd = _load("voice_dialogue.wav")
    peak_v = np.max(np.abs(vn)) + 1e-9
    vn = vn * (dsp.db(-3.0) / peak_v)               # narration peaks at -3 dBFS before the master
    act = follower(vn.mean(axis=1))
    # music sits 12 dB under the voice while it speaks (ducked), full level otherwise
    duck_music = 1 - act * (1 - dsp.db(-12.0))
    duck_sfx = 1 - act * (1 - dsp.db(-4.0))
    music_g = 0.55
    music_d = music * music_g * duck_music[:, None]
    sfx_d = sfx * 0.9 * duck_sfx[:, None] + sfxp * 0.9
    mixed = vn + vd + music_d + sfx_d
    # --- verify the 12 dB rule over the narration (speech-active) samples ------------------------------
    m = act > 0.8
    voice_db = rms_db(vn[m])
    music_db = rms_db(music_d[m])
    if music_db > voice_db - 12.0:
        fix = dsp.db(voice_db - 12.0 - music_db)
        music_d = music_d * fix
        mixed = vn + vd + music_d + sfx_d
        music_db = rms_db(music_d[m])
    # gentle bus limiter: tame the crest factor (booms/impacts) so the master reaches -14 LUFS without pumping
    mixed = dsp.soft_clip(mixed * 0.9, 0.9) / 0.9
    mixed = dsp.hp(mixed, 28, 2)                    # nothing useful below ~28 Hz
    dsp.write_wav(AUDIO / "mix_pre.wav", np.clip(mixed, -1.5, 1.5))
    rep = dict(voice_db=float(voice_db), music_under_voice_db=float(music_db), margin_db=float(voice_db - music_db))
    (AUDIO / "mix_report.json").write_text(json.dumps(rep, indent=1))
    print(f"[mix] voice {voice_db:.1f} dB, music under voice {music_db:.1f} dB  (margin {voice_db - music_db:.1f} dB)")
    return rep


def master(target_i=-14.0, target_tp=-1.25):
    src = AUDIO / "mix_pre.wav"
    p1 = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-af",
                         f"loudnorm=I={target_i}:TP={target_tp}:LRA=11:print_format=json", "-f", "null", "-"],
                        capture_output=True, text=True)
    js = json.loads(re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", p1.stderr, re.S).group(0))
    flt = (f"loudnorm=I={target_i}:TP={target_tp}:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
           f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true,"
           f"alimiter=limit=0.835:level=disabled")
    out = AUDIO / "master.wav"
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(src), "-af", flt, "-ar", "48000", "-c:a", "pcm_s24le",
                    "-t", f"{TOTAL:.3f}", str(out)], check=True)
    return out


def measure(path=None):
    path = path or AUDIO / "master.wav"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True)
    tail = r.stderr.split("Summary:")[-1]
    g = lambda pat: float(re.search(pat, tail).group(1))
    res = dict(integrated_lufs=g(r"I:\s+(-?[\d.]+) LUFS"), lra=g(r"LRA:\s+([\d.]+) LU"), true_peak_dbtp=g(r"Peak:\s+(-?[\d.]+) dBFS"))
    x, sr = dsp.read_wav(path)
    L, R = x[:, 0], x[:, 1]
    mid, side = (L + R) / 2, (L - R) / 2
    res["mono_loss_db"] = float(rms_db(mid) - rms_db(x.mean(axis=1) * 0 + (np.abs(L) + np.abs(R)) / 2))
    res["side_to_mid_db"] = float(rms_db(side) - rms_db(mid))
    corr = float(np.corrcoef(L, R)[0, 1])
    res["lr_correlation"] = corr
    f, P = signal.welch(mid, sr, nperseg=8192)
    tot = P.sum()
    res["energy_below_80Hz_pct"] = float(100 * P[f < 80].sum() / tot)
    res["energy_below_120Hz_pct"] = float(100 * P[f < 120].sum() / tot)
    res["energy_120_6000Hz_pct"] = float(100 * P[(f >= 120) & (f < 6000)].sum() / tot)
    res["clipped_samples"] = int(np.sum(np.abs(x) >= 0.999))
    res["duration_s"] = len(x) / sr
    return res


def run():
    mix()
    out = master()
    res = measure(out)
    for _ in range(2):          # land on -14.0 LUFS (loudnorm is true-peak-limited, so trim the input and redo)
        if abs(res["integrated_lufs"] + 14.0) <= 0.12:
            break
        x, sr = dsp.read_wav(AUDIO / "mix_pre.wav")
        dsp.write_wav(AUDIO / "mix_pre.wav", x * dsp.db(-14.0 - res["integrated_lufs"]))
        out = master()
        res = measure(out)
    (AUDIO / "master_report.json").write_text(json.dumps(res, indent=1))
    print("[master]", json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    run()
