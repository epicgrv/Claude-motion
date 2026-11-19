"""Render helper: python -m finance_shorts.tools_render <out.mp4> [t0 t1 | seg0a-seg0b,seg1a-seg1b,...]"""
import subprocess, sys
from pathlib import Path
from finance_shorts.engine.comp import render
TL = Path("finance_shorts/audio/pepsi-jet/timeline.json")
VO = Path("finance_shorts/audio/pepsi-jet/vo.wav")


def main():
    out = Path(sys.argv[1])
    if len(sys.argv) == 3:
        segs = [tuple(map(float, s.split("-"))) for s in sys.argv[2].split(",")]
    else:
        segs = [(float(sys.argv[2]), float(sys.argv[3]))]
    silent = out.with_name(out.stem + "_v.mp4")
    render("finance_shorts.visuals.pepsi_jet_shots", silent, TL, VO, 0, 0, segments=segs)
    audio = Path(sys.argv[4]) if len(sys.argv) > 4 else VO
    fl = "".join(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS[a{i}];" for i, (a, b) in enumerate(segs))
    fl += "".join(f"[a{i}]" for i in range(len(segs))) + f"concat=n={len(segs)}:v=0:a=1[a]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(audio), "-i", str(silent), "-filter_complex", fl,
                    "-map", "1:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)],
                   check=True)
    print(out)


if __name__ == "__main__":
    main()
