"""
Smart Vault CCTV - Flask Web Dashboard
Web interface for monitoring, access logs, IDS alerts, and face management
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from functools import wraps
import io
import base64
import cv2
import numpy as np
from PIL import Image

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, Response
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db_connection import DB
from src.unknown_handler import UnknownFaceHandler
from src.face_utils import detect_faces, get_embedding
from src.config import (
    FLASK_HOST, FLASK_PORT, FLASK_DEBUG, SECRET_KEY,
    DEFAULT_ADMIN_USER, DEFAULT_ADMIN_PASS, SESSION_TIMEOUT,
    SOCKETIO_ASYNC_MODE, SOCKETIO_CORS_ALLOWED_ORIGINS
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=SESSION_TIMEOUT)

# Enable CORS
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins=SOCKETIO_CORS_ALLOWED_ORIGINS, async_mode=SOCKETIO_ASYNC_MODE)

# Initialize database and handlers
db = DB()
unknown_handler = UnknownFaceHandler()

# In-memory user database (replace with proper DB in production)
USERS = {
    DEFAULT_ADMIN_USER: {
        'password': generate_password_hash(DEFAULT_ADMIN_PASS),
        'role': 'admin'
    }
}

# Failed login tracking for Fail2Ban integration and brute force protection
failed_logins = {}

# Brute force protection: Track failed attempts per IP
login_attempts = {}  # {ip: {'count': int, 'blocked_until': datetime, 'attempts': [timestamps]}}
MAX_LOGIN_ATTEMPTS = 5
BLOCK_DURATION_MINUTES = 5


# ==================== Authentication ====================

def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        username = session.get('username')
        if USERS.get(username, {}).get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function


def is_ip_blocked(ip_address):
    """Check if an IP address is currently blocked"""
    if ip_address not in login_attempts:
        return False, None
    
    attempt_data = login_attempts[ip_address]
    blocked_until = attempt_data.get('blocked_until')
    
    if blocked_until and datetime.now() < blocked_until:
        remaining = (blocked_until - datetime.now()).total_seconds()
        return True, remaining
    
    # Block expired, reset
    if blocked_until and datetime.now() >= blocked_until:
        login_attempts[ip_address] = {'count': 0, 'blocked_until': None, 'attempts': []}
    
    return False, None


def record_failed_login(ip_address, username):
    """Record a failed login attempt and block IP if threshold reached"""
    now = datetime.now()
    
    if ip_address not in login_attempts:
        login_attempts[ip_address] = {'count': 0, 'blocked_until': None, 'attempts': []}
    
    # Clean up old attempts (older than 15 minutes)
    login_attempts[ip_address]['attempts'] = [
        t for t in login_attempts[ip_address]['attempts'] 
        if (now - t).total_seconds() < 900
    ]
    
    # Record this attempt
    login_attempts[ip_address]['attempts'].append(now)
    login_attempts[ip_address]['count'] = len(login_attempts[ip_address]['attempts'])
    
    # Block if threshold reached
    if login_attempts[ip_address]['count'] >= MAX_LOGIN_ATTEMPTS:
        login_attempts[ip_address]['blocked_until'] = now + timedelta(minutes=BLOCK_DURATION_MINUTES)
        logger.warning(f"🔒 IP {ip_address} blocked for {BLOCK_DURATION_MINUTES} minutes after {MAX_LOGIN_ATTEMPTS} failed attempts")
        
        # Log to database for security monitoring
        try:
            db.logs_coll.insert_one({
                'event_type': 'brute_force_block',
                'ip_address': ip_address,
                'username_attempted': username,
                'attempts': login_attempts[ip_address]['count'],
                'blocked_until': login_attempts[ip_address]['blocked_until'],
                'timestamp': now
            })
        except Exception as e:
            logger.error(f"Failed to log brute force block: {e}")
        
        return True
    
    return False


def reset_login_attempts(ip_address):
    """Reset login attempts for an IP after successful login"""
    if ip_address in login_attempts:
        login_attempts[ip_address] = {'count': 0, 'blocked_until': None, 'attempts': []}


# ==================== Routes ====================

@app.route('/')
def index():
    """Redirect to dashboard or login"""
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page with brute force protection"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        ip_address = request.remote_addr
        
        # Check if IP is blocked
        is_blocked, remaining_time = is_ip_blocked(ip_address)
        if is_blocked:
            minutes = int(remaining_time // 60)
            seconds = int(remaining_time % 60)
            error_msg = f'Too many failed attempts. Your IP is blocked for {minutes}m {seconds}s'
            logger.warning(f"🔒 Blocked login attempt from {ip_address} ({username})")
            return render_template('login.html', error=error_msg, blocked=True)
        
        # Check credentials
        user = USERS.get(username)
        
        if user and check_password_hash(user['password'], password):
            # Successful login
            session['username'] = username
            session['role'] = user['role']
            session.permanent = True
            
            # Reset failed login counts
            failed_logins.pop(ip_address, None)
            reset_login_attempts(ip_address)
            
            logger.info(f"✓ Login successful: {username} from {ip_address}")
            return redirect(url_for('dashboard'))
        else:
            # Failed login
            failed_logins[ip_address] = failed_logins.get(ip_address, 0) + 1
            
            # Record failed attempt and check if should block
            was_blocked = record_failed_login(ip_address, username)
            
            if was_blocked:
                error_msg = f'Too many failed attempts. Your IP is blocked for {BLOCK_DURATION_MINUTES} minutes'
                logger.warning(f"🔒 IP {ip_address} BLOCKED after {MAX_LOGIN_ATTEMPTS} failed attempts")
                return render_template('login.html', error=error_msg, blocked=True)
            
            # Show remaining attempts
            attempts_left = MAX_LOGIN_ATTEMPTS - login_attempts[ip_address]['count']
            error_msg = f'Invalid credentials. {attempts_left} attempts remaining before block'
            
            # Log for Fail2Ban
            logger.warning(f"⚠ Login failed: {username} from {ip_address} (attempt {login_attempts[ip_address]['count']}/{MAX_LOGIN_ATTEMPTS})")
            
            return render_template('login.html', error=error_msg, attempts_left=attempts_left)
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout"""
    username = session.get('username')
    session.clear()
    logger.info(f"Logout: {username}")
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard with live feed and stats"""
    stats = db.get_stats()
    return render_template('dashboard.html', stats=stats, username=session.get('username'))


@app.route('/logs')
@login_required
def logs_page():
    """Access logs page"""
    return render_template('logs.html', username=session.get('username'))


@app.route('/security')
@login_required
def security_page():
    """Security logs and IDS alerts page"""
    return render_template('security.html', username=session.get('username'))


@app.route('/unknowns')
@login_required
def unknowns_page():
    """Unknown faces review page"""
    return render_template('unknowns.html', username=session.get('username'))


@app.route('/enroll')
@login_required
def enroll_page():
    """Face enrollment page"""
    return render_template('enroll.html', username=session.get('username'))


# ==================== API Endpoints ====================

@app.route('/api/stats')
@login_required
def api_stats():
    """Get database statistics"""
    try:
        stats = db.get_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/logs')
@login_required
def api_logs():
    """Get detection logs with filters"""
    try:
        limit = int(request.args.get('limit', 50))
        status = request.args.get('status')
        camera_id = request.args.get('camera_id')
        
        logs = db.get_detection_logs(limit=limit, status=status, camera_id=camera_id)
        
        # Convert timestamps to strings for JSON
        for log in logs:
            if 'timestamp' in log:
                log['timestamp'] = log['timestamp'].isoformat()
        
        return jsonify(logs)
    except Exception as e:
        logger.error(f"Logs API error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/image/<file_id>')
@login_required
def api_image(file_id):
    """Get face image from GridFS"""
    try:
        image_bytes = db.get_image(file_id)
        
        if image_bytes:
            return Response(image_bytes, mimetype='image/jpeg')
        else:
            return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        logger.error(f"Image API error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/authorized_persons')
@login_required
def api_authorized_persons():
    """Get all authorized persons with their details"""
    try:
        # Fetch all authorized persons from database
        persons = list(db.auth_coll.find({}))
        
        # Convert ObjectId and timestamps to strings
        for person in persons:
            person['_id'] = str(person['_id'])
            if 'image_id' in person and person['image_id'] is not None:
                person['image_id'] = str(person['image_id'])
            else:
                # If no image_id, try to use a default or skip
                person['image_id'] = None
                logger.warning(f"Person {person.get('name')} has no image_id")
            
            # Handle different date field names
            if 'enrolled_date' in person:
                person['enrolled_date'] = person['enrolled_date'].isoformat()
            elif 'added_date' in person:
                person['enrolled_date'] = person['added_date'].isoformat()
            else:
                person['enrolled_date'] = None
        
        return jsonify(persons)
    except Exception as e:
        logger.error(f"Authorized persons API error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/unknowns')
@login_required
def api_unknowns():
    """Get unknown faces for review"""
    try:
        limit = int(request.args.get('limit', 50))
        unknowns = unknown_handler.get_unknown_faces(limit=limit)
        
        # Convert timestamps
        for unknown in unknowns:
            if 'timestamp' in unknown:
                unknown['timestamp'] = unknown['timestamp'].isoformat()
        
        return jsonify(unknowns)
    except Exception as e:
        logger.error(f"Unknowns API error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/enroll', methods=['POST'])
@admin_required
def api_enroll():
    """Enroll an unknown face as authorized"""
    try:
        data = request.get_json()
        log_id = data.get('log_id')
        name = data.get('name')
        
        if not log_id or not name:
            return jsonify({'error': 'Missing log_id or name'}), 400
        
        # Sanitize name
        name = name.strip().replace(' ', '_')
        
        success = unknown_handler.enroll_unknown_as_authorized(log_id, name)
        
        if success:
            # Notify via WebSocket
            socketio.emit('face_enrolled', {'name': name, 'log_id': log_id})
            return jsonify({'success': True, 'message': f'Enrolled as {name}'})
        else:
            return jsonify({'success': False, 'error': 'Enrollment failed'}), 500
    
    except Exception as e:
        logger.error(f"Enroll API error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/dismiss', methods=['POST'])
@login_required
def api_dismiss():
    """Dismiss an unknown face"""
    try:
        data = request.get_json()
        log_id = data.get('log_id')
        
        if not log_id:
            return jsonify({'error': 'Missing log_id'}), 400
        
        success = unknown_handler.dismiss_unknown(log_id)
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False}), 500
    
    except Exception as e:
        logger.error(f"Dismiss API error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/blocked_ips')
@login_required
def api_blocked_ips():
    """Get list of currently blocked IPs"""
    try:
        blocked = []
        now = datetime.now()
        
        for ip, data in login_attempts.items():
            blocked_until = data.get('blocked_until')
            if blocked_until and now < blocked_until:
                remaining = (blocked_until - now).total_seconds()
                blocked.append({
                    'ip': ip,
                    'attempts': data['count'],
                    'blocked_until': blocked_until.strftime('%Y-%m-%d %H:%M:%S'),
                    'remaining_seconds': int(remaining)
                })
        
        return jsonify({'blocked_ips': blocked, 'count': len(blocked)})
    
    except Exception as e:
        logger.error(f"Blocked IPs API error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/alert', methods=['POST'])
def api_alert():
    """Receive IDS alerts (from Suricata forwarder)"""
    try:
        data = request.get_json()
        
        # Log alert
        logger.warning(f"IDS Alert: {data}")
        
        # Broadcast to all connected clients
        socketio.emit('security_alert', data)
        
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Alert API error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/detection', methods=['POST'])
def api_detection():
    """Receive detection event (from main.py)"""
    try:
        data = request.get_json()
        
        # Broadcast detection to connected clients
        socketio.emit('new_detection', data)
        
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Detection API error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stream_frame', methods=['POST'])
def api_stream_frame():
    """Receive video frame from main.py for live streaming"""
    try:
        data = request.get_json()
        frame_data = data.get('frame')
        
        if frame_data:
            # Broadcast frame to connected clients via WebSocket
            socketio.emit('video_frame', {'frame': frame_data})
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'No frame data'}), 400
    
    except Exception as e:
        logger.error(f"Stream frame error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze_face', methods=['POST'])
@login_required
def api_analyze_face():
    """Analyze uploaded face photo"""
    try:
        if 'photo' not in request.files:
            return jsonify({'success': False, 'error': 'No photo uploaded'}), 400
        
        file = request.files['photo']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No photo selected'}), 400
        
        # Read image
        image_bytes = file.read()
        
        # Check file size (max 10MB)
        if len(image_bytes) > 10 * 1024 * 1024:
            return jsonify({'success': False, 'error': 'Image too large. Maximum size is 10MB.'}), 400
        
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'success': False, 'error': 'Invalid image file'}), 400
        
        # Resize large images to reduce memory usage
        max_dimension = 1024
        height, width = img.shape[:2]
        if width > max_dimension or height > max_dimension:
            scale = min(max_dimension / width, max_dimension / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
            logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
        
        # Detect faces
        faces = detect_faces(img)
        
        if len(faces) == 0:
            return jsonify({
                'success': False,
                'error': 'No face detected in the image. Please upload a clear frontal face photo.'
            }), 400
        
        # Use the largest face (most prominent)
        if len(faces) > 1:
            faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)  # Sort by area (w*h)
        
        x, y, w, h = faces[0]
        
        # Validate face dimensions
        if w <= 0 or h <= 0 or x < 0 or y < 0:
            return jsonify({
                'success': False,
                'error': 'Invalid face detection. Please try another photo.'
            }), 400
        
        # Ensure coordinates are within image bounds
        img_height, img_width = img.shape[:2]
        x = max(0, min(x, img_width - 1))
        y = max(0, min(y, img_height - 1))
        w = min(w, img_width - x)
        h = min(h, img_height - y)
        
        # Crop face (x, y, w, h format)
        face_img = img[y:y+h, x:x+w]
        
        # Validate cropped image
        if face_img.size == 0 or face_img.shape[0] == 0 or face_img.shape[1] == 0:
            return jsonify({
                'success': False,
                'error': 'Failed to crop face. Please use a clearer frontal photo.'
            }), 400
        
        # Resize face
        try:
            face_img_resized = cv2.resize(face_img, (112, 112))
        except Exception as e:
            logger.error(f"Resize error: {e}, face_img shape: {face_img.shape}")
            return jsonify({
                'success': False,
                'error': 'Failed to resize face image. Please try another photo.'
            }), 400
        
        # Get embedding with error handling
        try:
            logger.info("Extracting face embedding...")
            embedding = get_embedding(face_img_resized)
            
            if embedding is None:
                return jsonify({
                    'success': False,
                    'error': 'Failed to extract face embedding. Please use a clearer photo.'
                }), 400
                
        except MemoryError:
            logger.error("MemoryError during embedding extraction")
            return jsonify({
                'success': False,
                'error': 'Out of memory. Please try a smaller image or restart the server.'
            }), 500
        except Exception as e:
            logger.error(f"Error extracting embedding: {e}")
            return jsonify({
                'success': False,
                'error': f'Embedding extraction failed: {str(e)}'
            }), 500
        
        # Convert image to base64 for storage
        _, buffer = cv2.imencode('.jpg', face_img_resized)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        logger.info(f"Face analyzed: {len(faces)} face(s) detected, embedding size: {len(embedding)}")
        
        return jsonify({
            'success': True,
            'faces_count': len(faces),
            'embedding_size': len(embedding),
            'embedding': embedding.tolist(),
            'image_data': img_base64,
            'quality': 'Good' if len(faces) == 1 else 'Multiple faces',
            'face_bbox': {'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)}
        })
    
    except Exception as e:
        logger.error(f"Face analysis error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/enroll_person', methods=['POST'])
@admin_required
def api_enroll_person():
    """Enroll a new authorized person"""
    try:
        data = request.get_json()
        
        name = data.get('name', '').strip()
        role = data.get('role', '')
        notes = data.get('notes', '')
        embedding = data.get('embedding')
        image_data = data.get('image_data')
        
        if not name:
            return jsonify({'success': False, 'error': 'Name is required'}), 400
        
        if not embedding:
            return jsonify({'success': False, 'error': 'Face embedding is required'}), 400
        
        # Sanitize name (replace spaces with underscores)
        name = name.replace(' ', '_')
        
        # Check if person already exists
        existing = db.auth_coll.find_one({'name': name})
        if existing:
            return jsonify({
                'success': False,
                'error': f'Person with name "{name}" already exists'
            }), 400
        
        # Decode image and save to GridFS
        image_id = None
        if image_data:
            try:
                image_bytes = base64.b64decode(image_data)
                image_id = db.save_image(image_bytes)
            except Exception as e:
                logger.warning(f"Failed to save image: {e}")
        
        # Add to database
        db.auth_coll.insert_one({
            'name': name,
            'embedding': embedding,
            'image_id': image_id,
            'role': role,
            'notes': notes,
            'added_date': datetime.now(),
            'added_by': session.get('username')
        })
        
        logger.info(f"New person enrolled: {name} by {session.get('username')}")
        
        # Notify via WebSocket
        socketio.emit('person_enrolled', {'name': name, 'role': role})
        
        return jsonify({
            'success': True,
            'message': f'{name} enrolled successfully',
            'name': name
        })
    
    except Exception as e:
        logger.error(f"Enrollment error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== WebSocket Events ====================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to Smart Vault CCTV'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")


@socketio.on('request_stats')
def handle_stats_request():
    """Send stats to client"""
    try:
        stats = db.get_stats()
        emit('stats_update', stats)
    except Exception as e:
        logger.error(f"Stats request error: {e}")


# ==================== Error Handlers ====================

@app.errorhandler(404)
def not_found(e):
    """404 error handler"""
    return render_template('error.html', error='Page not found', code=404), 404


@app.errorhandler(500)
def server_error(e):
    """500 error handler"""
    logger.error(f"Server error: {e}")
    return render_template('error.html', error='Internal server error', code=500), 500


# ==================== Main ====================

def main():
    """Run Flask app"""
    logger.info("=" * 60)
    logger.info("  Smart Vault CCTV - Web Dashboard")
    logger.info("=" * 60)
    logger.info(f"Host: {FLASK_HOST}")
    logger.info(f"Port: {FLASK_PORT}")
    logger.info(f"Debug: {FLASK_DEBUG}")
    logger.info("=" * 60)
    logger.info(f"\nAccess dashboard at: http://localhost:{FLASK_PORT}")
    logger.info(f"Default credentials: {DEFAULT_ADMIN_USER} / {DEFAULT_ADMIN_PASS}")
    logger.info("\n⚠ CHANGE DEFAULT PASSWORD IN PRODUCTION!\n")
    
    try:
        socketio.run(app, host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG, allow_unsafe_werkzeug=True)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")


if __name__ == '__main__':
    main()
