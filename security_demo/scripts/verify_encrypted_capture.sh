#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"
OUT_DIR="${SCRIPT_DIR}/../output"
mkdir -p "$OUT_DIR"
if [ -f "$ENV_FILE" ]; then set -a; . "$ENV_FILE"; set +a; fi

IFACE="${IFACE:-eth0}"
SRT_PORT="${SRT_PORT:-9000}"
RTSPS_PORT="${RTSPS_PORT:-8555}"

# Capture short samples
SRT_PCAP="$OUT_DIR/srt_capture.pcapng"
RTSPS_PCAP="$OUT_DIR/rtsps_capture.pcapng"

if command -v tshark >/dev/null 2>&1; then
  echo "[VERIFY] Capturing SRT (udp port $SRT_PORT) -> $SRT_PCAP"
  tshark -i "$IFACE" -a duration:5 -f "udp port $SRT_PORT" -w "$SRT_PCAP" || true

  echo "[VERIFY] Capturing RTSPS (tcp port $RTSPS_PORT) -> $RTSPS_PCAP"
  tshark -i "$IFACE" -a duration:5 -f "tcp port $RTSPS_PORT" -w "$RTSPS_PCAP" || true

  echo "[VERIFY] Checking if RTSP methods are visible in RTSPS capture (should be 0)"
  COUNT=$(tshark -r "$RTSPS_PCAP" -Y 'rtsp' 2>/dev/null | wc -l | tr -d ' ')
  if [ "${COUNT}" = "0" ]; then
    echo "[OK] Encrypted: RTSP methods are not visible over RTSPS"
  else
    echo "[WARN] RTSP methods detected (encryption not applied?)"
  fi
else
  echo "tshark not found. Please install Wireshark/tshark to perform verification."
fi
