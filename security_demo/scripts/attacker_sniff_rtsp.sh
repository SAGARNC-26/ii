#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"
OUT_DIR="${SCRIPT_DIR}/../output"
mkdir -p "$OUT_DIR"
if [ -f "$ENV_FILE" ]; then set -a; . "$ENV_FILE"; set +a; fi

IFACE="${IFACE:-eth0}"
RTSP_PORT="${RTSP_PORT:-8554}"
OUT_FILE="$OUT_DIR/sniff_rtsp.txt"

cat <<EOF
[ATTACKER] Sniffing RTSP on interface: $IFACE (tcp port $RTSP_PORT)
Saving to: $OUT_FILE
Press Ctrl+C to stop.
EOF

# Capture DESCRIBE/SETUP/PLAY RTSP methods and related fields
# Requires tshark (Wireshark CLI)
# Filter: RTSP over TCP port RTSP_PORT
exec tshark -i "$IFACE" -f "tcp port $RTSP_PORT" -Y 'rtsp || (tcp contains "DESCRIBE") || (tcp contains "SETUP") || (tcp contains "PLAY")' \
  -T fields \
  -e frame.time -e ip.src -e ip.dst -e rtsp.method -e rtsp.request -e rtsp.response -e rtsp.session \
  2>&1 | tee "$OUT_FILE"
