"""Utility functions for Image Processor."""

import os
import logging
from pathlib import Path
from typing import List, Tuple

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

logger = logging.getLogger("image_processor")


def scan_images(folder_path: str) -> List[str]:
    """Scan folder for supported image files. Returns sorted list of absolute paths."""
    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        logger.warning(f"Folder not found or not a directory: {folder_path}")
        return []

    images = []
    for f in folder.iterdir():
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
            images.append(str(f.resolve()))

    images.sort()
    logger.info(f"Found {len(images)} images in {folder_path}")
    return images


def ensure_output_dir(output_path: str) -> str:
    """Create output directory if it doesn't exist. Returns absolute path."""
    path = Path(output_path)
    path.mkdir(parents=True, exist_ok=True)
    return str(path.resolve())


def build_output_filename(
    original_path: str,
    naming_pattern: str,
    output_format: str,
    output_dir: str,
    overwrite: bool = False
) -> str:
    """Build output filename from original path and config settings.

    Args:
        original_path: Path to original image
        naming_pattern: Pattern like '{name}_processed'
        output_format: 'jpg' or 'png'
        output_dir: Output directory path
        overwrite: Whether to overwrite existing files

    Returns:
        Full output file path
    """
    stem = Path(original_path).stem
    ext = f".{output_format.lower()}"
    name = naming_pattern.replace("{name}", stem)
    out_path = Path(output_dir) / f"{name}{ext}"

    if not overwrite:
        counter = 1
        while out_path.exists():
            out_path = Path(output_dir) / f"{name}_{counter}{ext}"
            counter += 1

    return str(out_path)


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return (255, 255, 255)
    try:
        return tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    except ValueError:
        return (255, 255, 255)


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB values to hex color string."""
    return f"#{r:02x}{g:02x}{b:02x}"


def setup_logging(log_file: str = None, level: int = logging.INFO) -> None:
    """Setup logging for the application."""
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers = [logging.StreamHandler()]

    if log_file:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(level=level, format=fmt, handlers=handlers)


def validate_image(file_path: str) -> bool:
    """Quick check if file is a valid image by reading header bytes."""
    try:
        with open(file_path, "rb") as f:
            header = f.read(16)

        # JPEG
        if header[:2] == b"\xff\xd8":
            return True
        # PNG
        if header[:8] == b"\x89PNG\r\n\x1a\n":
            return True
        # BMP
        if header[:2] == b"BM":
            return True
        # WebP
        if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
            return True

        return False
    except (IOError, OSError):
        return False


def format_time(seconds: float) -> str:
    """Format seconds into human readable string."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"