# Security Demo: RTSP Attack → Defense (Two-Laptop Scenario)

This module demonstrates how an attacker can sniff and inject a fake video into an unencrypted RTSP feed, and how switching to encrypted transports (SRT or RTSPS) defeats the attack — without modifying any dashboard or face recognition code.

- Laptop 1 = CCTV Server (runs webcam → RTSP and hosts the dashboard)
- Laptop 2 = Attacker (sniffs RTSP, views live feed, injects prerecorded fake video)

All demo files live ONLY inside `security_demo/`.

## Prerequisites
- ffmpeg (both laptops)
- tshark/Wireshark (attacker laptop, optional on server for verification)
- stunnel (server laptop, for RTSPS TLS termination)
- OpenSSL (server laptop, to generate self-signed TLS cert)
- Local network connectivity between laptops

Optional but recommended:
- Set your dashboard camera source to the RTSP proxy URL (explained below) via environment/config, not code.

## Quick Setup
1) Copy env template and edit values

```bash
cd security_demo
cp .env.example .env
# Edit .env: set SERVER_IP (server laptop IP), ports, camera device, etc.
```

2) Create placeholders (already provided):
- `video/test_source.mp4` (placeholder)
- `video/fake_injection.mp4` (placeholder)

Replace them with your own short MP4s for a realistic demo.

---

# Part A: Vulnerable Mode (Plain RTSP)

Server (Laptop 1): start webcam as RTSP server

- Linux/macOS
```bash
./scripts/start_rtsp_webcam.sh
```
- Windows PowerShell
```powershell
./scripts/start_rtsp_webcam.ps1
```
By default, this exposes an RTSP server: `rtsp://0.0.0.0:${RTSP_PORT}/live.sdp`.

Start a lightweight RTSP Proxy on the server (bridge the source to the dashboard):

- Linux/macOS
```bash
# Initially point proxy SOURCE_URL to your real webcam RTSP
SOURCE_URL="rtsp://127.0.0.1:${RTSP_PORT}/live.sdp" ./scripts/start_rtsp_proxy.sh
```
- Windows PowerShell
```powershell
$env:SOURCE_URL = "rtsp://127.0.0.1:$env:RTSP_PORT/live.sdp"
./scripts/start_rtsp_proxy.ps1
```
The proxy listens at: `rtsp://0.0.0.0:${RTSP_PROXY_PORT}/live.sdp`.

Configure your dashboard to read from the proxy URL (no code change):
- Set the camera source to `rtsp://SERVER_IP:${RTSP_PROXY_PORT}/live.sdp` using environment or config.

Attacker (Laptop 2): sniff RTSP methods and URLs

- Linux/macOS
```bash
./scripts/attacker_sniff_rtsp.sh
```
- Windows PowerShell
```powershell
./scripts/attacker_sniff_rtsp.ps1
```
Output is saved to `security_demo/output/sniff_rtsp.txt`.

Attacker (Laptop 2): inject fake video into server’s RTSP

- Linux/macOS
```bash
./scripts/attacker_inject_video.sh
```
- Windows PowerShell
```powershell
./scripts/attacker_inject_video.ps1
```
This publishes `video/fake_injection.mp4` to the server’s RTSP endpoint.

Server (Laptop 1): switch proxy SOURCE_URL to the attacker’s fake stream

- Linux/macOS
```bash
# Stop old proxy (Ctrl+C if running in foreground), then:
SOURCE_URL="rtsp://${SERVER_IP}:${RTSP_PORT}/live.sdp" ./scripts/start_rtsp_proxy.sh
```
- Windows PowerShell
```powershell
# Close previous proxy window, then:
$env:SOURCE_URL = "rtsp://$env:SERVER_IP:$env:RTSP_PORT/live.sdp"
./scripts/start_rtsp_proxy.ps1
```
Now the dashboard (still pointed at the proxy URL) shows the FAKE VIDEO. No dashboard code changed.

---

# Part B: Defense — Encrypt the Stream

## Option 1: SRT with passphrase
Server (Laptop 1)

- Linux/macOS
```bash
./scripts/start_srt_secure.sh
```
- Windows PowerShell
```powershell
./scripts/start_srt_secure.ps1
```
This serves encrypted SRT at: `srt://0.0.0.0:${SRT_PORT}?listen=1&passphrase=${SRT_PASS}`

Update your dashboard camera source to the SRT URL (supported by your pipeline/player; if your current stack lacks SRT support, use an SRT → RTSP converter on the server side for demo purposes).

## Option 2: RTSPS (TLS)
Server (Laptop 1)

```bash
./scripts/generate_tls_cert.sh
# Ensure plain RTSP is running on ${RTSP_PORT}
./scripts/start_rtsps_secure.sh
```
This terminates TLS (RTSPS) on `${RTSPS_PORT}` and forwards to the plain RTSP on `${RTSP_PORT}`. Update the dashboard source to `rtsps://SERVER_IP:${RTSPS_PORT}/live.sdp`.

Attacker (Laptop 2) tries sniffing again

- Linux/macOS
```bash
./scripts/verify_encrypted_capture.sh
```
If configured correctly, packets are captured but are unreadable; RTSP methods cannot be parsed.

---

# How it Works (No Dashboard Code Changes)
- The dashboard always reads from the RTSP Proxy URL.
- The proxy’s upstream `SOURCE_URL` is switched between the real webcam and the attacker’s fake video.
- For the secure mode, the dashboard reads an encrypted transport (SRT/RTSPS). The attacker cannot parse or inject traffic.

See docs for detailed walkthrough:
- `docs/attack_flow.md`
- `docs/defense_flow.md`
- `docs/how_to_show_fake_video_on_dashboard.md`
- `docs/wireshark_filters.txt`

## Notes
- Scripts are safe: no ARP spoofing, no network MITM; purely RTSP restream and TLS/SRT.
- Dependencies: ffmpeg, tshark, stunnel, openssl — install from your OS package manager.
- This demo lives entirely inside `security_demo/` and does not modify the main application code.
