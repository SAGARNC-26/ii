"""
Alternative: Create a test entry without needing a photo
This demonstrates the workflow using a placeholder
"""
from src.db_connection import DB
from datetime import datetime
import numpy as np

print("Adding test authorized face...")

db = DB()

# Create a random embedding (normally this comes from a real face photo)
test_embedding = np.random.randn(512).tolist()

# Add to database
db.auth_coll.insert_one({
    'name': 'Test_User',
    'embedding': test_embedding,
    'image_id': None,  # No image for this test
    'added_date': datetime.now()
})

print("✓ Added 'Test_User' to authorized faces")
print("\nNext: Press 'r' in the recognition window to reload")
print("Or restart: python src/main.py")
