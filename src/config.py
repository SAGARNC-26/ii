"""
Smart Vault CCTV - Configuration Settings
Centralized configuration for all system components
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ===========================
# MongoDB Configuration
# ===========================
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = 'smart_vault_cctv'
AUTH_COLLECTION = 'authorized_faces'
LOGS_COLLECTION = 'face_logs'
GRIDFS_BUCKET = 'face_images'

# ===========================
# Camera Configuration
# ===========================
# Camera source: 0 for webcam, or RTSP URL for IP camera
CAMERA_SOURCE = int(os.getenv('CAMERA_SOURCE', 0)) if os.getenv('CAMERA_SOURCE', '0').isdigit() else os.getenv('CAMERA_SOURCE', 0)
CAMERA_ID = os.getenv('CAMERA_ID', 'cam_01')
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_FPS = 30

# ===========================
# Face Recognition Configuration
# ===========================
# Model selection: 'ArcFace', 'Facenet', 'VGG-Face', 'DeepFace', 'OpenFace'
RECOGNITION_MODEL = os.getenv('RECOGNITION_MODEL', 'ArcFace')

# Detection backend: 'opencv', 'ssd', 'mtcnn', 'retinaface'
DETECTION_BACKEND = os.getenv('DETECTION_BACKEND', 'opencv')

# Similarity threshold (0.0 - 1.0, lower = stricter)
# ArcFace recommended: 0.3-0.5
# Facenet recommended: 0.4-0.6
MATCH_THRESHOLD = float(os.getenv('MATCH_THRESHOLD', 0.40))

# Minimum face detection confidence
DETECTION_CONFIDENCE = 0.9

# Minimum face size (pixels)
MIN_FACE_SIZE = 80

# ===========================
# Multi-frame Averaging
# ===========================
# Number of frames to average for robust recognition
MULTIFRAME_COUNT = int(os.getenv('MULTIFRAME_COUNT', 3))

# Maximum frames to buffer
MAX_FRAME_BUFFER = 10

# ===========================
# Performance Configuration
# ===========================
# Process every Nth frame (reduce CPU usage)
PROCESS_EVERY_N_FRAMES = int(os.getenv('PROCESS_EVERY_N_FRAMES', 2))

# Enable GPU acceleration (requires tensorflow-gpu)
USE_GPU = os.getenv('USE_GPU', 'false').lower() == 'true'

# Use Faiss for fast search when authorized count exceeds this threshold
FAISS_THRESHOLD = int(os.getenv('FAISS_THRESHOLD', 50))

# ===========================
# Face Preprocessing
# ===========================
# Target face size for alignment
FACE_SIZE = (112, 112)

# Enable histogram equalization
ENABLE_HISTOGRAM_EQ = True

# Enable gamma correction
ENABLE_GAMMA_CORRECTION = True
GAMMA_VALUE = 1.2

# ===========================
# Augmentation Settings
# ===========================
# Enable augmentation when adding known faces
ENABLE_AUGMENTATION = False  # Disabled to avoid scipy memory issues

# Augmentation parameters
AUG_BRIGHTNESS_RANGE = (0.8, 1.2)
AUG_ROTATION_RANGE = (-10, 10)  # degrees
AUG_SAMPLES_PER_IMAGE = 3

# ===========================
# Adaptive Embedding Update
# ===========================
# Enable adaptive embedding updates over time
ENABLE_ADAPTIVE_UPDATE = True

# Running average weight (0.0 - 1.0)
# new_embedding = old * (1 - alpha) + new * alpha
ADAPTIVE_ALPHA = 0.1

# Update frequency (update every N successful recognitions)
ADAPTIVE_UPDATE_FREQUENCY = 10

# ===========================
# Web Dashboard Configuration
# ===========================
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

# Secret key for session management (CHANGE IN PRODUCTION!)
SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-secret-key-in-production')

# Session timeout (minutes)
SESSION_TIMEOUT = 30

# Default admin credentials (CHANGE IN PRODUCTION!)
DEFAULT_ADMIN_USER = os.getenv('ADMIN_USER', 'admin')
DEFAULT_ADMIN_PASS = os.getenv('ADMIN_PASS', 'changeme')

# ===========================
# WebSocket Configuration
# ===========================
SOCKETIO_ASYNC_MODE = 'threading'
SOCKETIO_CORS_ALLOWED_ORIGINS = '*'

# ===========================
# Unknown Face Handling
# ===========================
# Save unknown faces for review
SAVE_UNKNOWN_FACES = True

# Minimum confidence to save unknown face
UNKNOWN_MIN_CONFIDENCE = 0.5

# Auto-review threshold (faces with similarity > this but < MATCH_THRESHOLD)
AUTO_REVIEW_THRESHOLD = MATCH_THRESHOLD - 0.1

# ===========================
# Logging Configuration
# ===========================
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Log file path
LOG_FILE = 'smart_vault.log'

# Log format
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# ===========================
# Security Configuration
# ===========================
# Enable Fail2Ban integration
ENABLE_FAIL2BAN = os.getenv('ENABLE_FAIL2BAN', 'false').lower() == 'true'

# Login attempt limit
MAX_LOGIN_ATTEMPTS = 5

# Ban duration (seconds)
BAN_DURATION = 3600  # 1 hour

# Whitelisted IPs (never ban)
WHITELISTED_IPS = os.getenv('WHITELISTED_IPS', '127.0.0.1,::1').split(',')

# ===========================
# Suricata IDS Configuration
# ===========================
# Enable Suricata alert forwarding
ENABLE_SURICATA = os.getenv('ENABLE_SURICATA', 'false').lower() == 'true'

# Suricata alert log path
SURICATA_ALERT_LOG = os.getenv('SURICATA_ALERT_LOG', '/var/log/suricata/fast.log')

# Dashboard alert endpoint
ALERT_ENDPOINT = 'http://localhost:5000/api/alert'

# ===========================
# Stream Encryption
# ===========================
# Enable encrypted streams
ENABLE_ENCRYPTION = os.getenv('ENABLE_ENCRYPTION', 'false').lower() == 'true'

# SRT passphrase (if using SRT encryption)
SRT_PASSPHRASE = os.getenv('SRT_PASSPHRASE', '')

# ===========================
# Email Alert Configuration
# ===========================
# Enable email alerts for unauthorized detections
ENABLE_EMAIL_ALERTS = os.getenv('ENABLE_EMAIL_ALERTS', 'true').lower() == 'true'

# Email credentials
EMAIL_SENDER = os.getenv('EMAIL_SENDER', 'sagarnc199@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')  # Gmail App Password
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT', 'sagarnc26@gamil.com')

# SMTP settings (Gmail)
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))

# Alert cooldown (seconds) - don't spam emails
EMAIL_COOLDOWN = int(os.getenv('EMAIL_COOLDOWN', 300))  # 5 minutes

# Include snapshot in email
EMAIL_INCLUDE_SNAPSHOT = os.getenv('EMAIL_INCLUDE_SNAPSHOT', 'true').lower() == 'true'

# ===========================
# File Paths
# ===========================
KNOWN_FACES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'known_faces')
MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')

# ===========================
# Development/Testing
# ===========================
# Enable debug visualization
SHOW_DEBUG_WINDOW = os.getenv('SHOW_DEBUG_WINDOW', 'true').lower() == 'true'

# Save detection snapshots
SAVE_SNAPSHOTS = os.getenv('SAVE_SNAPSHOTS', 'false').lower() == 'true'
SNAPSHOTS_DIR = 'snapshots'

# Test mode (mock camera with static image)
TEST_MODE = os.getenv('TEST_MODE', 'false').lower() == 'true'
TEST_IMAGE_PATH = os.getenv('TEST_IMAGE_PATH', '')

# ===========================
# Validation
# ===========================
def validate_config():
    """Validate configuration settings"""
    errors = []
    
    if MATCH_THRESHOLD < 0 or MATCH_THRESHOLD > 1:
        errors.append(f"MATCH_THRESHOLD must be between 0 and 1, got {MATCH_THRESHOLD}")
    
    if MULTIFRAME_COUNT < 1:
        errors.append(f"MULTIFRAME_COUNT must be >= 1, got {MULTIFRAME_COUNT}")
    
    if not os.path.exists(KNOWN_FACES_DIR):
        os.makedirs(KNOWN_FACES_DIR)
    
    if not os.path.exists(MODELS_DIR):
        os.makedirs(MODELS_DIR)
    
    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(errors))

# Run validation on import
validate_config()

# ===========================
# Helper Functions
# ===========================
def get_config_summary():
    """Return a summary of current configuration"""
    return {
        'MongoDB': MONGO_URI,
        'Camera': CAMERA_SOURCE,
        'Model': RECOGNITION_MODEL,
        'Threshold': MATCH_THRESHOLD,
        'Multi-frame': MULTIFRAME_COUNT,
        'Faiss Enabled': 'Auto (based on count)',
        'Adaptive Update': ENABLE_ADAPTIVE_UPDATE,
    }

if __name__ == '__main__':
    print("Smart Vault CCTV - Configuration Summary")
    print("=" * 50)
    for key, value in get_config_summary().items():
        print(f"{key:20s}: {value}")
    print("=" * 50)
    print(f"Known faces directory: {KNOWN_FACES_DIR}")
    print(f"Models directory: {MODELS_DIR}")
