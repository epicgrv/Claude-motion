#!/bin/bash
# After the landscape pass: re-render the hook (scene 1) with many more samples, then render the vertical master.
cd "$(dirname "$0")/.." || exit 1
PY=${PY:-/tmp/claude-0/venv_root/bpy/bin/python}
until [ "$(ls out/exr/h/*.exr 2>/dev/null | wc -l)" -ge 1213 ]; do sleep 30; done
sleep 20
echo "[chain] landscape done, hook re-render" 
for f in $(seq 40 104); do rm -f out/exr/h/f_$(printf '%04d' $f).exr; done
$PY -m the_path.render_worker --fmt h --spp 40 --scale 67 --threads 4 --frames 40-104 --outdir out/exr/h > out/logs/hook_h.log 2>&1
echo "[chain] hook h done; vertical"
tools/render_all.sh v 2 6 67
until [ "$(ls out/exr/v/*.exr 2>/dev/null | wc -l)" -ge 1213 ]; do sleep 30; done
sleep 20
for f in $(seq 40 104); do rm -f out/exr/v/f_$(printf '%04d' $f).exr; done
$PY -m the_path.render_worker --fmt v --spp 40 --scale 67 --threads 4 --frames 40-104 --outdir out/exr/v > out/logs/hook_v.log 2>&1
echo "[chain] ALL DONE"
