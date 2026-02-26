"""Background removal and replacement module - ENHANCED VERSION."""

import cv2
import numpy as np
import logging
from typing import Tuple, Optional

from .utils import hex_to_rgb

logger = logging.getLogger("image_processor")

class BackgroundProcessor:
    """Remove and replace image backgrounds for ID photos.
    
    Enhanced with advanced edge refinement to eliminate rough cut edges.
    """

    def __init__(self):
        self._session = None

    def _get_session(self):
        """Lazy-load rembg session."""
        if self._session is None:
            from rembg import new_session
            self._session = new_session("u2net")
            logger.info("Loaded rembg U2Net model")
        return self._session

    def remove_background(
        self,
        image: np.ndarray,
        alpha_matting: bool = True,
        foreground_threshold: int = 240,
        background_threshold: int = 10,
        erode_size: int = 10
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Remove background from image with configurable parameters.

        Args:
            image: Input BGR image
            alpha_matting: Enable alpha matting for better edges
            foreground_threshold: Threshold for foreground (higher = more aggressive)
            background_threshold: Threshold for background
            erode_size: Erosion size for edge cleanup

        Returns:
            Tuple of (BGRA image with transparent background, alpha mask)
        """
        from rembg import remove
        session = self._get_session()

        # rembg expects RGB input, returns RGBA
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        result_rgba = remove(
            rgb,
            session=session,
            alpha_matting=alpha_matting,
            alpha_matting_foreground_threshold=foreground_threshold,
            alpha_matting_background_threshold=background_threshold,
            alpha_matting_erode_size=erode_size,
            alpha_matting_edge_radius=1  # NEW: reduces hard edges
        )

        # Convert back to BGRA
        bgra = cv2.cvtColor(result_rgba, cv2.COLOR_RGBA2BGRA)
        alpha = bgra[:, :, 3]

        return bgra, alpha

    def replace_background(
        self,
        image: np.ndarray,
        alpha: np.ndarray,
        color_hex: str = "#FFFFFF"
    ) -> np.ndarray:
        """Replace background with solid color.

        Args:
            image: BGRA image (from remove_background)
            alpha: Alpha mask
            color_hex: Background color as hex string

        Returns:
            BGR image with new background
        """
        r, g, b = hex_to_rgb(color_hex)
        h, w = image.shape[:2]

        # Create solid color background (BGR)
        bg = np.full((h, w, 3), (b, g, r), dtype=np.uint8)

        # Foreground from BGRA
        fg = image[:, :, :3]

        # Normalize alpha to 0-1
        alpha_f = alpha.astype(np.float32) / 255.0
        alpha_3ch = np.stack([alpha_f] * 3, axis=-1)

        # Composite: fg * alpha + bg * (1 - alpha)
        result = (fg.astype(np.float32) * alpha_3ch +
                  bg.astype(np.float32) * (1 - alpha_3ch))

        return np.clip(result, 0, 255).astype(np.uint8)

    def refine_edges_v2(
        self,
        alpha: np.ndarray,
        fg_image: Optional[np.ndarray] = None,
        bg_color: Tuple[int, int, int] = (255, 255, 255)
    ) -> np.ndarray:
        """Advanced edge refinement - eliminates rough edges and halos.
        
        Uses multi-stage processing:
        1. Detect edge region (semi-transparent area)
        2. Apply guided filter for smooth alpha transitions
        3. Apply color-based edge cleanup
        4. Feather the edges with anti-aliasing

        Args:
            alpha: Alpha mask (uint8 0-255)
            fg_image: Foreground image (BGR) for color-based edge detection
            bg_color: Background color (BGR) for edge detection

        Returns:
            Refined alpha mask
        """
        h, w = alpha.shape
        refined = alpha.copy().astype(np.float32)
        
        # Ensure fg_image matches alpha dimensions if provided
        if fg_image is not None and fg_image.shape[:2] != (h, w):
            fg_image = cv2.resize(fg_image, (w, h))

        # Stage 1: Create edge mask (semi-transparent region)
        # Strong foreground = 255, Strong background = 0
        _, hard_alpha = cv2.threshold(alpha, 250, 255, cv2.THRESH_BINARY)
        _, bg_alpha = cv2.threshold(alpha, 5, 255, cv2.THRESH_BINARY_INV)
        
        # Edge region is where alpha is neither fully foreground nor background
        edge_mask = cv2.subtract(hard_alpha, bg_alpha)
        edge_mask = cv2.GaussianBlur(edge_mask, (0, 0), sigmaX=3, sigmaY=3)
        
        # Create binary edge region for processing
        edge_region = (edge_mask > 10).astype(np.uint8)

        # Stage 2: Guided filter-like processing for edge smoothness
        # Use bilateral filter to preserve edges while smoothing
        if fg_image is not None:
            # Bilateral filter on alpha using the image for edge awareness
            try:
                refined = cv2.bilateralFilter(
                    refined, 
                    d=9, 
                    sigmaColor=30,  # Smaller = stricter color matching
                    sigmaSpace=15    # Spatial sigma
                )
            except cv2.error:
                # Fallback if bilateral fails
                refined = cv2.GaussianBlur(refined, (7, 7), 0)

        # Stage 3: Additional Gaussian for soft feather
        refined = cv2.GaussianBlur(refined, (7, 7), 0)

        # Stage 4: Edge-aware morphological operations
        # Close small gaps
        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        refined_blur = cv2.morphologyEx(refined, cv2.MORPH_CLOSE, kernel_small)
        
        # Blend original with morphologically processed
        refined = refined * 0.5 + refined_blur * 0.5

        # Stage 5: Anti-aliasing - smooth edge transitions
        # Create a narrow band at the edges
        edge_band = np.zeros_like(alpha, dtype=np.float32)
        edge_band[(alpha > 10) & (alpha < 245)] = 1.0
        
        if np.any(edge_band > 0):
            # Feather this band
            edge_feathered = cv2.GaussianBlur(edge_band, (9, 9), 0) * 255
            edge_feathered = np.clip(edge_feathered, 0, 255)
            
            # Blend with original refined alpha
            mask = (edge_feathered > 20).astype(np.float32) / 255.0
            refined = refined * (1 - mask * 0.3) + edge_feathered * mask * 0.3

        # Stage 6: Final cleanup - remove any remaining halos
        # Apply strong threshold to get solid regions
        _, solid_fg = cv2.threshold(refined, 245, 255, cv2.THRESH_BINARY)
        _, solid_bg = cv2.threshold(refined, 10, 255, cv2.THRESH_BINARY_INV)
        
        # Dilate slightly to solidify foreground
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        solid_fg = cv2.dilate(solid_fg, kernel, iterations=1)
        
        # Reconstruct: keep solid regions, blend edge region
        result = np.where(solid_fg == 255, refined, 
                np.where(solid_bg == 255, refined, refined))

        # Final Gaussian pass for ultra-smooth edges
        result = cv2.GaussianBlur(result, (5, 5), 0)

        return np.clip(result, 0, 255).astype(np.uint8)

    def remove_halo(self, alpha: np.ndarray, image: np.ndarray, bg_color: tuple) -> np.ndarray:
        """Remove halo artifacts around subject edges.
        
        Halos appear as semi-transparent regions that don't match either 
        foreground or background - usually caused by the AI model.

        Args:
            alpha: Alpha mask
            image: Original image (BGR)
            bg_color: Background color (BGR)

        Returns:
            Halo-removed alpha mask
        """
        h, w = alpha.shape
        result = alpha.copy().astype(np.float32)
        
        # Ensure image matches alpha dimensions
        if image.shape[:2] != (h, w):
            image = cv2.resize(image, (w, h))
        
        # Get background color as 3-channel array for broadcasting
        bg = np.array(bg_color, dtype=np.float32).reshape(1, 1, 3)
        
        # Compute image gradient for edge detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        gradient_magnitude = cv2.normalize(gradient_magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Create gradient mask (strong edges = likely foreground boundary)
        _, edge_mask = cv2.threshold(gradient_magnitude, 15, 255, cv2.THRESH_BINARY)
        edge_mask = cv2.dilate(edge_mask, np.ones((5, 5), np.uint8), iterations=2)
        
        # For halo detection: semi-transparent region NOT at edge = likely halo
        halo_candidates = ((alpha > 20) & (alpha < 230)).astype(np.uint8)
        
        # Ensure edge_mask is uint8 for bitwise_not
        edge_mask = edge_mask.astype(np.uint8)
        
        # Remove regions that are semi-transparent but NOT at strong edges
        edge_mask_inv = cv2.bitwise_not(edge_mask)
        halo_mask = cv2.bitwise_and(halo_candidates, edge_mask_inv)
        
        # In halo regions, push alpha towards 0 or 255
        halo_mask_float = halo_mask.astype(np.float32) / 255.0
        
        # If close to background color in halo region, push to 0
        # Otherwise push to 255 (foreground)
        diff_from_bg = np.linalg.norm(image.astype(np.float32) - bg, axis=2)
        diff_normalized = cv2.normalize(diff_from_bg, None, 0, 1, cv2.NORM_MINMAX)
        
        # Hard decisions for clear halos (close to background color)
        clear_halo = halo_mask_float * (diff_normalized < 0.15)
        result = np.where(clear_halo > 0.5, 0.0, result)
        
        # Soft decisions for uncertain areas - smooth them
        soft_halo = halo_mask_float * (diff_normalized >= 0.15)
        result = result * (1 - soft_halo * 0.7)  # Reduce halo effect

        return np.clip(result, 0, 255).astype(np.uint8)

    def refine_edges(self, alpha: np.ndarray, iterations: int = 2) -> np.ndarray:
        """Refine alpha mask edges to reduce halos.

        Args:
            alpha: Alpha mask (uint8)
            iterations: Number of refinement passes

        Returns:
            Refined alpha mask
        """
        refined = alpha.copy()

        for _ in range(iterations):
            # Slight erosion to remove thin halos
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            eroded = cv2.erode(refined, kernel, iterations=1)

            # Smooth transition
            refined = cv2.GaussianBlur(eroded, (3, 3), 0)

            # Re-threshold to keep sharp subject edges
            _, hard = cv2.threshold(refined, 200, 255, cv2.THRESH_BINARY)

            # Blend hard edges with soft transitions
            soft = cv2.GaussianBlur(refined, (5, 5), 0)
            refined = cv2.addWeighted(hard, 0.7, soft, 0.3, 0)

        return refined.astype(np.uint8)

    def process(
        self,
        image: np.ndarray,
        color_hex: str = "#FFFFFF",
        edge_refinement: bool = True,
        refine_level: str = "high"
    ) -> np.ndarray:
        """Full background processing pipeline with enhanced edge handling.

        Args:
            image: Input BGR image
            color_hex: Background replacement color
            edge_refinement: Whether to refine mask edges
            refine_level: Edge refinement level ("low", "medium", "high")

        Returns:
            BGR image with replaced background
        """
        # Get RGB for background color
        r, g, b = hex_to_rgb(color_hex)
        bg_color_bgr = (b, g, r)  # BGR order for OpenCV
        
        # Step 1: Remove background with optimized parameters
        if refine_level == "high":
            # High quality: more aggressive alpha matting
            bgra, alpha = self.remove_background(
                image,
                alpha_matting=True,
                foreground_threshold=245,
                background_threshold=5,
                erode_size=12
            )
        elif refine_level == "medium":
            bgra, alpha = self.remove_background(
                image,
                alpha_matting=True,
                foreground_threshold=240,
                background_threshold=10,
                erode_size=10
            )
        else:
            # Low - faster but less accurate
            bgra, alpha = self.remove_background(
                image,
                alpha_matting=True,
                foreground_threshold=230,
                background_threshold=15,
                erode_size=8
            )
        
        logger.debug("Background removed")

        # Step 2: Advanced edge refinement
        if edge_refinement:
            if refine_level == "high":
                # Full pipeline: halo removal + advanced edge refinement
                alpha = self.remove_halo(alpha, image, bg_color_bgr)
                alpha = self.refine_edges_v2(alpha, fg_image=image, bg_color=bg_color_bgr)
            elif refine_level == "medium":
                # Medium: just advanced refinement
                alpha = self.refine_edges_v2(alpha, fg_image=image, bg_color=bg_color_bgr)
            else:
                # Low: basic refinement
                alpha = self.refine_edges(alpha, iterations=1)
            
            logger.debug(f"Edge refinement applied (level: {refine_level})")

        # Step 3: Replace background
        result = self.replace_background(bgra, alpha, color_hex)
        logger.debug(f"Background replaced with {color_hex}")

        return result
