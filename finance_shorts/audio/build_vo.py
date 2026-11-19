"""Build the voiceover track for a script's lines.json.

For every line: generate with Fish S2.1 Pro (cached per text+voice), transcribe with faster-whisper and compare
with the script (retake up to 2× on mismatch), trim silence, level each line to the same speech loudness, then
assemble with the scripted gaps. Writes vo.wav (48 kHz mono) and timeline.json (line + word timestamps) used by the
visual and caption stages.

    python -m finance_shorts.audio.build_vo finance_shorts/scripts/pepsi-jet/lines.json finance_shorts/audio/pepsi-jet
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from finance_shorts.audio.fish_tts import tts

SR = 48000
_whisper = None


def whisper():
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel
        _whisper = WhisperModel("small.en", device="cpu", compute_type="int8")
    return _whisper


_NUM = {"0": "zero", "1": "one", "2": "two", "5": "five", "7": "seven", "10": "ten", "20": "twenty", "96": "ninety-six"}


def norm_words(s: str) -> list[str]:
    """Words for comparison: drop (tags), laughs, punctuation and anything numeric (whisper writes digits, the script
    spells them), so only real wording differences count."""
    s = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", s.lower())
    ws = re.findall(r"[a-z0-9']+", s)
    num = {"one", "two", "five", "seven", "ten", "twenty", "ninety", "six", "hundred", "thousand", "million", "eight",
           "fifty", "nine", "nineteen", "percent", "dollars", "cents", "and"}
    return [w for w in ws if not re.fullmatch(r"(ha)+h?|\d+|s", w) and w not in num]


def wer(ref: list[str], hyp: list[str]) -> float:
    d = np.arange(len(hyp) + 1)
    for i, r in enumerate(ref, 1):
        prev, d[0] = d.copy(), i
        for j, h in enumerate(hyp, 1):
            d[j] = min(prev[j] + 1, d[j - 1] + 1, prev[j - 1] + (r != h))
    return d[-1] / max(1, len(ref))


def load(path: Path) -> np.ndarray:
    x, sr = sf.read(path)
    x = x if x.ndim == 1 else x.mean(1)
    return resample_poly(x, SR, sr) if sr != SR else x


def trim(x: np.ndarray, thr_db=-42, pad=0.03) -> np.ndarray:
    n = int(SR * 0.01)
    e = np.array([np.sqrt((x[i:i + n] ** 2).mean() + 1e-12) for i in range(0, len(x) - n, n)])
    on = np.where(20 * np.log10(e) > thr_db)[0]
    if not len(on):
        return x
    a, b = max(0, on[0] * n - int(pad * SR)), min(len(x), (on[-1] + 1) * n + int(pad * SR))
    y = x[a:b].copy()
    f = int(0.008 * SR)
    y[:f] *= np.linspace(0, 1, f)
    y[-f:] *= np.linspace(1, 0, f)
    return y


def squeeze(x: np.ndarray, max_pause=0.22, thr_db=-40) -> np.ndarray:
    """Shorten silent runs inside a line to max_pause (keeps the read, removes dead air)."""
    n = int(SR * 0.01)
    e = np.array([np.sqrt((x[i:i + n] ** 2).mean() + 1e-12) for i in range(0, len(x) - n, n)])
    sil = 20 * np.log10(e) < thr_db
    keep = np.ones(len(x), bool)
    i = 0
    while i < len(sil):
        if sil[i]:
            j = i
            while j < len(sil) and sil[j]:
                j += 1
            run = (j - i) * n
            cut = run - int(max_pause * SR)
            if cut > 0 and i > 0 and j < len(sil):
                a = i * n + int(max_pause * SR / 2)
                keep[a:a + cut] = False
            i = j
        else:
            i += 1
    return x[keep]


def level(x: np.ndarray, target_db=-19.0) -> np.ndarray:
    n = int(SR * 0.02)
    e = np.array([np.sqrt((x[i:i + n] ** 2).mean() + 1e-12) for i in range(0, len(x) - n, n)])
    voiced = e[20 * np.log10(e) > -40]
    cur = 20 * np.log10(np.sqrt((voiced ** 2).mean())) if len(voiced) else -30
    y = x * 10 ** ((target_db - cur) / 20)
    pk = np.abs(y).max()
    return y / pk * 0.89 if pk > 0.89 else y


def transcribe(x: np.ndarray):
    a = resample_poly(x, 16000, SR).astype(np.float32)
    segs, _ = whisper().transcribe(a, word_timestamps=True, language="en")
    words = [(w.word.strip(), w.start, w.end) for s in segs for w in (s.words or [])]
    return " ".join(w[0] for w in words), words


def main(lines_json: str, outdir: str):
    spec = json.loads(Path(lines_json).read_text())
    out = Path(outdir)
    takes = out / "takes"
    takes.mkdir(parents=True, exist_ok=True)
    pieces, timeline, t = [], [], 0.0
    for ln in spec["lines"]:
        v = spec["voices"][ln["who"]]
        best = None
        for take in range(3):
            key = hashlib.sha1(f"{ln['tts']}|{v['id']}|{v.get('speed', 1)}|{spec['model']}|{take}".encode()).hexdigest()[:10]
            p = takes / f"{ln['id']}_{ln['who']}_{key}.wav"
            if not p.exists():
                tts(ln["tts"], p, voice=v["id"], model=spec["model"], speed=v.get("speed", 1.0))
            x = level(squeeze(trim(load(p)), ln.get("max_pause", spec.get("max_pause", 0.22))))
            text, words = transcribe(x)
            score = wer(norm_words(ln["text"].replace("$", "")), norm_words(text))
            # numbers come back as digits from whisper; also compare against the spoken tts text
            score = min(score, wer(norm_words(ln["tts"]), norm_words(text)))
            print(f"{ln['id']} {ln['who']:8} take{take} wer={score:.2f} | {text}")
            if best is None or score < best[0]:
                best = (score, x, words, p.name, text)
            if score <= 0.15:
                break
        score, x, words, name, text = best
        t += ln.get("gap", 0.15)
        start = t
        pieces.append((int(round(start * SR)), x))
        timeline.append({"id": ln["id"], "who": ln["who"], "text": ln["text"], "heard": text, "wer": round(score, 3),
                         "take": name, "start": round(start, 3), "end": round(start + len(x) / SR, 3),
                         "words": [{"w": w, "s": round(start + s, 3), "e": round(start + e, 3)} for w, s, e in words]})
        t = start + len(x) / SR
    total = int((t + 0.6) * SR)
    vo = np.zeros(total)
    for s, x in pieces:
        vo[s:s + len(x)] += x
    sf.write(out / "vo.wav", vo.astype(np.float32), SR, subtype="PCM_24")
    (out / "timeline.json").write_text(json.dumps({"duration": round(total / SR, 3), "lines": timeline}, indent=1))
    print(f"vo.wav {total / SR:.2f}s, worst wer {max(l['wer'] for l in timeline):.2f}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
