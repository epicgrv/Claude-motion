"""Split a flat plate into background + foreground layers for parallax, using Depth Anything V2 (ONNX).

    python -m finance_shorts.engine.depth_layers P03_bedroom 0.62
writes plates/<name>_bg.png (foreground removed, holes inpainted), plates/<name>_fg.png (RGBA), plates/<name>_depth.png
The threshold is on normalised inverse depth (1 = nearest)."""
from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort
from huggingface_hub import hf_hub_download

PLATES = Path(__file__).resolve().parents[1] / "visuals" / "pepsi-jet" / "plates"


def depth(img_rgb: np.ndarray) -> np.ndarray:
    model = hf_hub_download("onnx-community/depth-anything-v2-small", "onnx/model.onnx")
    sess = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
    h, w = 924, 518
    x = cv2.resize(img_rgb, (w, h), interpolation=cv2.INTER_CUBIC).astype(np.float32) / 255.0
    x = (x - np.array([0.485, 0.456, 0.406], np.float32)) / np.array([0.229, 0.224, 0.225], np.float32)
    x = x.transpose(2, 0, 1)[None]
    name = sess.get_inputs()[0].name
    d = sess.run(None, {name: x})[0].squeeze()
    d = cv2.resize(d, (img_rgb.shape[1], img_rgb.shape[0]), interpolation=cv2.INTER_CUBIC)
    d = (d - d.min()) / (d.max() - d.min() + 1e-9)
    return d


def split(name: str, thresh: float, feather=5, grow=18):
    src = cv2.cvtColor(cv2.imread(str(PLATES / f"{name}.png")), cv2.COLOR_BGR2RGB)
    d = depth(src)
    cv2.imwrite(str(PLATES / f"{name}_depth.png"), (d * 255).astype(np.uint8))
    m = (d > thresh).astype(np.uint8)
    k = np.ones((9, 9), np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
    alpha = cv2.GaussianBlur(m.astype(np.float32), (0, 0), feather)
    fg = np.dstack([src, (np.clip(alpha * 1.4, 0, 1) * 255).astype(np.uint8)])
    cv2.imwrite(str(PLATES / f"{name}_fg.png"), cv2.cvtColor(fg, cv2.COLOR_RGBA2BGRA))
    # background: remove the (grown) foreground and inpaint at quarter res, then blend in at full res
    hole = cv2.dilate(m, np.ones((grow, grow), np.uint8))
    sm = cv2.resize(src, (src.shape[1] // 4, src.shape[0] // 4), interpolation=cv2.INTER_AREA)
    hs = cv2.resize(hole, (sm.shape[1], sm.shape[0]), interpolation=cv2.INTER_NEAREST)
    filled = cv2.inpaint(cv2.cvtColor(sm, cv2.COLOR_RGB2BGR), hs * 255, 9, cv2.INPAINT_TELEA)
    filled = cv2.cvtColor(cv2.resize(filled, (src.shape[1], src.shape[0]), interpolation=cv2.INTER_CUBIC), cv2.COLOR_BGR2RGB)
    filled = cv2.GaussianBlur(filled, (0, 0), 2.0)
    hb = cv2.GaussianBlur(hole.astype(np.float32), (0, 0), 6)[..., None]
    bg = (src * (1 - hb) + filled * hb).astype(np.uint8)
    cv2.imwrite(str(PLATES / f"{name}_bg.png"), cv2.cvtColor(bg, cv2.COLOR_RGB2BGR))
    print(name, "fg coverage", round(float(m.mean()), 3))


if __name__ == "__main__":
    split(sys.argv[1], float(sys.argv[2]))
