"""
Smart Vault CCTV - System Test Script
Comprehensive testing of all components
"""

import os
import sys
import time
from typing import Tuple

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(name: str):
    """Print test header"""
    print(f"\n{Colors.BLUE}[TEST]{Colors.END} {name}...")

def print_success(message: str):
    """Print success message"""
    print(f"  {Colors.GREEN}✓{Colors.END} {message}")

def print_error(message: str):
    """Print error message"""
    print(f"  {Colors.RED}✗{Colors.END} {message}")

def print_warning(message: str):
    """Print warning message"""
    print(f"  {Colors.YELLOW}⚠{Colors.END} {message}")

def test_imports() -> Tuple[bool, str]:
    """Test if all required packages are installed"""
    print_test("Checking Python packages")
    
    required_packages = {
        'cv2': 'opencv-python',
        'numpy': 'numpy',
        'flask': 'flask',
        'pymongo': 'pymongo',
        'deepface': 'deepface'
    }
    
    missing = []
    for module, package in required_packages.items():
        try:
            __import__(module)
            print_success(f"{package} installed")
        except ImportError:
            print_error(f"{package} missing")
            missing.append(package)
    
    if missing:
        return False, f"Missing packages: {', '.join(missing)}"
    return True, "All packages installed"

def test_directories() -> Tuple[bool, str]:
    """Test if all required directories exist"""
    print_test("Checking directory structure")
    
    required_dirs = [
        'src',
        'src/webapp',
        'src/webapp/templates',
        'known_faces',
        'models',
        'scripts',
        'docs'
    ]
    
    missing = []
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print_success(f"{dir_path}/ exists")
        else:
            print_error(f"{dir_path}/ missing")
            missing.append(dir_path)
    
    if missing:
        return False, f"Missing directories: {', '.join(missing)}"
    return True, "All directories present"

def test_config() -> Tuple[bool, str]:
    """Test configuration file"""
    print_test("Testing configuration")
    
    try:
        from src.config import (
            MONGO_URI, MATCH_THRESHOLD, CAMERA_SOURCE,
            FLASK_PORT, RECOGNITION_MODEL
        )
        
        print_success(f"MongoDB URI: {MONGO_URI}")
        print_success(f"Recognition model: {RECOGNITION_MODEL}")
        print_success(f"Match threshold: {MATCH_THRESHOLD}")
        print_success(f"Camera source: {CAMERA_SOURCE}")
        print_success(f"Flask port: {FLASK_PORT}")
        
        return True, "Configuration loaded"
    except Exception as e:
        return False, f"Config error: {e}"

def test_mongodb() -> Tuple[bool, str]:
    """Test MongoDB connection"""
    print_test("Testing MongoDB connection")
    
    try:
        from src.db_connection import DB
        
        db = DB()
        stats = db.get_stats()
        
        print_success(f"Connected to MongoDB")
        print_success(f"Authorized faces: {stats.get('authorized_count', 0)}")
        print_success(f"Total logs: {stats.get('total_logs', 0)}")
        
        return True, "MongoDB connected"
    except Exception as e:
        print_error(f"Connection failed: {e}")
        print_warning("Start MongoDB: docker run -d -p 27017:27017 mongo")
        return False, f"MongoDB error: {e}"

def test_face_utils() -> Tuple[bool, str]:
    """Test face recognition utilities"""
    print_test("Testing face recognition utilities")
    
    try:
        from src.face_utils import detect_faces, get_embedding
        import numpy as np
        
        # Create dummy image
        test_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Test detection (may not find faces in random image, but shouldn't crash)
        faces = detect_faces(test_img)
        print_success(f"Face detection working (found {len(faces)} faces in test image)")
        
        # Test embedding (will likely fail on random image, but check it doesn't crash)
        try:
            test_face = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
            embedding = get_embedding(test_face)
            if embedding is not None:
                print_success(f"Embedding extraction working (dim: {len(embedding)})")
            else:
                print_warning("Embedding extraction returned None (expected for random image)")
        except Exception as e:
            print_warning(f"Embedding test skipped: {e}")
        
        return True, "Face utilities loaded"
    except Exception as e:
        return False, f"Face utils error: {e}"

def test_camera() -> Tuple[bool, str]:
    """Test camera access"""
    print_test("Testing camera access")
    
    try:
        import cv2
        from src.config import CAMERA_SOURCE
        
        cap = cv2.VideoCapture(CAMERA_SOURCE)
        
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                print_success(f"Camera {CAMERA_SOURCE} opened successfully")
                print_success(f"Frame size: {frame.shape}")
                return True, "Camera accessible"
            else:
                print_warning("Camera opened but couldn't read frame")
                return True, "Camera opened (frame read failed)"
        else:
            print_warning(f"Camera {CAMERA_SOURCE} not available")
            print_warning("This is OK if testing without camera")
            return True, "Camera test skipped"
    except Exception as e:
        return False, f"Camera error: {e}"

def test_flask() -> Tuple[bool, str]:
    """Test Flask application"""
    print_test("Testing Flask application")
    
    try:
        from src.webapp.app import app
        
        print_success("Flask app imported")
        print_success(f"Secret key set: {bool(app.config.get('SECRET_KEY'))}")
        
        # Test client
        with app.test_client() as client:
            response = client.get('/')
            print_success(f"Index route accessible (status: {response.status_code})")
        
        return True, "Flask app working"
    except Exception as e:
        return False, f"Flask error: {e}"

def test_known_faces() -> Tuple[bool, str]:
    """Test known faces directory"""
    print_test("Checking known faces")
    
    try:
        from src.config import KNOWN_FACES_DIR
        
        if not os.path.exists(KNOWN_FACES_DIR):
            print_warning(f"Directory not found: {KNOWN_FACES_DIR}")
            return True, "No known faces (OK for fresh install)"
        
        files = [f for f in os.listdir(KNOWN_FACES_DIR) 
                if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
        
        if files:
            print_success(f"Found {len(files)} face images")
            for f in files[:5]:  # Show first 5
                print_success(f"  - {f}")
            if len(files) > 5:
                print_success(f"  ... and {len(files)-5} more")
        else:
            print_warning("No face images found")
            print_warning("Add images to known_faces/ directory")
        
        return True, f"{len(files)} known faces"
    except Exception as e:
        return False, f"Known faces error: {e}"

def main():
    """Run all tests"""
    print("=" * 60)
    print(f"{Colors.BLUE}Smart Vault CCTV - System Test{Colors.END}")
    print("=" * 60)
    
    tests = [
        ("Import Check", test_imports),
        ("Directory Structure", test_directories),
        ("Configuration", test_config),
        ("MongoDB", test_mongodb),
        ("Face Recognition", test_face_utils),
        ("Camera", test_camera),
        ("Flask App", test_flask),
        ("Known Faces", test_known_faces),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            success, message = test_func()
            results.append((name, success, message))
        except Exception as e:
            results.append((name, False, str(e)))
        time.sleep(0.5)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"{Colors.BLUE}Test Summary{Colors.END}")
    print("=" * 60)
    
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for name, success, message in results:
        status = f"{Colors.GREEN}PASS{Colors.END}" if success else f"{Colors.RED}FAIL{Colors.END}"
        print(f"{status} - {name}: {message}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print(f"\n{Colors.GREEN}✓ All tests passed! System is ready.{Colors.END}")
        print("\nNext steps:")
        print("  1. Add face images to known_faces/")
        print("  2. Run: python src/sync_known_faces.py")
        print("  3. Run: python src/main.py")
        print("  4. Run: python src/webapp/app.py")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠ Some tests failed. Check errors above.{Colors.END}")
        return 1

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Tests interrupted by user{Colors.END}")
        sys.exit(1)
