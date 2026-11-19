#!/usr/bin/env bash
# Download the reference short (shared by the channel owner on Google Drive) to $1 (default: ./reference/ref.mp4).
set -euo pipefail
out="${1:-$(dirname "$0")/../reference/ref.mp4}"
mkdir -p "$(dirname "$out")"
curl -sSL -o "$out" "https://drive.usercontent.google.com/download?id=1zn4MvoxEaWMsqVwlVIrJsM36DIegEnkP&export=download&confirm=t"
ffprobe -v error -show_entries format=duration:stream=width,height -of default=nw=1 "$out"
