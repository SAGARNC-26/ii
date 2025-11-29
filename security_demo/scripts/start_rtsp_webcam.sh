#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"
if [ -f "$ENV_FILE" ]; then set -a; . "$ENV_FILE"; set +a; fi

RTSP_PORT="${RTSP_PORT:-8554}"
CAMERA_DEVICE="${CAMERA_DEVICE:-/dev/video0}"

# Vulnerable mode: plain RTSP from local webcam
# Implementation requirement (Linux): v4l2 device
exec ffmpeg -f v4l2 -i "$CAMERA_DEVICE" -c copy -f rtsp "rtsp://0.0.0.0:${RTSP_PORT}/live.sdp?listen=1"
