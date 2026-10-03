#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
[[ "${1:-}" =~ ^[0-9]+$ ]] || { echo 'Usage: src/compress.sh REVISION' >&2; exit 2; }
printf -v rev '%02d' "$1"
base=gpt6_astra_pro_mcp_blender_rgirljk
npx gltf-transform meshopt "build/${base}_r${rev}.glb" "build/${base}_web_r${rev}.glb" --level high --quantize-position 16 --quantize-normal 12 --quantize-texcoord 14 --quantize-color 8
