# Attack Flow (Unencrypted RTSP)

This walkthrough demonstrates sniffing and injecting a fake video on an unencrypted RTSP feed using two laptops.

- Laptop 1 (Server): hosts webcam→RTSP and the dashboard
- Laptop 2 (Attacker): sniffs RTSP and publishes a fake stream

## Steps
1. On Server (Laptop 1): start vulnerable RTSP webcam
   - Linux/macOS: `./scripts/start_rtsp_webcam.sh`
   - Windows: `./scripts/start_rtsp_webcam.ps1`

2. On Server: start the RTSP Proxy and point it to the real webcam source
   - Linux/macOS: `SOURCE_URL="rtsp://127.0.0.1:${RTSP_PORT}/live.sdp" ./scripts/start_rtsp_proxy.sh`
   - Windows: `$env:SOURCE_URL = "rtsp://127.0.0.1:$env:RTSP_PORT/live.sdp"; ./scripts/start_rtsp_proxy.ps1`

3. Configure the dashboard camera to `rtsp://SERVER_IP:${RTSP_PROXY_PORT}/live.sdp` (environment or config; no code change).

4. On Attacker (Laptop 2): sniff RTSP
   - Linux/macOS: `./scripts/attacker_sniff_rtsp.sh`
   - Windows: `./scripts/attacker_sniff_rtsp.ps1`
   - Observe RTSP DESCRIBE/SETUP/PLAY and URLs in `output/sniff_rtsp.txt`.

5. On Attacker: inject fake video
   - Linux/macOS: `./scripts/attacker_inject_video.sh`
   - Windows: `./scripts/attacker_inject_video.ps1`
   - This sends `fake_injection.mp4` to `rtsp://SERVER_IP:${RTSP_PORT}/live.sdp`.

6. On Server: switch the RTSP Proxy upstream to the attacker’s stream
   - Linux/macOS: `SOURCE_URL="rtsp://${SERVER_IP}:${RTSP_PORT}/live.sdp" ./scripts/start_rtsp_proxy.sh`
   - Windows: `$env:SOURCE_URL = "rtsp://$env:SERVER_IP:$env:RTSP_PORT/live.sdp"; ./scripts/start_rtsp_proxy.ps1`

7. Result: the dashboard now displays the FAKE VIDEO — without any dashboard code change.

8. Take screenshots of sniffed RTSP methods and the dashboard showing the fake video.
