#!/usr/bin/env bash
# Full-quality render of every Blender set (sequential; each render uses all cores).
#   finance_shorts/tools/render_sets.sh [SET ...]      SPP=40 by default
cd "$(dirname "$0")/../.."
SETS=$(python3 -c "from finance_shorts.engine.sets_pepsi import SETS; print(' '.join(SETS))")
for s in ${@:-$SETS}; do
  t0=$(date +%s)
  if python3 -m finance_shorts.engine.set3d "$s" --spp "${SPP:-40}" --scale 100 > "/tmp/render_$s.log" 2>&1; then
    echo "$s done $(( $(date +%s) - t0 ))s"
  else
    echo "$s FAILED"
  fi
done
echo ALL_DONE
