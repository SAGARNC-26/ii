# Video Stream Encryption Guide

Comprehensive guide to securing camera streams using RTSP over TLS and SRT (Secure Reliable Transport).

## Overview

Encrypting video streams protects against:
- Eavesdropping and surveillance
- Man-in-the-middle attacks
- Unauthorized access to camera feeds
- Stream tampering

## Option 1: RTSP over TLS (RTSPS)

RTSP over TLS encrypts the RTSP stream using SSL/TLS, similar to HTTPS.

### Camera Configuration

Most modern IP cameras support RTSPS. Check your camera documentation.

#### Enabling RTSPS on Camera

1. **Access camera web interface**
2. **Navigate to Network/Security settings**
3. **Enable RTSP over TLS/SSL**
4. **Configure certificate** (use camera's self-signed or upload CA cert)
5. **Set RTSPS port** (usually 322 or 8555)

#### Example URLs

```bash
# Standard RTSP (unencrypted)
rtsp://admin:password@192.168.1.100:554/stream

# RTSPS (encrypted)
rtsps://admin:password@192.168.1.100:322/stream
```

### Client Configuration (Python/OpenCV)

Modify `src/config.py`:

```python
# Use RTSPS URL
CAMERA_SOURCE = "rtsps://admin:password@192.168.1.100:322/stream"
```

For self-signed certificates, you may need to disable verification:

```python
import cv2
import os

# Disable SSL verification (for testing only!)
os.environ['OPENCV_FFMPEG_CAPTURE_OPTIONS'] = 'rtsp_transport;tcp|ssl_verify;0'
cap = cv2.VideoCapture(CAMERA_SOURCE)
```

### VLC Player Test

```bash
# Test RTSPS stream
vlc rtsps://admin:password@192.168.1.100:322/stream
```

## Option 2: SRT (Secure Reliable Transport)

SRT provides encryption, low latency, and packet loss recovery. Ideal for unreliable networks.

### Installing FFmpeg with SRT Support

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y ffmpeg

# Verify SRT support
ffmpeg -protocols | grep srt
```

If SRT is not supported, compile FFmpeg with SRT:

```bash
# Install dependencies
sudo apt-get install -y build-essential cmake libssl-dev

# Build libsrt
git clone https://github.com/Haivision/srt.git
cd srt
./configure
make
sudo make install

# Build FFmpeg with SRT
git clone https://git.ffmpeg.org/ffmpeg.git
cd ffmpeg
./configure --enable-libsrt --enable-openssl
make -j$(nproc)
sudo make install
```

### Creating Encrypted SRT Stream

#### From IP Camera (RTSP to SRT)

```bash
# Convert RTSP to encrypted SRT
ffmpeg -i rtsp://admin:password@192.168.1.100:554/stream \
       -c copy \
       -f mpegts \
       "srt://0.0.0.0:9000?mode=listener&pkt_size=1316&passphrase=YourSecretKey123&pbkeylen=32"
```

**Parameters:**
- `mode=listener`: Act as SRT server (camera side)
- `pkt_size=1316`: Packet size for network
- `passphrase`: Encryption key (16-32 chars)
- `pbkeylen`: Key length (16, 24, or 32 for AES-128, 192, 256)

#### From File (Testing)

```bash
# Stream a video file via SRT
ffmpeg -re -i test_video.mp4 \
       -c copy \
       -f mpegts \
       "srt://0.0.0.0:9000?mode=listener&passphrase=YourSecretKey123"
```

### Consuming SRT Stream

#### Using FFmpeg

```bash
# Receive and view SRT stream
ffplay "srt://192.168.1.100:9000?mode=caller&passphrase=YourSecretKey123&pbkeylen=32"
```

#### Using Python/OpenCV

Modify `src/config.py`:

```python
# SRT stream URL
CAMERA_SOURCE = "srt://192.168.1.100:9000?mode=caller&passphrase=YourSecretKey123&pbkeylen=32"
```

OpenCV with FFmpeg backend should handle SRT automatically.

#### Using VLC

```bash
vlc "srt://192.168.1.100:9000?mode=caller&passphrase=YourSecretKey123"
```

### SRT Configuration Options

```bash
# Full SRT URL with options
srt://host:port?option1=value1&option2=value2

# Common options:
# - mode: caller (client) or listener (server)
# - passphrase: Encryption password
# - pbkeylen: 16, 24, or 32 (AES-128, 192, 256)
# - latency: Target latency in milliseconds (default: 120)
# - maxbw: Maximum bandwidth in bytes/sec
# - lossmaxttl: Maximum TTL for lost packets
# - connect_timeout: Connection timeout in milliseconds
```

## Option 3: VPN Tunnel

For maximum security, stream over VPN (WireGuard or OpenVPN).

### WireGuard Setup

#### Server (where AI server runs)

```bash
# Install WireGuard
sudo apt-get install -y wireguard

# Generate keys
wg genkey | tee server_private.key | wg pubkey > server_public.key
wg genkey | tee client_private.key | wg pubkey > client_public.key

# Configure server
sudo nano /etc/wireguard/wg0.conf
```

```ini
[Interface]
PrivateKey = <server_private_key>
Address = 10.0.0.1/24
ListenPort = 51820

[Peer]
PublicKey = <client_public_key>
AllowedIPs = 10.0.0.2/32
```

```bash
# Start WireGuard
sudo wg-quick up wg0
sudo systemctl enable wg-quick@wg0
```

#### Client (camera network)

```ini
[Interface]
PrivateKey = <client_private_key>
Address = 10.0.0.2/24

[Peer]
PublicKey = <server_public_key>
Endpoint = <server_public_ip>:51820
AllowedIPs = 10.0.0.0/24
PersistentKeepalive = 25
```

#### Connect

```bash
# Client connects
sudo wg-quick up wg0

# Now access camera via VPN IP
# rtsp://10.0.0.2:554/stream (encrypted via VPN tunnel)
```

## Testing Encryption

### Wireshark Packet Capture

Verify streams are encrypted:

```bash
# Install Wireshark
sudo apt-get install -y wireshark

# Capture on interface
sudo tcpdump -i eth0 -w capture.pcap port 554 or port 9000

# Open in Wireshark
wireshark capture.pcap
```

**What to look for:**
- **RTSP (unencrypted)**: You'll see clear text (username, video frames)
- **RTSPS**: Encrypted TLS handshake, no clear content
- **SRT**: Encrypted UDP packets, no readable content

### SRT Statistics

Monitor SRT connection quality:

```bash
# During streaming
ffmpeg -i "srt://..." -f null - -stats
```

Check for:
- Packet loss
- Latency
- Retransmissions
- Bandwidth usage

## Performance Comparison

| Method | Encryption | Latency | CPU Overhead | Packet Loss Recovery |
|--------|-----------|---------|--------------|---------------------|
| RTSP | ❌ None | Low | Minimal | ❌ No |
| RTSPS | ✅ TLS | Low | Low | ❌ No |
| SRT | ✅ AES | Very Low | Medium | ✅ Yes |
| VPN (WireGuard) | ✅ ChaCha20 | Low | Low | ❌ No |

## Production Deployment

### Best Practices

1. **Use Strong Passphrases**
   ```bash
   # Generate random passphrase
   openssl rand -base64 32
   ```

2. **Rotate Keys Regularly**
   - Change SRT passphrases monthly
   - Update TLS certificates before expiry

3. **Monitor Stream Health**
   ```python
   # Check if stream is accessible
   import cv2
   cap = cv2.VideoCapture(CAMERA_SOURCE)
   if not cap.isOpened():
       # Send alert
       pass
   ```

4. **Use Dedicated Network**
   - Separate VLAN for cameras
   - Firewall rules to restrict access
   - No internet access for camera network

5. **Certificate Management (RTSPS)**
   ```bash
   # Generate self-signed cert
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
   
   # Upload to camera or use Let's Encrypt for public endpoints
   ```

### Docker Deployment

Run SRT proxy in container:

```dockerfile
FROM ubuntu:22.04

RUN apt-get update && \
    apt-get install -y ffmpeg

CMD ffmpeg -i rtsp://camera:554/stream \
           -c copy \
           -f mpegts \
           "srt://0.0.0.0:9000?mode=listener&passphrase=${SRT_PASSPHRASE}&pbkeylen=32"
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  srt-proxy:
    build: .
    ports:
      - "9000:9000/udp"
    environment:
      - SRT_PASSPHRASE=YourSecretKey123
    restart: unless-stopped
```

## Troubleshooting

### RTSPS Connection Failed

```bash
# Test with openssl
openssl s_client -connect 192.168.1.100:322

# Check certificate
echo | openssl s_client -connect 192.168.1.100:322 2>/dev/null | openssl x509 -noout -dates
```

### SRT Connection Issues

```bash
# Test SRT connection
srt-live-transmit "srt://host:port?mode=caller&passphrase=key" file://output.ts -v

# Check firewall
sudo ufw allow 9000/udp

# Verify FFmpeg SRT support
ffmpeg -hide_banner -protocols | grep srt
```

### High Latency

```bash
# Reduce SRT latency
srt://host:port?latency=50&mode=caller

# Use UDP for RTSP
rtsp_transport=udp
```

## Security Considerations

### ⚠️ Never Do This in Production

```bash
# DON'T: Disable SSL verification
# DON'T: Use weak passphrases (123456)
# DON'T: Expose SRT ports to internet without firewall
# DON'T: Hardcode credentials in code
```

### ✅ Do This Instead

```bash
# DO: Use environment variables
export SRT_PASSPHRASE=$(cat /secure/srt.key)

# DO: Use firewall rules
sudo ufw allow from 192.168.1.0/24 to any port 9000

# DO: Monitor for unauthorized access
fail2ban integration for repeated failed connections

# DO: Use certificate pinning for RTSPS
Verify camera certificate fingerprint
```

## Additional Resources

- [SRT Alliance](https://www.srtalliance.org/)
- [FFmpeg SRT Documentation](https://trac.ffmpeg.org/wiki/StreamingGuide)
- [RTSP RFC 2326](https://tools.ietf.org/html/rfc2326)
- [WireGuard Documentation](https://www.wireguard.com/)

## Summary

For Smart Vault CCTV deployment:

1. **Development/Testing**: Standard RTSP (acceptable for isolated networks)
2. **Small Deployment**: RTSPS (if cameras support it)
3. **Production**: SRT with strong passphrase + Firewall rules
4. **High Security**: VPN tunnel (WireGuard) + SRT encryption

Choose based on your threat model and network infrastructure.
