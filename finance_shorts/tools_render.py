"""Render helper: python -m finance_shorts.tools_render <out.mp4> [t0 t1 | seg0a-seg0b,seg1a-seg1b,...]"""
import subprocess, sys
from pathlib import Path
from finance_shorts.engine.comp import render
TL = Path("finance_shorts/audio/pepsi-jet/timeline.json")
VO = Path("finance_shorts/audio/pepsi-jet/vo.wav")


def main():
    out = Path(sys.argv[1])
    if "-" in sys.argv[2] or "," in sys.argv[2]:
        segs = [tuple(map(float, s.split("-"))) for s in sys.argv[2].split(",")]
        rest = sys.argv[3:]
    else:
        segs = [(float(sys.argv[2]), float(sys.argv[3]))]
        rest = sys.argv[4:]
    silent = out.with_name(out.stem + "_v.mp4")
    render("finance_shorts.visuals.pepsi_jet_shots", silent, TL, VO, 0, 0, segments=segs)
    audio = Path(rest[0]) if rest else VO
    fl = "".join(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={b - a - 0.03:.3f}:d=0.03[a{i}];"
                 for i, (a, b) in enumerate(segs))
    fl += "".join(f"[a{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=0:a=1[a]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(audio), "-i", str(silent), "-filter_complex", fl,
                    "-map", "1:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)],
                   check=True)
    print(out)


if __name__ == "__main__":
    main()
