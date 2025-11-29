#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"
if [ -f "$ENV_FILE" ]; then set -a; . "$ENV_FILE"; set +a; fi

RTSP_PROXY_PORT="${RTSP_PROXY_PORT:-8556}"

# Attempt to stop any proxy ffmpeg processes listening on RTSP_PROXY_PORT
# These commands are best-effort and may require sudo depending on your system.
if command -v pkill >/dev/null 2>&1; then
  pkill -f "ffmpeg .*rtsp://0.0.0.0:${RTSP_PROXY_PORT}/live.sdp\?listen=1" || true
fi

# Provide a quick way to restart the proxy back to the real webcam
echo "To restore real webcam on the proxy, run:"
echo "SOURCE_URL=\"rtsp://127.0.0.1:${RTSP_PORT:-8554}/live.sdp\" ./scripts/start_rtsp_proxy.sh"
