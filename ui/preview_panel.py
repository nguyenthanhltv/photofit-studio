"""Before/After preview panel - Modern dark theme design."""

import cv2
import numpy as np
import customtkinter as ctk
from PIL import Image, ImageTk
from typing import Optional

from .fullscreen_viewer import FullscreenViewer

# Color palette (shared with main_window)
C_BG = "#0B0F19"
C_SURFACE = "#131825"
C_CARD = "#1A2035"
C_CARD_HOVER = "#1F2740"
C_BORDER = "#2A3352"
C_ACCENT = "#3B82F6"
C_ACCENT_HOVER = "#2563EB"
C_TEXT = "#E2E8F0"
C_TEXT_DIM = "#94A3B8"
C_TEXT_MUTED = "#64748B"

FONT = "Segoe UI"


class PreviewPanel(ctk.CTkFrame):
    """Displays before/after comparison of a single image - modern dark theme."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._build()
        self._before_img = None
        self._after_img = None
        self._empty_img = ctk.CTkImage(
            light_image=Image.new("RGB", (2, 2), color=(19, 24, 37)),
            dark_image=Image.new("RGB", (2, 2), color=(19, 24, 37)),
            size=(2, 2),
        )
        self._fullscreen_viewer: Optional[FullscreenViewer] = None

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        # ── Header row ──
        header = ctk.CTkFrame(self, fg_color="transparent", height=36)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(12, 0))
        header.columnconfigure(0, weight=1)
        header.columnconfigure(1, weight=0)

        ctk.CTkLabel(header, text="Preview", font=(FONT, 13, "bold"),
                     text_color=C_TEXT).grid(row=0, column=0, sticky="w")

        # Fullscreen button
        self.fullscreen_btn = ctk.CTkButton(
            header,
            text="⛶ Phóng to",
            width=100,
            height=28,
            fg_color=C_ACCENT,
            hover_color=C_ACCENT_HOVER,
            font=(FONT, 11),
            corner_radius=6,
            command=self._open_fullscreen,
        )
        self.fullscreen_btn.grid(row=0, column=1, sticky="e", padx=(8, 0))
        self.fullscreen_btn.configure(state="disabled")

        self.info_label = ctk.CTkLabel(header, text="", font=(FONT, 10),
                                        text_color=C_TEXT_MUTED)
        self.info_label.grid(row=0, column=2, sticky="e")

        # ── Column labels ──
        label_row = ctk.CTkFrame(self, fg_color="transparent")
        label_row.grid(row=1, column=0, columnspan=2, sticky="ew", padx=16, pady=(8, 4))
        label_row.columnconfigure(0, weight=1)
        label_row.columnconfigure(1, weight=1)

        ctk.CTkLabel(label_row, text="BEFORE", font=(FONT, 9, "bold"),
                     text_color=C_TEXT_MUTED).grid(row=0, column=0, sticky="w", padx=4)
        ctk.CTkLabel(label_row, text="AFTER", font=(FONT, 9, "bold"),
                     text_color=C_ACCENT).grid(row=0, column=1, sticky="w", padx=4)

        # ── Image containers ──
        self.before_label = ctk.CTkLabel(
            self, text="No image", fg_color=C_SURFACE,
            text_color=C_TEXT_MUTED, font=(FONT, 11),
            corner_radius=10, width=200, height=260,
        )
        self.before_label.grid(row=2, column=0, padx=(16, 6), pady=(0, 16), sticky="nsew")

        self.after_label = ctk.CTkLabel(
            self, text="No image", fg_color=C_SURFACE,
            text_color=C_TEXT_MUTED, font=(FONT, 11),
            corner_radius=10, width=200, height=260,
        )
        self.after_label.grid(row=2, column=1, padx=(6, 16), pady=(0, 16), sticky="nsew")

    def _cv2_to_ctk_image(self, cv_img: np.ndarray,
                           max_w: int = 240, max_h: int = 320) -> Optional[ctk.CTkImage]:
        """Convert OpenCV BGR image to CTkImage, fitting within max dimensions."""
        if cv_img is None:
            return None
        h, w = cv_img.shape[:2]
        scale = min(max_w / w, max_h / h, 1.0)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        resized = cv2.resize(cv_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(new_w, new_h))

    def set_before(self, cv_img: np.ndarray) -> None:
        """Set the 'before' preview image."""
        self._before_img = cv_img
        ctk_img = self._cv2_to_ctk_image(cv_img)
        if ctk_img:
            self.before_label.configure(image=ctk_img, text="")
            self.before_label._image = ctk_img  # prevent GC
        else:
            self.before_label.configure(image=self._empty_img, text="No image")
            self.before_label._image = self._empty_img
        self._update_fullscreen_button()

    def set_after(self, cv_img: np.ndarray) -> None:
        """Set the 'after' preview image."""
        self._after_img = cv_img
        ctk_img = self._cv2_to_ctk_image(cv_img)
        if ctk_img:
            self.after_label.configure(image=ctk_img, text="")
            self.after_label._image = ctk_img
        else:
            self.after_label.configure(image=self._empty_img, text="No image")
            self.after_label._image = self._empty_img
        self._update_fullscreen_button()

    def set_after_placeholder(self, text: str = "Đang chờ xử lý") -> None:
        """Show placeholder text safely without broken image references."""
        self._after_img = None
        self.after_label.configure(image=self._empty_img, text=text)
        self.after_label._image = self._empty_img
        self._update_fullscreen_button()

    def _update_fullscreen_button(self) -> None:
        """Enable/disable fullscreen button based on available images."""
        has_before = self._before_img is not None
        has_after = self._after_img is not None
        
        if has_before or has_after:
            self.fullscreen_btn.configure(state="normal")
        else:
            self.fullscreen_btn.configure(state="disabled")

    def _open_fullscreen(self) -> None:
        """Open fullscreen viewer for before/after comparison."""
        # Make sure we have at least one image
        if self._before_img is None and self._after_img is None:
            return

        # Close existing viewer if any
        if self._fullscreen_viewer is not None:
            try:
                self._fullscreen_viewer.destroy()
            except:
                pass

        # Determine initial view mode based on available images
        has_before = self._before_img is not None
        has_after = self._after_img is not None
        
        # Create new fullscreen viewer (use placeholder if image not available)
        title = self.info_label.cget("text") or "Preview"
        
        # Use a blank image if after_img is not available
        after_img = self._after_img
        if after_img is None and has_before:
            # Create a copy of before image as placeholder
            after_img = self._before_img.copy()
        
        # Get image list and current index from parent if available
        image_list = []
        current_index = 0
        
        # Try to get image list from parent window
        try:
            parent = self.master
            if hasattr(parent, '_image_list'):
                image_list = parent._image_list
            if hasattr(parent, '_active_image_path') and image_list:
                current_index = image_list.index(parent._active_image_path) if parent._active_image_path in image_list else 0
        except:
            pass
        
        self._fullscreen_viewer = FullscreenViewer(
            self,
            before_img=self._before_img,
            after_img=after_img,
            title=title,
            has_before=has_before,
            has_after=has_after,
            image_list=image_list,
            current_index=current_index
        )
        
        # Set callback for image navigation
        self._fullscreen_viewer._on_navigate = self._on_fullscreen_navigate

    def _on_fullscreen_navigate(self, index: int) -> None:
        """Handle navigation from fullscreen viewer."""
        try:
            parent = self.master
            if hasattr(parent, '_image_list') and hasattr(parent, '_set_active_image'):
                image_list = parent._image_list
                if 0 <= index < len(image_list):
                    parent._set_active_image(image_list[index])
        except:
            pass

    def set_info(self, text: str) -> None:
        """Set info text in header."""
        self.info_label.configure(text=text)

    def clear(self) -> None:
        """Clear both previews."""
        self._before_img = None
        self._after_img = None
        self.before_label.configure(image=self._empty_img, text="No image")
        self.before_label._image = self._empty_img
        self.after_label.configure(image=self._empty_img, text="No image")
        self.after_label._image = self._empty_img
        self.info_label.configure(text="")
        self._update_fullscreen_button()
