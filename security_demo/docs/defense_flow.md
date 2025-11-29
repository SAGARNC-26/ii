# Defense Flow (Encrypted Streaming)

This walkthrough shows how encryption prevents sniffing and injection.

## Option A: SRT (with passphrase)
1. On Server: start encrypted SRT from the webcam
   - Linux/macOS: `./scripts/start_srt_secure.sh`
   - Windows: `./scripts/start_srt_secure.ps1`
2. Update dashboard camera source to `srt://SERVER_IP:${SRT_PORT}` (with `?passphrase=${SRT_PASS}` when required by player).
3. On Attacker: `./scripts/verify_encrypted_capture.sh`
   - Captures SRT traffic — raw packets are unreadable payloads.
   - No RTSP methods are visible.

## Option B: RTSPS (TLS termination)
1. On Server: generate self-signed cert
   - `./scripts/generate_tls_cert.sh`
2. Ensure plain RTSP webcam is running on `${RTSP_PORT}`.
3. Start TLS terminator on `${RTSPS_PORT}`
   - `./scripts/start_rtsps_secure.sh`
4. Update dashboard camera source to `rtsps://SERVER_IP:${RTSPS_PORT}/live.sdp`.
5. On Attacker: `./scripts/verify_encrypted_capture.sh`
   - Capture on `${RTSPS_PORT}` — RTSP methods should not be parseable.

## Expected Outcome
- Sniffing DESCRIBE/SETUP/PLAY fails in encrypted modes.
- Injection fails because attacker cannot synthesize or tamper with the encrypted stream.
- Dashboard shows the real feed; proxy switching is no longer used or points to a secure upstream.
