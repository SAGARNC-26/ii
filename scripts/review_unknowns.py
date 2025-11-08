"""
Smart Vault CCTV - Review Unknown Faces CLI
Interactive CLI tool to review and enroll unknown faces
"""

import os
import sys
import cv2
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.unknown_handler import UnknownFaceHandler
from src.db_connection import DB


def display_image(image_bytes: bytes, window_name: str = "Face"):
    """Display image in window"""
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is not None:
        # Resize for better viewing
        h, w = img.shape[:2]
        scale = min(400 / w, 400 / h)
        new_size = (int(w * scale), int(h * scale))
        img = cv2.resize(img, new_size)
        
        cv2.imshow(window_name, img)
    
    return img is not None


def main():
    """Main review loop"""
    print("=" * 70)
    print("  Smart Vault CCTV - Unknown Face Review")
    print("=" * 70)
    print()
    
    handler = UnknownFaceHandler()
    db = DB()
    
    # Get unknown faces
    print("Loading unknown faces...")
    unknowns = handler.get_unknown_faces(limit=100)
    
    if not unknowns:
        print("✓ No unknown faces to review!")
        print("\nAll caught up! 🎉")
        return
    
    print(f"Found {len(unknowns)} unknown faces pending review\n")
    
    for i, unknown in enumerate(unknowns, 1):
        print("=" * 70)
        print(f"Face {i}/{len(unknowns)}")
        print("=" * 70)
        
        log_id = unknown['_id']
        confidence = unknown.get('confidence', 0)
        timestamp = unknown.get('timestamp', 'N/A')
        camera_id = unknown.get('camera_id', 'N/A')
        
        print(f"ID:         {log_id}")
        print(f"Confidence: {confidence:.3f}")
        print(f"Timestamp:  {timestamp}")
        print(f"Camera:     {camera_id}")
        print()
        
        # Display image
        image_bytes = db.get_image(unknown['image_id'])
        if image_bytes:
            if display_image(image_bytes, "Unknown Face"):
                print("Image displayed in window...")
            else:
                print("⚠ Failed to display image")
        else:
            print("⚠ Image not found")
        
        # Options
        print("\nOptions:")
        print("  [e] Enroll as authorized person")
        print("  [d] Dismiss (don't enroll)")
        print("  [x] Delete this record")
        print("  [s] Skip to next")
        print("  [f] Find similar faces")
        print("  [q] Quit review")
        print()
        
        while True:
            choice = input("Your choice: ").strip().lower()
            
            if choice == 'e':
                # Enroll
                name = input("\nEnter person's name (e.g., John_Doe): ").strip()
                
                if not name:
                    print("⚠ Name cannot be empty")
                    continue
                
                # Replace spaces with underscores
                name = name.replace(' ', '_')
                
                print(f"Enrolling as: {name}...")
                if handler.enroll_unknown_as_authorized(log_id, name):
                    print(f"✓ Successfully enrolled as {name}")
                else:
                    print("✗ Enrollment failed")
                
                break
            
            elif choice == 'd':
                # Dismiss
                print("Dismissing...")
                if handler.dismiss_unknown(log_id):
                    print("✓ Dismissed")
                else:
                    print("✗ Dismiss failed")
                break
            
            elif choice == 'x':
                # Delete
                confirm = input("Delete this record? (y/n): ").strip().lower()
                if confirm == 'y':
                    print("Deleting...")
                    if handler.delete_unknown(log_id):
                        print("✓ Deleted")
                    else:
                        print("✗ Delete failed")
                    break
                else:
                    print("Cancelled")
            
            elif choice == 's':
                # Skip
                print("Skipped")
                break
            
            elif choice == 'f':
                # Find similar
                print("\nSearching for similar faces...")
                similar = handler.get_similar_unknowns(log_id, threshold=0.7, limit=5)
                
                if similar:
                    print(f"Found {len(similar)} similar faces:")
                    for j, sim in enumerate(similar, 1):
                        print(f"  {j}. ID: {sim['_id']}, Similarity: {sim['similarity']:.3f}, "
                              f"Timestamp: {sim.get('timestamp')}")
                else:
                    print("No similar faces found")
                print()
            
            elif choice == 'q':
                # Quit
                print("\nExiting review...")
                cv2.destroyAllWindows()
                return
            
            else:
                print("Invalid choice. Try again.")
        
        cv2.destroyAllWindows()
        print()
    
    print("=" * 70)
    print("✓ Review complete!")
    print("=" * 70)
    
    # Show stats
    stats = db.get_stats()
    print(f"\nDatabase Statistics:")
    print(f"  Authorized faces: {stats.get('authorized_count', 0)}")
    print(f"  Pending review:   {stats.get('pending_review', 0)}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nReview interrupted by user")
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        cv2.destroyAllWindows()
        sys.exit(1)
