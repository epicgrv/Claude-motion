"""Premium UGC edit. python3 render.py in.mp4 captions.json out_video_noaudio.mp4"""
import sys, json, subprocess, math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, CAP, OUT = sys.argv[1:4]
W, H, FPS = 1080, 1920, 24
END = 13.417                       # trim: cut before incomplete last words
CUTS = [4.0, 7.958, 12.0]          # source shot changes
N = int(round(END * FPS))
FD = "fonts/"
cfg = json.load(open(CAP)) if CAP != "-" else {"hook": None, "lines": []}

def ease_out(x): x = min(max(x, 0), 1); return 1 - (1 - x) ** 4
def ease_io(x): x = min(max(x, 0), 1); return x * x * (3 - 2 * x)

# ---------- camera (zoom) curve ----------
def zoom_at(t):
    z = 1.0
    if t < 0.6:                                   # hook: zoom OUT from tight
        z = 1.5 - 0.5 * ease_out(t / 0.6)
        return z
    # slow drifts per shot
    if t < CUTS[0]: z = 1.0 + 0.05 * (t - 0.6) / (CUTS[0] - 0.6)
    elif t < CUTS[1]: z = 1.04 + 0.08 * (t - CUTS[0]) / (CUTS[1] - CUTS[0])
    elif t < CUTS[2]: z = 1.0 + 0.04 * (t - CUTS[1]) / (CUTS[2] - CUTS[1])
    else: z = 1.02 + 0.12 * ease_io((t - CUTS[2]) / (END - CUTS[2]))
    # punch-ins on emphasis beats (hold, then ease back)
    for p, amt, hold in cfg.get("punches", [[2.3, 0.10, 1.2], [9.9, 0.10, 1.4]]):
        if p <= t < p + hold:
            k = ease_out((t - p) / 0.12) * (1 - ease_io((t - p - hold + 0.25) / 0.25))
            z += amt * k
    # transition zoom whip around cuts
    for c in CUTS:
        d = t - c
        if -0.17 < d < 0: z *= 1 + 0.25 * ease_io((d + 0.17) / 0.17) ** 2
        if 0 <= d < 0.25: z *= 1 + 0.25 * (1 - ease_out(d / 0.25))
    return z

def blur_at(t):
    for c in CUTS:
        d = t - c
        if -0.13 < d < 0.17: return 1 - abs(d) / (0.13 if d < 0 else 0.17)
    if t < 0.25: return 0.8 * (1 - t / 0.25)
    return 0

# ---------- film burn / light leak ----------
rng = np.random.default_rng(3)
lw, lh = 54, 96
yy, xx = np.mgrid[0:lh, 0:lw] / np.array([lh, lw])[:, None, None]
blobs = [(rng.uniform(-.2, 1.2), rng.uniform(-.2, 1.2), rng.uniform(.15, .45), rng.uniform(-1, 1), rng.uniform(-1, 1)) for _ in range(7)]
def burn(t, phase):
    f = np.zeros((lh, lw))
    for i, (bx, by, r, vx, vy) in enumerate(blobs):
        cx = bx + vx * (t + phase) * 0.9; cy = by + vy * (t + phase) * 0.9
        f += np.exp(-(((xx - cx) ** 2) * 2.2 + (yy - cy) ** 2) / (r * r))
    edge = np.clip(1.3 - np.minimum.reduce([xx, 1 - xx, yy * 1.6, (1 - yy) * 1.6]) * 3.5, 0, 1)
    f = np.clip(f * 0.55 + edge * 0.6, 0, 1.6)
    col = np.stack([np.clip(f * 1.25, 0, 1), np.clip(f * 0.62 - .05, 0, 1) ** 1.2, np.clip(f - 1.0, 0, 1) * 0.5], -1)
    im = Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC)
    return np.asarray(im).astype(np.float32) / 255

def burn_amt(t):
    a = 0.0
    if t < 1.0: a = max(a, 1.0 * (1 - ease_io(t / 1.0)) if t > 0.05 else 1.0)
    for c in CUTS:
        d = abs(t - c)
        if d < 0.3: a = max(a, 0.55 * (1 - d / 0.3))
    return a

# ---------- grade ----------
vy, vx = np.mgrid[0:H, 0:W]
vig = 1 - 0.28 * np.clip(((vx / W - .5) ** 2 * 1.4 + (vy / H - .5) ** 2) * 2.2, 0, 1) ** 1.5
vig = vig[..., None].astype(np.float32)
lut = np.arange(256) / 255.0
s_curve = np.clip(lut + 0.10 * np.sin(2 * np.pi * (lut - 0.5)) * -0.5 + 0.08 * (lut - lut * lut) * 0, 0, 1)
s_curve = (0.5 + (lut - 0.5) * 1.08 - 0.04 * np.sin(2 * np.pi * lut)).clip(0, 1)
LUT = np.stack([s_curve * 1.02, s_curve * 1.0, s_curve * 0.965], -1).clip(0, 1).astype(np.float32)
grain_bank = [rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32) for _ in range(6)]

# ---------- captions ----------
def font(name, size, var=None):
    f = ImageFont.truetype(FD + name, size)
    if var: f.set_variation_by_name(var)
    return f
SANS_BI = "/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf"
SANS_B = "/usr/share/fonts/opentype/inter/InterDisplay-ExtraBold.otf"

def draw_words(canvas, words, y, size, t0, t, center=True):
    """words: list of (text, style). style: 'sans','serif','hook_sans','hook_serif'"""
    fonts = {"sans": ImageFont.truetype(SANS_B, size),
             "serif": font("Playfair-Italic.ttf", int(size * 1.18), b"Black Italic"),
             "hook_sans": ImageFont.truetype(SANS_BI, size),
             "hook_serif": font("Playfair-Italic.ttf", int(size * 1.25), b"Black Italic")}
    gold = (244, 205, 120)
    d = ImageDraw.Draw(canvas)
    sp = size * 0.26
    widths = [d.textlength(w, font=fonts[s]) for w, s in words]
    total = sum(widths) + sp * (len(words) - 1)
    x = (W - total) / 2
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    for i, ((w, s), wd) in enumerate(zip(words, widths)):
        k = ease_out((t - t0 - i * 0.06) / 0.22)
        if k <= 0: x += wd + sp; continue
        dy = (1 - k) * size * 0.45
        a = int(255 * min(1, k * 1.4))
        fill = gold if "serif" in s else (255, 255, 255)
        ld.text((x, y + dy), w, font=fonts[s], fill=fill + (a,), anchor="ls",
                stroke_width=0)
        x += wd + sp
    sh = layer.split()[3].filter(ImageFilter.GaussianBlur(size * 0.18))
    shadow = Image.new("RGBA", canvas.size, (0, 0, 0, 0)); shadow.putalpha(sh.point(lambda v: int(v * 0.75)))
    canvas.alpha_composite(shadow, (0, int(size * 0.05)))
    canvas.alpha_composite(layer)

def caption_layer(t):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hk = cfg.get("hook")
    if hk and hk["start"] <= t < hk["end"]:
        fade = 1 - ease_io((t - hk["end"] + 0.15) / 0.15)
        tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        y = H * 0.40
        for li, line in enumerate(hk["lines"]):
            draw_words(tmp, [(w.strip("*"), "hook_serif" if w.startswith("*") else "hook_sans") for w in line.split()],
                       y + li * 132, 112, hk["start"] + li * 0.18, t)
        if fade < 1:
            a = tmp.split()[3].point(lambda v: int(v * fade)); tmp.putalpha(a)
        lay.alpha_composite(tmp)
    for ln in cfg.get("lines", []):
        if ln["start"] <= t < ln["end"]:
            words = [(w.strip("*"), "serif" if w.startswith("*") else "sans") for w in ln["text"].split()]
            draw_words(lay, words, H * 0.74, 78, ln["start"], t)
    return lay

# ---------- main loop ----------
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-t", str(END), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
for i in range(N):
    raw = dec.stdout.read(W * H * 3)
    if len(raw) < W * H * 3: break
    t = i / FPS
    img = Image.frombuffer("RGB", (W, H), raw)
    z = zoom_at(t)
    cw, ch = W / z, H / z
    img = img.transform((W, H), Image.EXTENT, ((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2), Image.BICUBIC)
    f = np.asarray(img).astype(np.float32) / 255
    b = blur_at(t)
    if b > 0.05:  # vertical motion blur (whip)
        n = int(2 + b * 10); step = int(4 + b * 9)
        acc = np.zeros_like(f)
        for k in range(-n, n + 1): acc += np.roll(f, k * step, axis=0)
        f = acc / (2 * n + 1)
    # grade
    idx = (f * 255).astype(np.uint8)
    f = np.stack([LUT[idx[..., c], c] for c in range(3)], -1)
    f *= vig
    # film burn (screen blend)
    a = burn_amt(t)
    if a > 0.01:
        L = burn(t, 0 if t < 1 else min(CUTS, key=lambda c: abs(c - t))) * a
        f = 1 - (1 - f) * (1 - L)
    # camera-click flash
    if t < 0.125: f = f + (1 - f) * (1 - t / 0.125) ** 1.5
    for c in CUTS:
        d = t - c
        if 0 <= d < 0.09: f = f + (1 - f) * 0.35 * (1 - d / 0.09)
    # grain
    g = grain_bank[i % 6]
    g = np.repeat(np.repeat(g, 2, 0), 2, 1)[..., None]
    f = np.clip(f + g * 0.018, 0, 1)
    out = Image.fromarray((f * 255).astype(np.uint8)).convert("RGBA")
    out.alpha_composite(caption_layer(t))
    enc.stdin.write(out.convert("RGB").tobytes())
    if i % 48 == 0: print(f"{i}/{N}", flush=True)
enc.stdin.close(); enc.wait(); dec.terminate()
