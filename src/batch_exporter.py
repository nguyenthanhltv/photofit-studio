"""Batch exporter for PhotoFit Studio.

Exports processed images to multiple formats simultaneously.
"""

import os
from typing import List, Optional, Tuple
import numpy as np
import cv2
from pathlib import Path


class BatchExporter:
    """Batch export processed images to multiple formats."""
    
    SUPPORTED_FORMATS = ["jpg", "jpeg", "png", "bmp", "tiff", "webp"]
    
    def __init__(self):
        pass
    
    def export_single(
        self,
        image_path: str,
        output_folder: str,
        formats: List[str] = None,
        quality: int = 95,
        naming_pattern: str = "{name}"
    ) -> dict:
        """Export a single image to multiple formats.
        
        Args:
            image_path: Source image path
            output_folder: Output directory
            formats: List of formats to export (default: jpg, png)
            quality: JPEG quality (1-100)
            naming_pattern: Output naming pattern
            
        Returns:
            Dict with export results
        """
        if formats is None:
            formats = ["jpg", "png"]
        
        img = cv2.imread(image_path)
        if img is None:
            return {"success": False, "error": "Cannot read image"}
        
        base_name = Path(image_path).stem
        results = {}
        
        os.makedirs(output_folder, exist_ok=True)
        
        for fmt in formats:
            if fmt.lower() not in self.SUPPORTED_FORMATS:
                continue
            
            # Build output name
            output_name = naming_pattern.replace("{name}", base_name)
            output_path = os.path.join(output_folder, f"{output_name}.{fmt.lower()}")
            
            # Save with format-specific settings
            success = self._save_with_format(img, output_path, fmt, quality)
            results[fmt] = success
        
        return {"success": True, "results": results}
    
    def export_batch(
        self,
        image_paths: List[str],
        output_folder: str,
        formats: List[str] = None,
        quality: int = 95,
        naming_pattern: str = "{name}",
        create_subfolders: bool = False,
        on_progress: Optional[callable] = None
    ) -> dict:
        """Export multiple images to multiple formats.
        
        Args:
            image_paths: List of source image paths
            output_folder: Output directory
            formats: List of formats to export
            quality: JPEG quality
            naming_pattern: Output naming pattern
            create_subfolders: Create subfolder per format
            on_progress: Progress callback(current, total)
            
        Returns:
            Dict with export results
        """
        if formats is None:
            formats = ["jpg", "png"]
        
        results = {
            "total": len(image_paths),
            "success": 0,
            "failed": 0,
            "by_format": {fmt: 0 for fmt in formats},
            "errors": []
        }
        
        for idx, image_path in enumerate(image_paths):
            if not os.path.exists(image_path):
                results["failed"] += 1
                results["errors"].append(f"File not found: {image_path}")
                continue
            
            # Create format subfolders if needed
            if create_subfolders:
                for fmt in formats:
                    fmt_folder = os.path.join(output_folder, fmt.upper())
                    os.makedirs(fmt_folder, exist_ok=True)
            else:
                os.makedirs(output_folder, exist_ok=True)
            
            # Export to each format
            for fmt in formats:
                try:
                    img = cv2.imread(image_path)
                    if img is None:
                        continue
                    
                    base_name = Path(image_path).stem
                    output_name = naming_pattern.replace("{name}", base_name)
                    
                    if create_subfolders:
                        output_path = os.path.join(
                            output_folder, fmt.upper(), f"{output_name}.{fmt.lower()}"
                        )
                    else:
                        output_path = os.path.join(
                            output_folder, f"{output_name}.{fmt.lower()}"
                        )
                    
                    if self._save_with_format(img, output_path, fmt, quality):
                        results["by_format"][fmt] += 1
                        results["success"] += 1
                    else:
                        results["failed"] += 1
                        
                except Exception as e:
                    results["failed"] += 1
                    results["errors"].append(f"{image_path}: {str(e)}")
            
            if on_progress:
                on_progress(idx + 1, len(image_paths))
        
        return results
    
    def export_with_variants(
        self,
        image_paths: List[str],
        output_folder: str,
        variants: List[dict] = None,
        on_progress: Optional[callable] = None
    ) -> dict:
        """Export images with different processing variants.
        
        Args:
            image_paths: List of source image paths
            output_folder: Output directory
            variants: List of variant configs (size, format, quality)
            on_progress: Progress callback
            
        Returns:
            Dict with export results
        """
        if variants is None:
            variants = [
                {"name": "original", "format": "jpg", "quality": 95},
                {"name": "thumb", "format": "jpg", "quality": 85, "size": (200, 300)},
                {"name": "web", "format": "png", "quality": 90, "size": (800, 1200)},
            ]
        
        results = {
            "total": len(image_paths) * len(variants),
            "success": 0,
            "failed": 0,
            "by_variant": {v["name"]: 0 for v in variants}
        }
        
        for idx, image_path in enumerate(image_paths):
            img = cv2.imread(image_path)
            if img is None:
                results["failed"] += len(variants)
                continue
            
            base_name = Path(image_path).stem
            
            for variant in variants:
                try:
                    variant_img = img.copy()
                    variant_name = variant.get("name", "variant")
                    fmt = variant.get("format", "jpg")
                    quality = variant.get("quality", 95)
                    
                    # Resize if specified
                    if "size" in variant:
                        variant_img = cv2.resize(
                            variant_img, 
                            variant["size"],
                            interpolation=cv2.INTER_LANCZOS4
                        )
                    
                    output_name = f"{base_name}_{variant_name}"
                    output_path = os.path.join(
                        output_folder, f"{output_name}.{fmt.lower()}"
                    )
                    
                    os.makedirs(output_folder, exist_ok=True)
                    
                    if self._save_with_format(variant_img, output_path, fmt, quality):
                        results["success"] += 1
                        results["by_variant"][variant_name] += 1
                    else:
                        results["failed"] += 1
                        
                except Exception as e:
                    results["failed"] += 1
            
            if on_progress:
                on_progress(idx + 1, len(image_paths))
        
        return results
    
    def export_pdf(
        self,
        image_paths: List[str],
        output_path: str,
        images_per_page: int = 1,
        page_size: Tuple[int, int] = None
    ) -> bool:
        """Export images as PDF.
        
        Args:
            image_paths: List of image paths
            output_path: Output PDF path
            images_per_page: Number of images per page
            page_size: Page size (width, height) in pixels
            
        Returns:
            True if successful
        """
        try:
            from PIL import Image
            
            images = []
            for path in image_paths:
                if not os.path.exists(path):
                    continue
                
                img = Image.open(path)
                img = img.convert("RGB")
                
                if page_size:
                    img = img.resize(page_size, Image.Resampling.LANCZOS)
                
                images.append(img)
            
            if images:
                if images_per_page == 1:
                    # One image per page
                    images[0].save(
                        output_path,
                        save_all=True,
                        append_images=images[1:],
                        resolution=300.0
                    )
                else:
                    # Multiple images per page
                    self._save_multi_page_pdf(images, output_path, images_per_page)
                
                return True
                
        except Exception as e:
            import logging
            logging.error(f"PDF export error: {e}")
        
        return False
    
    def _save_multi_page_pdf(
        self,
        images: List,
        output_path: str,
        images_per_page: int
    ):
        """Save multiple images per page PDF."""
        from PIL import Image
        
        if not images:
            return
        
        # Calculate page size from first image
        page_w, page_h = images[0].size
        
        # Create pages
        pages = []
        current_page = Image.new("RGB", (page_w, page_h * images_per_page), (255, 255, 255))
        
        for idx, img in enumerate(images):
            page_idx = idx // images_per_page
            img_idx = idx % images_per_page
            
            # Resize image to fit half page
            img_resized = img.resize(
                (page_w, page_h),
                Image.Resampling.LANCZOS
            )
            
            # Create new page if needed
            if img_idx == 0:
                if idx > 0:
                    pages.append(current_page)
                current_page = Image.new("RGB", (page_w, page_h * images_per_page), (255, 255, 255))
            
            # Paste image
            y_pos = img_idx * page_h
            current_page.paste(img_resized, (0, y_pos))
        
        # Add last page
        if current_page:
            pages.append(current_page)
        
        # Save PDF
        if pages:
            pages[0].save(
                output_path,
                save_all=True,
                append_images=pages[1:],
                resolution=300.0
            )
    
    def _save_with_format(
        self,
        img: np.ndarray,
        output_path: str,
        fmt: str,
        quality: int
    ) -> bool:
        """Save image with specific format and quality."""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            fmt = fmt.lower()
            
            if fmt in ["jpg", "jpeg"]:
                # Determine quality range (OpenCV uses 0-100, but 95 is good default)
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
                result, encoded = cv2.imencode(f".{fmt}", img, encode_param)
                if result:
                    with open(output_path, 'wb') as f:
                        f.write(encoded)
                    return True
                    
            elif fmt == "png":
                # PNG compression (0-9)
                png_quality = max(0, min(9, (100 - quality) // 10))
                encode_param = [int(cv2.IMWRITE_PNG_COMPRESSION), png_quality]
                result, encoded = cv2.imencode(f".{fmt}", img, encode_param)
                if result:
                    with open(output_path, 'wb') as f:
                        f.write(encoded)
                    return True
                    
            elif fmt in ["bmp", "tiff"]:
                result, encoded = cv2.imencode(f".{fmt}", img)
                if result:
                    with open(output_path, 'wb') as f:
                        f.write(encoded)
                    return True
                    
            elif fmt == "webp":
                encode_param = [int(cv2.IMWRITE_WEBP_QUALITY), quality]
                result, encoded = cv2.imencode(f".{fmt}", img, encode_param)
                if result:
                    with open(output_path, 'wb') as f:
                        f.write(encoded)
                    return True
            
            return False
            
        except Exception as e:
            import logging
            logging.error(f"Save error ({fmt}): {e}")
            return False


# Standalone function for simple use
def export_images(
    image_paths: List[str],
    output_folder: str,
    formats: List[str] = None
) -> dict:
    """Quick batch export function."""
    exporter = BatchExporter()
    return exporter.export_batch(image_paths, output_folder, formats)
