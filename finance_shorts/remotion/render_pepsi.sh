#!/bin/bash
# full-res render in chunks (resumable): out/pepsi/chunk_XX.mp4
cd "$(dirname "$0")"; mkdir -p out/pepsi
TOTAL=$1; STEP=300; i=0
for ((a=0; a<TOTAL; a+=STEP)); do
  b=$((a+STEP-1)); [ $b -ge $TOTAL ] && b=$((TOTAL-1))
  f=$(printf "out/pepsi/chunk_%02d.mp4" $i)
  if [ ! -f "$f" ]; then PROPS='{"post":{"captions":false}}' node media.mjs src/index.tsx PepsiShort "$f.tmp.mp4" $a $b 1 2 >> out/pepsi/render.log 2>&1 && mv "$f.tmp.mp4" "$f"; fi
  echo "chunk $i $a-$b $(date +%T)" >> out/pepsi/progress.log
  i=$((i+1))
done
echo ALLDONE >> out/pepsi/progress.log
