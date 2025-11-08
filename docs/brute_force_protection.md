# 🔒 Brute Force Protection

## Overview

The Smart Vault CCTV system includes **built-in brute force protection** to prevent unauthorized access through automated login attacks. After **5 failed login attempts**, the attacker's IP address is **blocked for 5 minutes**.

---

## 🎯 Key Features

✅ **IP-based blocking** - Blocks specific IP addresses, not users  
✅ **Automatic detection** - No configuration needed  
✅ **Time-based unblock** - Automatic unblock after 5 minutes  
✅ **Attempt tracking** - Shows remaining attempts before block  
✅ **Security logging** - All blocks logged to database  
✅ **Real-time warnings** - Clear feedback to users  
✅ **Clean-up mechanism** - Old attempts auto-expire after 15 minutes  

---

## ⚙️ Configuration

### **Default Settings:**

```python
MAX_LOGIN_ATTEMPTS = 5           # Failed attempts before block
BLOCK_DURATION_MINUTES = 5       # How long IP stays blocked
```

### **Location:**

File: `src/webapp/app.py` (lines 66-67)

### **Customizing:**

To change the thresholds, edit these values:

```python
# Block after 3 attempts instead of 5
MAX_LOGIN_ATTEMPTS = 3

# Block for 10 minutes instead of 5
BLOCK_DURATION_MINUTES = 10
```

---

## 🔄 How It Works

### **Attack Detection Flow:**

```
1. User attempts login
   ↓
2. Check if IP is already blocked
   ↓ (if blocked)
   → Show "IP blocked" message with countdown
   
   ↓ (if not blocked)
3. Validate credentials
   ↓ (if invalid)
4. Record failed attempt
   ↓
5. Check attempt count
   ↓ (if count >= 5)
6. Block IP for 5 minutes
   ↓
7. Log block event to database
   ↓
8. Show "IP blocked" message
```

### **Successful Login Flow:**

```
1. Valid credentials entered
   ↓
2. Reset all failed attempts for this IP
   ↓
3. Grant access to dashboard
```

---

## 🚨 User Experience

### **Attempt 1-4: Warning Messages**

After each failed login, users see:

```
⚠ Invalid credentials. X attempts remaining before block
```

### **Attempt 5: Immediate Block**

After the 5th failed attempt:

```
🔒 ACCESS BLOCKED
Too many failed attempts. Your IP is blocked for 5 minutes

Your IP has been temporarily blocked due to multiple failed login attempts.
```

### **While Blocked:**

Users trying to login see:

```
🔒 ACCESS BLOCKED
Too many failed attempts. Your IP is blocked for 4m 32s

Your IP has been temporarily blocked due to multiple failed login attempts.
```

The countdown updates in real-time if they refresh.

### **After Block Expires:**

- Attempts counter resets to 0
- User can try logging in again
- If they fail again, the count restarts

---

## 📊 Monitoring Blocked IPs

### **View Blocked IPs via API:**

**Endpoint:** `GET /api/blocked_ips`

**Authentication:** Login required

**Response:**
```json
{
  "blocked_ips": [
    {
      "ip": "192.168.1.100",
      "attempts": 5,
      "blocked_until": "2025-10-28 14:05:00",
      "remaining_seconds": 245
    }
  ],
  "count": 1
}
```

### **Check from Command Line:**

```bash
# Using curl (requires login cookie)
curl -b cookies.txt http://localhost:5000/api/blocked_ips
```

### **Check Database Logs:**

All blocks are logged to MongoDB:

```javascript
db.logs.find({event_type: "brute_force_block"})
```

**Example log entry:**
```json
{
  "event_type": "brute_force_block",
  "ip_address": "192.168.1.100",
  "username_attempted": "admin",
  "attempts": 5,
  "blocked_until": ISODate("2025-10-28T14:05:00Z"),
  "timestamp": ISODate("2025-10-28T14:00:00Z")
}
```

---

## 🔍 Log Messages

### **In Flask Server Logs:**

**Failed Attempt:**
```
WARNING:__main__:⚠ Login failed: admin from 192.168.1.100 (attempt 3/5)
```

**IP Blocked:**
```
WARNING:__main__:🔒 IP 192.168.1.100 blocked for 5 minutes after 5 failed attempts
```

**Blocked Attempt:**
```
WARNING:__main__:🔒 Blocked login attempt from 192.168.1.100 (admin)
```

**Successful Login:**
```
INFO:__main__:✓ Login successful: admin from 192.168.1.100
```

---

## 🛡️ Security Features

### **1. Automatic Cleanup**

Old attempts (>15 minutes) are automatically removed to prevent memory bloat:

```python
# Clean up old attempts (older than 15 minutes)
login_attempts[ip_address]['attempts'] = [
    t for t in login_attempts[ip_address]['attempts'] 
    if (now - t).total_seconds() < 900
]
```

### **2. Database Logging**

Every block is logged for security auditing:
- Timestamp of block
- IP address
- Username attempted
- Number of attempts
- Block expiration time

### **3. IP-Based, Not User-Based**

- Blocks the attacking IP, not the username
- Prevents lockout of legitimate users from other locations
- Multiple users behind same IP share the limit

### **4. Time-Based Unblock**

- No manual intervention needed
- Automatic unblock after time expires
- Prevents permanent lockouts

---

## 🧪 Testing

### **Test the Protection:**

1. **Open login page:** http://localhost:5000/login

2. **Enter wrong password 5 times:**
   - Attempt 1: "4 attempts remaining"
   - Attempt 2: "3 attempts remaining"
   - Attempt 3: "2 attempts remaining"
   - Attempt 4: "1 attempt remaining"
   - Attempt 5: "ACCESS BLOCKED for 5 minutes"

3. **Try to login while blocked:**
   - Should see countdown timer
   - Login form still disabled

4. **Wait 5 minutes:**
   - Block expires
   - Can attempt login again

### **Test from Command Line:**

```bash
# Simulate failed attempts
for i in {1..6}; do
  curl -X POST http://localhost:5000/login \
    -d "username=admin&password=wrong" \
    -c cookies.txt -b cookies.txt
  echo "Attempt $i"
done
```

### **Check Blocked Status:**

```python
# Python test script
import requests

# Try to login with wrong password
for i in range(6):
    response = requests.post('http://localhost:5000/login', 
                            data={'username': 'admin', 'password': 'wrong'})
    print(f"Attempt {i+1}: {response.status_code}")
    if 'blocked' in response.text.lower():
        print("IP BLOCKED!")
        break
```

---

## 🔧 Advanced Configuration

### **Per-IP Tracking**

The system tracks each IP separately:

```python
login_attempts = {
    '192.168.1.100': {
        'count': 5,
        'blocked_until': datetime(2025, 10, 28, 14, 5, 0),
        'attempts': [timestamp1, timestamp2, ...]
    },
    '192.168.1.101': {
        'count': 2,
        'blocked_until': None,
        'attempts': [timestamp1, timestamp2]
    }
}
```

### **Manual Unblock (Advanced)**

To manually unblock an IP via Python console:

```python
from src.webapp.app import login_attempts

# Clear all blocks
login_attempts.clear()

# Unblock specific IP
login_attempts['192.168.1.100'] = {'count': 0, 'blocked_until': None, 'attempts': []}
```

### **Whitelist IPs (Advanced)**

To whitelist specific IPs (never block), modify the code:

```python
WHITELISTED_IPS = ['127.0.0.1', '192.168.1.1']

def is_ip_blocked(ip_address):
    if ip_address in WHITELISTED_IPS:
        return False, None
    # ... rest of function
```

---

## 📈 Statistics & Monitoring

### **View Attack Statistics:**

```python
from src.db_connection import DB

db = DB()

# Count total blocks
total_blocks = db.logs_coll.count_documents({'event_type': 'brute_force_block'})

# Recent blocks
recent_blocks = db.logs_coll.find(
    {'event_type': 'brute_force_block'}
).sort('timestamp', -1).limit(10)

for block in recent_blocks:
    print(f"{block['ip_address']} - {block['username_attempted']} - {block['timestamp']}")
```

### **Most Attacked Usernames:**

```python
# Aggregation pipeline
pipeline = [
    {'$match': {'event_type': 'brute_force_block'}},
    {'$group': {'_id': '$username_attempted', 'count': {'$sum': 1}}},
    {'$sort': {'count': -1}}
]

results = db.logs_coll.aggregate(pipeline)
for result in results:
    print(f"{result['_id']}: {result['count']} attacks")
```

---

## 🔗 Integration with Fail2Ban

The brute force protection works **independently** but can also integrate with Fail2Ban:

### **Flask Logs Format:**

```
WARNING:__main__:⚠ Login failed: admin from 192.168.1.100 (attempt 3/5)
```

### **Fail2Ban Filter:**

Create `/etc/fail2ban/filter.d/smart-vault.conf`:

```ini
[Definition]
failregex = ^.*Login failed: .* from <HOST> \(attempt \d+/\d+\)$
ignoreregex =
```

### **Fail2Ban Jail:**

Add to `/etc/fail2ban/jail.local`:

```ini
[smart-vault]
enabled = true
port = 5000
filter = smart-vault
logpath = /path/to/flask.log
maxretry = 5
bantime = 300
```

This provides **dual protection**: built-in + Fail2Ban.

---

## ⚠️ Important Notes

### **Limitations:**

1. **In-Memory Storage**: Blocks are stored in memory and cleared on server restart
2. **No Distributed Protection**: Each Flask instance tracks separately (for load-balanced setups)
3. **IP Spoofing**: Advanced attackers can spoof IPs (use with Fail2Ban for defense)
4. **Shared IPs**: Users behind same NAT share the limit

### **Best Practices:**

1. ✅ Enable HTTPS to prevent password sniffing
2. ✅ Use strong passwords (>12 characters)
3. ✅ Monitor blocked IPs regularly
4. ✅ Review block logs for attack patterns
5. ✅ Consider adding CAPTCHA after 3 attempts
6. ✅ Implement 2FA for sensitive accounts
7. ✅ Use Fail2Ban for additional protection

---

## 🎯 Summary

**Brute Force Protection is now active!**

### **Key Points:**

- ✅ **5 attempts** before block
- ✅ **5 minutes** block duration
- ✅ **Automatic** detection and blocking
- ✅ **Logged** to database for auditing
- ✅ **Real-time** feedback to users
- ✅ **No configuration** needed (works out of the box)

### **What It Prevents:**

- ❌ Password guessing attacks
- ❌ Credential stuffing
- ❌ Dictionary attacks
- ❌ Automated brute force tools
- ❌ Bot attacks

### **Testing:**

Try entering wrong passwords 5 times at:
**http://localhost:5000/login**

---

## 📚 Related Documentation

- `docs/fail2ban_setup.md` - Additional Fail2Ban protection
- `src/webapp/app.py` - Implementation code
- `docs/encryption.md` - HTTPS setup for secure login

---

**Your login system is now protected against brute force attacks!** 🛡️
