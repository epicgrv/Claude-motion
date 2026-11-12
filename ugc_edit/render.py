"""Premium UGC edit v2. python3 render2.py in.mp4 edit.json out.mp4   (run from dir holding a/)"""
import sys, json, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, CFG, OUT = sys.argv[1:4]
cfg = json.load(open(CFG))
W, H, FPS = 1080, 1920, 24
END = cfg["end"]; CUTS = cfg["cuts"]; N = int(round(END * FPS))
A = "a/"

def clamp(x): return min(max(x, 0.0), 1.0)
def ease_out3(x): x = clamp(x); return 1 - (1 - x) ** 3
def ease_out5(x): x = clamp(x); return 1 - (1 - x) ** 5
def smooth(x): x = clamp(x); return x * x * x * (x * (6 * x - 15) + 10)   # smootherstep

# ---------------- camera ----------------
HOOK_Z, HOOK_T = 1.32, 1.25
def zoom_at(t):
    if t < HOOK_T:   # smooth zoom-out: fast start, long soft landing (C1-continuous into drift)
        return 1.0 + (HOOK_Z - 1.0) * (1 - ease_out5(t / HOOK_T))
    seg = [0, *CUTS, END]
    drift = cfg["drift"]
    for k in range(len(seg) - 1):
        if seg[k] <= t < seg[k + 1]:
            a, b = drift[k]; s0 = max(seg[k], HOOK_T if k == 0 else seg[k])
            z = a + (b - a) * smooth((t - s0) / (seg[k + 1] - s0))
            break
    else:
        z = drift[-1][1]
    for p, amt, hold in cfg["punches"]:
        if p <= t < p + hold:
            z *= 1 + amt * ease_out3((t - p) / 0.14) * (1 - smooth((t - p - hold + 0.3) / 0.3))
    for c in CUTS:   # zoom-through transition
        d = t - c
        if -0.2 < d < 0: z *= 1 + 0.22 * smooth((d + 0.2) / 0.2) ** 2
        if 0 <= d < 0.3: z *= 1 + 0.22 * (1 - ease_out3(d / 0.3))
    return z

def blur_at(t):
    for c in CUTS:
        d = t - c
        if -0.125 < d < 0.17: return 1 - (abs(d) / (0.125 if d < 0 else 0.17))
    return 0.0

# ---------------- film burns (from Drive pack, screen-blended) ----------------
def load_rgb(name):
    raw = np.fromfile(A + name + ".rgb", np.uint8)
    return raw.reshape(-1, H, W, 3)
TINT = np.array([1.0, 0.82, 0.62], np.float32)
BURNS = {k: load_rgb(k) for k in {b[1] for b in cfg["burns"]}}
def burn_frame(t):
    out = None
    for start, name, gain in cfg["burns"]:
        fi = int(round((t - start) * FPS))
        clip = BURNS[name]
        if 0 <= fi < len(clip):
            L = clip[fi].astype(np.float32) / 255 * gain * TINT
            out = L if out is None else 1 - (1 - out) * (1 - L)
    return out

# ---------------- grade: Drive LUT (TailorMade) @ mix + vignette + grain ----------------
def load_cube(p):
    rows, size = [], None
    for ln in open(p):
        s = ln.strip().split()
        if not s or s[0].startswith("#"): continue
        if s[0] == "LUT_3D_SIZE": size = int(s[1]); continue
        try: rows.append([float(v) for v in s[:3]])
        except ValueError: pass
    return np.array(rows, np.float32).reshape(size, size, size, 3), size   # [b][g][r]
CUBE, CS = load_cube(A + "tailormade.cube")
# bake to 64^3 uint8-indexed lookup via per-channel quantization (fast nearest on 6-bit)
q = np.linspace(0, CS - 1, 64)
def interp_axis(arr, axis):
    i0 = np.floor(q).astype(int); i1 = np.minimum(i0 + 1, CS - 1); f = (q - i0).astype(np.float32)
    a0 = np.take(arr, i0, axis); a1 = np.take(arr, i1, axis)
    sh = [1] * arr.ndim; sh[axis] = -1
    return a0 + (a1 - a0) * f.reshape(sh)
LUT64 = interp_axis(interp_axis(interp_axis(CUBE, 0), 1), 2)   # [b64][g64][r64][3]
MIX = cfg.get("lut_mix", 0.5)

vy, vx = np.mgrid[0:H, 0:W]
VIG = (1 - 0.22 * np.clip(((vx / W - .5) ** 2 * 1.3 + (vy / H - .5) ** 2) * 2.2, 0, 1) ** 1.6)[..., None].astype(np.float32)
rng = np.random.default_rng(3)
GRAIN = [np.repeat(np.repeat(rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32), 2, 0), 2, 1)[..., None] for _ in range(6)]

def grade(f):
    i = np.clip((f * 63 + 0.5).astype(np.int32), 0, 63)
    g = LUT64[i[..., 2], i[..., 1], i[..., 0]]
    f = f * (1 - MIX) + g * MIX
    f = 0.5 + (f - 0.5) * 1.05          # gentle contrast
    return np.clip(f, 0, 1) * VIG

# ---------------- captions ----------------
CREAM, GOLD = (255, 252, 246), (236, 196, 128)
FONTS = {}
def fnt(key, size):
    path = {"sans": "sequel_bold.otf", "sansB": "sequel_black.otf", "hook": "sequel_black_obl.otf", "serif": "garamond_bi.ttf"}[key]
    k = (key, size)
    if k not in FONTS: FONTS[k] = ImageFont.truetype(A + path, size)
    return FONTS[k]

def render_line(layer, words, y, size, t, sans="sans", serif_scale=1.22, letter_track=0):
    """words: [(text, accent:bool, start)] - each word rises+fades in at its own spoken time."""
    d = ImageDraw.Draw(layer)
    items = []
    for w, acc, st in words:
        f = fnt("serif", int(size * serif_scale)) if acc else fnt(sans, size)
        items.append((w, acc, st, f, d.textlength(w, font=f)))
    sp = size * 0.24
    total = sum(it[4] for it in items) + sp * (len(items) - 1)
    x = (W - total) / 2
    for w, acc, st, f, wd in items:
        k = ease_out3((t - st) / 0.2)
        if k > 0:
            dy = (1 - k) * size * 0.35
            a = int(255 * clamp(k * 1.6))
            sc = 0.92 + 0.08 * ease_out5((t - st) / 0.25)
            # draw on small tile for per-word scale pop
            tw, th = int(wd + size), int(size * 2.2)
            tile = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
            ImageDraw.Draw(tile).text((size / 2, th * 0.7), w, font=f, fill=(GOLD if acc else CREAM) + (a,), anchor="ls")
            if sc < 0.999:
                nw, nh = int(tw * sc), int(th * sc)
                tile = tile.resize((nw, nh), Image.LANCZOS)
                ox, oy = (tw - nw) / 2, (th - nh) * 0.7
            else: ox = oy = 0
            layer.alpha_composite(tile, (int(x - size / 2 + ox), int(y - th * 0.7 + dy + oy)))
        x += wd + sp

def with_shadow(layer, size):
    al = layer.split()[3]
    sh = al.filter(ImageFilter.GaussianBlur(size * 0.12)).point(lambda v: int(v * 0.75))
    glow = al.filter(ImageFilter.GaussianBlur(size * 0.75)).point(lambda v: int(min(255, v * 3.2) * 0.55))
    base = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    g = Image.new("RGBA", layer.size, (14, 9, 4, 0)); g.putalpha(glow)
    base.alpha_composite(g)
    shadow = Image.new("RGBA", layer.size, (10, 6, 2, 0)); shadow.putalpha(sh)
    base.alpha_composite(shadow, (0, int(size * 0.06)))
    base.alpha_composite(layer)
    return base

def fade_layer(layer, a):
    if a >= 0.999: return layer
    layer.putalpha(layer.split()[3].point(lambda v: int(v * a)))
    return layer

def caption_layer(t):
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for blk in cfg["captions"]:
        if not (blk["start"] <= t < blk["end"]): continue
        hook = blk.get("hook", False)
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        y = blk.get("y", 0.73) * H
        for li, line in enumerate(blk["lines"]):
            size = int(line.get("size", 112 if hook else 74) * cfg.get("type_scale", 1.0))
            render_line(lay, [(w[0], w[1], w[2]) for w in line["words"]], y, size, t,
                        sans="hook" if hook else "sansB", serif_scale=line.get("serif_scale", 1.25))
            y += size * line.get("lead", 1.12)
        a = 1 - smooth((t - blk["end"] + 0.14) / 0.14)
        out.alpha_composite(fade_layer(with_shadow(lay, 90 if hook else 70), a))
    return out

# ---------------- main ----------------
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-t", str(END), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
PAD = 140
for i in range(N):
    raw = dec.stdout.read(W * H * 3)
    if len(raw) < W * H * 3: break
    t = i / FPS
    src = Image.frombuffer("RGB", (W, H), raw)
    z = zoom_at(t); cw, ch = W / z, H / z
    img = src.transform((W, H), Image.EXTENT, ((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2), Image.BICUBIC)
    f = np.asarray(img).astype(np.float32) / 255
    b = blur_at(t)
    if b > 0.04:   # vertical whip blur, edge-padded (no wraparound)
        n = int(3 + b * 9); step = max(1, int(3 + b * 10))
        p = np.pad(f, ((n * step, n * step), (0, 0), (0, 0)), mode="edge")
        acc = np.zeros_like(f)
        for k in range(-n, n + 1):
            o = n * step + k * step; acc += p[o:o + H]
        f = acc / (2 * n + 1)
    f = grade(f)
    L = burn_frame(t)
    if L is not None: f = 1 - (1 - f) * (1 - L)
    if t < 0.09: f = f + (1 - f) * (1 - t / 0.09) ** 2 * 0.85          # shutter flash
    f = np.clip(f + GRAIN[i % 6] * 0.014, 0, 1)
    out = Image.fromarray((f * 255).astype(np.uint8)).convert("RGBA")
    out.alpha_composite(caption_layer(t))
    enc.stdin.write(out.convert("RGB").tobytes())
    if i % 48 == 0: print(f"{i}/{N}", flush=True)
enc.stdin.close(); enc.wait(); dec.terminate()
