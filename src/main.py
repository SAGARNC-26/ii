"""
Smart Vault CCTV - Real-time Face Recognition Main Loop
Core application for live face detection and recognition with MongoDB logging
"""

import os
import sys
import cv2
import numpy as np
import logging
from datetime import datetime
from collections import deque
from typing import Dict, List, Tuple, Optional
import time
import base64
import requests

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db_connection import DB
from src.face_utils import detect_faces, align_and_crop, get_embedding, cosine_similarity
from src.search_index import get_search_index, should_use_faiss
from src.email_alert import get_email_system
from src.config import (
    CAMERA_SOURCE, CAMERA_ID, CAMERA_WIDTH, CAMERA_HEIGHT,
    MATCH_THRESHOLD, MULTIFRAME_COUNT, PROCESS_EVERY_N_FRAMES,
    SHOW_DEBUG_WINDOW, SAVE_UNKNOWN_FACES, UNKNOWN_MIN_CONFIDENCE,
    AUTO_REVIEW_THRESHOLD, ENABLE_ADAPTIVE_UPDATE, ADAPTIVE_ALPHA,
    ADAPTIVE_UPDATE_FREQUENCY
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FaceRecognitionSystem:
    """
    Real-time face recognition system with multi-frame averaging and adaptive updates.
    """
    
    def __init__(self):
        """Initialize the recognition system"""
        logger.info("Initializing Smart Vault CCTV System...")
        logger.info("=" * 60)
        
        # Database connection
        self.db = DB()
        
        # Email alert system
        self.email_system = get_email_system()
        
        # Initialize caches first
        self.authorized_cache = {}
        self.recognition_counts = {}  # name -> count
        
        # Load authorized faces
        self.load_authorized_faces()
        
        # Faiss index for fast search (if applicable)
        self.search_index = None
        self.use_faiss = should_use_faiss(len(self.authorized_cache))
        if self.use_faiss:
            self._init_faiss_index()
        
        # Multi-frame buffers
        self.frame_buffers = {}  # track_id -> deque of embeddings
        
        # Performance tracking
        self.frame_count = 0
        self.fps = 0
        self.last_fps_update = time.time()
        
        # Camera
        self.camera = None
        
        # Streaming
        self.stream_enabled = True
        self.stream_url = 'http://localhost:5000/api/stream_frame'
        self.last_stream_time = 0
        self.stream_interval = 0.1  # Stream every 100ms (10 fps)
        
        logger.info("=" * 60)
        logger.info("✓ System initialized successfully")
    
    def load_authorized_faces(self):
        """Load authorized faces from database into memory cache"""
        logger.info("Loading authorized faces from database...")
        
        try:
            authorized_faces = self.db.get_all_authorized()
            
            if not authorized_faces:
                logger.warning("⚠ No authorized faces found in database!")
                logger.info("Please run: python src/sync_known_faces.py")
                return
            
            for face in authorized_faces:
                name = face['name']
                embedding = face['embedding']
                self.authorized_cache[name] = embedding
                self.recognition_counts[name] = 0
            
            logger.info(f"✓ Loaded {len(self.authorized_cache)} authorized faces")
            
        except Exception as e:
            logger.error(f"✗ Failed to load authorized faces: {e}")
            raise
    
    def _init_faiss_index(self):
        """Initialize Faiss index for fast search"""
        try:
            logger.info("Building Faiss index for fast search...")
            
            names = list(self.authorized_cache.keys())
            embeddings = [self.authorized_cache[name] for name in names]
            
            self.search_index = get_search_index(dimension=len(embeddings[0]))
            if self.search_index:
                self.search_index.build_index(embeddings, names, index_type='IP')
                logger.info("✓ Faiss index built")
            
        except Exception as e:
            logger.warning(f"Faiss index initialization failed: {e}")
            self.use_faiss = False
    
    def init_camera(self):
        """Initialize camera capture"""
        logger.info(f"Opening camera: {CAMERA_SOURCE}")
        
        try:
            self.camera = cv2.VideoCapture(CAMERA_SOURCE)
            
            if not self.camera.isOpened():
                raise RuntimeError("Failed to open camera")
            
            # Set camera properties
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            
            logger.info("✓ Camera initialized")
            
        except Exception as e:
            logger.error(f"✗ Camera initialization failed: {e}")
            raise
    
    def recognize_face(self, embedding: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Recognize a face by comparing embedding to authorized faces.
        
        Args:
            embedding: Face embedding to recognize
        
        Returns:
            (name, confidence) or (None, max_confidence)
        """
        if not self.authorized_cache:
            return None, 0.0
        
        try:
            if self.use_faiss and self.search_index:
                # Use Faiss for fast search
                results = self.search_index.query_index(embedding, k=1)
                if results:
                    name, similarity = results[0]
                    return (name, similarity) if similarity >= MATCH_THRESHOLD else (None, similarity)
            else:
                # Linear search
                best_match = None
                best_similarity = 0.0
                
                for name, auth_embedding in self.authorized_cache.items():
                    similarity = cosine_similarity(embedding, auth_embedding)
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        if similarity >= MATCH_THRESHOLD:
                            best_match = name
                
                return best_match, best_similarity
            
        except Exception as e:
            logger.error(f"Recognition error: {e}")
            return None, 0.0
        
        return None, 0.0
    
    def multi_frame_recognize(self, face_id: int, embedding: np.ndarray) -> Tuple[Optional[str], float]:
        """
        Perform multi-frame averaging for robust recognition.
        
        Args:
            face_id: Unique face tracking ID
            embedding: Current frame embedding
        
        Returns:
            (name, confidence) tuple
        """
        # Initialize buffer for this face
        if face_id not in self.frame_buffers:
            self.frame_buffers[face_id] = deque(maxlen=MULTIFRAME_COUNT)
        
        # Add current embedding
        self.frame_buffers[face_id].append(embedding)
        
        # Average embeddings
        averaged_embedding = np.mean(list(self.frame_buffers[face_id]), axis=0)
        averaged_embedding = averaged_embedding / np.linalg.norm(averaged_embedding)
        
        # Recognize with averaged embedding
        return self.recognize_face(averaged_embedding)
    
    def update_adaptive_embedding(self, name: str, new_embedding: np.ndarray):
        """
        Adaptively update embedding over time (handles aging, lighting changes).
        
        Args:
            name: Person name
            new_embedding: New observed embedding
        """
        if not ENABLE_ADAPTIVE_UPDATE:
            return
        
        try:
            # Increment recognition count
            self.recognition_counts[name] = self.recognition_counts.get(name, 0) + 1
            
            # Update every N recognitions
            if self.recognition_counts[name] % ADAPTIVE_UPDATE_FREQUENCY == 0:
                old_embedding = self.authorized_cache[name]
                
                # Running average: new = old * (1-α) + new * α
                updated_embedding = old_embedding * (1 - ADAPTIVE_ALPHA) + new_embedding * ADAPTIVE_ALPHA
                updated_embedding = updated_embedding / np.linalg.norm(updated_embedding)
                
                # Update cache
                self.authorized_cache[name] = updated_embedding
                
                # Update database
                self.db.update_authorized_embedding(name, updated_embedding)
                
                # Update Faiss index if using
                if self.use_faiss and self.search_index:
                    self.search_index.update_embedding(name, updated_embedding)
                
                logger.debug(f"Adaptive update for {name} (count: {self.recognition_counts[name]})")
                
        except Exception as e:
            logger.error(f"Adaptive update error: {e}")
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Process a single frame: detect, recognize, and annotate.
        
        Args:
            frame: Input frame (BGR)
        
        Returns:
            Annotated frame
        """
        # Detect faces
        faces = detect_faces(frame)
        
        # Process each detected face
        for i, bbox in enumerate(faces):
            x, y, w, h = bbox
            
            # Align and crop
            face_img = align_and_crop(frame, bbox)
            if face_img is None:
                continue
            
            # Get embedding
            embedding = get_embedding(face_img)
            if embedding is None:
                continue
            
            # Multi-frame recognition
            face_id = hash((x, y, w, h)) % 10000  # Simple tracking ID
            name, confidence = self.multi_frame_recognize(face_id, embedding)
            
            # Determine status
            if name:
                status = "Authorized"
                color = (0, 255, 0)  # Green
                label = f"{name.replace('_', ' ')}: {confidence:.2f}"
                
                # Adaptive update
                self.update_adaptive_embedding(name, embedding)
                
            else:
                status = "Unauthorized"
                color = (0, 0, 255)  # Red
                label = f"Unknown: {confidence:.2f}"
                
                # Send email alert for unauthorized person
                try:
                    self.email_system.send_alert(
                        camera_id=CAMERA_ID,
                        confidence=confidence,
                        frame=face_img,  # Send cropped face image
                        location="Main Entrance"
                    )
                except Exception as e:
                    logger.error(f"Failed to send email alert: {e}")
                
                # Handle unknown face
                if SAVE_UNKNOWN_FACES and confidence >= UNKNOWN_MIN_CONFIDENCE:
                    review_flag = confidence >= AUTO_REVIEW_THRESHOLD
                    self._save_unknown_face(face_img, embedding, confidence, review_flag)
            
            # Save detection log to database
            try:
                _, face_bytes = cv2.imencode('.jpg', face_img)
                self.db.save_detection_log(
                    name=name or "Unknown",
                    confidence=confidence,
                    status=status,
                    embedding=embedding,
                    image_bytes=face_bytes.tobytes(),
                    camera_id=CAMERA_ID,
                    review_flag=(status == "Unauthorized" and confidence >= AUTO_REVIEW_THRESHOLD)
                )
            except Exception as e:
                logger.debug(f"Log save error: {e}")
            
            # Draw bounding box and label
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
            # Draw label background
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(frame, (x, y - label_size[1] - 10), (x + label_size[0], y), color, -1)
            
            # Draw label text
            cv2.putText(frame, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def _save_unknown_face(self, face_img: np.ndarray, embedding: np.ndarray, 
                          confidence: float, review_flag: bool):
        """Save unknown face for later review"""
        try:
            _, face_bytes = cv2.imencode('.jpg', face_img)
            self.db.save_detection_log(
                name="Unknown",
                confidence=confidence,
                status="Unauthorized",
                embedding=embedding,
                image_bytes=face_bytes.tobytes(),
                camera_id=CAMERA_ID,
                review_flag=review_flag
            )
        except Exception as e:
            logger.debug(f"Log save error: {e}")
            
        # Draw bounding box and label
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            
        # Draw label background
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
        cv2.rectangle(frame, (x, y - label_size[1] - 10), (x + label_size[0], y), color, -1)
            
        # Draw label text
        cv2.putText(frame, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def update_fps(self):
        """Update FPS counter"""
        self.frame_count += 1
        current_time = time.time()
        
        if current_time - self.last_fps_update >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_fps_update = time.time()
    
    def stream_frame(self, frame):
        """Send frame to Flask dashboard for live streaming"""
        current_time = time.time()
        
        # Throttle streaming to avoid overload
        if current_time - self.last_stream_time < self.stream_interval:
            return
        
        try:
            # Encode frame to JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            
            # Convert to base64
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            
            # Send to Flask server (non-blocking)
            requests.post(
                self.stream_url,
                json={'frame': frame_base64},
                timeout=0.1
            )
            
            self.last_stream_time = current_time
            
        except Exception:
            # Silently fail to avoid disrupting main loop
            pass
    
    def run(self):
        """Main loop: capture, process, display"""
        logger.info("\nStarting face recognition...")
        logger.info("Press 'q' to quit, 'r' to reload authorized faces")
        logger.info("=" * 60)
        
        # Initialize camera
        self.init_camera()
        
        frame_counter = 0
        
        try:
            while True:
                # Capture frame
                ret, frame = self.camera.read()
                
                if not ret:
                    logger.error("Failed to capture frame")
                    break
                
                # Process every Nth frame
                if frame_counter % PROCESS_EVERY_N_FRAMES == 0:
                    annotated_frame = self.process_frame(frame)
                else:
                    annotated_frame = frame
                
                frame_counter += 1
                
                # Update FPS
                self.update_fps()
                
                # Stream frame to dashboard
                if self.stream_enabled:
                    self.stream_frame(annotated_frame)
                
                # Draw FPS and stats
                if SHOW_DEBUG_WINDOW:
                    cv2.putText(annotated_frame, f"FPS: {self.fps}", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(annotated_frame, f"Authorized: {len(self.authorized_cache)}", (10, 70),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    
                    # Show frame
                    cv2.imshow('Smart Vault CCTV', annotated_frame)
                
                # Handle key press
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    logger.info("Quit signal received")
                    break
                elif key == ord('r'):
                    logger.info("Reloading authorized faces...")
                    self.load_authorized_faces()
                    if self.use_faiss:
                        self._init_faiss_index()
                
        except KeyboardInterrupt:
            logger.info("\nInterrupted by user")
        except Exception as e:
            logger.error(f"Runtime error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        logger.info("\nCleaning up...")
        
        if self.camera:
            self.camera.release()
        
        cv2.destroyAllWindows()
        
        # Print stats
        stats = self.db.get_stats()
        logger.info("\nSession Statistics:")
        logger.info(f"  Total detections: {stats.get('total_logs', 0)}")
        logger.info(f"  Authorized: {stats.get('authorized_logs', 0)}")
        logger.info(f"  Unauthorized: {stats.get('unauthorized_logs', 0)}")
        logger.info(f"  Pending review: {stats.get('pending_review', 0)}")
        
        logger.info("\n✓ System shutdown complete")


def main():
    """Main entry point"""
    try:
        system = FaceRecognitionSystem()
        system.run()
    except Exception as e:
        logger.error(f"System error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
