"""
Smart Vault CCTV - Face Augmentation Module
Provides data augmentation techniques for robust face recognition
"""

import cv2
import numpy as np
from typing import List, Tuple
import logging

from src.config import (
    AUG_BRIGHTNESS_RANGE,
    AUG_ROTATION_RANGE,
    AUG_SAMPLES_PER_IMAGE,
    FACE_SIZE
)

logger = logging.getLogger(__name__)


class FaceAugmentor:
    """
    Face image augmentation for improving recognition robustness.
    Generates variations of input faces with different lighting, pose, etc.
    """
    
    def __init__(self):
        """Initialize augmentor with config settings"""
        self.brightness_range = AUG_BRIGHTNESS_RANGE
        self.rotation_range = AUG_ROTATION_RANGE
        self.samples_per_image = AUG_SAMPLES_PER_IMAGE
        self.target_size = FACE_SIZE
    
    def augment_face(self, face_img: np.ndarray, num_samples: int = None) -> List[np.ndarray]:
        """
        Generate augmented versions of a face image.
        
        Args:
            face_img: Input face image (BGR format)
            num_samples: Number of augmented samples to generate
        
        Returns:
            List of augmented face images including original
        """
        num_samples = num_samples or self.samples_per_image
        augmented = [face_img.copy()]  # Include original
        
        try:
            for _ in range(num_samples - 1):
                aug_img = face_img.copy()
                
                # Apply random transformations
                aug_img = self._adjust_brightness(aug_img)
                aug_img = self._rotate(aug_img)
                aug_img = self._add_noise(aug_img)
                
                augmented.append(aug_img)
            
            logger.debug(f"Generated {len(augmented)} augmented samples")
            return augmented
            
        except Exception as e:
            logger.error(f"Augmentation error: {e}")
            return [face_img]
    
    def _adjust_brightness(self, img: np.ndarray) -> np.ndarray:
        """
        Adjust image brightness randomly within configured range.
        
        Args:
            img: Input image
        
        Returns:
            Brightness-adjusted image
        """
        factor = np.random.uniform(self.brightness_range[0], self.brightness_range[1])
        
        # Convert to HSV and adjust V channel
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        hsv = hsv.astype(np.float32)
        hsv[:, :, 2] = hsv[:, :, 2] * factor
        hsv[:, :, 2] = np.clip(hsv[:, :, 2], 0, 255)
        hsv = hsv.astype(np.uint8)
        
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    def _rotate(self, img: np.ndarray) -> np.ndarray:
        """
        Rotate image by a random angle within configured range.
        
        Args:
            img: Input image
        
        Returns:
            Rotated image
        """
        angle = np.random.uniform(self.rotation_range[0], self.rotation_range[1])
        
        h, w = img.shape[:2]
        center = (w // 2, h // 2)
        
        # Get rotation matrix
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        # Rotate with border replication
        rotated = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
        
        return rotated
    
    def _add_noise(self, img: np.ndarray, noise_level: float = 5.0) -> np.ndarray:
        """
        Add Gaussian noise to image for robustness.
        
        Args:
            img: Input image
            noise_level: Standard deviation of noise
        
        Returns:
            Noisy image
        """
        noise = np.random.normal(0, noise_level, img.shape)
        noisy = img.astype(np.float32) + noise
        noisy = np.clip(noisy, 0, 255).astype(np.uint8)
        return noisy
    
    def apply_histogram_equalization(self, img: np.ndarray) -> np.ndarray:
        """
        Apply histogram equalization for lighting normalization.
        
        Args:
            img: Input image (BGR)
        
        Returns:
            Equalized image
        """
        # Convert to YCrCb and equalize Y channel
        ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        ycrcb[:, :, 0] = cv2.equalizeHist(ycrcb[:, :, 0])
        return cv2.cvtColor(ycrcb, cv2.COLOR_YCrCb2BGR)
    
    def apply_gamma_correction(self, img: np.ndarray, gamma: float = 1.2) -> np.ndarray:
        """
        Apply gamma correction for lighting adjustment.
        
        Args:
            img: Input image
            gamma: Gamma value (>1 brightens, <1 darkens)
        
        Returns:
            Gamma-corrected image
        """
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255
                         for i in np.arange(0, 256)]).astype("uint8")
        return cv2.LUT(img, table)
    
    def simulate_aging(self, img: np.ndarray) -> np.ndarray:
        """
        Simulate aged appearance (slightly blur and adjust contrast).
        
        Args:
            img: Input face image
        
        Returns:
            Aged-looking face image
        """
        # Slight blur
        aged = cv2.GaussianBlur(img, (3, 3), 0.5)
        
        # Reduce contrast slightly
        aged = cv2.convertScaleAbs(aged, alpha=0.9, beta=5)
        
        return aged
    
    def simulate_sunglasses(self, img: np.ndarray) -> np.ndarray:
        """
        Simulate sunglasses by darkening eye region.
        
        Args:
            img: Input face image
        
        Returns:
            Face with simulated sunglasses
        """
        h, w = img.shape[:2]
        
        # Approximate eye region (upper third, middle portion)
        eye_region = img.copy()
        y_start = int(h * 0.25)
        y_end = int(h * 0.45)
        
        # Darken eye region
        eye_region[y_start:y_end, :] = (eye_region[y_start:y_end, :] * 0.3).astype(np.uint8)
        
        return eye_region


# Convenience functions
def augment_face(face_img: np.ndarray, num_samples: int = AUG_SAMPLES_PER_IMAGE) -> List[np.ndarray]:
    """Generate augmented face samples"""
    augmentor = FaceAugmentor()
    return augmentor.augment_face(face_img, num_samples)


def apply_preprocessing(face_img: np.ndarray) -> np.ndarray:
    """Apply standard preprocessing (histogram eq + gamma correction)"""
    augmentor = FaceAugmentor()
    img = augmentor.apply_histogram_equalization(face_img)
    img = augmentor.apply_gamma_correction(img)
    return img


if __name__ == '__main__':
    # Test augmentation
    print("Testing Face Augmentation...")
    
    # Create test face image
    test_face = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
    
    augmentor = FaceAugmentor()
    
    print(f"\n1. Generating {AUG_SAMPLES_PER_IMAGE} augmented samples...")
    augmented = augmentor.augment_face(test_face)
    print(f"   Generated {len(augmented)} samples")
    
    print("\n2. Testing individual transformations...")
    bright = augmentor._adjust_brightness(test_face)
    print(f"   ✓ Brightness adjustment")
    
    rotated = augmentor._rotate(test_face)
    print(f"   ✓ Rotation")
    
    noisy = augmentor._add_noise(test_face)
    print(f"   ✓ Noise addition")
    
    print("\n3. Testing preprocessing...")
    preprocessed = apply_preprocessing(test_face)
    print(f"   ✓ Histogram equalization + gamma correction")
    
    print("\n✓ Augmentation test complete!")
