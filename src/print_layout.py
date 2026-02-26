"""Print layout generator for PhotoFit Studio.

Creates print layouts for ID photos (A4, 4x6, 2x3, etc.)
"""

import os
from typing import List, Tuple, Optional
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont


class PrintLayout:
    """Generate print layouts for ID photos."""
    
    # Standard paper sizes in mm
    PAPER_SIZES = {
        "A4": (210, 297),
        "A5": (148, 210),
        "4x6": (101.6, 152.4),
        "Letter": (215.9, 279.4),
    }
    
    # Standard photo sizes in mm
    PHOTO_SIZES = {
        "2x3": (20.3, 30.5),
        "3x4": (30.5, 40.6),
        "4x6": (40.6, 60.96),
        "passport": (35, 45),
    }
    
    # DPI for printing
    PRINT_DPI = 300
    
    def __init__(self):
        pass
    
    def mm_to_pixels(self, mm: float, dpi: int = None) -> int:
        """Convert millimeters to pixels at given DPI."""
        dpi = dpi or self.PRINT_DPI
        return int(mm / 25.4 * dpi)
    
    def create_a4_layout(
        self,
        image_paths: List[str],
        photo_size: str = "3x4",
        columns: int = 4,
        rows: int = 6,
        margin_mm: Tuple[float, float] = (10, 10),
        spacing_mm: float = 3,
        output_path: Optional[str] = None
    ) -> Optional[np.ndarray]:
        """Create A4 layout with photos.
        
        Args:
            image_paths: List of image file paths
            photo_size: Photo size key (2x3, 3x4, 4x6, passport)
            columns: Number of columns
            rows: Number of rows
            margin_mm: Margin (horizontal, vertical) in mm
            spacing_mm: Spacing between photos in mm
            output_path: Save path
            
        Returns:
            Layout as numpy array (BGR)
        """
        # Get sizes in pixels
        dpi = self.PRINT_DPI
        page_w = self.mm_to_pixels(self.PAPER_SIZES["A4"][0], dpi)
        page_h = self.mm_to_pixels(self.PAPER_SIZES["A4"][1], dpi)
        
        photo_w = self.mm_to_pixels(self.PHOTO_SIZES.get(photo_size, self.PHOTO_SIZES["3x4"])[0], dpi)
        photo_h = self.mm_to_pixels(self.PHOTO_SIZES.get(photo_size, self.PHOTO_SIZES["3x4"])[1], dpi)
        
        margin_h = self.mm_to_pixels(margin_mm[0], dpi)
        margin_v = self.mm_to_pixels(margin_mm[1], dpi)
        spacing = self.mm_to_pixels(spacing_mm, dpi)
        
        # Calculate grid
        grid_w = columns * photo_w + (columns - 1) * spacing
        grid_h = rows * photo_h + (rows - 1) * spacing
        
        # Center on page
        offset_x = (page_w - grid_w) // 2
        offset_y = (page_h - grid_h) // 2
        
        # Create white page
        page = np.ones((page_h, page_w, 3), dtype=np.uint8) * 255
        
        # Place photos
        idx = 0
        for row in range(rows):
            for col in range(columns):
                if idx >= len(image_paths):
                    break
                
                x = offset_x + col * (photo_w + spacing)
                y = offset_y + row * (photo_h + spacing)
                
                img = cv2.imread(image_paths[idx])
                if img is not None:
                    # Resize to photo size
                    img_resized = cv2.resize(img, (photo_w, photo_h))
                    page[y:y+photo_h, x:x+photo_w] = img_resized
                
                idx += 1
            
            if idx >= len(image_paths):
                break
        
        # Save if output path provided
        if output_path:
            cv2.imwrite(output_path, page)
        
        return page
    
    def create_single_photo(
        self,
        image_path: str,
        photo_size: str = "3x4",
        background_color: Tuple[int, int, int] = (255, 255, 255),
        output_path: Optional[str] = None
    ) -> Optional[np.ndarray]:
        """Create single photo at standard size.
        
        Args:
            image_path: Image file path
            photo_size: Photo size key
            background_color: Background color (BGR)
            output_path: Save path
            
        Returns:
            Photo as numpy array
        """
        photo_w = self.mm_to_pixels(self.PHOTO_SIZES.get(photo_size, self.PHOTO_SIZES["3x4"])[0])
        photo_h = self.mm_to_pixels(self.PHOTO_SIZES.get(photo_size, self.PHOTO_SIZES["3x4"])[1])
        
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        # Create background
        result = np.ones((photo_h, photo_w, 3), dtype=np.uint8)
        result[:] = background_color
        
        # Resize image to fit
        h, w = img.shape[:2]
        scale = min(photo_w / w, photo_h / h)
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        img_resized = cv2.resize(img, (new_w, new_h))
        
        # Center on background
        x = (photo_w - new_w) // 2
        y = (photo_h - new_h) // 2
        result[y:y+new_h, x:x+new_w] = img_resized
        
        if output_path:
            cv2.imwrite(output_path, result)
        
        return result
    
    def create_contact_sheet(
        self,
        image_paths: List[str],
        thumb_size: Tuple[int, int] = (150, 200),
        cols: int = 4,
        output_path: Optional[str] = None
    ) -> Optional[np.ndarray]:
        """Create contact sheet (thumbnail grid).
        
        Args:
            image_paths: List of image paths
            thumb_size: Thumbnail size (width, height)
            cols: Number of columns
            output_path: Save path
            
        Returns:
            Contact sheet as numpy array
        """
        if not image_paths:
            return None
        
        rows = (len(image_paths) + cols - 1) // cols
        thumb_w, thumb_h = thumb_size
        
        # Create canvas
        canvas_h = rows * thumb_h
        canvas_w = cols * thumb_w
        canvas = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 255
        
        for idx, path in enumerate(image_paths):
            img = cv2.imread(path)
            if img is None:
                continue
            
            row = idx // cols
            col = idx % cols
            
            # Resize to thumbnail
            thumb = cv2.resize(img, (thumb_w, thumb_h))
            
            y = row * thumb_h
            x = col * thumb_w
            canvas[y:y+thumb_h, x:x+thumb_w] = thumb
        
        if output_path:
            cv2.imwrite(output_path, canvas)
        
        return canvas
    
    def create_pdf_layout(
        self,
        image_paths: List[str],
        photo_size: str = "3x4",
        output_path: str = "layout.pdf"
    ) -> bool:
        """Create PDF layout for printing.
        
        Args:
            image_paths: List of image paths
            photo_size: Photo size key
            output_path: Output PDF path
            
        Returns:
            True if successful
        """
        try:
            from PIL import Image
            
            photo_w = self.mm_to_pixels(self.PHOTO_SIZES.get(photo_size, self.PHOTO_SIZES["3x4"])[0])
            photo_h = self.mm_to_pixels(self.PHOTO_SIZES.get(photo_size, self.PHOTO_SIZES["3x4"])[1])
            
            images = []
            for path in image_paths:
                img = Image.open(path)
                img = img.convert("RGB")
                img = img.resize((photo_w, photo_h), Image.Resampling.LANCZOS)
                images.append(img)
            
            if images:
                # Save first image as PDF
                images[0].save(
                    output_path,
                    save_all=True,
                    append_images=images[1:],
                    resolution=300.0,
                    quality=95
                )
                return True
        except Exception as e:
            import logging
            logging.error(f"PDF creation error: {e}")
        
        return False
    
    def calculate_layout(
        self,
        paper_size: str,
        photo_size: str,
        margin_mm: Tuple[float, float] = (10, 10),
        spacing_mm: float = 3
    ) -> dict:
        """Calculate layout parameters.
        
        Args:
            paper_size: Paper size key
            photo_size: Photo size key
            margin_mm: Margin (horizontal, vertical)
            spacing_mm: Spacing between photos
            
        Returns:
            Dict with layout parameters
        """
        dpi = self.PRINT_DPI
        
        paper_w = self.mm_to_pixels(self.PAPER_SIZES.get(paper_size, self.PAPER_SIZES["A4"])[0], dpi)
        paper_h = self.mm_to_pixels(self.PAPER_SIZES.get(paper_size, self.PAPER_SIZES["A4"])[1], dpi)
        
        photo_w = self.mm_to_pixels(self.PHOTO_SIZES.get(photo_size, self.PHOTO_SIZES["3x4"])[0], dpi)
        photo_h = self.mm_to_pixels(self.PHOTO_SIZES.get(photo_size, self.PHOTO_SIZES["3x4"])[1], dpi)
        
        margin_h = self.mm_to_pixels(margin_mm[0], dpi)
        margin_v = self.mm_to_pixels(margin_mm[1], dpi)
        spacing = self.mm_to_pixels(spacing_mm, dpi)
        
        available_w = paper_w - 2 * margin_h
        available_h = paper_h - 2 * margin_v
        
        cols = max(1, (available_w + spacing) // (photo_w + spacing))
        rows = max(1, (available_h + spacing) // (photo_h + spacing))
        
        return {
            "paper_size": paper_size,
            "photo_size": photo_size,
            "columns": cols,
            "rows": rows,
            "total_slots": cols * rows,
            "paper_dimensions_px": (paper_w, paper_h),
            "photo_dimensions_px": (photo_w, photo_h),
        }


# Standalone function for simple use
def create_print_layout(
    image_paths: List[str],
    photo_size: str = "3x4",
    output_path: str = "layout.jpg"
) -> Optional[np.ndarray]:
    """Create print layout from images.
    
    Args:
        image_paths: List of image paths
        photo_size: Photo size key
        output_path: Save path
        
    Returns:
        Layout as numpy array
    """
    layout = PrintLayout()
    return layout.create_a4_layout(image_paths, photo_size, output_path=output_path)
