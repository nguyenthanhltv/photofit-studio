"""Main image processing pipeline - orchestrates all processing steps."""

import cv2
import numpy as np
import logging
from typing import Optional, Tuple

from .face_detector import FaceDetector
from .beautifier import Beautifier
from .background import BackgroundProcessor
from .resizer import Resizer
from .ai_enhancer import AIEnhancer

logger = logging.getLogger("image_processor")

class ImageProcessor:
    """Single image processing pipeline for ID photos."""

    def __init__(self, config: dict):
        self.config = config
        self.face_detector = FaceDetector()
        self.beautifier = Beautifier(config.get("beautify", {}).get("level", "medium"))
        self.background = BackgroundProcessor()
        self.resizer = Resizer()
        # AI Enhancement module
        ai_level = config.get("ai_enhance", {}).get("level", "medium")
        self.ai_enhancer = AIEnhancer(ai_level)

    def update_config(self, config: dict) -> None:
        """Update processing configuration."""
        self.config = config
        level = config.get("beautify", {}).get("level", "medium")
        self.beautifier.set_level(level)
        # Update AI enhancer level
        ai_level = config.get("ai_enhance", {}).get("level", "medium")
        self.ai_enhancer.set_level(ai_level)

    def process_image(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], dict]:
        """Process a single image through the full pipeline.

        Pipeline order:
        1. Beautification (skin smooth, brightness, hair)
        2. Background removal & replacement
        3. AI Enhancement (NEW: sharpen, colors, denoise, super resolution)
        4. Face detection, alignment & center crop
        5. Resize to target dimensions

        Args:
            image: Input BGR image

        Returns:
            Tuple of (processed_image, status_dict)
            status_dict contains: success, steps_applied, error
        """
        status = {"success": False, "steps_applied": [], "error": None}
        result = image.copy()
        beautify_cfg = self.config.get("beautify", {})
        bg_cfg = self.config.get("background", {})
        resize_cfg = self.config.get("resize", {})
        ai_cfg = self.config.get("ai_enhance", {})

        try:
            # Step 1: Beautification (before face crop so we work on full image)
            if beautify_cfg.get("enabled", True):
                result = self.beautifier.process(
                    result,
                    skin_smoothing=beautify_cfg.get("skin_smoothing", True),
                    brightness_auto=beautify_cfg.get("brightness_auto", True),
                    hair_smoothing=beautify_cfg.get("hair_smoothing", True)
                )
                status["steps_applied"].append("beautify")

            # Step 2: Background removal & replacement
            if bg_cfg.get("enabled", True):
                color = bg_cfg.get("color", "#FFFFFF")
                edge_ref = bg_cfg.get("edge_refinement", True)
                refine_level = bg_cfg.get("refine_level", "high")  # NEW: edge refinement level
                result = self.background.process(result, color, edge_ref, refine_level)
                status["steps_applied"].append("background")

            # Step 2.5: AI Enhancement (NEW - improves overall quality)
            if ai_cfg.get("enabled", True):
                result = self.ai_enhancer.process(
                    result,
                    enhance_sharpness=ai_cfg.get("enhance_sharpness", True),
                    enhance_colors=ai_cfg.get("enhance_colors", True),
                    denoise=ai_cfg.get("denoise", True),
                    super_resolve=ai_cfg.get("super_resolution", False),
                    scale=ai_cfg.get("scale", 2),
                    auto_exposure=ai_cfg.get("auto_exposure", True)
                )
                status["steps_applied"].append("ai_enhance")

            # Step 3: Face detection, alignment & center crop
            target_w = resize_cfg.get("width_px", 354)
            target_h = resize_cfg.get("height_px", 472)
            auto_subject_fit = resize_cfg.get("auto_subject_fit", True)
            distance_level = resize_cfg.get("distance_level", "medium")
            resize_enabled = resize_cfg.get("enabled", True)

            if resize_enabled and auto_subject_fit:
                face_result, _face_info = self.face_detector.process(
                    result,
                    target_w,
                    target_h,
                    distance_level=distance_level,
                )

                if face_result is not None:
                    result = face_result
                    status["steps_applied"].append(f"face_crop_{distance_level}")
                    logger.debug(f"Applied auto subject fit: {distance_level}")
                else:
                    result = self.resizer.process(
                        result,
                        target_w,
                        target_h,
                        maintain_aspect=resize_cfg.get("maintain_aspect", True),
                    )
                    status["steps_applied"].append("resize_only")
                    logger.warning("No face detected, applied basic resize")
            elif resize_enabled:
                # Manual resize mode without auto subject fitting
                result = self.resizer.process(
                    result,
                    target_w,
                    target_h,
                    maintain_aspect=resize_cfg.get("maintain_aspect", True)
                )
                status["steps_applied"].append("resize_only")
                logger.info("Auto subject fit disabled, used basic resize")

            if not resize_enabled:
                # Keep original size if resize disabled
                status["steps_applied"].append("keep_original_size")

            status["success"] = True

        except Exception as e:
            status["error"] = str(e)
            logger.error(f"Processing error: {e}")

        return result, status

    def process_file(self, input_path: str) -> Tuple[Optional[np.ndarray], dict]:
        """Load and process an image file.

        Args:
            input_path: Path to input image

        Returns:
            Tuple of (processed_image, status_dict)
        """
        image = cv2.imread(input_path)
        if image is None:
            return None, {"success": False, "steps_applied": [], "error": f"Cannot read: {input_path}"}

        return self.process_image(image)

    def save_result(self, image: np.ndarray, output_path: str) -> str:
        """Save processed image with configured DPI and format.

        Args:
            image: Processed BGR image
            output_path: Output file path

        Returns:
            Output file path
        """
        resize_cfg = self.config.get("resize", {})
        output_cfg = self.config.get("output", {})

        dpi = resize_cfg.get("dpi", 300)
        fmt = output_cfg.get("format", "jpg")
        quality = output_cfg.get("quality", 95)

        return self.resizer.save_with_dpi(image, output_path, dpi, fmt, quality)

    def close(self):
        """Release all resources."""
        self.face_detector.close()