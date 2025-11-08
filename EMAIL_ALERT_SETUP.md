# 📧 Email Alert Setup Guide

## Overview

The Smart Vault CCTV system now sends automatic email alerts when **unauthorized persons** are detected. Alerts include:

- 🚨 Real-time notifications
- 📸 Face snapshot attached
- 📊 Detection details (time, location, confidence)
- 🔗 Direct dashboard link

---

## 🎯 Quick Setup (5 Minutes)

### **Step 1: Generate Gmail App Password**

Gmail requires an "App Password" for security (not your regular password).

**Instructions:**

1. **Go to Google Account:**
   - Visit: https://myaccount.google.com/security
   - Sign in with: **sagarnc199@gmail.com**

2. **Enable 2-Step Verification** (if not already enabled):
   - Click "2-Step Verification"
   - Follow prompts to enable

3. **Create App Password:**
   - Go to: https://myaccount.google.com/apppasswords
   - Or search "App Passwords" in your Google Account
   - Select app: "Mail"
   - Select device: "Windows Computer"
   - Click **Generate**
   - Copy the 16-character password (like: `abcd efgh ijkl mnop`)

**⚠️ Important:** This is a one-time display - save it immediately!

---

### **Step 2: Create .env File**

Create a file named `.env` in the project root:

```bash
# Location: C:\Users\user\Downloads\ii\.env
```

**Copy this content:**

```env
# ===========================
# Email Alert Configuration
# ===========================
ENABLE_EMAIL_ALERTS=true

# Gmail credentials
EMAIL_SENDER=sagarnc199@gmail.com
EMAIL_PASSWORD=your_16_char_app_password_here
EMAIL_RECIPIENT=sagarnc26@gamil.com

# SMTP settings (Gmail)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Alert cooldown (seconds) - prevents spam
EMAIL_COOLDOWN=300

# Include face snapshot
EMAIL_INCLUDE_SNAPSHOT=true
```

**Replace `your_16_char_app_password_here` with the App Password from Step 1.**

---

### **Step 3: Test the System**

**Start the system:**

```bash
# Terminal 1 - MongoDB
mongod --dbpath C:/data/db

# Terminal 2 - Flask
python src/webapp/app.py

# Terminal 3 - Face Recognition
python -u src/main.py
```

**Trigger a detection:**
- Show an unknown face to the camera
- Or use a face not in the database

**Expected result:**
- ✅ Email sent to sagarnc26@gamil.com
- ✅ Snapshot attached
- ✅ Alert details included

---

## 📧 Email Preview

**Subject:**
```
🚨 SECURITY ALERT - Unauthorized Person Detected
```

**Body:**
```
┌─────────────────────────────────────────┐
│  🚨 UNAUTHORIZED PERSON DETECTED        │
├─────────────────────────────────────────┤
│  Timestamp: 2025-10-28 22:30:45        │
│  Location: Main Entrance                │
│  Camera ID: cam_01                      │
│  Detection Confidence: 75.3%            │
│  ⚠️ NOT in authorized database          │
├─────────────────────────────────────────┤
│  📸 [Snapshot Image Attached]           │
└─────────────────────────────────────────┘

Smart Vault CCTV Security System
Dashboard: http://localhost:5000
```

---

## 🎛️ Configuration Options

### **Cooldown Period**

Prevents email spam by limiting alert frequency.

```env
EMAIL_COOLDOWN=300  # 5 minutes (default)
```

**Options:**
- `60` - 1 minute (frequent)
- `300` - 5 minutes (recommended)
- `600` - 10 minutes (less frequent)
- `1800` - 30 minutes (rare updates)

### **Enable/Disable Alerts**

```env
ENABLE_EMAIL_ALERTS=true   # On
ENABLE_EMAIL_ALERTS=false  # Off
```

### **Include Snapshots**

```env
EMAIL_INCLUDE_SNAPSHOT=true   # Attach face image
EMAIL_INCLUDE_SNAPSHOT=false  # Text only
```

### **Change Recipient**

```env
EMAIL_RECIPIENT=another@email.com
```

### **Multiple Recipients** (not yet supported)

For now, use one recipient. To send to multiple emails:
- Set up email forwarding in Gmail
- Or contact developer for multi-recipient feature

---

## 🔧 Troubleshooting

### **Problem: "Email authentication failed"**

**Cause:** Wrong app password or regular password used

**Fix:**
1. Generate new App Password (Step 1 above)
2. Copy the 16-character code exactly
3. Update `.env` file
4. Restart Python processes

### **Problem: "2-Step Verification required"**

**Cause:** Gmail requires 2FA for app passwords

**Fix:**
1. Enable 2-Step Verification in Google Account
2. Then create App Password
3. Use App Password in `.env`

### **Problem: "Email not received"**

**Check:**
1. ✅ `.env` file exists and has correct password
2. ✅ Check spam/junk folder
3. ✅ Email address correct (check typos)
4. ✅ Internet connection active
5. ✅ Cooldown period passed (5 minutes default)

**Test email manually:**
```bash
python src/email_alert.py
```

### **Problem: "Email cooldown active"**

**Cause:** Sent email within last 5 minutes

**Fix:**
- Wait for cooldown period
- Or reduce `EMAIL_COOLDOWN` in `.env`
- Or restart system to reset cooldown

### **Problem: "Module not found: email_alert"**

**Cause:** Old process running

**Fix:**
```bash
taskkill /F /IM python.exe
python -u src/main.py
```

---

## 📊 Alert Statistics

**Cooldown prevents spam:**
- Without cooldown: 100+ emails/hour possible
- With 5min cooldown: Max 12 emails/hour
- With 10min cooldown: Max 6 emails/hour

**Recommended settings:**
- **High security area:** 1-2 minute cooldown
- **Normal area:** 5 minute cooldown (default)
- **Low priority:** 10-30 minute cooldown

---

## 🎯 Advanced Configuration

### **Custom Location Name**

Edit `src/main.py` line ~306:

```python
self.email_system.send_alert(
    camera_id=CAMERA_ID,
    confidence=confidence,
    frame=face_img,
    location="Main Entrance"  # ← Change this
)
```

**Examples:**
- `"Main Entrance"`
- `"Parking Lot"`
- `"Building A - Floor 2"`
- `"Server Room"`

### **Use Different Email Provider**

For non-Gmail (Outlook, Yahoo, etc.):

```env
SMTP_SERVER=smtp.office365.com  # Outlook
SMTP_PORT=587
```

### **Disable Snapshots** (faster emails)

```env
EMAIL_INCLUDE_SNAPSHOT=false
```

---

## 🧪 Testing

### **Test Script:**

```bash
python src/email_alert.py
```

**Expected output:**
```
Testing Email Alert System
==================================================
Enabled: True
Sender: sagarnc199@gmail.com
Recipient: sagarnc26@gamil.com
Cooldown: 300s

Sending test email...
✅ Alert email sent successfully!
Result: ✅ Sent
```

### **Check Logs:**

```bash
# In running system, watch for:
INFO:src.email_alert:✓ Email alerts enabled
INFO:src.email_alert:📧 Sending alert email to sagarnc26@gamil.com...
INFO:src.email_alert:✅ Alert email sent successfully!
```

---

## 📝 Security Best Practices

### **✅ Do:**
- ✅ Use App Password (not regular password)
- ✅ Keep `.env` file private (never commit to Git)
- ✅ Use strong 2FA on Gmail account
- ✅ Set appropriate cooldown to avoid spam
- ✅ Monitor email delivery

### **❌ Don't:**
- ❌ Share App Password with anyone
- ❌ Commit `.env` to version control
- ❌ Use regular Gmail password
- ❌ Set cooldown too low (spam risk)
- ❌ Disable 2FA after creating App Password

---

## 🔑 .env File Location

**Correct path:**
```
C:\Users\user\Downloads\ii\.env
```

**File structure:**
```
ii/
├── .env              ← Create this file
├── .env.example      ← Template (already exists)
├── src/
│   ├── main.py
│   ├── email_alert.py  ← New module
│   └── config.py       ← Updated with email config
└── ...
```

---

## 🚀 Quick Start Checklist

- [ ] Generate Gmail App Password
- [ ] Create `.env` file in project root
- [ ] Add App Password to `.env`
- [ ] Verify sender/recipient emails
- [ ] Start MongoDB
- [ ] Start Flask
- [ ] Start Face Recognition
- [ ] Test with unknown face
- [ ] Check email inbox (and spam folder)
- [ ] Verify snapshot attached

---

## 📞 Support

**If emails not working:**

1. **Check configuration:**
   ```bash
   # Verify .env file exists
   cat .env
   
   # Test email system
   python src/email_alert.py
   ```

2. **Check logs:**
   - Look for email-related messages
   - Check for authentication errors

3. **Common fixes:**
   - Regenerate App Password
   - Check internet connection
   - Verify email addresses (typos?)
   - Wait for cooldown period
   - Restart all services

---

## 🎉 Success!

When everything works, you'll see:

**In Logs:**
```
INFO:src.email_alert:✓ Email alerts enabled: sagarnc199@gmail.com → sagarnc26@gamil.com
INFO:__main__:🚨 Unauthorized person detected!
INFO:src.email_alert:📧 Sending alert email to sagarnc26@gamil.com...
INFO:src.email_alert:✅ Alert email sent successfully!
```

**In Your Email:**
- Subject: 🚨 SECURITY ALERT - Unauthorized Person Detected
- Body: Full alert details
- Attachment: Face snapshot (if enabled)

---

## 📚 Related Documentation

- `docs/brute_force_protection.md` - Login security
- `LIVE_STREAMING_GUIDE.md` - Video streaming setup
- `README.md` - Main documentation

---

**🔒 Your security system is now monitoring 24/7 with instant email notifications!**
