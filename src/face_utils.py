"""
Smart Vault CCTV - Face Recognition Utilities
Provides functions for face detection, alignment, embedding extraction, and comparison
"""

import logging
import cv2
import numpy as np
from typing import List, Tuple, Optional
from deepface import DeepFace

from src.config import (
    RECOGNITION_MODEL, DETECTION_BACKEND, FACE_SIZE, 
    MIN_FACE_SIZE, DETECTION_CONFIDENCE,
    ENABLE_HISTOGRAM_EQ, ENABLE_GAMMA_CORRECTION, GAMMA_VALUE
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FaceUtils:
    """
    Face recognition utilities for Smart Vault CCTV system.
    Provides optimized functions for single-face detection and recognition.
    """
    
    def __init__(self):
        """Initialize face recognition components"""
        self.model_name = RECOGNITION_MODEL
        self.detector_backend = DETECTION_BACKEND
        self.target_size = FACE_SIZE
        
        logger.info(f"Initializing Face Recognition: {self.model_name} with {self.detector_backend}")
        
        # Pre-load model for faster inference
        try:
            self._warmup_model()
            logger.info("✓ Face recognition model loaded")
        except Exception as e:
            logger.warning(f"Model warmup failed: {e}")
    
    def _warmup_model(self):
        """Pre-load the model with a dummy image"""
        dummy = np.zeros((112, 112, 3), dtype=np.uint8)
        try:
            DeepFace.represent(
                img_path=dummy,
                model_name=self.model_name,
                detector_backend='skip',
                enforce_detection=False
            )
        except:
            pass
    
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect faces in a frame and return bounding boxes.
        
        Args:
            frame: Input image (BGR format)
        
        Returns:
            List of bounding boxes as (x, y, w, h) tuples
        """
        try:
            # Use DeepFace's detector
            face_objs = DeepFace.extract_faces(
                img_path=frame,
                detector_backend=self.detector_backend,
                enforce_detection=False,
                align=False
            )
            
            bboxes = []
            for face_obj in face_objs:
                facial_area = face_obj.get('facial_area', {})
                if facial_area:
                    x = facial_area.get('x', 0)
                    y = facial_area.get('y', 0)
                    w = facial_area.get('w', 0)
                    h = facial_area.get('h', 0)
                    
                    # Filter by minimum size
                    if w >= MIN_FACE_SIZE and h >= MIN_FACE_SIZE:
                        # Check confidence if available
                        confidence = face_obj.get('confidence', 1.0)
                        if confidence >= DETECTION_CONFIDENCE:
                            bboxes.append((x, y, w, h))
            
            return bboxes
            
        except Exception as e:
            logger.debug(f"Detection error: {e}")
            return []
    
    def align_and_crop(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
        """
        Align and crop a face from a frame given its bounding box.
        
        Args:
            frame: Input image (BGR format)
            bbox: Bounding box as (x, y, w, h)
        
        Returns:
            Aligned face image resized to target size, or None if failed
        """
        try:
            x, y, w, h = bbox
            
            # Add padding
            padding = int(max(w, h) * 0.2)
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(frame.shape[1], x + w + padding)
            y2 = min(frame.shape[0], y + h + padding)
            
            # Crop face region
            face_img = frame[y1:y2, x1:x2]
            
            if face_img.size == 0:
                return None
            
            # Resize to target size
            face_img = cv2.resize(face_img, self.target_size)
            
            # Apply preprocessing
            face_img = self._preprocess_face(face_img)
            
            return face_img
            
        except Exception as e:
            logger.debug(f"Align/crop error: {e}")
            return None
    
    def _preprocess_face(self, face_img: np.ndarray) -> np.ndarray:
        """
        Apply preprocessing to face image for better recognition.
        
        Args:
            face_img: Face image (BGR format)
        
        Returns:
            Preprocessed face image
        """
        try:
            # Convert to grayscale for preprocessing, then back to BGR
            if ENABLE_HISTOGRAM_EQ:
                # Histogram equalization on Y channel (YCrCb color space)
                ycrcb = cv2.cvtColor(face_img, cv2.COLOR_BGR2YCrCb)
                ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
                face_img = cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
            
            if ENABLE_GAMMA_CORRECTION:
                # Gamma correction for lighting normalization
                inv_gamma = 1.0 / GAMMA_VALUE
                table = np.array([((i / 255.0) ** inv_gamma) * 255
                                 for i in np.arange(0, 256)]).astype("uint8")
                face_img = cv2.LUT(face_img, table)
            
            return face_img
            
        except Exception as e:
            logger.debug(f"Preprocessing error: {e}")
            return face_img
    
    def get_embedding(self, face_img: np.ndarray, model: str = None) -> Optional[np.ndarray]:
        """
        Extract face embedding vector from a face image.
        
        Args:
            face_img: Aligned face image (BGR format)
            model: Model name (default: from config)
        
        Returns:
            Normalized embedding vector (numpy array) or None if failed
        """
        try:
            model_name = model or self.model_name
            
            # Get embedding using DeepFace
            embedding_objs = DeepFace.represent(
                img_path=face_img,
                model_name=model_name,
                detector_backend='skip',  # Face already detected and cropped
                enforce_detection=False
            )
            
            if not embedding_objs:
                return None
            
            # Extract embedding vector
            embedding = np.array(embedding_objs[0]['embedding'])
            
            # Normalize to unit vector
            embedding = self._normalize_embedding(embedding)
            
            return embedding
            
        except Exception as e:
            logger.debug(f"Embedding extraction error: {e}")
            return None
    
    def _normalize_embedding(self, embedding: np.ndarray) -> np.ndarray:
        """
        Normalize embedding to unit vector (L2 normalization).
        
        Args:
            embedding: Embedding vector
        
        Returns:
            Normalized embedding
        """
        norm = np.linalg.norm(embedding)
        if norm == 0:
            return embedding
        return embedding / norm
    
    def cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            emb1: First embedding vector
            emb2: Second embedding vector
        
        Returns:
            Similarity score (0.0 to 1.0, higher is more similar)
        """
        try:
            # Ensure embeddings are numpy arrays
            emb1 = np.array(emb1)
            emb2 = np.array(emb2)
            
            # Normalize if not already
            emb1 = self._normalize_embedding(emb1)
            emb2 = self._normalize_embedding(emb2)
            
            # Cosine similarity: dot product of normalized vectors
            similarity = np.dot(emb1, emb2)
            
            # Clamp to [0, 1] range
            similarity = np.clip(similarity, 0.0, 1.0)
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Similarity calculation error: {e}")
            return 0.0
    
    def euclidean_distance(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """
        Calculate Euclidean distance between two embeddings.
        
        Args:
            emb1: First embedding vector
            emb2: Second embedding vector
        
        Returns:
            Distance (lower is more similar)
        """
        try:
            emb1 = np.array(emb1)
            emb2 = np.array(emb2)
            return float(np.linalg.norm(emb1 - emb2))
        except Exception as e:
            logger.error(f"Distance calculation error: {e}")
            return float('inf')
    
    def batch_compare(self, query_embedding: np.ndarray, 
                     database_embeddings: List[np.ndarray]) -> List[float]:
        """
        Compare a query embedding against multiple database embeddings.
        Optimized for batch processing.
        
        Args:
            query_embedding: Query face embedding
            database_embeddings: List of database embeddings
        
        Returns:
            List of similarity scores
        """
        try:
            query = np.array(query_embedding)
            db_matrix = np.array(database_embeddings)
            
            # Normalize
            query = self._normalize_embedding(query)
            db_matrix = db_matrix / np.linalg.norm(db_matrix, axis=1, keepdims=True)
            
            # Compute all similarities at once (matrix multiplication)
            similarities = np.dot(db_matrix, query)
            
            return similarities.tolist()
            
        except Exception as e:
            logger.error(f"Batch comparison error: {e}")
            return [0.0] * len(database_embeddings)


# Singleton instance
_face_utils_instance = None

def get_face_utils() -> FaceUtils:
    """Get or create singleton FaceUtils instance"""
    global _face_utils_instance
    if _face_utils_instance is None:
        _face_utils_instance = FaceUtils()
    return _face_utils_instance


# Convenience functions for direct access
def detect_faces(frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """Detect faces in a frame"""
    return get_face_utils().detect_faces(frame)

def align_and_crop(frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> Optional[np.ndarray]:
    """Align and crop a face"""
    return get_face_utils().align_and_crop(frame, bbox)

def get_embedding(face_img: np.ndarray, model: str = None) -> Optional[np.ndarray]:
    """Extract face embedding"""
    return get_face_utils().get_embedding(face_img, model)

def cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    """Calculate cosine similarity"""
    return get_face_utils().cosine_similarity(emb1, emb2)


if __name__ == '__main__':
    # Test face utilities
    print("Testing Face Recognition Utilities...")
    print(f"Model: {RECOGNITION_MODEL}")
    print(f"Detector: {DETECTION_BACKEND}")
    print(f"Target size: {FACE_SIZE}")
    
    # Create test image
    test_img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    print("\n1. Testing face detection...")
    faces = detect_faces(test_img)
    print(f"   Detected {len(faces)} faces")
    
    print("\n2. Testing embedding extraction...")
    face_crop = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
    embedding = get_embedding(face_crop)
    if embedding is not None:
        print(f"   Embedding shape: {embedding.shape}")
        print(f"   Embedding norm: {np.linalg.norm(embedding):.3f}")
    else:
        print("   Embedding extraction skipped (model may need real face)")
    
    print("\n3. Testing similarity calculation...")
    emb1 = np.random.randn(512)
    emb2 = np.random.randn(512)
    sim = cosine_similarity(emb1, emb2)
    print(f"   Similarity: {sim:.3f}")
    
    print("\n✓ Face utilities test complete!")
