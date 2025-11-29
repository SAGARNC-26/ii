#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/../.env"
OUT_DIR="${SCRIPT_DIR}/../output"
mkdir -p "$OUT_DIR"
if [ -f "$ENV_FILE" ]; then set -a; . "$ENV_FILE"; set +a; fi

TLS_CN="${TLS_CN:-localhost}"

# Generate self-signed TLS cert (server usage)
openssl req -x509 -nodes -newkey rsa:2048 \
  -keyout "$OUT_DIR/rtsps.key" \
  -out "$OUT_DIR/rtsps.crt" \
  -days 365 \
  -subj "/CN=${TLS_CN}"

# stunnel expects a single PEM sometimes; provide combined file
cat "$OUT_DIR/rtsps.crt" "$OUT_DIR/rtsps.key" > "$OUT_DIR/rtsps.pem"
echo "Generated: $OUT_DIR/rtsps.crt, $OUT_DIR/rtsps.key, $OUT_DIR/rtsps.pem"
