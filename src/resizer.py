"""Image resize and DPI management module."""

import cv2
import numpy as np
import logging
from PIL import Image
from io import BytesIO

logger = logging.getLogger("image_processor")

class Resizer:
    """Resize images to ID photo preset dimensions with DPI support."""

    def resize(
        self,
        image: np.ndarray,
        width: int,
        height: int,
        maintain_aspect: bool = True
    ) -> np.ndarray:
        """Resize image to target dimensions.

        Args:
            image: Input BGR image
            width: Target width in pixels
            height: Target height in pixels
            maintain_aspect: If True, pad to maintain aspect ratio

        Returns:
            Resized image
        """
        img_h, img_w = image.shape[:2]

        if maintain_aspect:
            # Calculate scale to fit within target while maintaining aspect
            scale = min(width / img_w, height / img_h)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)

            resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

            # Center on canvas
            canvas = np.full((height, width, 3), 255, dtype=np.uint8)
            x_off = (width - new_w) // 2
            y_off = (height - new_h) // 2
            canvas[y_off:y_off + new_h, x_off:x_off + new_w] = resized
            return canvas
        else:
            return cv2.resize(image, (width, height), interpolation=cv2.INTER_LANCZOS4)

    def save_with_dpi(
        self,
        image: np.ndarray,
        output_path: str,
        dpi: int = 300,
        fmt: str = "jpg",
        quality: int = 95
    ) -> str:
        """Save image with embedded DPI metadata using Pillow.

        Args:
            image: BGR image (numpy array)
            output_path: Output file path
            dpi: DPI value to embed
            fmt: Output format ('jpg' or 'png')
            quality: JPEG quality (1-100)

        Returns:
            Output file path
        """
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)

        save_kwargs = {"dpi": (dpi, dpi)}

        if fmt.lower() in ("jpg", "jpeg"):
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True
            pil_img = pil_img.convert("RGB")
        elif fmt.lower() == "png":
            save_kwargs["compress_level"] = 6

        pil_img.save(output_path, **save_kwargs)
        logger.debug(f"Saved {output_path} ({dpi} DPI, {fmt})")
        return output_path

    def process(
        self,
        image: np.ndarray,
        width: int = 354,
        height: int = 472,
        maintain_aspect: bool = True
    ) -> np.ndarray:
        """Resize image to target dimensions.

        Args:
            image: Input BGR image
            width: Target width pixels
            height: Target height pixels
            maintain_aspect: Maintain aspect ratio with padding

        Returns:
            Resized image
        """
        return self.resize(image, width, height, maintain_aspect)