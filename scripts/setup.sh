#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for tool in python3 ffmpeg ffprobe; do
  command -v "$tool" >/dev/null || { echo "Missing $tool (install Python 3.12 and FFmpeg 7+)" >&2; exit 1; }
done
python3 -m venv "$ROOT/.venv"
export PIP_CACHE_DIR="$ROOT/.cache/pip"
"$ROOT/.venv/bin/python" -m pip install --disable-pip-version-check -r "$ROOT/requirements.lock"
"$ROOT/.venv/bin/python" -m pip check
"$ROOT/.venv/bin/python" - <<'PY'
import cv2, PIL, numpy, scipy, faster_whisper
import subprocess
filters = subprocess.run(['ffmpeg', '-hide_banner', '-filters'], capture_output=True, text=True, check=True).stdout
for name in ['huesaturation', 'colortemperature', 'sidechaincompress', 'loudnorm']:
    assert f' {name} ' in filters, f'Missing FFmpeg filter: {name}'
print('Python dependencies and FFmpeg filters OK')
PY
echo "Ready. Activate: source $ROOT/scripts/activate.sh"
