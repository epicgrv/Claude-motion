"""Voice stage: narration (brief section 9) + the three on-screen lines.

Backends, tried in this order (``PATH_VOICE`` can force one):

  elevenlabs  ELEVENLABS_API_KEY (+ ELEVENLABS_VOICE_ID) set and api.elevenlabs.io reachable. One continuous
              take with character timestamps, cut into phrases - the way the brief asks for it.
              NOTE: written against the public API but NOT exercised in the build environment (its network
              policy blocks api.elevenlabs.io).
  dropin      WAV files you recorded/generated yourself in ``assets/voice/`` (narr0..narr5.wav, duo_line.wav,
              duo_hi.wav, user_line.wav).
  scratch     offline guide voice (espeak-ng + MBROLA). Intelligible and perfectly timed, but robotic - it
              exists so picture, lip-sync, waveform and mix can be built and validated. REPLACE FOR RELEASE.

Whatever the backend, the actual audio drives the picture: ``voice_env.json`` carries the real amplitude
envelope and 3-band energy of each on-screen line (jaw movement, 3-D waveform).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

from ..config import ASSETS, OUT, VOICE_CUES, VOICE_SCRIPT, VOICE_SYNC
from . import dsp

AUDIO = OUT / "audio"

# on-screen dialogue (text, start, target duration, voice id)
DIALOGUE = dict(
    duo_line=("Quiero un café, por favor.", 3.10, 1.08, "duo"),
    duo_hi=("¡Hola! ¿Qué tal tu día?", 9.55, 0.85, "duo"),
    user_line=("¡Muy bien! Pedí un café en español.", 10.28, 1.10, "user"),
)
NARR_WINDOWS = [(0.50, 2.95), (2.95, 9.05), (9.05, 11.67), (11.67, 14.93), (14.93, 17.33), (17.33, 18.30)]

SCRATCH_VOICES = dict(narr=("mb-es3", 150, 52), duo=("mb-mx2", 150, 78), user=("mb-mx1", 150, 45))


# ---------------------------------------------------------------- scratch backend
def _scratch(text, voice, target=None, max_tempo=1.9):
    v, spd, pit = SCRATCH_VOICES[voice]
    with tempfile.TemporaryDirectory() as td:
        raw = Path(td) / "r.wav"
        subprocess.run(["espeak-ng", "-v", v, "-s", str(spd), "-p", str(pit), "-g", "2", "-w", str(raw), text],
                       check=True, capture_output=True)
        x, sr = dsp.read_wav(raw)
        nat = x.shape[0] / sr
        tempo = 1.0
        if target and nat > target:
            tempo = min(nat / target, max_tempo)
            out = Path(td) / "t.wav"
            subprocess.run(["sox", str(raw), str(out), "tempo", "-s", f"{tempo:.4f}"], check=True, capture_output=True)
            x, sr = dsp.read_wav(out)
    y = dsp.resample(x[:, 0], sr, dsp.SR)
    # trim leading/trailing silence so the cue time is the onset of the first word
    m = np.abs(y) > 0.02 * np.max(np.abs(y))
    i0, i1 = np.argmax(m), len(m) - np.argmax(m[::-1])
    y = y[max(i0 - dsp.n_of(0.01), 0): i1 + dsp.n_of(0.03)]
    # gentle body + presence so it sits like a voice, not a beep
    y = dsp.hp(y, 90)
    y = y + 0.25 * dsp.bp(y, 180, 420)
    y = dsp.normalize(y, 0.8)
    return y, dict(natural=nat, tempo=tempo)


# ---------------------------------------------------------------- elevenlabs backend (untested here)
def _elevenlabs_take(texts):
    import base64
    import urllib.request
    key = os.environ["ELEVENLABS_API_KEY"]
    vid = os.environ.get("ELEVENLABS_VOICE_ID", "")
    if not vid:
        raise RuntimeError("set ELEVENLABS_VOICE_ID to a young, optimistic Latin-American Spanish female voice")
    body = json.dumps(dict(text="\n".join(texts), model_id="eleven_multilingual_v2",
                           voice_settings=dict(stability=0.38, similarity_boost=0.8, style=0.35, use_speaker_boost=True))).encode()
    req = urllib.request.Request(f"https://api.elevenlabs.io/v1/text-to-speech/{vid}/with-timestamps?output_format=mp3_44100_128",
                                 data=body, headers={"xi-api-key": key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        js = json.loads(r.read())
    mp3 = Path(tempfile.mkdtemp()) / "take.mp3"
    mp3.write_bytes(base64.b64decode(js["audio_base64"]))
    wav = mp3.with_suffix(".wav")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp3), "-ar", str(dsp.SR), "-ac", "1", str(wav)], check=True)
    x, sr = dsp.read_wav(wav)
    al = js["alignment"]
    starts = al["character_start_times_seconds"]
    ends = al["character_end_times_seconds"]
    # char offsets of each phrase inside the joined text
    pos, bounds = 0, []
    for t in texts:
        bounds.append((pos, pos + len(t) - 1))
        pos += len(t) + 1
    clips = []
    for a, b in bounds:
        i0, i1 = int(starts[a] * sr), int(ends[b] * sr)
        clips.append(x[i0:i1, 0])
    return clips


# ---------------------------------------------------------------- public API
def pick_backend():
    forced = os.environ.get("PATH_VOICE")
    if forced:
        return forced
    if os.environ.get("ELEVENLABS_API_KEY"):
        try:
            import urllib.request
            urllib.request.urlopen("https://api.elevenlabs.io/v1/models", timeout=6)
        except Exception as e:  # 401 means reachable
            if getattr(e, "code", None) not in (401, 403):
                print("[voice] ElevenLabs not reachable here:", e)
            else:
                return "elevenlabs"
        else:
            return "elevenlabs"
    if (ASSETS / "voice" / "narr0.wav").exists():
        return "dropin"
    return "scratch"


def analyze(y, rate=100):
    """Amplitude envelope + low/mid/high band energy at ``rate`` Hz, normalised to [0,1]."""
    hop = dsp.SR // rate

    def rms(sig):
        n = len(sig) // hop
        r = np.sqrt(np.mean(sig[: n * hop].reshape(n, hop) ** 2, axis=1))
        k = np.hanning(5)
        k /= k.sum()
        return np.convolve(r, k, mode="same")

    def norm(r):
        ref = np.percentile(r, 96) + 1e-9
        return np.clip(r / ref, 0, 1) ** 0.8

    env = norm(rms(y))
    bands = [norm(rms(dsp.lp(y, 400, 2))), norm(rms(dsp.bp(y, 400, 2500, 2))), norm(rms(dsp.hp(y, 2500, 2)))]
    return env, bands


def build(report_path=None):
    backend = pick_backend()
    AUDIO.mkdir(parents=True, exist_ok=True)
    clips, info = {}, {}
    if backend == "scratch":
        for i, ((c0, c1), text) in enumerate(zip(NARR_WINDOWS, VOICE_SCRIPT)):
            y, inf = _scratch(text, "narr", target=(c1 - c0) - 0.12)
            clips[f"narr{i}"], info[f"narr{i}"] = y, inf
        for k, (text, t0, dur, voice) in DIALOGUE.items():
            y, inf = _scratch(text, voice, target=dur)
            clips[k], info[k] = y, inf
    elif backend == "dropin":
        for name in [f"narr{i}" for i in range(6)] + list(DIALOGUE):
            x, sr = dsp.read_wav(ASSETS / "voice" / f"{name}.wav")
            clips[name] = dsp.resample(x[:, 0], sr, dsp.SR)
            info[name] = dict(source="dropin")
    elif backend == "elevenlabs":
        ys = _elevenlabs_take(VOICE_SCRIPT)
        for i, y in enumerate(ys):
            clips[f"narr{i}"], info[f"narr{i}"] = y, dict(source="elevenlabs")
        for k, (text, t0, dur, voice) in DIALOGUE.items():
            clips[k], info[k] = _elevenlabs_take([text])[0], dict(source="elevenlabs")
    else:
        raise SystemExit(f"unknown voice backend {backend}")

    total = 21.2 + 1.0
    narr = dsp.Track(total)
    dial = dsp.Track(total)
    placed = {}
    for (idx, t0) in VOICE_CUES:
        y = clips[f"narr{idx}"]
        narr.add(y, t0, 1.0)
        placed[f"narr{idx}"] = dict(start=t0, end=t0 + len(y) / dsp.SR)
    env_json = {}
    for k, (text, t0, dur, voice) in DIALOGUE.items():
        y = clips[k]
        # diegetic: it comes out of a phone / video call - band-limited, slightly saturated, a touch of room
        d = dsp.bp(y, 280, 4200, 2)
        d = dsp.soft_clip(d * 1.5, 1.2) * 0.8
        dial.add(d, t0, 0.55, p=-0.15 if voice == "duo" else 0.15)
        env, bands = analyze(y)
        env_json[k] = dict(t0=t0, rate=100, env=[round(float(v), 4) for v in env], bands=[[round(float(v), 4) for v in b] for b in bands])
        placed[k] = dict(start=t0, end=t0 + len(y) / dsp.SR)
    dsp.write_wav(AUDIO / "voice_narration.wav", narr.buf)
    dsp.write_wav(AUDIO / "voice_dialogue.wav", dial.buf)
    (AUDIO / "voice_env.json").write_text(json.dumps(env_json))
    rep = dict(backend=backend, placed=placed, info=info, sync_targets=VOICE_SYNC)
    (AUDIO / "voice_report.json").write_text(json.dumps(rep, indent=1, default=float))
    print(f"[voice] backend={backend}")
    for k, v in placed.items():
        print(f"  {k:10s} {v['start']:6.2f} -> {v['end']:6.2f}")
    return rep


if __name__ == "__main__":
    build()
