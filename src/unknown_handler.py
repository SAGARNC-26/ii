"""
Smart Vault CCTV - Unknown Face Handler
Manages unknown face detections and provides review/enrollment functionality
"""

import logging
import numpy as np
import cv2
from typing import List, Dict, Optional
from datetime import datetime

from src.db_connection import DB
from src.face_utils import get_embedding

logger = logging.getLogger(__name__)


class UnknownFaceHandler:
    """
    Handle unknown face detections and provide enrollment workflow.
    """
    
    def __init__(self):
        """Initialize handler"""
        self.db = DB()
    
    def get_unknown_faces(self, limit: int = 50) -> List[Dict]:
        """
        Get all unknown face detections pending review.
        
        Args:
            limit: Maximum number of records to return
        
        Returns:
            List of unknown face records
        """
        try:
            unknowns = self.db.get_detection_logs(
                limit=limit,
                status="Unauthorized",
                review_flag=True
            )
            
            logger.info(f"Retrieved {len(unknowns)} unknown faces for review")
            return unknowns
            
        except Exception as e:
            logger.error(f"Failed to get unknown faces: {e}")
            return []
    
    def get_unknown_by_id(self, log_id: str) -> Optional[Dict]:
        """
        Get a specific unknown face record by ID.
        
        Args:
            log_id: Detection log ID
        
        Returns:
            Face record or None
        """
        try:
            logs = self.db.logs_coll.find_one({'_id': log_id})
            if logs:
                logs['_id'] = str(logs['_id'])
            return logs
        except Exception as e:
            logger.error(f"Failed to get unknown face: {e}")
            return None
    
    def enroll_unknown_as_authorized(self, log_id: str, name: str) -> bool:
        """
        Convert an unknown face to an authorized face.
        
        Args:
            log_id: Detection log ID of unknown face
            name: Name to assign to this person
        
        Returns:
            True if successful
        """
        try:
            from bson.objectid import ObjectId
            
            # Get the log entry
            log = self.db.logs_coll.find_one({'_id': ObjectId(log_id)})
            
            if not log:
                logger.error(f"Log not found: {log_id}")
                return False
            
            # Extract embedding and image
            embedding = np.array(log['embedding'])
            image_id = log['image_id']
            
            # Get image bytes
            image_bytes = self.db.get_image(image_id)
            
            if not image_bytes:
                logger.error("Failed to retrieve image")
                return False
            
            # Add to authorized faces
            self.db.add_authorized_face(name, embedding, image_bytes)
            
            # Update the log to mark as enrolled
            self.db.logs_coll.update_one(
                {'_id': ObjectId(log_id)},
                {'$set': {
                    'review_flag': False,
                    'enrolled_as': name,
                    'enrolled_at': datetime.utcnow()
                }}
            )
            
            logger.info(f"✓ Enrolled unknown face as: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Enrollment failed: {e}")
            return False
    
    def dismiss_unknown(self, log_id: str) -> bool:
        """
        Dismiss an unknown face (mark as reviewed, don't enroll).
        
        Args:
            log_id: Detection log ID
        
        Returns:
            True if successful
        """
        try:
            from bson.objectid import ObjectId
            
            result = self.db.logs_coll.update_one(
                {'_id': ObjectId(log_id)},
                {'$set': {
                    'review_flag': False,
                    'dismissed': True,
                    'dismissed_at': datetime.utcnow()
                }}
            )
            
            if result.modified_count > 0:
                logger.info(f"✓ Dismissed unknown face: {log_id}")
                return True
            else:
                logger.warning(f"No record updated for: {log_id}")
                return False
                
        except Exception as e:
            logger.error(f"Dismiss failed: {e}")
            return False
    
    def delete_unknown(self, log_id: str) -> bool:
        """
        Delete an unknown face record entirely.
        
        Args:
            log_id: Detection log ID
        
        Returns:
            True if successful
        """
        try:
            from bson.objectid import ObjectId
            
            # Get record first to delete image
            log = self.db.logs_coll.find_one({'_id': ObjectId(log_id)})
            
            if log and 'image_id' in log:
                try:
                    self.db.fs.delete(ObjectId(log['image_id']))
                except:
                    pass
            
            # Delete log
            result = self.db.logs_coll.delete_one({'_id': ObjectId(log_id)})
            
            if result.deleted_count > 0:
                logger.info(f"✓ Deleted unknown face: {log_id}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False
    
    def get_similar_unknowns(self, log_id: str, threshold: float = 0.8, limit: int = 10) -> List[Dict]:
        """
        Find similar unknown faces (potential duplicates).
        
        Args:
            log_id: Reference face log ID
            threshold: Similarity threshold
            limit: Maximum results
        
        Returns:
            List of similar unknown faces
        """
        try:
            from bson.objectid import ObjectId
            from src.face_utils import cosine_similarity
            
            # Get reference face
            ref_log = self.db.logs_coll.find_one({'_id': ObjectId(log_id)})
            if not ref_log:
                return []
            
            ref_embedding = np.array(ref_log['embedding'])
            
            # Get all other unknowns
            unknowns = self.db.get_detection_logs(
                limit=1000,
                status="Unauthorized",
                review_flag=True
            )
            
            # Find similar ones
            similar = []
            for unknown in unknowns:
                if unknown['_id'] == log_id:
                    continue
                
                unknown_embedding = np.array(unknown['embedding'])
                similarity = cosine_similarity(ref_embedding, unknown_embedding)
                
                if similarity >= threshold:
                    unknown['similarity'] = similarity
                    similar.append(unknown)
            
            # Sort by similarity
            similar.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similar[:limit]
            
        except Exception as e:
            logger.error(f"Similar search failed: {e}")
            return []


if __name__ == '__main__':
    # Test unknown handler
    print("Testing Unknown Face Handler...")
    
    handler = UnknownFaceHandler()
    
    print("\n1. Getting unknown faces...")
    unknowns = handler.get_unknown_faces(limit=10)
    print(f"   Found {len(unknowns)} unknown faces pending review")
    
    if unknowns:
        print("\n2. First unknown face:")
        first = unknowns[0]
        print(f"   ID: {first['_id']}")
        print(f"   Confidence: {first.get('confidence', 0):.3f}")
        print(f"   Timestamp: {first.get('timestamp')}")
    
    print("\n✓ Unknown handler test complete!")
