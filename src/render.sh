#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
exec /home/dev/.local/opt/blender-4.2.3-linux-x64/blender -b -t 8 --factory-startup --python src/build_character.py -- "$@"
