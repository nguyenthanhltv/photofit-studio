"""Skin smoothing, beautification, and hair edge smoothing module."""

import cv2
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger("image_processor")

# Beautify level parameters: (bilateral_d, sigma_color, sigma_space, blend_alpha)
LEVEL_PARAMS = {
    "light":  (5, 30, 30, 0.3),
    "medium": (7, 50, 50, 0.5),
    "strong": (9, 75, 75, 0.7),
}


class Beautifier:
    """Skin smoothing and beautification for ID photos."""

    def __init__(self, level: str = "medium"):
        self.set_level(level)

    def set_level(self, level: str) -> None:
        """Set beautification level: light, medium, or strong."""
        self.level = level if level in LEVEL_PARAMS else "medium"
        self.params = LEVEL_PARAMS[self.level]

    def create_skin_mask(self, image: np.ndarray) -> np.ndarray:
        """Create a mask for skin regions using YCrCb color space."""
        ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
        # Skin color range in YCrCb
        lower = np.array([0, 133, 77], dtype=np.uint8)
        upper = np.array([255, 173, 127], dtype=np.uint8)
        mask = cv2.inRange(ycrcb, lower, upper)

        # Clean up mask with morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Blur edges for smooth blending
        mask = cv2.GaussianBlur(mask, (9, 9), 0)
        return mask

    def smooth_skin(self, image: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
        """Apply skin smoothing using bilateral filter + frequency separation.

        Args:
            image: Input BGR image
            mask: Optional skin mask (auto-generated if None)

        Returns:
            Smoothed image
        """
        if mask is None:
            mask = self.create_skin_mask(image)

        d, sigma_c, sigma_s, alpha = self.params

        # Step 1: Bilateral filter for edge-preserving smoothing
        smoothed = cv2.bilateralFilter(image, d, sigma_c, sigma_s)

        # Step 2: Frequency separation - preserve high-frequency details
        # Low frequency = smoothed colors, High frequency = texture/details
        low_freq = cv2.GaussianBlur(image, (0, 0), 3)
        high_freq = cv2.subtract(image, low_freq)

        # Combine: smoothed base + original texture
        combined = cv2.add(smoothed, high_freq)

        # Step 3: Blend with original using skin mask
        mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR).astype(np.float32) / 255.0
        original_f = image.astype(np.float32)
        combined_f = combined.astype(np.float32)

        result = original_f * (1 - mask_3ch * alpha) + combined_f * (mask_3ch * alpha)
        return np.clip(result, 0, 255).astype(np.uint8)

    def auto_brightness_contrast(self, image: np.ndarray, clip_pct: float = 1.0) -> np.ndarray:
        """Adaptive brightness normalization for mixed-light batches.

        Strategy:
        1) Local contrast normalization with CLAHE on LAB L channel.
        2) Gentle gamma correction toward target luminance.
        3) Highlight protection to avoid overexposed faces.
        4) Blend with original image based on how far luminance is from target.
        """
        if image is None or image.size == 0:
            return image

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        mean_luma = float(np.mean(gray))
        std_luma = float(np.std(gray))

        # 1) Local contrast normalization (safer than global linear stretch)
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)

        clip_limit = 2.0 if std_luma > 42 else 1.6
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
        l_eq = clahe.apply(l)

        # 2) Gentle gamma correction toward target luminance band
        target_luma = 132.0
        gamma = 1.0
        if mean_luma < 100:
            gamma = 0.88
        elif mean_luma < 118:
            gamma = 0.94
        elif mean_luma > 168:
            gamma = 1.10
        elif mean_luma > 150:
            gamma = 1.05

        l_norm = l_eq.astype(np.float32) / 255.0
        l_gamma = np.power(np.clip(l_norm, 0.0, 1.0), gamma)

        # 3) Highlight protection: compress only very bright regions
        bright_mask = np.clip((l_gamma - 0.84) / 0.16, 0.0, 1.0)
        l_protected = l_gamma * (1.0 - 0.22 * bright_mask)

        l_out = np.clip(l_protected * 255.0, 0, 255).astype(np.uint8)
        merged = cv2.merge([l_out, a, b])
        adjusted = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

        # 4) Adaptive blend with original to keep natural skin tone
        #    Stronger correction only when image is too dark/too bright.
        deviation = min(abs(mean_luma - target_luma) / 55.0, 1.0)
        blend = 0.30 + 0.45 * deviation  # 0.30..0.75

        result = cv2.addWeighted(adjusted, blend, image, 1.0 - blend, 0)
        return np.clip(result, 0, 255).astype(np.uint8)

    def smooth_hair_edges(self, image: np.ndarray) -> np.ndarray:
        """Smooth hair edges to reduce flyaway and jagged edges.

        Uses edge detection on the upper portion of the image
        and applies targeted Gaussian smoothing.
        """
        h, w = image.shape[:2]
        result = image.copy()

        # Focus on upper 60% where hair typically is
        hair_region = result[:int(h * 0.6), :]

        # Detect edges
        gray = cv2.cvtColor(hair_region, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)

        # Dilate edges slightly
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        edges = cv2.dilate(edges, kernel, iterations=1)

        # Create smooth version
        smooth = cv2.GaussianBlur(hair_region, (5, 5), 0)

        # Blend edges with smooth version
        edge_mask = edges.astype(np.float32) / 255.0
        edge_mask = cv2.GaussianBlur(edge_mask, (5, 5), 0)
        edge_mask_3ch = np.stack([edge_mask] * 3, axis=-1)

        blended = (hair_region.astype(np.float32) * (1 - edge_mask_3ch * 0.5) +
                   smooth.astype(np.float32) * (edge_mask_3ch * 0.5))

        result[:int(h * 0.6), :] = np.clip(blended, 0, 255).astype(np.uint8)
        return result

    def enhance_eyes(self, image: np.ndarray) -> np.ndarray:
        """Enhance eyes - brighten and sharpen eye region.
        
        Uses face mesh to detect eye positions and apply targeted enhancement.
        
        Args:
            image: Input BGR image
            
        Returns:
            Image with enhanced eyes
        """
        try:
            import mediapipe as mp
            mp_face = mp.solutions.face_mesh
            
            # Create face mesh detector
            with mp_face.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True
            ) as face_mesh:
                # Convert to RGB
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(rgb)
                
                if not results.multi_face_landmarks:
                    return image
                
                # Get landmarks
                landmarks = results.multi_face_landmarks[0]
                
                # Eye landmarks (approximate positions)
                # Left eye: 33-133, Right eye: 362-263
                left_eye_indices = list(range(33, 133))
                right_eye_indices = list(range(362, 263, -1))
                
                h, w = image.shape[:2]
                
                # Process each eye
                result = image.copy()
                
                for eye_indices in [left_eye_indices, right_eye_indices]:
                    # Get eye bounding box
                    xs = [int(landmarks[i].x * w) for i in eye_indices]
                    ys = [int(landmarks[i].y * h) for i in eye_indices]
                    
                    # Expand box slightly
                    margin = 10
                    x1 = max(0, min(xs) - margin)
                    x2 = min(w, max(xs) + margin)
                    y1 = max(0, min(ys) - margin)
                    y2 = min(h, max(ys) + margin)
                    
                    if x2 > x1 and y2 > y1:
                        eye_region = result[y1:y2, x1:x2]
                        
                        # Brighten the eye region slightly
                        lab = cv2.cvtColor(eye_region, cv2.COLOR_BGR2LAB)
                        l, a, b = cv2.split(lab)
                        
                        # Increase L channel brightness
                        l = cv2.add(l, 10)
                        l = np.clip(l, 0, 255).astype(np.uint8)
                        
                        lab = cv2.merge([l, a, b])
                        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                        
                        # Apply slight sharpening
                        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
                        sharpened = cv2.filter2D(enhanced, -1, kernel * 0.1)
                        
                        # Blend with original
                        result[y1:y2, x1:x2] = cv2.addWeighted(
                            enhanced, 0.8, sharpened, 0.2, 0
                        )
                
                logger.debug("Applied eye enhancement")
                return result
                
        except ImportError:
            logger.warning("MediaPipe not available for eye enhancement")
            return image
        except Exception as e:
            logger.error(f"Eye enhancement error: {e}")
            return image

    def whiten_teeth(self, image: np.ndarray) -> np.ndarray:
        """Whiten teeth in the mouth region.
        
        Uses face mesh to detect mouth and apply teeth whitening.
        
        Args:
            image: Input BGR image
            
        Returns:
            Image with whitened teeth
        """
        try:
            import mediapipe as mp
            mp_face = mp.solutions.face_mesh
            
            # Create face mesh detector
            with mp_face.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True
            ) as face_mesh:
                # Convert to RGB
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                results = face_mesh.process(rgb)
                
                if not results.multi_face_landmarks:
                    return image
                
                # Get landmarks
                landmarks = results.multi_face_landmarks[0]
                
                # Mouth landmarks: 13, 14 (upper lip), 78, 308 (corners)
                # Teeth region is between 13-14 and 78-308
                h, w = image.shape[:2]
                
                # Get mouth region bounding box
                mouth_indices = list(range(13, 18)) + list(range(78, 85)) + list(range(308, 315))
                xs = [int(landmarks[i].x * w) for i in mouth_indices if i < len(landmarks)]
                ys = [int(landmarks[i].y * h) for i in mouth_indices if i < len(landmarks)]
                
                if not xs or not ys:
                    return image
                
                # Expand box slightly for teeth region
                margin = 8
                x1 = max(0, min(xs) - margin)
                x2 = min(w, max(xs) + margin)
                y1 = max(0, min(ys))
                y2 = min(h, max(ys) + margin * 2)
                
                if x2 > x1 and y2 > y1 and (y2 - y1) < 100:
                    mouth_region = image[y1:y2, x1:x2]
                    
                    # Convert to LAB color space
                    lab = cv2.cvtColor(mouth_region, cv2.COLOR_BGR2LAB)
                    l, a, b = cv2.split(lab)
                    
                    # Increase L channel slightly and shift A channel (more white)
                    l = cv2.add(l, 5)
                    a = cv2.add(a, 3)  # Slightly more red-yellow
                    b = cv2.add(b, 5)   # Slightly more yellow
                    
                    l = np.clip(l, 0, 255).astype(np.uint8)
                    a = np.clip(a, 0, 255).astype(np.uint8)
                    b = np.clip(b, 0, 255).astype(np.uint8)
                    
                    lab = cv2.merge([l, a, b])
                    whitened = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                    
                    # Create soft mask for blending
                    mask = np.ones((y2 - y1, x2 - x1), dtype=np.float32) * 0.4
                    mask = cv2.GaussianBlur(mask, (15, 15), 0)
                    mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)
                    
                    # Blend with original
                    result = image.copy()
                    original_region = result[y1:y2, x1:x2].astype(np.float32)
                    whitened_float = whitened.astype(np.float32)
                    mask_float = mask.astype(np.float32) / 255.0
                    
                    blended = original_region * (1 - mask_float) + whitened_float * mask_float
                    result[y1:y2, x1:x2] = np.clip(blended, 0, 255).astype(np.uint8)
                    
                    logger.debug("Applied teeth whitening")
                    return result
                
                return image
                
        except ImportError:
            logger.warning("MediaPipe not available for teeth whitening")
            return image
        except Exception as e:
            logger.error(f"Teeth whitening error: {e}")
            return image

    def process(
        self,
        image: np.ndarray,
        skin_smoothing: bool = True,
        brightness_auto: bool = True,
        hair_smoothing: bool = True,
        eye_enhancement: bool = False,
        teeth_whitening: bool = False
    ) -> np.ndarray:
        """Full beautification pipeline.

        Args:
            image: Input BGR image
            skin_smoothing: Enable skin smoothing
            brightness_auto: Enable auto brightness/contrast
            hair_smoothing: Enable hair edge smoothing
            eye_enhancement: Enable eye enhancement
            teeth_whitening: Enable teeth whitening

        Returns:
            Beautified image
        """
        result = image.copy()

        if brightness_auto:
            result = self.auto_brightness_contrast(result)
            logger.debug("Applied auto brightness/contrast")

        if skin_smoothing:
            result = self.smooth_skin(result)
            logger.debug(f"Applied skin smoothing (level={self.level})")

        if hair_smoothing:
            result = self.smooth_hair_edges(result)
            logger.debug("Applied hair edge smoothing")

        if eye_enhancement:
            result = self.enhance_eyes(result)
            logger.debug("Applied eye enhancement")

        if teeth_whitening:
            result = self.whiten_teeth(result)
            logger.debug("Applied teeth whitening")

        return result
