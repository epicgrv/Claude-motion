#!/bin/bash
# Preview frames through the real finishing pipeline.
# usage: tools/pv.sh <h|v> <scene_modules,comma|all> <frames> [scale=50] [spp=10] [outname]
cd "$(dirname "$0")/.." || exit 1
PY=${PY:-/tmp/claude-0/venv_root/bpy/bin/python}
FMT=$1; SC=$2; FR=$3; SCALE=${4:-50}; SPP=${5:-10}; NAME=${6:-pv}
ARGS=(--fmt "$FMT" --preview --scale "$SCALE" --spp "$SPP" --frames "$FR" --outdir "out/preview/$NAME")
[ "$SC" != "all" ] && ARGS+=(--scenes "$SC")
$PY -m the_path.render_worker "${ARGS[@]}" 2>&1 | grep -v -E 'CUEW|Deprecat|use_nodes|Topology differs|Saved:' | tail -${TAILN:-6}
# contact sheet of everything just rendered, in frame order
IFS=',' read -ra F <<< "$FR"
FILES=()
for f in "${F[@]}"; do FILES+=("out/preview/$NAME/p_$(printf '%04d' $f).png"); done
$PY tools/contact.py "out/preview/$NAME/sheet.png" ${COLS:-4} ${TW:-480} "${FILES[@]}"
echo "sheet: out/preview/$NAME/sheet.png"
