"""Face detection and alignment module using MediaPipe Tasks API."""

import cv2
import numpy as np
import logging
import os
import urllib.request
from typing import Optional, Tuple, List

logger = logging.getLogger("image_processor")

# MediaPipe model file
_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/blaze_face_short_range.tflite"
_MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "models")
_MODEL_PATH = os.path.join(_MODEL_DIR, "blaze_face_short_range.tflite")


def _ensure_model():
    """Download the face detection model if not present."""
    if os.path.exists(_MODEL_PATH):
        return _MODEL_PATH
    os.makedirs(_MODEL_DIR, exist_ok=True)
    logger.info("Downloading face detection model...")
    urllib.request.urlretrieve(_MODEL_URL, _MODEL_PATH)
    logger.info("Face detection model downloaded.")
    return _MODEL_PATH


class FaceDetector:
    """Detect faces, align, and center-crop for ID photos."""

    DISTANCE_PROFILE = {
        "near": {"zoom": 1.12, "top_margin": 0.10},
        "medium": {"zoom": 1.00, "top_margin": 0.14},
        "far": {"zoom": 1.00, "top_margin": 0.18},
    }

    def __init__(self):
        self._detector = None

    def _get_detector(self):
        """Lazy-load MediaPipe face detection (Tasks API)."""
        if self._detector is None:
            import mediapipe as mp

            model_path = _ensure_model()
            base_options = mp.tasks.BaseOptions(model_asset_path=model_path)
            options = mp.tasks.vision.FaceDetectorOptions(
                base_options=base_options,
                min_detection_confidence=0.5,
            )
            self._detector = mp.tasks.vision.FaceDetector.create_from_options(options)
        return self._detector

    def detect_faces(self, image: np.ndarray) -> List[dict]:
        """Detect all faces in image.

        Returns list of dicts with keys:
            - bbox: (x, y, w, h) in pixels
            - confidence: detection confidence
            - landmarks: dict of landmark points
        """
        import mediapipe as mp

        detector = self._get_detector()
        h, w = image.shape[:2]
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        results = detector.detect(mp_image)

        faces = []
        if results.detections:
            for det in results.detections:
                bb = det.bounding_box
                x = max(0, bb.origin_x)
                y = max(0, bb.origin_y)
                bw = min(bb.width, w - x)
                bh = min(bb.height, h - y)

                landmarks = {}
                kps = det.keypoints
                if kps and len(kps) >= 2:
                    landmarks["left_eye"] = (int(kps[0].x * w), int(kps[0].y * h))
                    landmarks["right_eye"] = (int(kps[1].x * w), int(kps[1].y * h))
                if kps and len(kps) >= 3:
                    landmarks["nose"] = (int(kps[2].x * w), int(kps[2].y * h))

                score = det.categories[0].score if det.categories else 0.0

                faces.append({
                    "bbox": (x, y, bw, bh),
                    "confidence": score,
                    "landmarks": landmarks,
                })

        return faces

    def get_primary_face(self, image: np.ndarray) -> Optional[dict]:
        """Get the largest (closest) face in the image."""
        faces = self.detect_faces(image)
        if not faces:
            return None
        return max(faces, key=lambda f: f["bbox"][2] * f["bbox"][3])

    def align_face(self, image: np.ndarray, face: dict) -> np.ndarray:
        """Rotate image to align face horizontally based on eye positions."""
        landmarks = face.get("landmarks", {})
        left_eye = landmarks.get("left_eye")
        right_eye = landmarks.get("right_eye")

        if not left_eye or not right_eye:
            return image

        dx = right_eye[0] - left_eye[0]
        dy = right_eye[1] - left_eye[1]
        angle = np.degrees(np.arctan2(dy, dx))

        # Only align if tilt is significant but not extreme
        if abs(angle) < 0.5 or abs(angle) > 30:
            return image

        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

        cos_a = abs(matrix[0, 0])
        sin_a = abs(matrix[0, 1])
        new_w = int(h * sin_a + w * cos_a)
        new_h = int(h * cos_a + w * sin_a)
        matrix[0, 2] += (new_w - w) / 2
        matrix[1, 2] += (new_h - h) / 2

        # IMPORTANT:
        # Using reflective border can create duplicated body/head fragments
        # near image edges after rotation (visible as mirrored artifacts).
        # For ID photos, a clean solid fill is safer.
        aligned = cv2.warpAffine(
            image,
            matrix,
            (new_w, new_h),
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=(255, 255, 255),
        )
        return aligned

    def center_crop(
        self,
        image: np.ndarray,
        face: dict,
        target_w: int,
        target_h: int,
        distance_level: str = "medium"
    ) -> np.ndarray:
        """Crop image centered on face with proper ID photo framing.

        Args:
            image: Input image (BGR)
            face: Face detection result dict
            target_w: Target width in pixels
            target_h: Target height in pixels
            distance_level: near/medium/far composition profile

        Returns:
            Cropped image resized to target dimensions
        """
        img_h, img_w = image.shape[:2]
        x, y, fw, fh = face["bbox"]

        profile = self.DISTANCE_PROFILE.get(distance_level, self.DISTANCE_PROFILE["medium"])
        zoom = profile["zoom"]
        top_margin_ratio = profile["top_margin"]

        # Face center
        face_cx = x + fw // 2
        face_cy = y + fh // 2

        # Calculate minimal crop (keep maximum original composition)
        target_aspect = target_w / target_h

        src_aspect = img_w / img_h
        if src_aspect > target_aspect:
            # Source too wide -> crop width only
            base_crop_h = img_h
            base_crop_w = int(base_crop_h * target_aspect)
        else:
            # Source too tall/narrow -> crop height only
            base_crop_w = img_w
            base_crop_h = int(base_crop_w / target_aspect)

        # Optional gentle zoom for "near" while preserving composition for others
        crop_w = max(1, min(img_w, int(base_crop_w / zoom)))
        crop_h = max(1, min(img_h, int(base_crop_h / zoom)))

        # Keep aspect ratio exact after zoom quantization
        crop_h = min(crop_h, int(crop_w / target_aspect))
        crop_w = min(crop_w, int(crop_h * target_aspect))

        if crop_w <= 0 or crop_h <= 0:
            crop_w, crop_h = base_crop_w, base_crop_h

        # Position: face should be in upper-center of frame
        # Head top controlled by profile
        crop_top = face_cy - int(fh / 2) - int(crop_h * top_margin_ratio)
        crop_left = face_cx - crop_w // 2

        # Clamp to image bounds
        crop_top = max(0, min(crop_top, img_h - crop_h))
        crop_left = max(0, min(crop_left, img_w - crop_w))

        # Ensure crop doesn't exceed image
        crop_h = min(crop_h, img_h - crop_top)
        crop_w = min(crop_w, img_w - crop_left)

        cropped = image[crop_top:crop_top + crop_h, crop_left:crop_left + crop_w]

        # Resize to target
        result = cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)
        return result

    def process(
        self,
        image: np.ndarray,
        target_w: int = 354,
        target_h: int = 472,
        distance_level: str = "medium"
    ) -> Tuple[Optional[np.ndarray], Optional[dict]]:
        """Full face detection pipeline: detect → align → crop.

        Returns:
            Tuple of (processed_image, face_info) or (None, None) if no face found.
        """
        face = self.get_primary_face(image)
        if face is None:
            logger.warning("No face detected in image")
            return None, None

        aligned = self.align_face(image, face)

        # Re-detect face after alignment
        face_aligned = self.get_primary_face(aligned)
        if face_aligned is None:
            face_aligned = face
            aligned = image

        cropped = self.center_crop(aligned, face_aligned, target_w, target_h, distance_level=distance_level)
        return cropped, face_aligned

    def close(self):
        """Release resources."""
        if self._detector:
            self._detector.close()
            self._detector = None