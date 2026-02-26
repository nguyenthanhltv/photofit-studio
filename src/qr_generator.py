"""QR Code generator for PhotoFit Studio.

Generates QR codes containing student information for ID card processing.
"""

import os
from typing import Optional, Tuple
import numpy as np

# Try to import qrcode, provide fallback if not available
try:
    import qrcode
    from qrcode.image.styledpil import StyledPilImage
    from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, SquareModuleDrawer
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False


class QRGenerator:
    """QR Code generator for student information."""
    
    def __init__(self):
        self.qrcode_available = QRCODE_AVAILABLE
        
        if not QRCODE_AVAILABLE:
            import logging
            logging.warning("qrcode library not available. Install with: pip install qrcode[pil]")
    
    def generate(
        self,
        student_id: str,
        name: str = "",
        data: dict = None,
        box_size: int = 10,
        border: int = 4,
        output_path: Optional[str] = None
    ) -> Optional[np.ndarray]:
        """Generate QR code from student information.
        
        Args:
            student_id: Student ID (MSSV)
            name: Student name (optional)
            data: Additional data dict (optional)
            box_size: QR code box size
            border: QR code border size
            output_path: Save path (optional)
            
        Returns:
            QR code as numpy array (BGR) or None if failed
        """
        if not self.qrcode_available:
            return None
        
        # Build QR data
        qr_data = self._build_data(student_id, name, data)
        
        try:
            # Create QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=box_size,
                border=border,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Generate image with rounded style
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer()
            )
            
            # Convert to numpy array (BGR for OpenCV)
            img_array = np.array(img)
            if len(img_array.shape) == 2:
                # Grayscale - convert to BGR
                img_bgr = np.stack([img_array] * 3, axis=-1)
            else:
                # RGB - convert to BGR
                img_bgr = img_array[:, :, ::-1]
            
            # Save if output path provided
            if output_path:
                # Save as RGB for PIL
                import cv2
                cv2.imwrite(output_path, img_bgr)
            
            return img_bgr
            
        except Exception as e:
            import logging
            logging.error(f"QR generation error: {e}")
            return None
    
    def generate_simple(
        self,
        data: str,
        box_size: int = 10,
        border: int = 4,
        output_path: Optional[str] = None
    ) -> Optional[np.ndarray]:
        """Generate QR code from simple string data.
        
        Args:
            data: String data to encode
            box_size: QR code box size
            border: QR code border size
            output_path: Save path (optional)
            
        Returns:
            QR code as numpy array (BGR) or None if failed
        """
        if not self.qrcode_available:
            return None
        
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=box_size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer()
            )
            
            img_array = np.array(img)
            if len(img_array.shape) == 2:
                img_bgr = np.stack([img_array] * 3, axis=-1)
            else:
                img_bgr = img_array[:, :, ::-1]
            
            if output_path:
                import cv2
                cv2.imwrite(output_path, img_bgr)
            
            return img_bgr
            
        except Exception as e:
            import logging
            logging.error(f"QR generation error: {e}")
            return None
    
    def generate_with_logo(
        self,
        student_id: str,
        name: str = "",
        data: dict = None,
        logo_path: Optional[str] = None,
        logo_size: int = 80,
        output_path: Optional[str] = None
    ) -> Optional[np.ndarray]:
        """Generate QR code with logo in center.
        
        Args:
            student_id: Student ID
            name: Student name
            data: Additional data dict
            logo_path: Path to logo image
            logo_size: Logo size in pixels
            output_path: Save path
            
        Returns:
            QR code with logo as numpy array (BGR)
        """
        if not self.qrcode_available:
            return None
        
        qr_data = self._build_data(student_id, name, data)
        
        try:
            qr = qrcode.QRCode(
                version=2,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=2,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Generate with logo
            from PIL import Image
            
            img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=RoundedModuleDrawer()
            )
            
            # Add logo if provided
            if logo_path and os.path.exists(logo_path):
                logo = Image.open(logo_path)
                logo = logo.convert("RGBA")
                
                # Resize logo
                logo.thumbnail((logo_size, logo_size), Image.Resampling.LANCZOS)
                
                # Calculate position
                pos = ((img.size[0] - logo.size[0]) // 2,
                       (img.size[1] - logo.size[1]) // 2)
                
                # Paste logo
                img.paste(logo, pos, logo)
            
            # Convert to numpy
            img_array = np.array(img)
            if len(img_array.shape) == 2:
                img_bgr = np.stack([img_array] * 3, axis=-1)
            else:
                img_bgr = img_array[:, :, ::-1]
            
            if output_path:
                import cv2
                cv2.imwrite(output_path, img_bgr)
            
            return img_bgr
            
        except Exception as e:
            import logging
            logging.error(f"QR generation with logo error: {e}")
            return None
    
    def _build_data(self, student_id: str, name: str, data: dict) -> str:
        """Build QR data string from parameters."""
        # Build JSON-like string
        parts = [f"mssv:{student_id}"]
        
        if name:
            parts.append(f"name:{name}")
        
        if data:
            for key, value in data.items():
                parts.append(f"{key}:{value}")
        
        return "|".join(parts)
    
    @staticmethod
    def parse_qr_data(qr_data: str) -> dict:
        """Parse QR data string back to dict.
        
        Args:
            qr_data: QR data string
            
        Returns:
            Parsed dict
        """
        result = {}
        parts = qr_data.split("|")
        
        for part in parts:
            if ":" in part:
                key, value = part.split(":", 1)
                result[key] = value
        
        return result
    
    def is_available(self) -> bool:
        """Check if QR code generation is available."""
        return self.qrcode_available


# Standalone function for simple use
def generate_student_qr(
    student_id: str,
    name: str = "",
    output_path: Optional[str] = None
) -> Optional[np.ndarray]:
    """Generate QR code for student.
    
    Args:
        student_id: Student ID (MSSV)
        name: Student name
        output_path: Save path
        
    Returns:
        QR code as numpy array
    """
    generator = QRGenerator()
    return generator.generate(student_id, name, output_path=output_path)
