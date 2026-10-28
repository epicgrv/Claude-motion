#!/bin/bash
# Render one master. usage: tools/render_all.sh <h|v> [workers=2] [spp=6] [scale=67]
cd "$(dirname "$0")/.." || exit 1
PY=${PY:-/tmp/claude-0/venv_root/bpy/bin/python}
FMT=$1; WK=${2:-2}; SPP=${3:-6}; SCALE=${4:-67}
THR=$((4 / WK))
mkdir -p out/logs out/exr/$FMT
for ((k=0; k<WK; k++)); do
  nohup $PY -m the_path.render_worker --fmt $FMT --spp $SPP --scale $SCALE --threads $THR \
      --frames "$k-1212:$WK" --outdir out/exr/$FMT > out/logs/render_${FMT}_$k.log 2>&1 &
done
echo "launched $WK workers for $FMT (spp=$SPP scale=$SCALE)"
