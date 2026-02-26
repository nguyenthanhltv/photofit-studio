"""Import Panel - Tiếp nhận ảnh"""

import os
import cv2
import threading
import time
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import List, Optional

# Color palette
C_BG = "#0B0F19"
C_SURFACE = "#131825"
C_CARD = "#1A2035"
C_CARD_HOVER = "#1F2740"
C_BORDER = "#2A3352"
C_ACCENT = "#3B82F6"
C_ACCENT_HOVER = "#2563EB"
C_SUCCESS = "#10B981"
C_TEXT = "#E2E8F0"
C_TEXT_DIM = "#94A3B8"
C_TEXT_MUTED = "#64748B"

FONT = "Segoe UI"

DEFAULT_CAPTURE = "capture"
DEFAULT_ORIGINAL = "original"
DEFAULT_SMALL = "small"


class ImportPanel(ctk.CTkFrame):
    """Tiếp nhận ảnh"""

    def __init__(self, master, config_manager, **kwargs):
        super().__init__(master, **kwargs)
        self.cm = config_manager
        self._build()

        self._capture_folder = ""
        self._original_folder = ""
        self._small_folder = ""
        self._detected_images: List[str] = []
        self._selected_image: Optional[str] = None
        self._selected_image_size: tuple = (0, 0)  # (width, height) của ảnh gốc
        self._is_processing = False
        self._refresh_job = None
        self._auto_refresh()

    def _ensure_folders(self, base_path: str):
        folders = [
            os.path.join(base_path, DEFAULT_CAPTURE),
            os.path.join(base_path, DEFAULT_ORIGINAL),
            os.path.join(base_path, DEFAULT_SMALL),
        ]
        for folder in folders:
            os.makedirs(folder, exist_ok=True)

    def _get_output_folders(self):
        base = self.cm.get("base_folder", "")
        if not base:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._ensure_folders(base)
        return (
            os.path.join(base, DEFAULT_ORIGINAL),
            os.path.join(base, DEFAULT_SMALL)
        )

    def _build(self):
        self.columnconfigure(0, weight=35)
        self.columnconfigure(1, weight=65)
        self.rowconfigure(0, weight=1)

        # LEFT: Folder + List (Danh sách ảnh)
        left_panel = ctk.CTkFrame(self, fg_color="transparent")
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        left_panel.columnconfigure(0, weight=1)
        left_panel.rowconfigure(2, weight=1)

        ctk.CTkLabel(
            left_panel, text="📥 TIẾP NHẬN ẢNH",
            font=(FONT, 14, "bold"), text_color=C_TEXT
        ).grid(row=0, column=0, sticky="w", pady=(0, 12))

        # Folder selection
        folder_frame = ctk.CTkFrame(left_panel, fg_color=C_CARD, corner_radius=10,
                                    border_width=1, border_color=C_BORDER)
        folder_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        folder_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(folder_frame, text="📂 Capture:",
                      font=(FONT, 10), text_color=C_TEXT_DIM
                      ).grid(row=0, column=0, padx=12, pady=10, sticky="w")

        self.capture_var = ctk.StringVar(value="Chọn thư mục...")
        ctk.CTkEntry(folder_frame, textvariable=self.capture_var, state="readonly",
                     fg_color=C_SURFACE, border_color=C_BORDER,
                     text_color=C_TEXT_DIM, font=(FONT, 10)
                     ).grid(row=0, column=1, sticky="ew", padx=4, pady=10)

        ctk.CTkButton(folder_frame, text="📂", width=36, height=28,
                       fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
                       font=(FONT, 11), corner_radius=6,
                       command=self._select_capture_folder
                       ).grid(row=0, column=2, padx=(4, 10), pady=10)

        # Image List
        self.image_list_frame = ctk.CTkScrollableFrame(
            left_panel, fg_color=C_CARD, corner_radius=8,
            scrollbar_button_color=C_BORDER,
            scrollbar_button_hover_color=C_TEXT_MUTED,
        )
        self.image_list_frame.grid(row=2, column=0, sticky="nsew")
        self.image_list_frame.grid_columnconfigure(0, weight=1)

        # RIGHT: Preview + Input
        right_panel = ctk.CTkFrame(self, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        right_panel.columnconfigure(0, weight=1)
        right_panel.rowconfigure(0, weight=60)
        right_panel.rowconfigure(1, weight=40)

        preview_card = ctk.CTkFrame(right_panel, fg_color=C_CARD, corner_radius=12,
                                     border_width=1, border_color=C_BORDER)
        preview_card.grid(row=0, column=0, sticky="nsew", pady=(0, 12))
        preview_card.columnconfigure(0, weight=1)
        preview_card.rowconfigure(0, weight=1)

        self.preview_placeholder = ctk.CTkLabel(
            preview_card, text="👆 Click vào ảnh bên trái để xem",
            font=(FONT, 12), text_color=C_TEXT_MUTED
        )
        self.preview_placeholder.place(relx=0.5, rely=0.5, anchor="center")

        self.preview_label = ctk.CTkLabel(
            preview_card, text="", fg_color=C_SURFACE,
            text_color=C_TEXT_MUTED, font=(FONT, 11)
        )

        input_frame = ctk.CTkFrame(right_panel, fg_color=C_CARD, corner_radius=12,
                                    border_width=1, border_color=C_BORDER)
        input_frame.grid(row=1, column=0, sticky="nsew")
        input_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(input_frame, text="📝 Nhập MSSV:",
                      font=(FONT, 12, "bold"), text_color=C_TEXT
                      ).grid(row=0, column=0, padx=16, pady=16, sticky="w")

        self.mssv_var = ctk.StringVar()
        self.mssv_entry = ctk.CTkEntry(
            input_frame, textvariable=self.mssv_var,
            fg_color=C_SURFACE, border_color=C_BORDER,
            text_color=C_TEXT, font=(FONT, 14),
            placeholder_text="VD: 21001234"
        )
        self.mssv_entry.grid(row=0, column=1, sticky="ew", padx=8)

        self.process_btn = ctk.CTkButton(
            input_frame, text="▶ XỬ LÝ", height=40,
            fg_color=C_SUCCESS, hover_color="#059669",
            font=(FONT, 12, "bold"), corner_radius=8,
            command=self._start_import
        )
        self.process_btn.grid(row=0, column=2, padx=(12, 16), pady=16)
        self.process_btn.configure(state="disabled")

        self.progress_bar = ctk.CTkProgressBar(
            input_frame, fg_color=C_SURFACE, progress_color=C_ACCENT
        )
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, columnspan=3, sticky="ew", padx=16, pady=(0, 8))

        self.progress_label = ctk.CTkLabel(
            input_frame, text="Sẵn sàng", font=(FONT, 10), text_color=C_TEXT_MUTED
        )
        self.progress_label.grid(row=2, column=0, columnspan=3, padx=16, pady=(0, 12))

    def _select_capture_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục Capture")
        if not folder:
            return

        self._capture_folder = folder
        short = folder if len(folder) < 35 else "..." + folder[-32:]
        self.capture_var.set(short)

        base = os.path.dirname(folder.rstrip(os.sep))
        self._ensure_folders(base)

        self._scan_images()

    def _scan_images(self):
        if not self._capture_folder:
            return

        self._original_folder, self._small_folder = self._get_output_folders()

        from src.utils import scan_images
        all_images = scan_images(self._capture_folder)

        processed_names = set()
        if os.path.exists(self._original_folder):
            for f in os.listdir(self._original_folder):
                if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                    processed_names.add(os.path.splitext(f)[0])

        self._detected_images = []
        for img in all_images:
            name = os.path.splitext(os.path.basename(img))[0]
            if name not in processed_names:
                self._detected_images.append(img)

        self._render_image_list()

    def _on_image_click(self, image_path: str):
        """Handler for image click - need to call actual select method"""
        self._select_image(image_path)

    def _render_image_list(self):
        for w in self.image_list_frame.winfo_children():
            w.destroy()

        if not self._detected_images:
            ctk.CTkLabel(
                self.image_list_frame,
                text="Không có ảnh mới",
                text_color=C_TEXT_MUTED,
                font=(FONT, 11),
            ).grid(row=0, column=0, sticky="w", padx=8, pady=8)
            return

        for idx, path in enumerate(self._detected_images):
            row = ctk.CTkFrame(self.image_list_frame, fg_color=C_CARD, corner_radius=8)
            row.grid(row=idx, column=0, sticky="ew", padx=4, pady=4)
            row.grid_columnconfigure(1, weight=1)

            # Bind click using lambda with default argument to capture current value
            row.bind("<Button-1>", lambda e, p=path: self._on_image_click(p))

            thumb = self._make_thumbnail(path, 40)
            thumb_label = ctk.CTkLabel(row, text="", image=thumb, width=44, height=44,
                          fg_color=C_SURFACE, corner_radius=6
                          )
            thumb_label.grid(row=0, column=0, padx=6, pady=6)
            thumb_label.bind("<Button-1>", lambda e, p=path: self._on_image_click(p))

            text_label = ctk.CTkLabel(
                row,
                text=os.path.basename(path),
                text_color=C_TEXT,
                font=(FONT, 10),
                anchor="w"
            )
            text_label.grid(row=0, column=1, sticky="ew", padx=(2, 6), pady=8)
            text_label.bind("<Button-1>", lambda e, p=path: self._on_image_click(p))

    def _make_thumbnail(self, image_path: str, size: int = 52):
        img = cv2.imread(image_path)
        if img is None:
            return None
        h, w = img.shape[:2]
        scale = min(size / w, size / h)
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        from PIL import Image
        pil = Image.fromarray(rgb)
        return ctk.CTkImage(light_image=pil, dark_image=pil, size=(nw, nh))

    def _select_image(self, image_path: str):
        self._selected_image = image_path

        img = cv2.imread(image_path)
        if img is not None:
            h, w = img.shape[:2]
            # Lưu kích thước ảnh gốc
            self._selected_image_size = (w, h)

            # Preview với kích thước lớn hơn (450x350)
            max_h, max_w = 350, 450
            scale = min(max_w / w, max_h / h)
            new_w, new_h = int(w * scale), int(h * scale)
            resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            from PIL import Image
            pil = Image.fromarray(rgb)
            ctk_img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(new_w, new_h))

            # Hide placeholder, show image
            self.preview_placeholder.place_forget()
            self.preview_label.configure(image=ctk_img, text="")
            self.preview_label.place(relx=0.5, rely=0.5, anchor="center")
            self.preview_label._image = ctk_img

        # Enable button when image is selected (even without MSSV)
        self.process_btn.configure(state="normal")

    def _start_import(self):
        mssv = self.mssv_var.get().strip()
        if not mssv:
            messagebox.showwarning("Chưa nhập MSSV", "Vui lòng nhập MSSV trước.")
            self.mssv_entry.focus()
            return

        if not self._selected_image:
            messagebox.showwarning("Chưa chọn ảnh", "Vui lòng click vào ảnh bên trái để chọn.")
            return

        self.process_btn.configure(state="disabled")
        self._is_processing = True

        thread = threading.Thread(target=self._process_single, args=(mssv,))
        thread.daemon = True
        thread.start()

    def _process_single(self, mssv: str):
        img_path = self._selected_image
        start_time = time.time()
        
        try:
            # Lấy kích thước từ config - trực tiếp từ import_settings nếu có
            target_w, target_h = 800, 600
            
            # Ưu tiên lấy từ import_settings (sidebar)
            if hasattr(self, 'parent') and hasattr(self.parent, 'import_settings'):
                settings = self.parent.import_settings
                if hasattr(settings, 'width_var') and hasattr(settings, 'height_var'):
                    try:
                        target_w = int(settings.width_var.get())
                        target_h = int(settings.height_var.get())
                    except:
                        pass
            
            # Nếu không được thì lấy từ config manager
            if target_w <= 0 or target_h <= 0:
                try:
                    target_w = self.cm.get("import", "width") or 800
                    target_h = self.cm.get("import", "height") or 600
                except:
                    target_w, target_h = 800, 600
            
            # Lấy đường dẫn folder từ config
            original_folder_path = self.cm.get("import", "original_folder") or ""
            resized_folder_path = self.cm.get("import", "resized_folder") or ""
            
            # Nếu là đường dẫn đầy đủ thì dùng trực tiếp
            if original_folder_path and os.path.isabs(original_folder_path):
                original_folder = original_folder_path
            else:
                # Nếu là tên folder tương đối, lấy base từ capture
                base_folder = os.path.dirname(self._capture_folder.rstrip(os.sep))
                original_folder = os.path.join(base_folder, original_folder_path) if original_folder_path else os.path.join(base_folder, "original")
            
            if resized_folder_path and os.path.isabs(resized_folder_path):
                resized_folder = resized_folder_path
            else:
                base_folder = os.path.dirname(self._capture_folder.rstrip(os.sep))
                resized_folder = os.path.join(base_folder, resized_folder_path) if resized_folder_path else os.path.join(base_folder, "small")
            
            # Tạo các thư mục output
            os.makedirs(original_folder, exist_ok=True)
            os.makedirs(resized_folder, exist_ok=True)
            
            ext = os.path.splitext(img_path)[1].lower()
            if not ext:
                ext = ".jpg"
            
            # Tên file không có _small
            new_filename = f"{mssv}{ext}"
            
            img = cv2.imread(img_path)
            if img is None:
                return

            h, w = img.shape[:2]
            
            # Lưu ảnh gốc (chưa resize) vào folder gốc
            original_path = os.path.join(original_folder, new_filename)
            cv2.imwrite(original_path, img)

            # Resize theo kích thước config - fit vào target (không giới hạn 1.0)
            scale = min(target_w / w, target_h / h)
            new_w, new_h = int(w * scale), int(h * scale)
            small = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            
            # Lưu ảnh đã resize vào folder resize (tên không có _small)
            resized_filename = f"{mssv}{ext}"
            resized_path = os.path.join(resized_folder, resized_filename)
            cv2.imwrite(resized_path, small)
            
            # Xóa ảnh gốc khỏi thư mục capture
            try:
                if os.path.exists(img_path):
                    os.remove(img_path)
            except:
                pass

            # Record to statistics
            duration = time.time() - start_time
            try:
                from src.statistics import record_import
                record_import(renamed=True, duration=duration)
            except:
                pass

            # Refresh UI after processing
            def on_complete():
                # Reset MSSV input
                self.mssv_var.set("")
                self.mssv_entry.focus()
                
                # Refresh image list (remove processed image)
                self._scan_images()
                
                # Clear preview if no more images
                if not self._detected_images:
                    self._clear_preview()
                    self.process_btn.configure(state="disabled")
                else:
                    # Select next image if available
                    self._select_image(self._detected_images[0])
                
                # Show success message
                messagebox.showinfo("Hoàn tất", f"Đã tiếp nhận ảnh:\n{new_filename}\nKích thước: {new_w}x{new_h}\n\nẢnh gốc: {original_folder}\nẢnh resize: {resized_folder}")
                
                # Re-enable process button
                self.process_btn.configure(state="normal")
            
            self.after(0, on_complete)

        except Exception as e:
            self.after(0, lambda: [
                self.process_btn.configure(state="normal"),
                messagebox.showerror("Lỗi", str(e))
            ])

    def _clear_preview(self):
        """Clear preview area"""
        self._selected_image = None
        self.preview_label.configure(image=None, text="")
        self.preview_placeholder.place(relx=0.5, rely=0.5, anchor="center")

    def _auto_refresh(self):
        """Auto refresh image list when new images are added"""
        if self._capture_folder and os.path.exists(self._capture_folder):
            # Check for new images without disrupting current selection
            old_selected = self._selected_image
            self._scan_images()
            
            # If selected image was removed (processed), select next
            if old_selected and old_selected not in self._detected_images:
                if self._detected_images:
                    self._select_image(self._detected_images[0])
                else:
                    self._clear_preview()
        
        # Schedule next refresh
        self._refresh_job = self.after(3000, self._auto_refresh)

    def stop_processing(self):
        self._is_processing = False
        if self._refresh_job:
            self.after_cancel(self._refresh_job)
