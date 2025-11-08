"""
Smart Vault CCTV - Sync Known Faces to MongoDB
Iterates through known_faces directory and adds authorized faces to database
"""

import os
import sys
import logging
import cv2
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.db_connection import DB
from src.face_utils import detect_faces, align_and_crop, get_embedding
from src.config import KNOWN_FACES_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KnownFacesSyncer:
    """Synchronize known faces from filesystem to MongoDB"""
    
    def __init__(self):
        """Initialize syncer"""
        self.db = DB()
        self.known_faces_dir = KNOWN_FACES_DIR
        self.added_count = 0
        self.skipped_count = 0
        self.failed_count = 0
    
    def sync(self, force_update: bool = False):
        """
        Sync all images in known_faces directory to database.
        
        Args:
            force_update: If True, update existing faces; if False, skip them
        """
        logger.info(f"Starting sync from: {self.known_faces_dir}")
        logger.info("=" * 60)
        
        # Check if directory exists
        if not os.path.exists(self.known_faces_dir):
            logger.error(f"Directory not found: {self.known_faces_dir}")
            logger.info("Creating directory...")
            os.makedirs(self.known_faces_dir)
            logger.info(f"✓ Created: {self.known_faces_dir}")
            logger.info("\nPlease add face images in format: FirstName_LastName.jpg")
            return
        
        # Get all image files
        image_files = self._get_image_files()
        
        if not image_files:
            logger.warning("No image files found in known_faces directory")
            logger.info("\nAdd face images in format: FirstName_LastName.jpg")
            logger.info("Supported formats: .jpg, .jpeg, .png")
            return
        
        logger.info(f"Found {len(image_files)} image files\n")
        
        # Process each image
        for image_path in image_files:
            self._process_image(image_path, force_update)
        
        # Print summary
        self._print_summary()
    
    def _get_image_files(self) -> list:
        """Get all image files from known_faces directory"""
        supported_formats = ['.jpg', '.jpeg', '.png', '.bmp']
        image_files = []
        
        for file in os.listdir(self.known_faces_dir):
            file_path = os.path.join(self.known_faces_dir, file)
            if os.path.isfile(file_path):
                ext = os.path.splitext(file)[1].lower()
                if ext in supported_formats:
                    image_files.append(file_path)
        
        return sorted(image_files)
    
    def _process_image(self, image_path: str, force_update: bool):
        """
        Process a single image file.
        
        Args:
            image_path: Path to image file
            force_update: Whether to update if face already exists
        """
        filename = os.path.basename(image_path)
        
        # Extract name from filename (remove extension)
        name = os.path.splitext(filename)[0]
        
        # Replace underscores with spaces for display
        display_name = name.replace('_', ' ')
        
        logger.info(f"Processing: {display_name}")
        
        try:
            # Check if already exists
            existing = self.db.get_authorized_by_name(name)
            if existing and not force_update:
                logger.info(f"  ⊙ Skipped (already exists)")
                self.skipped_count += 1
                return
            
            # Load image
            frame = cv2.imread(image_path)
            if frame is None:
                logger.error(f"  ✗ Failed to load image")
                self.failed_count += 1
                return
            
            # Detect faces
            faces = detect_faces(frame)
            
            if len(faces) == 0:
                logger.warning(f"  ✗ No face detected")
                self.failed_count += 1
                return
            
            if len(faces) > 1:
                logger.warning(f"  ⚠ Multiple faces detected, using largest")
            
            # Use the largest face
            bbox = max(faces, key=lambda f: f[2] * f[3])
            
            # Align and crop
            face_img = align_and_crop(frame, bbox)
            if face_img is None:
                logger.error(f"  ✗ Failed to align face")
                self.failed_count += 1
                return
            
            # Get embedding
            embedding = get_embedding(face_img)
            if embedding is None:
                logger.error(f"  ✗ Failed to extract embedding")
                self.failed_count += 1
                return
            
            # Read original image as bytes
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            # Add to database
            metadata = {
                'source_file': filename,
                'embedding_dim': len(embedding)
            }
            
            doc_id = self.db.add_authorized_face(name, embedding, image_bytes, metadata)
            
            action = "Updated" if existing else "Added"
            logger.info(f"  ✓ {action} (embedding dim: {len(embedding)})")
            self.added_count += 1
            
        except Exception as e:
            logger.error(f"  ✗ Error: {e}")
            self.failed_count += 1
    
    def _print_summary(self):
        """Print sync summary"""
        logger.info("\n" + "=" * 60)
        logger.info("Sync Summary:")
        logger.info(f"  ✓ Added/Updated: {self.added_count}")
        logger.info(f"  ⊙ Skipped: {self.skipped_count}")
        logger.info(f"  ✗ Failed: {self.failed_count}")
        logger.info("=" * 60)
        
        # Database stats
        stats = self.db.get_stats()
        logger.info(f"\nDatabase Statistics:")
        logger.info(f"  Total authorized faces: {stats.get('authorized_count', 0)}")
        
        if self.added_count > 0:
            logger.info(f"\n✓ Sync completed successfully!")
            logger.info(f"You can now run: python src/main.py")
        elif self.skipped_count > 0:
            logger.info(f"\n⊙ All faces were already in database")
            logger.info(f"Use --force to update existing faces")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Sync known faces from filesystem to MongoDB'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force update existing faces'
    )
    
    args = parser.parse_args()
    
    try:
        syncer = KnownFacesSyncer()
        syncer.sync(force_update=args.force)
    except KeyboardInterrupt:
        logger.info("\n\nSync interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nSync failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
