# Smart Vault CCTV - Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites

- Python 3.8+
- MongoDB (local or Docker)
- Webcam or IP Camera
- Windows/Linux/macOS

## Step 1: Install Dependencies

### Option A: Quick Start Script (Linux/macOS)

```bash
chmod +x start.sh
./start.sh
```

### Option B: Manual Installation (Windows/All Platforms)

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/macOS)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Start MongoDB

### Using Docker (Recommended)

```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### Or install locally

- **Windows**: Download from [MongoDB Download Center](https://www.mongodb.com/try/download/community)
- **Linux**: `sudo apt-get install mongodb`
- **macOS**: `brew install mongodb-community`

## Step 3: Add Known Faces

```bash
# Create known_faces directory (already exists)
# Add face images named: FirstName_LastName.jpg

# Example:
# known_faces/Alice_Smith.jpg
# known_faces/Bob_Jones.jpg
# known_faces/Charlie_Brown.jpg
```

**Tips:**
- Use clear, frontal face photos
- Good lighting
- One face per image
- Minimum size: 200x200 pixels

## Step 4: Sync Faces to Database

```bash
python src/sync_known_faces.py
```

Expected output:
```
✓ Added Alice Smith
✓ Added Bob Jones
✓ Added Charlie Brown
Sync Summary: 3 added, 0 skipped, 0 failed
```

## Step 5: Run Face Recognition

```bash
python src/main.py
```

You should see:
- Camera feed window opens
- Face detection in real-time
- Green boxes for authorized faces
- Red boxes for unknown faces
- Logs saved to MongoDB

**Controls:**
- Press `q` to quit
- Press `r` to reload authorized faces

## Step 6: Start Web Dashboard

In a **new terminal**:

```bash
python src/webapp/app.py
```

Then open browser:
```
http://localhost:5000
```

**Default Login:**
- Username: `admin`
- Password: `changeme`

## Verify Everything Works

### Test 1: Database Connection

```bash
python -c "from src.db_connection import DB; db = DB(); print('✓ Connected! Auth faces:', db.auth_coll.count_documents({}))"
```

### Test 2: Face Detection

```bash
python -c "from src.face_utils import detect_faces; import cv2; print('✓ Face utilities loaded')"
```

### Test 3: Web Dashboard

```bash
curl http://localhost:5000
# Should return HTML (login page)
```

## Common Issues

### Issue: "No module named 'cv2'"

```bash
pip install opencv-python
```

### Issue: "MongoDB connection failed"

Check if MongoDB is running:
```bash
# Docker
docker ps | grep mongo

# Local
mongosh --eval "db.version()"
```

### Issue: "Camera not opening"

Check camera index:
```bash
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera opened:', cap.isOpened())"
```

Try different camera sources in `src/config.py`:
```python
CAMERA_SOURCE = 0  # or 1, 2, etc.
```

### Issue: "Face not detected"

- Ensure good lighting
- Face should be frontal (not side profile)
- Move closer to camera
- Adjust `MIN_FACE_SIZE` in config

## Next Steps

### 1. Review Unknown Faces

```bash
python scripts/review_unknowns.py
```

### 2. Configure Settings

Edit `src/config.py`:
```python
MATCH_THRESHOLD = 0.40  # Lower = stricter
MULTIFRAME_COUNT = 3    # More frames = more accurate
```

### 3. Security Features

**Built-in (No Setup Required):**
- ✅ **Brute Force Protection** - Blocks IPs after 5 failed logins (5 min block)
  - See: `docs/brute_force_protection.md`
  - Test: Try wrong password 5 times
  - Monitor: http://localhost:5000/security

**Optional Advanced Security:**
- `docs/Suricata_integration.md` - IDS setup
- `docs/fail2ban_setup.md` - OS-level auto-blocking
- `docs/encryption.md` - Stream encryption

### 4. Deploy with Docker

```bash
docker-compose up -d
```

Access:
- MongoDB: `localhost:27017`
- Dashboard: `http://localhost:5000`

## Production Checklist

Before deploying to production:

- [ ] Change default password in `src/config.py`
- [ ] Set `SECRET_KEY` to random value
- [ ] Enable HTTPS for Flask
- [ ] Set up Fail2Ban
- [ ] Configure Suricata IDS
- [ ] Enable stream encryption
- [ ] Set up backup for MongoDB
- [ ] Configure firewall rules
- [ ] Review logs regularly

## Getting Help

1. Check `README.md` for detailed documentation
2. Review logs: `smart_vault.log`
3. Test individual components (see README Testing section)
4. Check MongoDB: `mongosh smart_vault_cctv`

## All Set! 🎉

Your Smart Vault CCTV system is now running!

- Main app: Shows live recognition
- Dashboard: `http://localhost:5000`
- Logs: Stored in MongoDB
- Unknown faces: Review via dashboard or CLI

Enjoy your AI-powered security system!
