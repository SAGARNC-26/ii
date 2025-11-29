#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"
if [ -f "$ENV_FILE" ]; then set -a; . "$ENV_FILE"; set +a; fi

CAMERA_DEVICE="${CAMERA_DEVICE:-/dev/video0}"
SRT_PORT="${SRT_PORT:-9000}"
SRT_PASS="${SRT_PASS:-secretkey}"

echo "[SRT] Serving encrypted SRT at srt://0.0.0.0:${SRT_PORT}?listen=1&passphrase=***"
exec ffmpeg -f v4l2 -i "$CAMERA_DEVICE" -c copy -f mpegts "srt://0.0.0.0:${SRT_PORT}?listen=1&passphrase=${SRT_PASS}"
