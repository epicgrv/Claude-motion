#!/bin/bash
# full-res render in chunks (resumable): out/glitch/chunk_XX.mp4
cd "$(dirname "$0")"; mkdir -p out/glitch
TOTAL=$1; STEP=300; i=0
for ((a=0; a<TOTAL; a+=STEP)); do
  b=$((a+STEP-1)); [ $b -ge $TOTAL ] && b=$((TOTAL-1))
  f=$(printf "out/glitch/chunk_%02d.mp4" $i)
  if [ ! -f "$f" ]; then PROPS='{"post":{"captions":false}}' node media.mjs src/index.tsx GlitchShort "$f.tmp.mp4" $a $b 1 2 >> out/glitch/render.log 2>&1 && mv "$f.tmp.mp4" "$f"; fi
  echo "chunk $i $a-$b $(date +%T)" >> out/glitch/progress.log
  i=$((i+1))
done
echo ALLDONE >> out/glitch/progress.log
