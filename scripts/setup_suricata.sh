#!/bin/bash

# Smart Vault CCTV - Suricata IDS Installation Script
# Automated setup for Ubuntu/Debian systems

set -e

echo "================================================"
echo "  Suricata IDS Installation for Smart Vault"
echo "================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Error: This script must be run as root"
    echo "Please run: sudo bash $0"
    exit 1
fi

# Detect network interface
echo "[1/7] Detecting network interface..."
INTERFACE=$(ip route | grep default | awk '{print $5}' | head -n1)
echo "  Detected interface: $INTERFACE"
echo ""

# Update package lists
echo "[2/7] Updating package lists..."
apt-get update -qq

# Install Suricata
echo "[3/7] Installing Suricata..."
apt-get install -y suricata

# Check installation
if ! command -v suricata &> /dev/null; then
    echo "Error: Suricata installation failed"
    exit 1
fi

SURICATA_VERSION=$(suricata --version | head -n1)
echo "  Installed: $SURICATA_VERSION"
echo ""

# Configure Suricata
echo "[4/7] Configuring Suricata..."

# Backup original config
cp /etc/suricata/suricata.yaml /etc/suricata/suricata.yaml.bak

# Set network interface
sed -i "s/interface: eth0/interface: $INTERFACE/" /etc/suricata/suricata.yaml

# Get local network
LOCAL_NETWORK=$(ip -o -f inet addr show | awk '/scope global/ {print $4}' | head -n1)
if [ -z "$LOCAL_NETWORK" ]; then
    LOCAL_NETWORK="192.168.1.0/24"
fi
echo "  HOME_NET: $LOCAL_NETWORK"

# Update HOME_NET in config
sed -i "s|HOME_NET:.*|HOME_NET: \"[$LOCAL_NETWORK]\"|" /etc/suricata/suricata.yaml

echo "  ✓ Configuration updated"
echo ""

# Create custom rules
echo "[5/7] Creating custom rules..."

cat > /etc/suricata/rules/local.rules << 'EOF'
# Smart Vault CCTV Security Rules

# RTSP Stream Security
alert tcp any any -> $HOME_NET 554 (msg:"RTSP Connection Attempt"; flow:to_server,established; sid:1000001; rev:1;)
alert tcp any any -> $HOME_NET 554 (msg:"RTSP Brute Force Attempt"; flow:to_server; threshold:type threshold, track by_src, count 10, seconds 60; sid:1000002; rev:1;)
alert tcp any any -> $HOME_NET 554 (msg:"RTSP Failed Authentication"; flow:established; content:"401 Unauthorized"; sid:1000003; rev:1;)

# Port Scan Detection
alert tcp any any -> $HOME_NET any (msg:"Potential Port Scan"; flags:S; threshold:type threshold, track by_src, count 20, seconds 10; sid:1000004; rev:1;)

# SSH Brute Force
alert tcp any any -> $HOME_NET 22 (msg:"SSH Brute Force Attempt"; flow:to_server; threshold:type threshold, track by_src, count 5, seconds 60; sid:1000005; rev:1;)

# Camera Web Interface Access
alert tcp any any -> $HOME_NET 80 (msg:"Camera HTTP Access Attempt"; flow:to_server,established; sid:1000006; rev:1;)
alert tcp any any -> $HOME_NET 443 (msg:"Camera HTTPS Access Attempt"; flow:to_server,established; sid:1000007; rev:1;)

# Flask Dashboard Security
alert tcp any any -> $HOME_NET 5000 (msg:"Flask Dashboard Excessive Access"; threshold:type threshold, track by_src, count 20, seconds 60; sid:1000008; rev:1;)
alert tcp any any -> $HOME_NET 5000 (msg:"Flask Login POST Attempt"; flow:to_server,established; content:"POST"; http_method; content:"/login"; http_uri; sid:1000009; rev:1;)

# MongoDB Access (if exposed)
alert tcp any any -> $HOME_NET 27017 (msg:"MongoDB Connection Attempt"; flow:to_server,established; sid:1000010; rev:1;)

# Excessive Connection Rate
alert tcp any any -> $HOME_NET any (msg:"Excessive Connection Rate from Single Source"; threshold:type threshold, track by_src, count 100, seconds 10; sid:1000011; rev:1;)

# SRT Stream Security
alert udp any any -> $HOME_NET 9000 (msg:"SRT Stream Connection Attempt"; sid:1000012; rev:1;)
EOF

echo "  ✓ Custom rules created"
echo ""

# Update rules
echo "[6/7] Updating Suricata rules..."
suricata-update || echo "  ⚠ Rule update failed (continuing anyway)"
echo ""

# Start Suricata
echo "[7/7] Starting Suricata..."
systemctl enable suricata
systemctl restart suricata

# Wait for startup
sleep 3

# Check status
if systemctl is-active --quiet suricata; then
    echo "  ✓ Suricata is running"
else
    echo "  ✗ Suricata failed to start"
    echo "  Check logs: journalctl -u suricata -n 50"
    exit 1
fi

echo ""
echo "================================================"
echo "  Installation Complete!"
echo "================================================"
echo ""
echo "Suricata is now monitoring: $INTERFACE"
echo "HOME_NET: $LOCAL_NETWORK"
echo ""
echo "Configuration files:"
echo "  - /etc/suricata/suricata.yaml"
echo "  - /etc/suricata/rules/local.rules"
echo ""
echo "Log files:"
echo "  - /var/log/suricata/fast.log (alerts)"
echo "  - /var/log/suricata/eve.json (detailed)"
echo ""
echo "Useful commands:"
echo "  - sudo systemctl status suricata"
echo "  - sudo tail -f /var/log/suricata/fast.log"
echo "  - sudo suricata-update (update rules)"
echo "  - sudo fail2ban-client status (if using Fail2Ban)"
echo ""
echo "Next steps:"
echo "  1. Run alert forwarder: python scripts/alert_forwarder.py"
echo "  2. View alerts in dashboard: http://localhost:5000/security"
echo "  3. Test with: nmap -sS localhost"
echo ""
