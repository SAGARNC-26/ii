# Suricata IDS Integration

This guide explains how to integrate Suricata IDS with Smart Vault CCTV for comprehensive network security monitoring.

## Overview

Suricata is an open-source Intrusion Detection System (IDS) that can monitor network traffic and detect:
- Port scans and reconnaissance
- RTSP stream access attempts
- Brute force attacks
- Anomalous network behavior

## Installation

### Ubuntu/Debian

```bash
# Run the automated setup script
sudo bash scripts/setup_suricata.sh
```

### Manual Installation

```bash
# Update package list
sudo apt-get update

# Install Suricata
sudo apt-get install -y suricata

# Check installation
suricata --version
```

## Configuration

### 1. Configure Network Interface

Edit `/etc/suricata/suricata.yaml`:

```yaml
# Set your network interface
af-packet:
  - interface: eth0  # Change to your interface (eth0, ens33, etc.)
    threads: auto
    cluster-id: 99
    cluster-type: cluster_flow
    defrag: yes

# Set HOME_NET to your local network
vars:
  address-groups:
    HOME_NET: "[192.168.1.0/24]"  # Change to your network
    EXTERNAL_NET: "!$HOME_NET"
```

### 2. Enable Rule Sets

Edit `/etc/suricata/suricata.yaml` to enable rule files:

```yaml
rule-files:
  - suricata.rules
  - local.rules
```

### 3. Custom Rules for CCTV Security

Create `/etc/suricata/rules/local.rules`:

```bash
# RTSP Stream Security
alert tcp any any -> $HOME_NET 554 (msg:"RTSP Connection Attempt"; sid:1000001; rev:1;)
alert tcp any any -> $HOME_NET 554 (msg:"RTSP Brute Force Attempt"; threshold:type threshold, track by_src, count 10, seconds 60; sid:1000002; rev:1;)
alert tcp any any -> $HOME_NET 554 (msg:"RTSP Failed Auth"; content:"401 Unauthorized"; sid:1000003; rev:1;)

# Port Scan Detection
alert tcp any any -> $HOME_NET any (msg:"Port Scan Detected"; flags:S; threshold:type threshold, track by_src, count 20, seconds 10; sid:1000004; rev:1;)

# SSH Brute Force
alert tcp any any -> $HOME_NET 22 (msg:"SSH Brute Force Attempt"; threshold:type threshold, track by_src, count 5, seconds 60; sid:1000005; rev:1;)

# HTTP/HTTPS to Camera Management
alert tcp any any -> $HOME_NET 80 (msg:"Camera Web Interface Access"; sid:1000006; rev:1;)
alert tcp any any -> $HOME_NET 443 (msg:"Camera HTTPS Access"; sid:1000007; rev:1;)

# Flask Dashboard Security
alert tcp any any -> $HOME_NET 5000 (msg:"Flask Dashboard Access"; threshold:type threshold, track by_src, count 20, seconds 60; sid:1000008; rev:1;)
alert tcp any any -> $HOME_NET 5000 (msg:"Flask Login Attempt"; content:"POST"; content:"/login"; sid:1000009; rev:1;)

# Unusual Traffic Patterns
alert tcp any any -> $HOME_NET any (msg:"Excessive Connection Rate"; threshold:type threshold, track by_src, count 100, seconds 10; sid:1000010; rev:1;)
```

### 4. Update Rules

```bash
# Update Suricata rules
sudo suricata-update

# Enable ET Open ruleset (optional)
sudo suricata-update enable-source et/open
sudo suricata-update
```

## Running Suricata

### Start Suricata

```bash
# Start in IDS mode
sudo suricata -c /etc/suricata/suricata.yaml -i eth0

# Or use systemd
sudo systemctl start suricata
sudo systemctl enable suricata
```

### Check Status

```bash
# View status
sudo systemctl status suricata

# View logs
sudo tail -f /var/log/suricata/fast.log
sudo tail -f /var/log/suricata/eve.json
```

## Alert Forwarding to Dashboard

### Method 1: Alert Forwarder Script

The `scripts/alert_forwarder.py` script monitors Suricata logs and forwards alerts to the Flask dashboard via WebSocket.

```bash
# Run the alert forwarder
python scripts/alert_forwarder.py
```

**Script Features:**
- Monitors `/var/log/suricata/fast.log` in real-time
- Parses alert messages
- Forwards to Flask endpoint `/api/alert`
- Automatic reconnection on failure

### Method 2: Direct Integration

Configure Suricata to output alerts in EVE JSON format, then use a custom script to read and forward them:

```python
import json
import requests
import time

def monitor_eve_log():
    with open('/var/log/suricata/eve.json', 'r') as f:
        f.seek(0, 2)  # Go to end
        while True:
            line = f.readline()
            if line:
                try:
                    alert = json.loads(line)
                    if alert.get('event_type') == 'alert':
                        requests.post('http://localhost:5000/api/alert', json=alert)
                except Exception as e:
                    print(f"Error: {e}")
            time.sleep(0.1)
```

## Testing

### 1. Generate Test Alerts

```bash
# Port scan test (from another machine)
nmap -sS 192.168.1.100

# RTSP connection test
ffmpeg -i rtsp://192.168.1.100:554/stream -t 1 -f null -

# Failed login test
curl -X POST http://localhost:5000/login -d "username=test&password=wrong"
```

### 2. View Alerts

```bash
# Real-time alerts
sudo tail -f /var/log/suricata/fast.log

# Detailed JSON alerts
sudo tail -f /var/log/suricata/eve.json | jq .

# Statistics
sudo suricatasc -c "dump-counters"
```

### 3. Check Dashboard

- Navigate to `http://localhost:5000/security`
- Alerts should appear in real-time
- Verify WebSocket connection in browser console

## Performance Tuning

### High Traffic Networks

Edit `/etc/suricata/suricata.yaml`:

```yaml
# Increase performance
threading:
  set-cpu-affinity: yes
  cpu-affinity:
    - management-cpu-set:
        cpu: [ 0 ]
    - receive-cpu-set:
        cpu: [ 1, 2 ]
    - worker-cpu-set:
        cpu: [ 3, 4, 5, 6 ]

# Tune buffer sizes
stream:
  memcap: 128mb
  max-sessions: 262144

# Disable unnecessary protocols
app-layer:
  protocols:
    http:
      enabled: yes
    ssh:
      enabled: yes
    # Disable unused protocols for better performance
```

## Troubleshooting

### Suricata Not Starting

```bash
# Check configuration
sudo suricata -T -c /etc/suricata/suricata.yaml

# Check permissions
sudo chown -R root:root /var/log/suricata
sudo chmod -R 755 /var/log/suricata

# Check interface
ip addr show  # Verify interface name
```

### No Alerts Generated

```bash
# Verify rules are loaded
sudo suricatasc -c "ruleset-stats"

# Check rule syntax
sudo suricata -T -c /etc/suricata/suricata.yaml

# Increase logging verbosity
sudo suricata -c /etc/suricata/suricata.yaml -i eth0 -v
```

### Alert Forwarder Not Working

```bash
# Check log file permissions
sudo chmod 644 /var/log/suricata/fast.log

# Test manual POST
curl -X POST http://localhost:5000/api/alert -H "Content-Type: application/json" -d '{"message":"test"}'

# Check forwarder logs
python scripts/alert_forwarder.py --debug
```

## Production Deployment

### Security Best Practices

1. **Run Suricata as non-root user** (use capabilities):
```bash
sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/suricata
```

2. **Rotate logs regularly**:
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/suricata
```

3. **Monitor Suricata health**:
```bash
# Add to cron
*/5 * * * * systemctl is-active --quiet suricata || systemctl restart suricata
```

4. **Secure alert endpoint**:
- Use API key authentication for `/api/alert`
- Rate limit the endpoint
- Whitelist Suricata server IP

### High Availability

For production, consider:
- Multiple Suricata instances with load balancing
- Centralized log aggregation (ELK stack)
- Redundant alert forwarders
- Database replication for alert storage

## Additional Resources

- [Suricata Documentation](https://suricata.readthedocs.io/)
- [Emerging Threats Rules](https://rules.emergingthreats.net/)
- [RTSP Security Best Practices](https://www.cisco.com/c/en/us/support/docs/security/video-surveillance-manager/118941-configure-vsm-00.html)

## Support

For issues:
1. Check `/var/log/suricata/suricata.log`
2. Verify network interface configuration
3. Test rules manually with `suricata -T`
4. Check Smart Vault dashboard logs
