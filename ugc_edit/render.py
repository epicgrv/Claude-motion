"""Premium UGC edit v2. python3 render2.py in.mp4 edit.json out.mp4   (run from dir holding a/)"""
import sys, json, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

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
VIG = (1 - 0.12 * np.clip(((vx / W - .5) ** 2 * 1.3 + (vy / H - .5) ** 2) * 2.2, 0, 1) ** 1.6)[..., None].astype(np.float32)
rng = np.random.default_rng(3)
GRAIN = [np.repeat(np.repeat(rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32), 2, 0), 2, 1)[..., None] for _ in range(6)]

def grade(f):
    i = np.clip((f * 63 + 0.5).astype(np.int32), 0, 63)
    g = LUT64[i[..., 2], i[..., 1], i[..., 0]]
    f = f * (1 - MIX) + g * MIX
    f = 0.5 + (f - 0.5) * 1.02          # gentle contrast
    return np.clip(f, 0, 1) * VIG

# ---------------- captions: stacked "small / BIG KEYWORD / small" style ----------------
WHITE, GREY, LIME = (255, 255, 255), (228, 228, 222), (214, 245, 60)
FONTS = {}
def fnt(path, size):
    k = (path, size)
    if k not in FONTS: FONTS[k] = ImageFont.truetype(A + path, size)
    return FONTS[k]

def tracked_len(text, f, track):
    return sum(f.getlength(ch) for ch in text) + track * (len(text) - 1)

def draw_tracked(d, x, y, text, f, fill, track):
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill, anchor="ls"); x += f.getlength(ch) + track

def small_words(layer, words, x0, y, size, t, color, align_right_at=None):
    f = fnt("helv_bold.ttf", size); tr = -size * 0.03; sp = size * 0.28
    widths = [tracked_len(w, f, tr) for w, _ in words]
    total = sum(widths) + sp * (len(words) - 1)
    x = (align_right_at - total) if align_right_at is not None else x0
    if align_right_at is None and total > (W - 2 * x0): x = (W - total) / 2
    x = min(max(x, 70), W - 70 - total)
    d = ImageDraw.Draw(layer)
    for (w, st), wd in zip(words, widths):
        k = ease_out3((t - st) / 0.18)
        if k > 0:
            a = int(255 * clamp(k * 1.5))
            draw_tracked(d, x, y + (1 - k) * size * 0.4, w, f, color + (a,), tr)
        x += wd + sp

def caption_layer(t):
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for blk in cfg["captions"]:
        if not (blk["start"] <= t < blk["end"]): continue
        key, kst = blk["key"]
        kfont_path = "helv_boldobl.ttf" if blk.get("italic") else "helv_bold.ttf"
        S = blk.get("size", 190)
        f = fnt(kfont_path, S); tr = -S * 0.045
        kw = tracked_len(key, f, tr)
        if kw > 930: S = int(S * 930 / kw); f = fnt(kfont_path, S); tr = -S * 0.045; kw = tracked_len(key, f, tr)
        x0 = (W - kw) / 2; y = blk["y"] * H
        cap = f.getbbox("H", anchor="ls")[1]          # negative: cap height above baseline
        ss = blk.get("small", 68)
        txt = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if blk.get("top"):
            small_words(txt, blk["top"], x0 + S * 0.06, y + cap - S * 0.07, ss, t, WHITE)
        if blk.get("bottom"):
            small_words(txt, blk["bottom"], 0, y + ss * 1.25, ss, t, GREY, align_right_at=x0 + kw - S * 0.03)
        # keyword: scale-pop in
        k = ease_out5((t - kst) / 0.28)
        keyl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if k > 0:
            tile = Image.new("RGBA", (int(kw + S), int(S * 1.6)), (0, 0, 0, 0))
            draw_tracked(ImageDraw.Draw(tile), S / 2, S * 1.15, key, f, LIME + (int(255 * clamp(k * 1.4)),), tr)
            sc = 1.18 - 0.18 * k
            tw, th = tile.size
            if abs(sc - 1) > 0.002:
                tile = tile.resize((int(tw * sc), int(th * sc)), Image.LANCZOS)
            keyl.alpha_composite(tile, (int(x0 - S / 2 * sc - (tw * sc - tw) / 2 + (S / 2) * (sc - 1)), int(y - S * 1.15 * sc)))
        # lime glow on keyword
        ka = keyl.split()[3]
        glow = Image.new("RGBA", (W, H), LIME + (0,)); glow.putalpha(ka.filter(ImageFilter.GaussianBlur(S * 0.16)).point(lambda v: int(v * 0.55)))
        allA = ImageChops.lighter(ka, txt.split()[3])
        dark = Image.new("RGBA", (W, H), (8, 8, 6, 0))
        dark.putalpha(ImageChops.lighter(
            allA.filter(ImageFilter.GaussianBlur(S * 0.36)).point(lambda v: int(min(255, v * 2.8) * 0.55)),
            allA.filter(ImageFilter.GaussianBlur(S * 0.09)).point(lambda v: int(min(255, v * 2.0) * 0.6))))
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sh.putalpha(allA.filter(ImageFilter.GaussianBlur(4)).point(lambda v: int(v * 0.5)))
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for L_ in (dark, glow): lay.alpha_composite(L_)
        lay.alpha_composite(sh, (0, 4))
        lay.alpha_composite(keyl); lay.alpha_composite(txt)
        fa = 1 - smooth((t - blk["end"] + 0.14) / 0.14)
        out.alpha_composite(fade_layer(lay, fa))
    return out

def fade_layer(layer, a):
    if a >= 0.999: return layer
    layer.putalpha(layer.split()[3].point(lambda v: int(v * a)))
    return layer

# ---------------- main ----------------
dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", SRC, "-t", str(END), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
PAD = 140
BBOX = open("caption_bbox.txt", "w")
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
    f = np.clip(f + GRAIN[i % 6] * 0.010, 0, 1)
    out = Image.fromarray((f * 255).astype(np.uint8)).convert("RGBA")
    cl = caption_layer(t)
    bb = cl.split()[3].point(lambda v: 255 if v > 40 else 0).getbbox()
    BBOX.write(f"{t:.3f} {bb[1] / H if bb else -1:.3f} {bb[3] / H if bb else -1:.3f}\n")
    out.alpha_composite(cl)
    enc.stdin.write(out.convert("RGB").tobytes())
    if i % 48 == 0: print(f"{i}/{N}", flush=True)
enc.stdin.close(); enc.wait(); dec.terminate()
