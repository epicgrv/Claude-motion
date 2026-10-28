"""Contact sheet of images: python tools/contact.py out.png cols thumb_w img1 img2 ..."""
import sys
from pathlib import Path

from PIL import Image, ImageDraw


def sheet(out, cols, tw, paths):
    ims = []
    for p in paths:
        im = Image.open(p).convert("RGB")
        r = tw / im.width
        ims.append((Path(p).stem, im.resize((tw, int(im.height * r)), Image.LANCZOS)))
    th = max(i.height for _, i in ims)
    rows = (len(ims) + cols - 1) // cols
    S = Image.new("RGB", (cols * tw, rows * th), (20, 20, 24))
    d = ImageDraw.Draw(S)
    for k, (name, im) in enumerate(ims):
        x, y = (k % cols) * tw, (k // cols) * th
        S.paste(im, (x, y))
        d.text((x + 6, y + 4), name, fill=(255, 255, 0))
    S.save(out)


if __name__ == "__main__":
    out, cols, tw = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    sheet(out, cols, tw, sys.argv[4:])
