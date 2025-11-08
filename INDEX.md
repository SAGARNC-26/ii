# Smart Vault CCTV - File Index

Quick reference to all project files and their purposes.

## 📄 Root Level

| File | Purpose |
|------|---------|
| `README.md` | **START HERE** - Complete project documentation |
| `QUICKSTART.md` | 5-minute setup guide |
| `PROJECT_SUMMARY.md` | Deliverables checklist and overview |
| `CHANGELOG.md` | Version history and release notes |
| `LICENSE` | MIT License |
| `requirements.txt` | Python dependencies |
| `start.sh` | Automated installation script (Linux/macOS) |
| `test_system.py` | System test suite |
| `docker-compose.yml` | Docker orchestration |
| `Dockerfile.flask` | Flask app container |
| `Dockerfile.forwarder` | Alert forwarder container |
| `.env.example` | Environment variables template |
| `.gitignore` | Git ignore patterns |

## 📁 src/ - Core Application

| File | Purpose |
|------|---------|
| `config.py` | **Configuration hub** - All settings |
| `main.py` | **Main application** - Real-time recognition loop |
| `db_connection.py` | MongoDB + GridFS wrapper |
| `face_utils.py` | Face detection, alignment, embedding |
| `augmentation.py` | Image preprocessing and augmentation |
| `search_index.py` | Faiss fast search implementation |
| `sync_known_faces.py` | Sync faces from filesystem to DB |
| `unknown_handler.py` | Unknown face management |

## 📁 src/webapp/ - Web Dashboard

| File | Purpose |
|------|---------|
| `app.py` | Flask server + API + WebSocket |
| `templates/base.html` | Base template with navigation |
| `templates/login.html` | Login page |
| `templates/dashboard.html` | Main dashboard with stats |
| `templates/logs.html` | Access logs page |
| `templates/security.html` | Security logs and IDS alerts |
| `templates/unknowns.html` | Unknown face review interface |
| `templates/error.html` | Error page template |

## 📁 scripts/ - Utility Scripts

| File | Purpose |
|------|---------|
| `setup_suricata.sh` | **Automated Suricata installation** |
| `alert_forwarder.py` | Forward Suricata alerts to dashboard |
| `review_unknowns.py` | **CLI tool to review unknown faces** |

## 📁 docs/ - Documentation

| File | Purpose |
|------|---------|
| `Suricata_integration.md` | **IDS setup guide** (installation, rules, testing) |
| `fail2ban_setup.md` | **Auto-blocking guide** (config, jails, testing) |
| `encryption.md` | **Stream security guide** (RTSPS, SRT, VPN) |

## 📁 known_faces/ - Training Data

| File | Purpose |
|------|---------|
| `README.md` | Instructions for adding face images |
| `*.jpg` | Authorized face images (format: FirstName_LastName.jpg) |

## 📁 models/ - AI Models

| File | Purpose |
|------|---------|
| `README.md` | Model download and management info |
| `*.h5` | Model weights (auto-downloaded by DeepFace) |

## 🎯 Quick Navigation

### Getting Started
1. `README.md` - Full documentation
2. `QUICKSTART.md` - Fast setup
3. `requirements.txt` - Install dependencies
4. `src/config.py` - Configure system

### Main Components
- **Recognition Engine**: `src/main.py`
- **Web Dashboard**: `src/webapp/app.py`
- **Database**: `src/db_connection.py`
- **Face AI**: `src/face_utils.py`

### Security Setup
- **IDS**: `docs/Suricata_integration.md` + `scripts/setup_suricata.sh`
- **Fail2Ban**: `docs/fail2ban_setup.md`
- **Encryption**: `docs/encryption.md`

### Management Tools
- **Sync Faces**: `src/sync_known_faces.py`
- **Review Unknowns**: `scripts/review_unknowns.py`
- **Test System**: `test_system.py`

### Deployment
- **Docker**: `docker-compose.yml`
- **Config**: `.env.example` → `.env`

## 📊 File Count Summary

- **Python Files**: 10 core + 3 scripts = 13
- **HTML Templates**: 7
- **Documentation**: 7 (including README, guides)
- **Configuration**: 5 (docker, env, requirements, etc.)
- **Total**: 35+ files

## 🔍 Finding Things

### "How do I..."

- **Change camera source?** → `src/config.py` (CAMERA_SOURCE)
- **Adjust recognition threshold?** → `src/config.py` (MATCH_THRESHOLD)
- **Add a new user?** → Add photo to `known_faces/`, run `sync_known_faces.py`
- **Review unknown faces?** → `scripts/review_unknowns.py` or dashboard
- **Setup IDS?** → `docs/Suricata_integration.md`
- **Enable encryption?** → `docs/encryption.md`
- **Deploy with Docker?** → `docker-compose up -d`
- **Test the system?** → `python test_system.py`

### "What does X do?"

- **main.py**: Real-time face recognition loop
- **app.py**: Web dashboard server
- **db_connection.py**: Database operations
- **face_utils.py**: AI face recognition
- **sync_known_faces.py**: Import faces to database
- **alert_forwarder.py**: Bridge Suricata → Dashboard
- **review_unknowns.py**: Manage unknown detections

## 🎓 Learning Path

1. **Beginner**: Start with `QUICKSTART.md`
2. **Understanding**: Read `README.md` architecture section
3. **Customizing**: Edit `src/config.py`
4. **Security**: Follow docs in `docs/`
5. **Advanced**: Study source code in `src/`

## 📞 Need Help?

- **Setup Issues**: `QUICKSTART.md` troubleshooting
- **Configuration**: `src/config.py` comments
- **API Reference**: `src/webapp/app.py` docstrings
- **Security**: `docs/` folder guides
- **Testing**: `test_system.py` for diagnostics

---

**Pro Tip**: Use `grep -r "search_term" src/` to find code references quickly!
