"""Busy Co. UGC edit. python3 render_busy.py src.mov edit.json out.mp4  (run from dir holding a/)"""
import sys, json, math, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, CFG, OUT = sys.argv[1:4]
cfg = json.load(open(CFG))
W, H, FPS = 1080, 1920, 30
END = cfg["end"]; N = int(round(END * FPS)); CUTS = cfg["cuts"]
A = "a/"
# Busy Co. brand palette (getbusy.co CSS)
INK, CREAM, MAUVE, BLUSH, ORANGE, YELLOW = (36, 31, 33), (242, 237, 235), (201, 128, 163), (250, 194, 217), (235, 112, 69), (240, 222, 54)
WHITE = (255, 255, 255)

def clamp(x): return min(max(x, 0.0), 1.0)
def eo3(x): x = clamp(x); return 1 - (1 - x) ** 3
def eo5(x): x = clamp(x); return 1 - (1 - x) ** 5
def smooth(x): x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10)
def back(x, s=1.7):  # ease-out-back (overshoot pop)
    x = clamp(x) - 1; return 1 + (s + 1) * x ** 3 + s * x ** 2

# ---------------- camera ----------------
def seg_index(t):
    for k, c in enumerate(CUTS):
        if t < c: return k
    return len(CUTS)
def zoom_at(t):
    seg = [0, *CUTS, END]; k = seg_index(t)
    a, b = cfg["drift"][k]
    z = a + (b - a) * smooth((t - seg[k]) / (seg[k + 1] - seg[k]))
    for p, amt, hold in cfg["punches"]:
        if p <= t < p + hold:
            z *= 1 + amt * eo3((t - p) / 0.12) * (1 - smooth((t - p - hold + 0.3) / 0.3))
    for c in cfg["whips"]:
        d = t - c
        if -0.17 < d < 0: z *= 1 + 0.2 * smooth((d + 0.17) / 0.17) ** 2
        if 0 <= d < 0.27: z *= 1 + 0.2 * (1 - eo3(d / 0.27))
    imp = cfg["impact"]; d = t - imp
    if 0 <= d < 0.6: z *= 1 + 0.16 * (1 - eo3(d / 0.6))
    return z
rng = np.random.default_rng(11)
SHAKE = rng.uniform(-1, 1, (64, 2))
def shake_at(t):
    d = t - cfg["impact"]
    if not (0 <= d < 0.35): return 0, 0
    amp = 22 * (1 - d / 0.35) ** 2; j = int(d * FPS)
    return SHAKE[j, 0] * amp, SHAKE[j, 1] * amp
def blur_at(t):
    for c in cfg["whips"]:
        d = t - c
        if -0.12 < d < 0.16: return 1 - abs(d) / (0.12 if d < 0 else 0.16)
    return 0.0

# ---------------- light grade ----------------
vy, vx = np.mgrid[0:H, 0:W]
VIG = (1 - 0.08 * np.clip(((vx / W - .5) ** 2 * 1.3 + (vy / H - .5) ** 2) * 2.2, 0, 1) ** 1.6)[..., None].astype(np.float32)
WARM = np.array([1.012, 1.0, 0.985], np.float32)
GRAIN = [np.repeat(np.repeat(rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32), 2, 0), 2, 1)[..., None] for _ in range(6)]
def grade(f):
    f = f * WARM
    l = f.mean(-1, keepdims=True)
    f = l + (f - l) * 1.05            # +5% saturation
    f = 0.5 + (f - 0.5) * 1.03        # +3% contrast
    return np.clip(f, 0, 1) * VIG

# ---------------- type ----------------
FONTS = {}
def fnt(name, size):
    k = (name, size)
    if k not in FONTS: FONTS[k] = ImageFont.truetype(A + name, size)
    return FONTS[k]
PB, SUP = "Pangram-Bold.otf", "Supply-Bold.otf"

def soft_shadow(layer, r, a, off=4, color=INK):
    al = layer.split()[3].filter(ImageFilter.GaussianBlur(r)).point(lambda v: int(v * a))
    s = Image.new("RGBA", layer.size, color + (0,)); s.putalpha(al)
    base = Image.new("RGBA", layer.size, (0, 0, 0, 0)); base.alpha_composite(s, (0, off)); base.alpha_composite(layer)
    return base

def rotate_paste(dst, tile, cx, cy, ang, scale=1.0, alpha=1.0):
    if scale != 1.0:
        tile = tile.resize((max(1, int(tile.width * scale)), max(1, int(tile.height * scale))), Image.LANCZOS)
    if ang: tile = tile.rotate(ang, Image.BICUBIC, expand=True)
    if alpha < 0.999: tile.putalpha(tile.split()[3].point(lambda v: int(v * alpha)))
    dst.alpha_composite(tile, (int(cx - tile.width / 2), int(cy - tile.height / 2)))

# --- main karaoke captions: white Pangram Bold, active word on sliding orange pill
def caption_chunk(layer, ch, t):
    size = ch.get("size", 72); f = fnt(PB, size)
    words = ch["words"]                                        # [text, start]
    d = ImageDraw.Draw(layer)
    sp = size * 0.28
    wd = [d.textlength(w, font=f) for w, _ in words]
    total = sum(wd) + sp * (len(words) - 1)
    k_in = eo5((t - ch["start"]) / 0.16)
    k_out = 1 - smooth((t - ch["end"] + 0.1) / 0.1)
    alpha = k_in * k_out
    if alpha <= 0: return
    tile = Image.new("RGBA", (int(total + size * 1.4), int(size * 2.2)), (0, 0, 0, 0))
    td = ImageDraw.Draw(tile)
    x0 = size * 0.7; base = size * 1.45
    xs = []; x = x0
    for w in wd: xs.append(x); x += w + sp
    # active word index + smooth pill slide
    act = -1
    for i, (w, st) in enumerate(words):
        if t >= st: act = i
    if act >= 0:
        st = words[act][1]; k = eo3((t - st) / 0.09)
        px0, pw0 = (xs[act - 1], wd[act - 1]) if act > 0 and k < 1 else (xs[act], wd[act])
        px = px0 + (xs[act] - px0) * k; pw = pw0 + (wd[act] - pw0) * k
        if act == 0 and k < 1: pw *= 0.6 + 0.4 * k; px = xs[0] + (wd[0] - pw) / 2
        hl = ch.get("hl", {}).get(str(act), "orange")
        col = {"orange": ORANGE, "blush": BLUSH, "yellow": YELLOW, "mauve": MAUVE}[hl]
        pad_x, pad_y = size * 0.2, size * 0.14
        td.rounded_rectangle((px - pad_x, base - size * 0.82 - pad_y, px + pw + pad_x, base + size * 0.2 + pad_y),
                             radius=size * 0.26, fill=col + (255,))
    for i, ((w, st), x) in enumerate(zip(words, xs)):
        hl = ch.get("hl", {}).get(str(i), "orange")
        on_light = i == act and hl in ("blush", "yellow")
        col = INK if on_light else WHITE
        td.text((x, base), w, font=f, fill=col + (255,), anchor="ls")
    tile = soft_shadow(tile, size * 0.12, 0.55)
    rotate_paste(layer, tile, W / 2, ch["y"] * H, 0, scale=0.86 + 0.14 * back((t - ch["start"]) / 0.22), alpha=alpha)

# --- hook: two big lines, second line in an orange pill tilted
def hook(layer, hk, t):
    if not (hk["start"] <= t < hk["end"]): return
    out = 1 - smooth((t - hk["end"] + 0.12) / 0.12)
    y = hk["y"] * H
    for li, ln in enumerate(hk["lines"]):
        st = ln["start"]; k = back((t - st) / 0.26, 2.2)
        if t < st: continue
        size = ln["size"]; f = fnt(PB, size)
        tw = ImageDraw.Draw(layer).textlength(ln["text"], font=f)
        tile = Image.new("RGBA", (int(tw + size * 1.2), int(size * 1.9)), (0, 0, 0, 0)); td = ImageDraw.Draw(tile)
        base = size * 1.3
        if ln.get("pill"):
            col = {"orange": ORANGE, "blush": BLUSH}[ln["pill"]]
            td.rounded_rectangle((size * 0.32, base - size * 0.95, size * 0.88 + tw, base + size * 0.28), radius=size * 0.3, fill=col + (255,))
        td.text((size * 0.6, base), ln["text"], font=f, fill=(CREAM if ln.get("pill") else WHITE) + (255,), anchor="ls")
        tile = soft_shadow(tile, size * 0.1, 0.5, off=6)
        rotate_paste(layer, tile, W / 2, y, ln.get("rot", 0), scale=max(0.01, 0.5 + 0.5 * k), alpha=clamp((t - st) / 0.08) * out)
        y += size * ln.get("lead", 1.25)

# --- feature chips: Supply Bold caps, ink pill + orange dot, stacked, slide in from left
def chips(layer, stack, t):
    if not (stack["start"] <= t < stack["end"]): return
    out = 1 - smooth((t - stack["end"] + 0.15) / 0.15)
    size = 48; f = fnt(SUP, size)
    y = stack["y"] * H
    for txt, st in stack["items"]:
        if t < st: continue
        k = eo5((t - st) / 0.3)
        d = ImageDraw.Draw(layer); tw = d.textlength(txt, font=f)
        hgt = int(size * 1.75); wid = int(tw + size * 2.1)
        tile = Image.new("RGBA", (wid + 8, hgt + 8), (0, 0, 0, 0)); td = ImageDraw.Draw(tile)
        td.rounded_rectangle((4, 4, wid + 4, hgt + 4), radius=hgt / 2, fill=INK + (235,), outline=CREAM + (90,), width=2)
        cy = 4 + hgt / 2; r = size * 0.22
        td.ellipse((4 + size * 0.55 - r, cy - r, 4 + size * 0.55 + r, cy + r), fill=tuple(stack.get("dot", ORANGE)) + (255,))
        td.text((4 + size * 1.05, cy + size * 0.36), txt, font=f, fill=CREAM + (255,), anchor="ls")
        tile = soft_shadow(tile, 8, 0.45, off=4)
        if out < 0.999 or k < 0.999:
            tile.putalpha(tile.split()[3].point(lambda v, a=clamp(k * 1.3) * out: int(v * a)))
        layer.alpha_composite(tile, (int(56 - (1 - k) * 60), int(y)))
        y += hgt + 16

# --- price card: yellow tilted card, ink Pangram price, Supply label
def price(layer, pc, t):
    if not (pc["start"] <= t < pc["end"]): return
    out = 1 - smooth((t - pc["end"] + 0.12) / 0.12)
    k = back((t - pc["start"]) / 0.3, 2.0)
    f = fnt(PB, 150); fl = fnt(SUP, 36)
    d = ImageDraw.Draw(layer); tw = d.textlength(pc["text"], font=f)
    wid, hgt = int(tw + 120), 270
    tile = Image.new("RGBA", (wid, hgt), (0, 0, 0, 0)); td = ImageDraw.Draw(tile)
    td.rounded_rectangle((0, 0, wid - 1, hgt - 1), radius=34, fill=YELLOW + (255,))
    td.text((wid / 2, 70), pc["label"], font=fl, fill=INK + (255,), anchor="ms")
    td.text((wid / 2, 225), pc["text"], font=f, fill=INK + (255,), anchor="ms")
    tile = soft_shadow(tile, 18, 0.45, off=10)
    rotate_paste(layer, tile, W / 2, pc["y"] * H, pc.get("rot", 4), scale=max(0.01, 0.4 + 0.6 * k), alpha=clamp((t - pc["start"]) / 0.06) * out)

# --- brand wipe transition: orange panel with blush leading band sweeps up across the cut
def brand_wipe(f, t):
    for c in cfg.get("brand_wipes", []):
        d = t - c
        if -0.2 < d < 0.2:
            p = smooth((d + 0.2) / 0.4)                       # 0..1 sweep
            top = int(H * (1.15 - 1.5 * p)); bot = top + int(H * 0.85)
            lo, hi = max(top, 0), min(bot, H)
            if hi > lo:
                f[lo:hi] = np.array(ORANGE, np.float32) / 255
            bl, bh = max(top - 70, 0), min(top, H)
            if bh > bl: f[bl:bh] = np.array(BLUSH, np.float32) / 255
            if 0 < bot < H:
                b2 = min(bot + 30, H); f[bot:b2] = np.array(CREAM, np.float32) / 255
    return f

def overlay(t):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hook(lay, cfg["hook"], t)
    for st in cfg["chips"]: chips(lay, st, t)
    for ch in cfg["captions"]:
        if ch["start"] <= t < ch["end"]: caption_chunk(lay, ch, t)
    price(lay, cfg["price"], t)
    return lay

# ---------------- main ----------------
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-t", str(END), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
BB = open("caption_bbox.txt", "w")
for i in range(N):
    raw = dec.stdout.read(W * H * 3)
    if len(raw) < W * H * 3: break
    t = i / FPS
    src = Image.frombuffer("RGB", (W, H), raw)
    z = zoom_at(t); sx, sy = shake_at(t); cw, ch = W / z, H / z
    x0 = (W - cw) / 2 - sx / z; y0 = (H - ch) / 2 - sy / z
    x0 = min(max(x0, 0), W - cw); y0 = min(max(y0, 0), H - ch)
    img = src.transform((W, H), Image.EXTENT, (x0, y0, x0 + cw, y0 + ch), Image.BICUBIC)
    f = np.asarray(img).astype(np.float32) / 255
    b = blur_at(t)
    if b > 0.04:
        n = int(3 + b * 9); step = max(1, int(3 + b * 10))
        p = np.pad(f, ((n * step, n * step), (0, 0), (0, 0)), mode="edge"); acc = np.zeros_like(f)
        for k in range(-n, n + 1): o = n * step + k * step; acc += p[o:o + H]
        f = acc / (2 * n + 1)
    f = grade(f)
    d = t - cfg["impact"]
    if 0 <= d < 0.1: f = f + (1 - f) * 0.55 * (1 - d / 0.1)        # impact flash
    for c in cfg["whips"]:
        dd = t - c
        if 0 <= dd < 0.07: f = f + (1 - f) * 0.25 * (1 - dd / 0.07)
    f = brand_wipe(f, t)
    f = np.clip(f + GRAIN[i % 6] * 0.006, 0, 1)
    out = Image.fromarray((f * 255).astype(np.uint8)).convert("RGBA")
    ov = overlay(t)
    bb = ov.split()[3].point(lambda v: 255 if v > 60 else 0).getbbox()
    BB.write(f"{t:.3f} {bb[1] / H if bb else -1:.3f} {bb[3] / H if bb else -1:.3f}\n")
    out.alpha_composite(ov)
    enc.stdin.write(out.convert("RGB").tobytes())
    if i % 90 == 0: print(f"{i}/{N}", flush=True)
enc.stdin.close(); enc.wait(); dec.terminate()
