# Fail2Ban Setup for Smart Vault CCTV

Complete guide to setting up Fail2Ban for automated IP blocking on failed login attempts and suspicious activity.

## Overview

Fail2Ban monitors log files and automatically bans IPs that show malicious behavior (excessive failed logins, port scans, etc.).

## Installation

### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y fail2ban
```

### CentOS/RHEL

```bash
sudo yum install -y epel-release
sudo yum install -y fail2ban
```

### Verify Installation

```bash
sudo systemctl status fail2ban
fail2ban-client --version
```

## Configuration

### 1. Create Local Configuration

Never edit the default config (`/etc/fail2ban/jail.conf`). Instead, create a local override:

```bash
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo nano /etc/fail2ban/jail.local
```

### 2. Global Settings

Edit `/etc/fail2ban/jail.local`:

```ini
[DEFAULT]
# Ban duration (seconds): 1 hour = 3600, 1 day = 86400
bantime  = 3600

# Time window for counting failures (seconds)
findtime  = 600

# Number of failures before ban
maxretry = 5

# Backend for monitoring logs
backend = auto

# Email alerts (optional)
destemail = admin@example.com
sendername = Fail2Ban-SmartVault
action = %(action_mwl)s

# Whitelist local IPs (never ban these)
ignoreip = 127.0.0.1/8 ::1 192.168.1.0/24
```

### 3. Flask Dashboard Protection

Create `/etc/fail2ban/filter.d/smartvault-flask.conf`:

```ini
[Definition]
# Fail2Ban filter for Smart Vault Flask dashboard

# Failed login pattern
# Match: "Login failed: username from IP (attempt N)"
failregex = ^.*Login failed:.*from <HOST>.*$

# Ignore successful logins
ignoreregex = ^.*Login successful:.*$
```

Create jail configuration in `/etc/fail2ban/jail.local`:

```ini
[smartvault-flask]
enabled = true
port = 5000
protocol = tcp
filter = smartvault-flask
logpath = /path/to/smart_vault.log
maxretry = 5
findtime = 600
bantime = 3600
action = iptables-multiport[name=flask, port="5000", protocol=tcp]
```

### 4. SSH Protection (Recommended)

Already included in default config, but verify:

```ini
[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log  # Ubuntu/Debian
# logpath = /var/log/secure  # CentOS/RHEL
maxretry = 3
findtime = 600
bantime = 3600
```

### 5. MongoDB Protection (Optional)

If MongoDB is exposed, create `/etc/fail2ban/filter.d/mongodb.conf`:

```ini
[Definition]
failregex = ^.*\[conn\d+\] authenticate db: admin .* failed for user .* from <HOST>:\d+$
ignoreregex =
```

Add to `/etc/fail2ban/jail.local`:

```ini
[mongodb]
enabled = true
port = 27017
filter = mongodb
logpath = /var/log/mongodb/mongodb.log
maxretry = 3
bantime = 7200
```

## Advanced Configuration

### Custom Actions

Create `/etc/fail2ban/action.d/smartvault-notify.conf` for webhook notifications:

```ini
[Definition]
actionstart = curl -X POST http://localhost:5000/api/alert -H "Content-Type: application/json" -d '{"alert_type":"fail2ban","action":"start","message":"Fail2Ban started"}'

actionstop = curl -X POST http://localhost:5000/api/alert -H "Content-Type: application/json" -d '{"alert_type":"fail2ban","action":"stop","message":"Fail2Ban stopped"}'

actioncheck =

actionban = curl -X POST http://localhost:5000/api/alert -H "Content-Type: application/json" -d '{"alert_type":"fail2ban","action":"ban","ip":"<ip>","message":"IP <ip> has been banned"}'

actionunban = curl -X POST http://localhost:5000/api/alert -H "Content-Type: application/json" -d '{"alert_type":"fail2ban","action":"unban","ip":"<ip>","message":"IP <ip> has been unbanned"}'
```

Update jail to use the action:

```ini
[smartvault-flask]
enabled = true
...
action = iptables-multiport[name=flask, port="5000", protocol=tcp]
         smartvault-notify
```

### Permanent Bans

For repeat offenders, create a permanent ban list in `/etc/fail2ban/jail.local`:

```ini
[recidive]
enabled = true
logpath = /var/log/fail2ban.log
banaction = iptables-allports
bantime = -1  # Permanent ban
findtime = 86400  # 1 day
maxretry = 3
```

## Starting Fail2Ban

```bash
# Start service
sudo systemctl start fail2ban

# Enable on boot
sudo systemctl enable fail2ban

# Check status
sudo systemctl status fail2ban
```

## Testing

### 1. Test Configuration

```bash
# Test config syntax
sudo fail2ban-client -t

# Test specific jail
sudo fail2ban-client -vvv start smartvault-flask
```

### 2. Simulate Failed Logins

From another machine or terminal:

```bash
# Attempt multiple failed logins
for i in {1..6}; do
    curl -X POST http://YOUR_SERVER:5000/login \
         -d "username=test&password=wrong" \
         -w "\nResponse: %{http_code}\n"
    sleep 1
done

# After 5 attempts, the IP should be banned
```

### 3. Check Ban Status

```bash
# View all active jails
sudo fail2ban-client status

# View specific jail status
sudo fail2ban-client status smartvault-flask

# View banned IPs
sudo fail2ban-client status smartvault-flask | grep "Banned IP"

# Check iptables rules
sudo iptables -L -n | grep 5000
```

### 4. Manual Ban/Unban

```bash
# Manual ban
sudo fail2ban-client set smartvault-flask banip 192.168.1.100

# Manual unban
sudo fail2ban-client set smartvault-flask unbanip 192.168.1.100

# Unban all
sudo fail2ban-client unban --all
```

## Monitoring

### View Logs

```bash
# Fail2Ban log
sudo tail -f /var/log/fail2ban.log

# See ban actions
sudo grep 'Ban' /var/log/fail2ban.log

# See unban actions
sudo grep 'Unban' /var/log/fail2ban.log
```

### Statistics

```bash
# Jail statistics
sudo fail2ban-client status smartvault-flask

# All jails summary
sudo fail2ban-client status | grep "Jail list"

# Database queries (SQLite backend)
sudo sqlite3 /var/lib/fail2ban/fail2ban.sqlite3 "SELECT * FROM bans;"
```

## Whitelisting

### Add IPs to Whitelist

Edit `/etc/fail2ban/jail.local`:

```ini
[DEFAULT]
ignoreip = 127.0.0.1/8 ::1 
           192.168.1.0/24
           10.0.0.0/8
           YOUR_ADMIN_IP
```

### Whitelist Specific Users

For Flask app, modify filter to ignore specific usernames:

```ini
[Definition]
failregex = ^.*Login failed: (?!admin|monitoring).*from <HOST>.*$
```

## Troubleshooting

### Fail2Ban Not Banning

```bash
# Check if jail is running
sudo fail2ban-client status

# Verify log path exists and is readable
ls -la /path/to/smart_vault.log

# Test regex manually
fail2ban-regex /path/to/smart_vault.log /etc/fail2ban/filter.d/smartvault-flask.conf

# Increase verbosity
sudo fail2ban-client -vvv reload
```

### Accidental Self-Ban

```bash
# From physical server console or SSH from another IP:
sudo fail2ban-client set smartvault-flask unbanip YOUR_IP

# Or temporarily disable Fail2Ban
sudo systemctl stop fail2ban

# Clear all bans
sudo fail2ban-client unban --all

# Restart
sudo systemctl start fail2ban
```

### Service Not Starting

```bash
# Check configuration
sudo fail2ban-client -t

# View detailed errors
sudo journalctl -u fail2ban -n 50

# Test specific filter
fail2ban-regex /var/log/auth.log /etc/fail2ban/filter.d/sshd.conf
```

## Production Best Practices

### 1. Adjust Ban Times

For production, use stricter settings:

```ini
[DEFAULT]
bantime  = 86400     # 24 hours
findtime  = 3600     # 1 hour window
maxretry = 3         # Only 3 attempts
```

### 2. Email Notifications

Configure email alerts:

```ini
[DEFAULT]
destemail = security@yourcompany.com
sender = fail2ban@yourserver.com
action = %(action_mwl)s
```

Install mail utility:

```bash
sudo apt-get install -y mailutils
```

### 3. Database Logging

Enable database backend for better analytics:

```ini
[DEFAULT]
dbfile = /var/lib/fail2ban/fail2ban.sqlite3
dbpurgeage = 86400
```

### 4. Monitor Fail2Ban Health

Create a monitoring script:

```bash
#!/bin/bash
# Check if Fail2Ban is running
if ! systemctl is-active --quiet fail2ban; then
    systemctl start fail2ban
    curl -X POST http://localhost:5000/api/alert \
         -H "Content-Type: application/json" \
         -d '{"alert_type":"system","message":"Fail2Ban restarted"}'
fi
```

Add to cron:

```bash
*/5 * * * * /path/to/monitor_fail2ban.sh
```

## Integration with Smart Vault Dashboard

### Real-time Ban Notifications

The Flask dashboard can receive Fail2Ban events via the webhook action configured earlier. Events will appear in the Security Logs page.

### View Ban Statistics

Create a dashboard widget to show:
- Currently banned IPs
- Ban history
- Most attacked services
- Geographic distribution of attacks (optional, with GeoIP)

## Uninstallation

If needed to remove Fail2Ban:

```bash
# Stop service
sudo systemctl stop fail2ban
sudo systemctl disable fail2ban

# Remove package
sudo apt-get remove --purge fail2ban  # Ubuntu/Debian
sudo yum remove fail2ban              # CentOS/RHEL

# Clean up iptables rules
sudo iptables -F
```

## Additional Resources

- [Fail2Ban Official Documentation](https://www.fail2ban.org/wiki/index.php/Main_Page)
- [Fail2Ban Filters](https://www.fail2ban.org/wiki/index.php/MANUAL_0_8#Filters)
- [Common Fail2Ban Recipes](https://www.digitalocean.com/community/tutorials/how-fail2ban-works-to-protect-services-on-a-linux-server)

## Support

For issues with Fail2Ban:
1. Test configuration: `sudo fail2ban-client -t`
2. Check logs: `/var/log/fail2ban.log`
3. Verify regex: `fail2ban-regex`
4. Review iptables: `sudo iptables -L -n`
