from src.db_connection import DB

db = DB()
total_logs = db.logs_coll.count_documents({})
unknown_faces = db.logs_coll.count_documents({"review_flag": True})
authorized_faces = db.auth_coll.count_documents({})

print(f"\n📊 Database Status:")
print(f"  Authorized faces: {authorized_faces}")
print(f"  Total detections: {total_logs}")
print(f"  Unknown faces pending review: {unknown_faces}")

if unknown_faces > 0:
    print(f"\n✓ Ready to review unknowns!")
    print(f"  Go to: http://localhost:5000/unknowns")
elif total_logs == 0:
    print(f"\n⚠ No detections yet.")
    print(f"  Show your face to the camera!")
