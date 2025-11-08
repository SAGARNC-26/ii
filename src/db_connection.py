"""
Smart Vault CCTV - MongoDB Database Connection Module
Handles all database operations including GridFS for image storage
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
import io

from pymongo import MongoClient, errors
from gridfs import GridFS
from bson.objectid import ObjectId
import numpy as np

from src.config import MONGO_URI, DB_NAME, AUTH_COLLECTION, LOGS_COLLECTION, GRIDFS_BUCKET

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DB:
    """
    MongoDB database wrapper with GridFS support for Smart Vault CCTV system.
    
    Provides methods to:
    - Store and retrieve authorized face embeddings
    - Log face detection events
    - Store and retrieve face images using GridFS
    """
    
    def __init__(self, uri: str = None, db_name: str = None):
        """
        Initialize MongoDB connection and GridFS.
        
        Args:
            uri: MongoDB connection URI (default: from config)
            db_name: Database name (default: from config)
        """
        self.uri = uri or MONGO_URI
        self.db_name = db_name or DB_NAME
        
        try:
            # Connect to MongoDB
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"✓ Connected to MongoDB: {self.db_name}")
            
            # Get database and collections
            self.db = self.client[self.db_name]
            self.auth_coll = self.db[AUTH_COLLECTION]
            self.logs_coll = self.db[LOGS_COLLECTION]
            
            # Initialize GridFS
            self.fs = GridFS(self.db, collection=GRIDFS_BUCKET)
            
            # Create indexes for better performance
            self._create_indexes()
            
        except errors.ConnectionFailure as e:
            logger.error(f"✗ Failed to connect to MongoDB: {e}")
            raise
        except Exception as e:
            logger.error(f"✗ Database initialization error: {e}")
            raise
    
    def _create_indexes(self):
        """Create database indexes for optimized queries"""
        try:
            # Index on name for authorized faces
            self.auth_coll.create_index('name', unique=True)
            self.auth_coll.create_index('created_at')
            
            # Indexes for logs
            self.logs_coll.create_index('timestamp')
            self.logs_coll.create_index('status')
            self.logs_coll.create_index('review_flag')
            self.logs_coll.create_index('camera_id')
            self.logs_coll.create_index([('name', 1), ('timestamp', -1)])
            
            logger.info("✓ Database indexes created")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    def add_authorized_face(self, name: str, embedding: np.ndarray, 
                           image_bytes: bytes, metadata: Dict = None) -> str:
        """
        Add or update an authorized face in the database.
        
        Args:
            name: Person's name (e.g., "Alice_Smith")
            embedding: Face embedding vector (numpy array)
            image_bytes: Original face image as bytes
            metadata: Optional additional metadata
        
        Returns:
            Document ID (str)
        
        Raises:
            Exception: If database operation fails
        """
        try:
            # Store image in GridFS
            image_id = self.fs.put(
                image_bytes,
                filename=f"{name}.jpg",
                content_type='image/jpeg',
                metadata={'type': 'authorized', 'name': name}
            )
            
            # Prepare document
            doc = {
                'name': name,
                'embedding': embedding.tolist() if isinstance(embedding, np.ndarray) else embedding,
                'image_id': str(image_id),
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'metadata': metadata or {}
            }
            
            # Check if face already exists
            existing = self.auth_coll.find_one({'name': name})
            
            if existing:
                # Update existing
                self.auth_coll.update_one(
                    {'name': name},
                    {'$set': {
                        'embedding': doc['embedding'],
                        'image_id': doc['image_id'],
                        'updated_at': doc['updated_at'],
                        'metadata': doc['metadata']
                    }}
                )
                doc_id = str(existing['_id'])
                logger.info(f"✓ Updated authorized face: {name}")
            else:
                # Insert new
                result = self.auth_coll.insert_one(doc)
                doc_id = str(result.inserted_id)
                logger.info(f"✓ Added new authorized face: {name}")
            
            return doc_id
            
        except errors.DuplicateKeyError:
            logger.warning(f"Duplicate face name: {name}")
            raise ValueError(f"Face with name '{name}' already exists")
        except Exception as e:
            logger.error(f"✗ Failed to add authorized face: {e}")
            raise
    
    def get_all_authorized(self) -> List[Dict[str, Any]]:
        """
        Retrieve all authorized faces from database.
        
        Returns:
            List of dictionaries containing name, embedding, image_id, etc.
        """
        try:
            faces = list(self.auth_coll.find())
            
            # Convert embeddings back to numpy arrays
            for face in faces:
                face['_id'] = str(face['_id'])
                if 'embedding' in face:
                    face['embedding'] = np.array(face['embedding'])
            
            logger.info(f"✓ Retrieved {len(faces)} authorized faces")
            return faces
            
        except Exception as e:
            logger.error(f"✗ Failed to retrieve authorized faces: {e}")
            raise
    
    def get_authorized_by_name(self, name: str) -> Optional[Dict]:
        """
        Get a specific authorized face by name.
        
        Args:
            name: Person's name
        
        Returns:
            Face document or None if not found
        """
        try:
            face = self.auth_coll.find_one({'name': name})
            if face:
                face['_id'] = str(face['_id'])
                face['embedding'] = np.array(face['embedding'])
            return face
        except Exception as e:
            logger.error(f"✗ Failed to get face by name: {e}")
            return None
    
    def update_authorized_embedding(self, name: str, new_embedding: np.ndarray):
        """
        Update the embedding for an authorized face (adaptive learning).
        
        Args:
            name: Person's name
            new_embedding: Updated embedding vector
        """
        try:
            result = self.auth_coll.update_one(
                {'name': name},
                {'$set': {
                    'embedding': new_embedding.tolist(),
                    'updated_at': datetime.utcnow()
                }}
            )
            
            if result.modified_count > 0:
                logger.info(f"✓ Updated embedding for: {name}")
            else:
                logger.warning(f"No document found to update: {name}")
                
        except Exception as e:
            logger.error(f"✗ Failed to update embedding: {e}")
            raise
    
    def save_detection_log(self, name: str, confidence: float, status: str,
                          embedding: np.ndarray, image_bytes: bytes,
                          camera_id: str = 'cam_01', review_flag: bool = False,
                          metadata: Dict = None) -> str:
        """
        Save a face detection event to the logs collection.
        
        Args:
            name: Detected person's name or "Unknown"
            confidence: Match confidence score (0.0 - 1.0)
            status: "Authorized" or "Unauthorized"
            embedding: Face embedding vector
            image_bytes: Face image as bytes
            camera_id: Camera identifier
            review_flag: Whether this detection needs review
            metadata: Optional additional metadata
        
        Returns:
            Log document ID (str)
        """
        try:
            # Store image in GridFS
            image_id = self.fs.put(
                image_bytes,
                filename=f"detection_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.jpg",
                content_type='image/jpeg',
                metadata={
                    'type': 'detection',
                    'name': name,
                    'status': status,
                    'camera_id': camera_id
                }
            )
            
            # Create log document
            log = {
                'name': name,
                'confidence': float(confidence),
                'status': status,
                'embedding': embedding.tolist() if isinstance(embedding, np.ndarray) else embedding,
                'image_id': str(image_id),
                'camera_id': camera_id,
                'review_flag': review_flag,
                'timestamp': datetime.utcnow(),
                'metadata': metadata or {}
            }
            
            result = self.logs_coll.insert_one(log)
            log_id = str(result.inserted_id)
            
            logger.debug(f"✓ Saved detection log: {name} ({status})")
            return log_id
            
        except Exception as e:
            logger.error(f"✗ Failed to save detection log: {e}")
            raise
    
    def get_detection_logs(self, limit: int = 100, status: str = None,
                          camera_id: str = None, review_flag: bool = None) -> List[Dict]:
        """
        Retrieve detection logs with optional filters.
        
        Args:
            limit: Maximum number of logs to return
            status: Filter by status ("Authorized" or "Unauthorized")
            camera_id: Filter by camera
            review_flag: Filter by review flag
        
        Returns:
            List of log documents
        """
        try:
            query = {}
            if status:
                query['status'] = status
            if camera_id:
                query['camera_id'] = camera_id
            if review_flag is not None:
                query['review_flag'] = review_flag
            
            logs = list(self.logs_coll.find(query).sort('timestamp', -1).limit(limit))
            
            # Convert ObjectIds to strings
            for log in logs:
                log['_id'] = str(log['_id'])
            
            logger.info(f"✓ Retrieved {len(logs)} detection logs")
            return logs
            
        except Exception as e:
            logger.error(f"✗ Failed to retrieve logs: {e}")
            raise
    
    def get_image(self, file_id: str) -> Optional[bytes]:
        """
        Retrieve an image from GridFS by file ID.
        
        Args:
            file_id: GridFS file ID (string)
        
        Returns:
            Image bytes or None if not found
        """
        try:
            grid_out = self.fs.get(ObjectId(file_id))
            image_bytes = grid_out.read()
            logger.debug(f"✓ Retrieved image: {file_id}")
            return image_bytes
        except Exception as e:
            logger.error(f"✗ Failed to retrieve image {file_id}: {e}")
            return None
    
    def delete_authorized_face(self, name: str) -> bool:
        """
        Delete an authorized face from the database.
        
        Args:
            name: Person's name
        
        Returns:
            True if deleted, False if not found
        """
        try:
            # Get the document first to delete associated image
            face = self.auth_coll.find_one({'name': name})
            if not face:
                logger.warning(f"Face not found: {name}")
                return False
            
            # Delete GridFS image
            if 'image_id' in face:
                try:
                    self.fs.delete(ObjectId(face['image_id']))
                except Exception as e:
                    logger.warning(f"Could not delete image: {e}")
            
            # Delete document
            self.auth_coll.delete_one({'name': name})
            logger.info(f"✓ Deleted authorized face: {name}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to delete face: {e}")
            raise
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with counts of authorized faces, logs, etc.
        """
        try:
            stats = {
                'authorized_count': self.auth_coll.count_documents({}),
                'total_logs': self.logs_coll.count_documents({}),
                'authorized_logs': self.logs_coll.count_documents({'status': 'Authorized'}),
                'unauthorized_logs': self.logs_coll.count_documents({'status': 'Unauthorized'}),
                'pending_review': self.logs_coll.count_documents({'review_flag': True}),
            }
            return stats
        except Exception as e:
            logger.error(f"✗ Failed to get stats: {e}")
            return {}
    
    def close(self):
        """Close database connection"""
        try:
            self.client.close()
            logger.info("✓ Database connection closed")
        except Exception as e:
            logger.error(f"✗ Error closing connection: {e}")


# Singleton instance
_db_instance = None

def get_db() -> DB:
    """Get or create singleton DB instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DB()
    return _db_instance


if __name__ == '__main__':
    # Test database connection
    print("Testing MongoDB connection...")
    
    try:
        db = DB()
        print(f"\n✓ Connection successful!")
        print(f"\nDatabase Statistics:")
        stats = db.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print(f"\nCollections:")
        print(f"  - {AUTH_COLLECTION}")
        print(f"  - {LOGS_COLLECTION}")
        print(f"  - {GRIDFS_BUCKET} (GridFS)")
        
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        print("\nMake sure MongoDB is running:")
        print("  - Local: mongod")
        print("  - Docker: docker run -d -p 27017:27017 mongo")
