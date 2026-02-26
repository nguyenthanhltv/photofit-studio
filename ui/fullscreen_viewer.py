"""Fullscreen image viewer - Before/After comparison with zoom."""

import cv2
import numpy as np
import customtkinter as ctk
from PIL import Image
from typing import Optional, List

# Color palette (shared)
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


class FullscreenViewer(ctk.CTkToplevel):
    """
    Fullscreen dialog for before/after image comparison.
    Supports three view modes: BOTH | BEFORE | AFTER
    """

    def __init__(self, master, before_img: np.ndarray, after_img: np.ndarray, 
                 title: str = "Preview", has_before: bool = True, has_after: bool = True,
                 image_list: List[str] = None, current_index: int = 0):
        super().__init__(master)
        
        # Store copies of images to prevent them from being modified
        self._before_img = before_img.copy() if before_img is not None else None
        self._after_img = after_img.copy() if after_img is not None else None
        self._title = title
        self._has_before = has_before
        self._has_after = has_after
        self._view_mode = "BOTH"  # BOTH | BEFORE | AFTER
        self._zoom_level = 1.0
        
        # Navigation
        self._image_list = image_list or []
        self._current_index = current_index
        self._on_navigate = None  # Callback for navigation
        
        # Keep strong references to CTkImage objects
        self._left_ctk_image: Optional[ctk.CTkImage] = None
        self._right_ctk_image: Optional[ctk.CTkImage] = None

        # Auto-select mode based on available images
        if not has_after:
            self._view_mode = "BEFORE"
        elif not has_before:
            self._view_mode = "AFTER"

        self._setup_window()
        self._build_ui()
        self._show_current_view()

    def _setup_window(self):
        self.title(self._title)
        self.geometry(f"{self.winfo_screenwidth()}x{self.winfo_screenheight()}")
        self.attributes("-fullscreen", True)
        self.configure(fg_color=C_BG)
        self._is_maximized = True
        
        # Make window appear on top
        self.transient(self.master)
        self.grab_set()
        
        # Bind escape to close
        self.bind("<Escape>", lambda e: self.destroy())
        # Bind keyboard shortcuts
        self.bind("<Key-1>", lambda e: self._set_mode("BEFORE"))
        self.bind("<Key-2>", lambda e: self._set_mode("AFTER"))
        self.bind("<Key-3>", lambda e: self._set_mode("BOTH"))
        self.bind("<Key-q>", lambda e: self.destroy())
        self.bind("<Key-f>", lambda e: self._toggle_fullscreen())
        self.bind("<Left>", lambda e: self._prev_image())
        self.bind("<Right>", lambda e: self._next_image())
        # Mouse wheel for zoom
        self.bind("<MouseWheel>", self._on_mouse_wheel)

    def _toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        self._is_maximized = not self._is_maximized
        self.attributes("-fullscreen", self._is_maximized)
        if not self._is_maximized:
            self.geometry("1200x800")
        self._show_current_view()

    def _build_ui(self):
        # Main container
        self.container = ctk.CTkFrame(self, fg_color=C_BG)
        self.container.pack(fill="both", expand=True)

        # Header bar
        header = ctk.CTkFrame(self.container, height=56, fg_color=C_SURFACE, corner_radius=0)
        header.pack(fill="x", side="top")
        
        # Title
        ctk.CTkLabel(
            header, 
            text=f"📺 {self._title}",
            font=(FONT, 16, "bold"),
            text_color=C_TEXT
        ).pack(side="left", padx=20)

        # View mode buttons using SegmentedButton
        mode_frame = ctk.CTkFrame(header, fg_color="transparent")
        mode_frame.pack(side="left", padx=20)

        self.view_mode_var = ctk.StringVar(value=self._view_mode)
        
        # Create segmented button for view modes
        self.segmented_button = ctk.CTkSegmentedButton(
            mode_frame,
            values=["BEFORE", "AFTER", "BOTH"],
            variable=self.view_mode_var,
            fg_color=C_CARD,
            selected_color=C_ACCENT,
            unselected_color=C_CARD,
            text_color=C_TEXT,
            font=(FONT, 11),
            command=self._on_view_mode_changed,
        )
        self.segmented_button.pack()

        # Zoom controls
        zoom_frame = ctk.CTkFrame(header, fg_color="transparent")
        zoom_frame.pack(side="right", padx=(0, 10))

        ctk.CTkButton(
            zoom_frame, text="−", width=36, height=36,
            fg_color=C_CARD, hover_color=C_CARD_HOVER,
            border_width=1, border_color=C_BORDER,
            font=(FONT, 16, "bold"), corner_radius=8,
            command=self._zoom_out
        ).pack(side="left", padx=2)

        self.zoom_label = ctk.CTkLabel(
            zoom_frame, text="100%", width=60,
            font=(FONT, 11), text_color=C_TEXT_DIM
        )
        self.zoom_label.pack(side="left", padx=4)

        ctk.CTkButton(
            zoom_frame, text="+", width=36, height=36,
            fg_color=C_CARD, hover_color=C_CARD_HOVER,
            border_width=1, border_color=C_BORDER,
            font=(FONT, 16, "bold"), corner_radius=8,
            command=self._zoom_in
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            zoom_frame, text="↺", width=36, height=36,
            fg_color=C_CARD, hover_color=C_CARD_HOVER,
            border_width=1, border_color=C_BORDER,
            font=(FONT, 14), corner_radius=8,
            command=self._reset_view
        ).pack(side="left", padx=8)

        # Window controls frame
        window_frame = ctk.CTkFrame(header, fg_color="transparent")
        window_frame.pack(side="right", padx=(0, 10))

        # Fullscreen toggle button
        self.btn_fullscreen = ctk.CTkButton(
            window_frame, text="⛶", width=36, height=36,
            fg_color=C_CARD, hover_color=C_CARD_HOVER,
            border_width=1, border_color=C_BORDER,
            font=(FONT, 14), corner_radius=8,
            command=self._toggle_fullscreen,
        )
        self.btn_fullscreen.pack(side="left", padx=2)

        # Close button
        ctk.CTkButton(
            header, text="✕ Đóng (Esc)", width=110, height=36,
            fg_color="#EF4444", hover_color="#DC2626",
            font=(FONT, 11), corner_radius=8,
            command=self.destroy
        ).pack(side="right", padx=(0, 20))

        # Image display area
        self.image_frame = ctk.CTkFrame(self.container, fg_color=C_BG)
        self.image_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Labels for images - use padx/pady=0 to avoid shadow
        self.left_label = ctk.CTkLabel(
            self.image_frame, text="", fg_color=C_BG,
            text_color=C_TEXT_MUTED, font=(FONT, 12)
        )
        self.left_label.place(relx=0.25, rely=0.5, anchor="center")

        self.right_label = ctk.CTkLabel(
            self.image_frame, text="", fg_color=C_BG,
            text_color=C_TEXT_MUTED, font=(FONT, 12)
        )
        self.right_label.place(relx=0.75, rely=0.5, anchor="center")

        # Info bar
        info_bar = ctk.CTkFrame(self.container, height=32, fg_color=C_SURFACE, corner_radius=0)
        info_bar.pack(fill="x", side="bottom")

        self.info_label = ctk.CTkLabel(
            info_bar, text="Nhấn 1/2/3 chế độ | Scroll zoom | F: Phóng to/thu nhỏ | Esc: Đóng",
            font=(FONT, 10), text_color=C_TEXT_MUTED
        )
        self.info_label.pack(side="left", padx=20)

    def _on_view_mode_changed(self, value):
        """Handle segmented button selection change."""
        mode = value
        # Validate mode selection
        if mode == "BOTH" and (not self._has_before or not self._has_after):
            # Reset to current mode if can't show both
            self.view_mode_var.set(self._view_mode)
            return
        
        self._view_mode = mode
        self._reset_view()
        self._show_current_view()

    def _update_nav_buttons(self):
        """Update navigation button states."""
        # Previous button
        if self._current_index > 0 and len(self._image_list) > 1:
            self.btn_prev.configure(state="normal")
        else:
            self.btn_prev.configure(state="disabled")
        
        # Next button
        if self._current_index < len(self._image_list) - 1 and len(self._image_list) > 1:
            self.btn_next.configure(state="normal")
        else:
            self.btn_next.configure(state="disabled")

    def _prev_image(self):
        """Go to previous image."""
        if self._current_index > 0:
            self._current_index -= 1
            self._update_nav_buttons()
            # Notify parent to load previous image (will be handled via callback)
            self._notify_image_change()

    def _next_image(self):
        """Go to next image."""
        if self._current_index < len(self._image_list) - 1:
            self._current_index += 1
            self._update_nav_buttons()
            self._notify_image_change()

    def _notify_image_change(self):
        """Notify parent to load new image via callback."""
        if self._on_navigate and self._current_index < len(self._image_list):
            self._on_navigate(self._current_index)

    def _set_mode(self, mode: str):
        """Switch between BEFORE, AFTER, or BOTH view mode."""
        # Validate mode selection
        if mode == "BOTH" and (not self._has_before or not self._has_after):
            return
        
        self._view_mode = mode
        self.view_mode_var.set(mode)
        self._reset_view()
        self._show_current_view()

    def _reset_view(self):
        """Reset zoom and pan."""
        self._zoom_level = 1.0
        self.zoom_label.configure(text="100%")
        self._show_current_view()

    def _zoom_in(self):
        """Zoom in."""
        self._zoom_level = min(self._zoom_level * 1.25, 5.0)
        self.zoom_label.configure(text=f"{int(self._zoom_level * 100)}%")
        self._show_current_view()

    def _zoom_out(self):
        """Zoom out."""
        self._zoom_level = max(self._zoom_level / 1.25, 0.2)
        self.zoom_label.configure(text=f"{int(self._zoom_level * 100)}%")
        self._show_current_view()

    def _on_mouse_wheel(self, event):
        """Handle mouse wheel for zoom."""
        if event.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()

    def _resize_for_display(self, cv_img: np.ndarray, max_w: int, max_h: int) -> np.ndarray:
        """Resize image to fit within max dimensions while maintaining aspect ratio."""
        if cv_img is None:
            return None
        h, w = cv_img.shape[:2]
        scale = min(max_w / w, max_h / h, 1.0)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        return cv2.resize(cv_img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    def _apply_zoom(self, cv_img: np.ndarray) -> np.ndarray:
        """Apply zoom to the image."""
        if cv_img is None:
            return None
        
        h, w = cv_img.shape[:2]
        
        # Apply zoom
        if self._zoom_level != 1.0:
            new_w = int(w * self._zoom_level)
            new_h = int(h * self._zoom_level)
            cv_img = cv2.resize(cv_img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
        return cv_img

    def _cv2_to_ctk_image(self, cv_img: np.ndarray) -> Optional[ctk.CTkImage]:
        """Convert OpenCV BGR image to CTkImage."""
        if cv_img is None:
            return None
        rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(rgb)
        return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(cv_img.shape[1], cv_img.shape[0]))

    def _clear_label_image(self, label):
        """Safely clear image from a label."""
        try:
            # First, forget the current image by setting to empty string
            label.configure(image="")
        except:
            pass
        try:
            label.configure(image=None)
        except:
            pass

    def _show_current_view(self):
        """Show images based on current view mode."""
        # Get actual window dimensions
        self.update_idletasks()
        win_w = self.winfo_width()
        win_h = self.winfo_height()
        
        screen_w = max(win_w - 40, 400)
        screen_h = max(win_h - 150, 400)

        # Clear all images first to avoid garbage collection issues
        self._clear_label_image(self.left_label)
        self._clear_label_image(self.right_label)
        
        # Force update
        self.update_idletasks()

        if self._view_mode == "BOTH":
            # Show both images side by side
            max_w = screen_w // 2 - 20
            max_h = screen_h - 20

            # At 100% zoom: show original image size
            # At other zoom levels: resize to fit screen first, then zoom
            if self._zoom_level == 1.0:
                before_display = self._before_img.copy() if self._before_img is not None else None
                after_display = self._after_img.copy() if self._after_img is not None else None
            else:
                before_display = self._resize_for_display(self._before_img, max_w, max_h)
                after_display = self._resize_for_display(self._after_img, max_w, max_h)
                before_display = self._apply_zoom(before_display)
                after_display = self._apply_zoom(after_display)

            # Create CTkImage
            left_img = self._cv2_to_ctk_image(before_display)
            right_img = self._cv2_to_ctk_image(after_display)
            
            # Store references to prevent garbage collection
            self._left_ctk_image = left_img
            self._right_ctk_image = right_img
            
            # Update labels
            if left_img:
                self.left_label.configure(image=left_img, text="")
            else:
                self.left_label.configure(text="Không thể hiển thị ảnh Before")
            
            if right_img:
                self.right_label.configure(image=right_img, text="")
            else:
                self.right_label.configure(text="Không thể hiển thị ảnh After")

            # Update labels position
            self.left_label.place_configure(relx=0.25, rely=0.5, anchor="center")
            self.right_label.place_configure(relx=0.75, rely=0.5, anchor="center")

        elif self._view_mode == "BEFORE":
            # Show only before image
            max_w = screen_w - 40
            max_h = screen_h - 20

            # At 100% zoom: show original image size
            # At other zoom levels: resize to fit screen first, then zoom
            if self._zoom_level == 1.0:
                before_display = self._before_img.copy() if self._before_img is not None else None
            else:
                before_display = self._resize_for_display(self._before_img, max_w, max_h)
                before_display = self._apply_zoom(before_display)

            left_img = self._cv2_to_ctk_image(before_display)
            self._left_ctk_image = left_img
            
            if left_img:
                self.left_label.configure(image=left_img, text="")
            else:
                self.left_label.configure(text="Không thể hiển thị ảnh Before")
            
            self._right_ctk_image = None

            # Center single image
            self.left_label.place_configure(relx=0.5, rely=0.5, anchor="center")

        elif self._view_mode == "AFTER":
            # Show only after image
            max_w = screen_w - 40
            max_h = screen_h - 20

            # At 100% zoom: show original image size
            # At other zoom levels: resize to fit screen first, then zoom
            if self._zoom_level == 1.0:
                after_display = self._after_img.copy() if self._after_img is not None else None
            else:
                after_display = self._resize_for_display(self._after_img, max_w, max_h)
                after_display = self._apply_zoom(after_display)

            left_img = self._cv2_to_ctk_image(after_display)
            self._left_ctk_image = left_img
            
            if left_img:
                self.left_label.configure(image=left_img, text="")
            else:
                self.left_label.configure(text="Không thể hiển thị ảnh After")
            
            self._right_ctk_image = None

            # Center single image
            self.left_label.place_configure(relx=0.5, rely=0.5, anchor="center")
