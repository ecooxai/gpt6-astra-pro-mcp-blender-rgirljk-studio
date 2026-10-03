#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ "${1:-}" =~ ^[0-9]+$ ]] || { echo 'Usage: src/compress.sh REVISION' >&2; exit 2; }
printf -v rev '%02d' "$1"
base=gpt6_astra_pro_mcp_blender_rgirljk
for variant in '' '_lite'; do
 input="build/${base}${variant}_r${rev}.glb"
 [[ -f "$input" ]] || continue
 npx gltf-transform meshopt "$input" "build/${base}${variant}_web_r${rev}.glb" --level high --quantize-position 16 --quantize-normal 12 --quantize-texcoord 14 --quantize-color 8
done
