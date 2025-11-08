# Models Directory

This directory stores face recognition model files.

## Automatic Download

DeepFace will automatically download required models on first use:

- **ArcFace** (default): ~180 MB
- **Facenet**: ~90 MB
- **VGG-Face**: ~550 MB
- **DeepFace**: ~140 MB
- **OpenFace**: ~30 MB

Models are cached here to avoid repeated downloads.

## Manual Download (Optional)

If you need to pre-download models:

```python
from deepface import DeepFace

# Download ArcFace model
DeepFace.build_model("ArcFace")

# Download other models
DeepFace.build_model("Facenet")
DeepFace.build_model("VGG-Face")
```

## Switching Models

Edit `src/config.py`:

```python
# Options: ArcFace, Facenet, VGG-Face, OpenFace, DeepFace
RECOGNITION_MODEL = 'ArcFace'
```

**Recommendations:**
- **ArcFace**: Best accuracy, fast (default)
- **Facenet**: Good balance of speed and accuracy
- **VGG-Face**: High accuracy, slower
- **OpenFace**: Fastest, lower accuracy

## Model Comparison

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| ArcFace | 180MB | Fast | Excellent | Production |
| Facenet | 90MB | Fast | Very Good | General |
| VGG-Face | 550MB | Slow | Excellent | High Security |
| OpenFace | 30MB | Very Fast | Good | Edge Devices |

## Custom Models (Advanced)

For custom-trained models, place them in this directory and modify `src/face_utils.py` to load them.

## Storage

Models are stored in TensorFlow/Keras format:
- `.h5` files (weights)
- `.pb` files (frozen graphs)
- `.json` files (architecture)

## Troubleshooting

### Model Download Fails

```bash
# Check internet connection
# Clear cache and retry
rm -rf ~/.deepface/weights/
python -c "from deepface import DeepFace; DeepFace.build_model('ArcFace')"
```

### Out of Memory

Use a lighter model:
```python
RECOGNITION_MODEL = 'OpenFace'  # Smallest model
```

Or reduce batch size in face detection.
