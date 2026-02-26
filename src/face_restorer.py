"""Face restoration module for PhotoFit Studio.

Provides face restoration using GFPGAN-style enhancement.
Works with or without PyTorch - falls back to traditional methods when AI models not available.
"""

import cv2
import numpy as np
import logging
from typing import Optional, Tuple

logger = logging.getLogger("face_restorer")

# Try to import torch for GPU-accelerated restoration
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class FaceRestorer:
    """Face restoration for blurry or low-quality face images."""
    
    def __init__(self, model_path: str = None, device: str = "auto"):
        self.model = None
        self.device = self._get_device(device)
        self.model_path = model_path
        self._load_model()
    
    def _get_device(self, device: str) -> str:
        """Get processing device."""
        if device == "auto":
            if TORCH_AVAILABLE and torch.cuda.is_available():
                return "cuda"
            return "cpu"
        return device
    
    def _load_model(self):
        """Load face restoration model.
        
        Note: Full GFPGAN model requires external download.
        This implementation provides a simplified version using traditional CV methods
        as fallback when PyTorch models are not available.
        """
        if not TORCH_AVAILABLE:
            logger.info("PyTorch not available, using traditional face enhancement")
            return
        
        # Check if model file exists
        if self.model_path and not self.model_path.endswith('.pth'):
            # Try to load a custom model
            try:
                # Placeholder for custom model loading
                logger.info(f"Face restoration model path: {self.model_path}")
            except Exception as e:
                logger.warning(f"Could not load model: {e}")
        
        logger.info(f"Face restorer initialized on device: {self.device}")
    
    def restore(self, image: np.ndarray, face_region: Tuple[int, int, int, int] = None) -> np.ndarray:
        """Restore face in image.
        
        Args:
            image: Input BGR image
            face_region: (x, y, w, h) face region to restore
            
        Returns:
            Restored image
        """
        if image is None or image.size == 0:
            return image
        
        result = image.copy()
        
        if face_region:
            x, y, w, h = face_region
            # Restore only the face region
            face_img = result[y:y+h, x:x+w]
            restored = self._enhance_face(face_img)
            result[y:y+h, x:x+w] = restored
        else:
            # Try to detect and restore face
            result = self._enhance_face(result)
        
        return result
    
    def _enhance_face(self, image: np.ndarray) -> np.ndarray:
        """Enhance face using available methods.
        
        Uses traditional CV methods as fallback when deep learning models unavailable.
        """
        if TORCH_AVAILABLE and self.model is not None:
            # Use deep learning model (if loaded)
            return self._enhance_with_model(image)
        
        # Fallback to traditional enhancement
        return self._enhance_traditional(image)
    
    def _enhance_with_model(self, image: np.ndarray) -> np.ndarray:
        """Enhance with deep learning model."""
        # This would use actual GFPGAN/CodeFormer
        # For now, fall back to traditional
        return self._enhance_traditional(image)
    
    def _enhance_traditional(self, image: np.ndarray) -> np.ndarray:
        """Enhance face using traditional CV methods.
        
        Applies:
        1. Denoising
        2. Sharpening
        3. Detail enhancement
        4. Color/contrast adjustment
        """
        result = image.copy()
        h, w = result.shape[:2]
        
        # Step 1: Denoise (preserve edges)
        result = cv2.fastNlMeansDenoisingColored(result, None, 10, 10, 7, 21)
        
        # Step 2: Enhance details (multi-scale)
        # Create detail-enhanced version
        blurred = cv2.GaussianBlur(result, (0, 0), 1.0)
        detail1 = cv2.addWeighted(result, 1.0, blurred, -0.2, 0)
        
        blurred = cv2.GaussianBlur(result, (0, 0), 2.0)
        detail2 = cv2.addWeighted(result, 1.0, blurred, -0.3, 0)
        
        # Blend detail layers
        result = cv2.addWeighted(detail1, 0.6, detail2, 0.4, 0)
        
        # Step 3: Sharpen
        kernel = np.array([
            [-1, -1, -1],
            [-1,  9, -1],
            [-1, -1, -1]
        ])
        sharpened = cv2.filter2D(result, -1, kernel * 0.15)
        result = cv2.addWeighted(result, 0.85, sharpened, 0.15, 0)
        
        # Step 4: Enhance contrast (CLAHE on LAB)
        lab = cv2.cvtColor(result, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        lab = cv2.merge([l, a, b])
        result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        # Step 5: Subtle color enhancement
        # Increase saturation slightly
        hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        s = cv2.add(s, 10)  # Increase saturation
        s = np.clip(s, 0, 255).astype(np.uint8)
        hsv = cv2.merge([h, s, v])
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        # Step 6: Smooth skin (gentle bilateral)
        result = cv2.bilateralFilter(result, 7, 30, 30)
        
        return np.clip(result, 0, 255).astype(np.uint8)
    
    def is_available(self) -> bool:
        """Check if GPU-accelerated restoration is available."""
        return TORCH_AVAILABLE and self.model is not None
    
    def get_device(self) -> str:
        """Get current device."""
        return self.device


class FaceQualityAssessor:
    """Assess face image quality."""
    
    def __init__(self):
        pass
    
    def assess_quality(self, image: np.ndarray) -> dict:
        """Assess face image quality.
        
        Args:
            image: Input BGR image
            
        Returns:
            Dict with quality metrics
        """
        if image is None or image.size == 0:
            return {"quality_score": 0, "issues": ["No image"]}
        
        issues = []
        score = 100
        
        # Check brightness
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_brightness = np.mean(gray)
        
        if mean_brightness < 60:
            issues.append("Too dark")
            score -= 20
        elif mean_brightness > 200:
            issues.append("Too bright")
            score -= 20
        
        # Check contrast
        contrast = np.std(gray)
        if contrast < 30:
            issues.append("Low contrast")
            score -= 15
        elif contrast > 100:
            issues.append("High contrast")
            score -= 10
        
        # Check sharpness (Laplacian variance)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()
        
        if sharpness < 50:
            issues.append("Blurry")
            score -= 25
        elif sharpness < 100:
            issues.append("Slightly blurry")
            score -= 10
        
        # Check resolution
        h, w = image.shape[:2]
        if w < 200 or h < 200:
            issues.append("Low resolution")
            score -= 20
        
        score = max(0, score)
        
        return {
            "quality_score": score,
            "brightness": mean_brightness,
            "contrast": contrast,
            "sharpness": sharpness,
            "resolution": (w, h),
            "issues": issues if issues else ["Good quality"],
            "recommendation": self._get_recommendation(score)
        }
    
    def _get_recommendation(self, score: int) -> str:
        """Get recommendation based on score."""
        if score >= 80:
            return "Quality is good for ID photo"
        elif score >= 60:
            return "Acceptable quality, minor improvements possible"
        elif score >= 40:
            return "Consider retaking or using enhancement"
        else:
            return "Poor quality, recommend retaking photo"


class SuperResolution:
    """Super resolution for image upscaling."""
    
    def __init__(self, scale: int = 2, device: str = "auto"):
        self.scale = scale
        self.device = self._get_device(device)
        self.model = None
        self._load_model()
    
    def _get_device(self, device: str) -> str:
        """Get processing device."""
        if device == "auto":
            if TORCH_AVAILABLE and torch.cuda.is_available():
                return "cuda"
            return "cpu"
        return device
    
    def _load_model(self):
        """Load super resolution model."""
        if not TORCH_AVAILABLE:
            logger.info("PyTorch not available, using bicubic upscaling")
            return
        
        logger.info(f"Super resolution initialized on device: {self.device}")
    
    def upscale(self, image: np.ndarray, scale: int = None) -> np.ndarray:
        """Upscale image using super resolution.
        
        Args:
            image: Input BGR image
            scale: Upscale factor (default: self.scale)
            
        Returns:
            Upscaled image
        """
        if image is None or image.size == 0:
            return image
        
        scale = scale or self.scale
        
        if TORCH_AVAILABLE and self.model is not None:
            return self._upscale_with_model(image, scale)
        
        # Fallback to Lanczos
        return self._upscale_lanczos(image, scale)
    
    def _upscale_with_model(self, image: np.ndarray, scale: int) -> np.ndarray:
        """Upscale with deep learning model."""
        # Would use Real-ESRGAN or similar
        return self._upscale_lanczos(image, scale)
    
    def _upscale_lanczos(self, image: np.ndarray, scale: int) -> np.ndarray:
        """Upscale using Lanczos interpolation."""
        h, w = image.shape[:2]
        new_w = w * scale
        new_h = h * scale
        
        result = cv2.resize(
            image, 
            (new_w, new_h), 
            interpolation=cv2.INTER_LANCZOS4
        )
        
        # Apply sharpening after upscale
        kernel = np.array([
            [-1, -1, -1],
            [-1,  9, -1],
            [-1, -1, -1]
        ])
        sharpened = cv2.filter2D(result, -1, kernel * 0.1)
        result = cv2.addWeighted(result, 0.9, sharpened, 0.1, 0)
        
        return result
    
    def is_available(self) -> bool:
        """Check if GPU-accelerated SR is available."""
        return TORCH_AVAILABLE and self.model is not None


# Standalone functions
def enhance_face(image: np.ndarray) -> np.ndarray:
    """Quick face enhancement function."""
    restorer = FaceRestorer()
    return restorer.restore(image)


def assess_face_quality(image: np.ndarray) -> dict:
    """Quick face quality assessment."""
    assessor = FaceQualityAssessor()
    return assessor.assess_quality(image)


def upscale_image(image: np.ndarray, scale: int = 2) -> np.ndarray:
    """Quick image upscaling."""
    sr = SuperResolution(scale=scale)
    return sr.upscale(image)
