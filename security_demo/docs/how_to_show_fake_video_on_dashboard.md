# How the Dashboard Shows a Fake Video Without Code Changes

The dashboard reads a single RTSP URL. We keep that URL constant by introducing a lightweight RTSP proxy that restreams an upstream source:

```
Dashboard -> rtsp://SERVER_IP:${RTSP_PROXY_PORT}/live.sdp
                        ^
                        |
                RTSP Proxy (ffmpeg)
                        |
               SOURCE_URL (switch)
                    ├─ Real webcam:  rtsp://127.0.0.1:${RTSP_PORT}/live.sdp
                    └─ Attacker fake: rtsp://${SERVER_IP}:${RTSP_PORT}/live.sdp
```

- Initially, the proxy’s `SOURCE_URL` points to the real webcam RTSP.
- During the attack, we restart the proxy with `SOURCE_URL` pointing to the attacker’s fake feed.
- The dashboard URL never changes, so no code change is needed. Only the proxy upstream changes.

To restore, switch `SOURCE_URL` back to the real webcam RTSP and restart the proxy.
