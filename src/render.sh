#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
B="${BLENDER_BIN:-/home/dev/.local/opt/blender-4.2.3-linux-x64/blender}"
if [[ ! -x "$B" ]]; then B="$(command -v blender || true)"; fi
if [[ -z "$B" ]]; then echo 'Set BLENDER_BIN to a working Blender 4.2+ executable.' >&2; exit 1; fi
exec "$B" -b -t "${BLENDER_THREADS:-8}" --factory-startup --python src/build_character.py -- "$@"
