#!/bin/bash
# Let the vertical pass reach frame ~640 with the OLD scene, then restart it with the corrected hand-off scene.
cd "$(dirname "$0")/.." || exit 1
PY=/tmp/claude-0/venv_root/bpy/bin/python
until [ "$(ls out/exr/v/*.exr | wc -l)" -ge 636 ]; do sleep 20; done
pkill -f "render_worker --fmt v"
sleep 5
for f in $(seq 636 1212); do rm -f out/exr/v/f_$(printf '%04d' $f).exr; done
echo "[watch] vertical restarted at $(ls out/exr/v | wc -l) frames"
tools/render_all.sh v 2 6 67
until [ "$(ls out/exr/v/*.exr | wc -l)" -ge 1213 ]; do sleep 30; done
sleep 25
for f in $(seq 40 104); do rm -f out/exr/v/f_$(printf '%04d' $f).exr; done
$PY -m the_path.render_worker --fmt v --spp 40 --scale 67 --threads 4 --frames 40-104 --outdir out/exr/v > out/logs/hook_v.log 2>&1
echo "[watch] ALL DONE"
