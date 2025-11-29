#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"
if [ -f "$ENV_FILE" ]; then set -a; . "$ENV_FILE"; set +a; fi

RTSP_PROXY_PORT="${RTSP_PROXY_PORT:-8556}"
RTSP_PORT="${RTSP_PORT:-8554}"
SOURCE_URL="${SOURCE_URL:-rtsp://127.0.0.1:${RTSP_PORT}/live.sdp}"

echo "[RTSP PROXY] Listening at rtsp://0.0.0.0:${RTSP_PROXY_PORT}/live.sdp"
echo "[RTSP PROXY] Forwarding from SOURCE_URL=${SOURCE_URL}"

# Lightweight RTSP bridge: pull SOURCE_URL, restream as an RTSP server
# Switch SOURCE_URL to swap feeds without changing the dashboard camera URL
exec ffmpeg -rtsp_transport tcp -i "$SOURCE_URL" -c copy -f rtsp "rtsp://0.0.0.0:${RTSP_PROXY_PORT}/live.sdp?listen=1"
