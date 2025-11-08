# Smart Vault CCTV System

A comprehensive AI-powered facial recognition CCTV system with MongoDB storage, real-time detection, IDS integration, and web dashboard.

## 🏗️ Architecture

```
Smart Vault CCTV
├── Face Recognition Engine (DeepFace/ArcFace)
├── MongoDB + GridFS (face images & logs)
├── Real-time Detection & Multi-frame Averaging
├── Flask Dashboard + WebSocket Live Feed
├── Suricata IDS Integration
├── Fail2Ban Auto-blocking
└── Encrypted Stream Support (RTSP/SRT)
```

## 📁 Project Structure

```
smart-vault-cctv/
├── known_faces/           # Store authorized face images (name.jpg)
├── models/                # Pre-trained face recognition models
├── src/
│   ├── main.py           # Real-time recognition main loop
│   ├── face_utils.py     # Face detection, alignment, embedding
│   ├── db_connection.py  # MongoDB + GridFS wrapper
│   ├── config.py         # Configuration settings
│   ├── sync_known_faces.py  # Load known faces into DB
│   ├── unknown_handler.py   # Handle unknown face detections
│   ├── search_index.py      # Faiss index for fast search
│   ├── augmentation.py      # Face preprocessing & augmentation
│   ├── webapp/
│   │   ├── app.py        # Flask server
│   │   ├── templates/    # HTML templates
│   │   ├── static/       # CSS, JS, images
│   │   └── frontend/     # React app (optional)
├── scripts/
│   ├── review_unknowns.py   # CLI to review/enroll unknowns
│   ├── setup_suricata.sh    # Suricata installation
│   └── alert_forwarder.py   # Forward IDS alerts to dashboard
├── docs/
│   ├── Suricata_integration.md
│   ├── fail2ban_setup.md
│   └── encryption.md
├── docker-compose.yml
├── requirements.txt
├── start.sh
└── README.md
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- MongoDB 4.4+ (running locally or Docker)
- Webcam/IP Camera
- Ubuntu/Debian for IDS features (optional)

### 2. Installation

#### Option A: Quick Start Script
```bash
chmod +x start.sh
./start.sh
```

#### Option B: Manual Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start MongoDB (if using Docker)
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 3. Setup Known Faces

```bash
# Add authorized face images to known_faces/
# Format: FirstName_LastName.jpg (e.g., Alice_Smith.jpg, Bob_Jones.jpg)

# Example:
cp /path/to/alice_photo.jpg known_faces/Alice_Smith.jpg
cp /path/to/bob_photo.jpg known_faces/Bob_Jones.jpg

# Sync faces to MongoDB
python src/sync_known_faces.py
```

### 4. Configuration

Edit `src/config.py` to customize:
- MongoDB connection string
- Recognition threshold
- Camera source
- Multi-frame averaging window
- Security settings

### 5. Run the System

#### Start Real-time Recognition
```bash
python src/main.py
```

#### Start Web Dashboard
```bash
python src/webapp/app.py
# Access at http://localhost:5000
```

#### Using Docker Compose (All Services)
```bash
docker-compose up -d
```

## 🎯 Features

### Core Features
- ✅ Real-time face detection and recognition
- ✅ Multi-frame averaging for robust matching
- ✅ MongoDB + GridFS for scalable storage
- ✅ Unknown face detection and review workflow
- ✅ Adaptive embedding updates (handles aging/lighting)
- ✅ Faiss index for fast similarity search (scales to 1000s)

### Security Features
- ✅ **Brute Force Protection** - Blocks IPs for 5 mins after 5 failed logins
- ✅ Suricata IDS integration (port scans, RTSP attacks)
- ✅ Fail2Ban auto-blocking (login attempts, SSH)
- ✅ Encrypted video streams (RTSP/TLS, SRT)
- ✅ Role-based dashboard access (Admin/Operator)
- ✅ Security event logging to MongoDB

### Web Dashboard
- ✅ Live camera feed (WebSocket streaming)
- ✅ Access logs with face thumbnails
- ✅ IDS alert notifications
- ✅ Unknown face review interface
- ✅ Real-time detection events

## 🔧 Configuration

### MongoDB Connection

Default: `mongodb://localhost:27017/`

Set custom URI via environment variable:
```bash
export MONGO_URI="mongodb://user:pass@host:27017/"
```

### Camera Source

In `src/config.py`:
```python
CAMERA_SOURCE = 0  # Webcam
# or
CAMERA_SOURCE = "rtsp://admin:pass@192.168.1.100:554/stream"
```

### Recognition Threshold

```python
MATCH_THRESHOLD = 0.4  # Lower = stricter (0.3-0.5 recommended)
```

### Multi-frame Averaging

```python
MULTIFRAME_COUNT = 3  # Average embeddings over N frames
```

## 📊 Database Schema

### Collections

#### `authorized_faces`
```json
{
  "_id": "ObjectId",
  "name": "Alice Smith",
  "embedding": [0.123, -0.456, ...],  // 512D vector
  "image_id": "GridFS file_id",
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

#### `face_logs`
```json
{
  "_id": "ObjectId",
  "name": "Alice Smith" | "Unknown",
  "confidence": 0.85,
  "status": "Authorized" | "Unauthorized",
  "embedding": [...],
  "image_id": "GridFS file_id",
  "camera_id": "cam_01",
  "review_flag": false,
  "timestamp": "ISODate"
}
```

## 🧪 Testing

### Test MongoDB Connection
```bash
python -c "from src.db_connection import DB; db = DB(); print(f'Connected! Auth count: {db.auth_coll.count_documents({})}')"
```

### Test Face Detection
```bash
python -c "from src.face_utils import detect_faces, get_embedding; import cv2; img = cv2.imread('known_faces/Alice.jpg'); faces = detect_faces(img); print(f'Detected {len(faces)} faces')"
```

### Test Embedding
```bash
python -c "from src.face_utils import get_embedding; import cv2; img = cv2.imread('known_faces/Alice.jpg'); emb = get_embedding(img); print(f'Embedding shape: {emb.shape}, Norm: {(emb**2).sum()**0.5:.3f}')"
```

### Simulate Unknown Detection
1. Show a different person's face to camera
2. Check MongoDB: `db.face_logs.find({status: "Unauthorized"})`
3. Review: `python scripts/review_unknowns.py`

## 🔐 Security Setup

### Suricata IDS

```bash
# Install and configure
sudo bash scripts/setup_suricata.sh

# Start alert forwarder
python scripts/alert_forwarder.py
```

See `docs/Suricata_integration.md` for details.

### Fail2Ban

```bash
# Follow setup guide
cat docs/fail2ban_setup.md

# Test ban
python -c "from src.webapp.app import app; [app.test_client().post('/login', data={'password':'wrong'}) for _ in range(6)]"

# Check status
sudo fail2ban-client status flask-auth
```

### Stream Encryption

```bash
# Setup encrypted SRT stream
ffmpeg -re -i rtsp://camera/stream -f mpegts "srt://localhost:9000?pkt_size=1316&passphrase=secretkey"

# Configure client to decrypt
# See docs/encryption.md
```

## 🐳 Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all
docker-compose down
```

Services:
- MongoDB: `localhost:27017`
- Flask Dashboard: `localhost:5000`
- Suricata: monitoring mode

## 🎨 Web Dashboard

### Default Credentials
- Username: `admin`
- Password: `changeme` (change in production!)

### Pages
- **Dashboard**: Live feed + real-time notifications
- **Access Logs**: Searchable detection history with images
- **Security Logs**: IDS alerts and threats
- **Unknown Faces**: Review and enroll new authorized users

### API Endpoints
- `POST /api/alert` - Receive IDS alerts
- `GET /api/logs` - Fetch detection logs
- `GET /api/image/<file_id>` - Retrieve face image
- `POST /api/enroll` - Add new authorized face
- `WS /socket.io` - Real-time updates

## 🔍 Troubleshooting

### Camera Not Opening
```bash
# Check available cameras
ls /dev/video*

# Test with OpenCV
python -c "import cv2; cap = cv2.VideoCapture(0); print(f'Opened: {cap.isOpened()}')"
```

### MongoDB Connection Error
```bash
# Check MongoDB is running
sudo systemctl status mongod
# or
docker ps | grep mongo
```

### Face Not Detected
- Ensure good lighting
- Face should be frontal (±30°)
- Minimum face size: 80x80 pixels
- Check `DETECTION_THRESHOLD` in config

### Low Recognition Accuracy
- Add more training images per person (3-5 recommended)
- Use multi-frame averaging (increase `MULTIFRAME_COUNT`)
- Adjust `MATCH_THRESHOLD` (lower = stricter)
- Enable preprocessing: alignment, histogram equalization

## 📈 Performance Optimization

### Fast Search with Faiss
For 100+ authorized persons:
```python
from src.search_index import build_index, query_index
# Automatically enabled when auth count > 50
```

### GPU Acceleration
Install GPU-enabled TensorFlow:
```bash
pip install tensorflow-gpu==2.15.0
```

### Reduce Frame Processing
In `src/config.py`:
```python
PROCESS_EVERY_N_FRAMES = 3  # Process every 3rd frame
```

## 📝 Development

### Add New Face Recognition Model

Edit `src/face_utils.py`:
```python
def get_embedding(face_img, model='ArcFace'):
    if model == 'ArcFace':
        # Current implementation
    elif model == 'FaceNet':
        # Add FaceNet support
```

### Custom Alert Rules

Add Suricata rules in `/etc/suricata/rules/local.rules`:
```
alert tcp any any -> $HOME_NET 554 (msg:"RTSP Brute Force"; threshold:type threshold, track by_src, count 10, seconds 60; sid:1000001;)
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

MIT License - see LICENSE file

## 🙏 Acknowledgments

- DeepFace for face recognition models
- OpenCV for computer vision
- MongoDB for scalable storage
- Suricata for network security

## 📞 Support

For issues and questions:
- GitHub Issues: [your-repo]/issues
- Documentation: `docs/`
- Email: support@smartvault.example

---

**⚠️ Security Notice**: This is a security-critical system. Always:
- Change default passwords
- Use HTTPS in production
- Enable authentication on MongoDB
- Keep dependencies updated
- Follow security best practices in `docs/`
