"""Fish Audio TTS client for the channel voiceover.

Model: S2.1 Pro. The free route is `s2.1-pro-free` (works with a $0 wallet); `s2.1-pro` is the paid production route
(returns HTTP 402 until the wallet has credit).

The API key is NOT stored here. In the cloud session it is a network secret that the proxy injects into requests to
api.fish.audio; locally, set FISH_API_KEY.

Usage:
    python -m finance_shorts.audio.fish_tts script.txt out.wav [--voice <reference_id>] [--model s2.1-pro-free]
    python -m finance_shorts.audio.fish_tts --list-voices "storyteller"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

API = "https://api.fish.audio"
DEFAULT_MODEL = "s2.1-pro-free"


def _headers(model: str | None = None) -> dict:
    h = {"Authorization": f"Bearer {os.environ.get('FISH_API_KEY', 'proxy-injected')}"}
    if model:
        h["model"] = model
    return h


def tts(text: str, out: Path, voice: str | None = None, model: str = DEFAULT_MODEL, fmt: str = "wav",
        sample_rate: int = 44100, speed: float = 1.0, temperature: float | None = None, top_p: float | None = None,
        retries: int = 4) -> Path:
    body: dict = {"text": text, "format": fmt, "sample_rate": sample_rate, "normalize": True, "latency": "normal",
                  "prosody": {"speed": speed, "volume": 0}}
    if voice:
        body["reference_id"] = voice
    if temperature is not None:
        body["temperature"] = temperature
    if top_p is not None:
        body["top_p"] = top_p
    for attempt in range(retries):
        r = requests.post(f"{API}/v1/tts", headers={**_headers(model), "Content-Type": "application/json"},
                          data=json.dumps(body), timeout=300)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("audio"):
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(r.content)
            return out
        if r.status_code in (429, 500, 502, 503, 504) and attempt < retries - 1:
            time.sleep(2 ** attempt * 2)
            continue
        raise RuntimeError(f"Fish TTS failed: HTTP {r.status_code}: {r.text[:400]}")
    raise RuntimeError("unreachable")


def list_voices(query: str = "", page_size: int = 20, language: str = "en") -> list[dict]:
    params = {"page_size": page_size, "title": query, "language": language, "sort_by": "task_count"}
    r = requests.get(f"{API}/model", headers=_headers(), params=params, timeout=60)
    r.raise_for_status()
    return [{"id": m["_id"], "title": m.get("title"), "tags": m.get("tags"), "uses": m.get("task_count"),
             "description": (m.get("description") or "")[:120]} for m in r.json().get("items", [])]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("script", nargs="?")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--voice")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--list-voices", metavar="QUERY")
    a = ap.parse_args(argv)
    if a.list_voices is not None:
        for v in list_voices(a.list_voices):
            print(json.dumps(v))
        return
    if not (a.script and a.out):
        ap.error("script and out are required")
    text = Path(a.script).read_text()
    print(tts(text, Path(a.out), voice=a.voice, model=a.model, speed=a.speed))


if __name__ == "__main__":
    sys.exit(main())
