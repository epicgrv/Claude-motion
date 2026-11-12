import sys, subprocess, numpy as np, wave
D, OUT, DUR = sys.argv[1], sys.argv[2], float(sys.argv[3])
SR = 48000
bus = np.zeros((int(DUR * SR) + SR * 2, 2), np.float32)
def load(n):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", f"{D}/{n}", "-ac", "2", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True).stdout
    a = np.frombuffer(raw, np.float32).reshape(-1, 2).copy(); return a / (np.abs(a).max() + 1e-9)
def place(s, t, g, dur=None):
    s = s.copy()
    if dur: n = int(dur * SR); s = s[:n]; m = min(int(0.12 * SR), len(s)); s[-m:] *= np.linspace(1, 0, m)[:, None]
    i = int(t * SR)
    if i < 0: s = s[-i:]; i = 0
    n = min(len(s), len(bus) - i); bus[i:i + n] += s[:n] * 10 ** (g / 20)
whoosh = load("Short whoose_1.mp3"); swoosh = load("smooth woosh.wav")[:int(1.6 * SR)]
punch = load("Punch sound .mp3"); boom = load("Cinematic_boom_01.wav"); pop = load("Pop sound ef.mp3")
click = load("click-button.mp3"); cash = load("Cash Register.wav"); ding = load("Correct.mp3"); typ = load("Typewriter s.mp3")
# hook: throw whoosh -> impact punch + boom
place(whoosh, 0.42 - 0.5, -11)
place(punch, 0.40, -5, dur=0.6)
place(boom, 0.34, -12, dur=1.5)
place(pop, 0.72, -17, dur=0.4)            # pill pop "took me out."
# whip transitions
for c in [3.2, 7.333, 8.9, 21.15]:
    place(whoosh, c - 0.5, -12)
place(swoosh, 5.433 - 0.4, -10, dur=1.0)   # brand wipe
place(boom, 5.40, -22, dur=1.0)
# chips: soft click + typewriter tick
for t in [6.30, 7.32, 8.22, 10.04, 14.36, 15.20, 17.60, 18.78, 19.54]:
    place(click, t, -17); place(typ, t + 0.02, -27, dur=0.18)
place(ding, 20.42, -19)                    # nothing complicated
place(cash, 21.98, -11, dur=1.4)           # price
place(pop, 22.0, -18, dur=0.4)
place(punch, 24.34, -17, dur=0.4)          # "hit in the face"
place(boom, 25.50, -20, dur=1.1)           # "never skipping"
bus = bus[:int(DUR * SR)]; pk = np.abs(bus).max()
if pk > 0.95: bus *= 0.95 / pk
w = wave.open(OUT, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
w.writeframes((np.clip(bus, -1, 1) * 32767).astype("<i2").tobytes()); w.close()
