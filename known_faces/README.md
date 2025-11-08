# Known Faces Directory

Add authorized face images to this directory.

## Naming Convention

Use the format: `FirstName_LastName.jpg`

Examples:
- `Alice_Smith.jpg`
- `Bob_Jones.jpg`
- `Charlie_Brown.jpg`
- `Diana_Prince.jpg`

## Image Requirements

- **Format**: JPG, JPEG, or PNG
- **Quality**: Clear, well-lit frontal face photo
- **Size**: Minimum 200x200 pixels (recommended: 640x480 or higher)
- **Face Size**: Face should occupy at least 30% of image
- **Angle**: Frontal view (±15 degrees acceptable)
- **One Face**: Only one person per image
- **No Obstructions**: No sunglasses, masks, or heavy shadows

## Good Examples

✓ Professional headshot-style photos
✓ Passport-style photos
✓ Clear webcam captures
✓ Good indoor/outdoor lighting
✓ Neutral background

## Poor Examples

✗ Side profile or extreme angles
✗ Very small or distant faces
✗ Dark or poorly lit photos
✗ Motion blur
✗ Heavy shadows or glare
✗ Partial face occlusion

## After Adding Images

Run the sync script to add faces to the database:

```bash
python src/sync_known_faces.py
```

This will:
1. Detect faces in each image
2. Extract face embeddings
3. Store in MongoDB with name association

## Tips

- Add 2-3 photos per person for better accuracy
- Include photos with different expressions
- Capture under different lighting conditions
- Update photos periodically (especially for aging)

## Testing

After syncing, verify with:

```bash
# Check database
python -c "from src.db_connection import DB; db = DB(); print('Faces:', db.auth_coll.count_documents({}))"

# Run recognition
python src/main.py
```

## Updating Faces

To update an existing face:

```bash
# Run sync with --force flag
python src/sync_known_faces.py --force
```

This will replace existing embeddings with new ones.
