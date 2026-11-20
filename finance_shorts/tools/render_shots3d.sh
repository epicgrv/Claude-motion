#!/usr/bin/env bash
# Render true-3D shots sequentially: finance_shorts/tools/render_shots3d.sh H01_hook K12_calc ...
cd "$(dirname "$0")/../.."
for s in "$@"; do
  t0=$(date +%s)
  if PYTHONPATH=. python3 -m finance_shorts.engine.shot3d "$s" > "/tmp/shot3d_$s.log" 2>&1; then
    echo "$s done $(( $(date +%s) - t0 ))s"
  else
    echo "$s FAILED"; grep -E "Error|Traceback|line [0-9]+," "/tmp/shot3d_$s.log" | tail -4
  fi
done
echo ALL_DONE
