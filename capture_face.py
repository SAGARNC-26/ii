"""
Quick script to capture your face from the camera
"""
import cv2
import sys

print("=" * 60)
print("  Face Capture Utility")
print("=" * 60)
print("\nInstructions:")
print("  1. Position your face in the camera")
print("  2. Press SPACE to capture")
print("  3. Press ESC to exit without capturing")
print("=" * 60)

# Open camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("✗ Error: Cannot open camera")
    sys.exit(1)

print("\n✓ Camera opened. Press SPACE to capture, ESC to exit...")

captured = False
while True:
    ret, frame = cap.read()
    
    if not ret:
        print("✗ Error: Cannot read frame")
        break
    
    # Display frame
    cv2.putText(frame, "Press SPACE to capture", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    cv2.imshow('Capture Face - Press SPACE', frame)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == 27:  # ESC
        print("\n✗ Capture cancelled")
        break
    elif key == 32:  # SPACE
        # Get name
        cap.release()
        cv2.destroyAllWindows()
        
        name = input("\nEnter your name (e.g., John_Doe): ").strip()
        
        if not name:
            print("✗ No name provided")
            sys.exit(1)
        
        # Replace spaces with underscores
        name = name.replace(' ', '_')
        
        # Save image
        filename = f"known_faces/{name}.jpg"
        cv2.imwrite(filename, frame)
        print(f"\n✓ Face captured: {filename}")
        print(f"\nNext step:")
        print(f"  python src/sync_known_faces.py")
        captured = True
        break

cap.release()
cv2.destroyAllWindows()

if captured:
    sys.exit(0)
else:
    sys.exit(1)
