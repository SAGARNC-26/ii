#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"
OUT_DIR="${SCRIPT_DIR}/../output"
mkdir -p "$OUT_DIR"
if [ -f "$ENV_FILE" ]; then set -a; . "$ENV_FILE"; set +a; fi

RTSP_PORT="${RTSP_PORT:-8554}"
RTSPS_PORT="${RTSPS_PORT:-8555}"
PEM_FILE="$OUT_DIR/rtsps.pem"
CONF_FILE="$OUT_DIR/stunnel_rtsps.conf"

if ! command -v stunnel >/dev/null 2>&1; then
  echo "stunnel not found. Install it (e.g., apt install stunnel4)."
  exit 1
fi

if [ ! -f "$PEM_FILE" ]; then
  echo "TLS PEM not found: $PEM_FILE"
  echo "Run ./scripts/generate_tls_cert.sh first."
  exit 1
fi

cat > "$CONF_FILE" <<EOF
foreground = yes
pid =
cert = $PEM_FILE

[rtsp-tls]
accept = $RTSPS_PORT
connect = 127.0.0.1:$RTSP_PORT
EOF

echo "[RTSPS] Terminating TLS on :$RTSPS_PORT and forwarding to RTSP :$RTSP_PORT"
exec stunnel "$CONF_FILE"
