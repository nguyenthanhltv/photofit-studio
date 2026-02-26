"""Main application window - Modern dark theme design."""

import os
import cv2
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import List, Optional, Dict
from pathlib import Path

from src.config_manager import ConfigManager
from src.batch_runner import BatchRunner, BatchResult
from src.utils import scan_images
from .settings_panel import SettingsPanel
from .preview_panel import PreviewPanel
from .progress_panel import ProgressPanel
from .import_panel import ImportPanel

# Color palette
C_BG = "#0B0F19"
C_SURFACE = "#131825"
C_CARD = "#1A2035"
C_CARD_HOVER = "#1F2740"
C_BORDER = "#2A3352"
C_ACCENT = "#3B82F6"
C_ACCENT_HOVER = "#2563EB"
C_SUCCESS = "#10B981"
C_DANGER = "#EF4444"
C_WARNING = "#F59E0B"
C_TEXT = "#E2E8F0"
C_TEXT_DIM = "#94A3B8"
C_TEXT_MUTED = "#64748B"

APP_NAME = "PhotoFit Studio"
APP_VERSION = "v1.0"
APP_LOGO = "🪪"

UPDATE_LOGS = [
    "v1.0",
    "- Phiên bản đầu tiên",
    "- Menu Tiếp nhận: Tiếp nhận ảnh thẻ, đổi tên theo MSSV",
    "- Menu Xử lý: Xử lý ảnh hàng loạt",
    "- Làm đẹp: Smooth da, tóc, mắt, răng",
    "- Tách nền: Xóa/thay nền tự động",
    "- AI Enhance: Tăng chất lượng ảnh",
    "- Resize: Nhiều kích thước chuẩn (2x3, 3x4, 4x6, passport)",
    "- Công cụ mở rộng:",
    "  • Template System",
    "  • Statistics",
    "  • Print Layout",
    "  • Batch Export",
    "  • Web Server",
    "  • Face Quality",
    "- Đa ngôn ngữ: VI/EN",
    "- Cấu hình: Lưu/Import/Export",
]

INPUT_REFRESH_MS = 2000


class MainWindow(ctk.CTk):
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.cm = config_manager
        self.runner: Optional[BatchRunner] = None
        self._batch_thread = None
        self._image_list: List[str] = []
        self._input_folder = ""
        self._output_folder = ""
        self._file_rows: Dict[str, Dict[str, object]] = {}
        self._thumb_cache: Dict[str, ctk.CTkImage] = {}
        self._processed_output_map: Dict[str, str] = {}
        self._image_status: Dict[str, str] = {}
        self._active_image_path: Optional[str] = None
        self._input_refresh_job = None
        self._current_view = "import"

        self._setup_window()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_window(self):
        self.title(f"{APP_NAME}")
        self.geometry("1080x720")
        self.minsize(900, 640)
        self.configure(fg_color=C_BG)
        ctk.set_appearance_mode("dark")

    def _build_ui(self):
        self.columnconfigure(0, weight=0, minsize=260)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # HEADER
        header = ctk.CTkFrame(self, height=56, fg_color=C_SURFACE, corner_radius=0)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        header.grid_propagate(False)

        # Logo + Title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=20, pady=10)
        ctk.CTkLabel(title_frame, text=APP_LOGO, font=("Segoe UI Emoji", 20), text_color=C_TEXT).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(title_frame, text=APP_NAME, font=("Segoe UI", 18, "bold"), text_color=C_TEXT).pack(side="left")
        ctk.CTkLabel(title_frame, text=f"  {APP_VERSION}", font=("Segoe UI", 11), text_color=C_TEXT_MUTED).pack(side="left", pady=(4, 0))

        # Menu buttons in center
        menu_frame = ctk.CTkFrame(header, fg_color="transparent")
        menu_frame.pack(side="left", padx=40)

        self.btn_import = ctk.CTkButton(
            menu_frame, text="📥 Tiếp nhận", width=120, height=36,
            fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
            font=("Segoe UI", 11, "bold"), corner_radius=8,
            command=self._show_import
        )
        self.btn_import.pack(side="left", padx=4)

        self.btn_process = ctk.CTkButton(
            menu_frame, text="🔧 Xử lý", width=120, height=36,
            fg_color=C_CARD, hover_color=C_CARD_HOVER,
            border_width=1, border_color=C_BORDER,
            font=("Segoe UI", 11), corner_radius=8,
            command=self._show_process
        )
        self.btn_process.pack(side="left", padx=4)

        # Right header buttons
        header_btns = ctk.CTkFrame(header, fg_color="transparent")
        header_btns.pack(side="right", padx=20)

        # Language toggle - segmented button (VN | EN)
        saved_lang = self.cm.get("settings", "language") or "VI"
        self.lang_var = ctk.StringVar(value=saved_lang)

        # Create a frame for the segmented control
        lang_frame = ctk.CTkFrame(header_btns, fg_color="transparent")
        lang_frame.pack(side="right", padx=(8, 0))

        # VN button (red when active)
        self.btn_vn = ctk.CTkButton(
            lang_frame, text="VN", width=36, height=32,
            fg_color=C_DANGER, hover_color="#DC2626",
            font=("Segoe UI", 11, "bold"), text_color="#FFFFFF",
            command=lambda: self._set_language("VI")
        )
        self.btn_vn.pack(side="left", padx=(0, 1))

        # EN button (green when active)
        self.btn_en = ctk.CTkButton(
            lang_frame, text="EN", width=36, height=32,
            fg_color=C_CARD, hover_color=C_CARD_HOVER,
            border_width=1, border_color=C_BORDER,
            font=("Segoe UI", 11), text_color=C_TEXT_DIM,
            command=lambda: self._set_language("EN")
        )
        self.btn_en.pack(side="left")

        # Set initial button state based on saved language
        self._update_language_buttons()

        ctk.CTkButton(header_btns, text="ℹ Thông tin", width=80, height=32,
                       fg_color=C_CARD, hover_color=C_CARD_HOVER,
                       border_width=1, border_color=C_BORDER,
                       font=("Segoe UI", 10), command=self._show_software_info).pack(side="right", padx=(4, 0))

        ctk.CTkButton(header_btns, text="🛠️ Công cụ", width=80, height=32,
                       fg_color=C_CARD, hover_color=C_CARD_HOVER,
                       border_width=1, border_color=C_BORDER,
                       font=("Segoe UI", 10), command=self._show_tools).pack(side="right", padx=(4, 0))

        ctk.CTkButton(header_btns, text="⚙️ Cấu hình", width=100, height=32,
                       fg_color=C_CARD, hover_color=C_CARD_HOVER,
                       border_width=1, border_color=C_BORDER,
                       font=("Segoe UI", 10), command=self._show_config_menu).pack(side="right", padx=(4, 0))

        ctk.CTkButton(header_btns, text="📘 Hướng dẫn", width=90, height=32,
                       fg_color=C_CARD, hover_color=C_CARD_HOVER,
                       border_width=1, border_color=C_BORDER,
                       font=("Segoe UI", 10), command=self._show_user_guide).pack(side="right", padx=(4, 0))

        # LEFT SIDEBAR
        self.sidebar = ctk.CTkFrame(self, fg_color=C_SURFACE, corner_radius=0, width=260)
        self.sidebar.grid(row=1, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Content area
        self.main_content = ctk.CTkFrame(self, fg_color=C_BG, corner_radius=0)
        self.main_content.grid(row=1, column=1, sticky="nsew")

        # Default view
        self._show_import()

    def _load_saved_paths(self):
        """Load saved paths from config"""
        # Load capture folder for import
        capture_folder = self.cm.get("import", "capture_folder")
        if capture_folder and os.path.exists(capture_folder):
            if hasattr(self, 'import_panel'):
                self.import_panel._capture_folder = capture_folder
                short = capture_folder if len(capture_folder) < 35 else "..." + capture_folder[-32:]
                self.import_panel.capture_var.set(short)
                self.import_panel._scan_images()

        # Load input/output folders for process
        input_folder = self.cm.get("base_folder", "input_folder")
        output_folder = self.cm.get("base_folder", "output_folder")

        if input_folder and os.path.exists(input_folder):
            self._input_folder = input_folder
            short = input_folder if len(input_folder) < 45 else "..." + input_folder[-42:]
            self.input_path_var.set(short)
            self._schedule_input_refresh()

        if output_folder and os.path.exists(output_folder):
            self._output_folder = output_folder
            short = output_folder if len(output_folder) < 45 else "..." + output_folder[-42:]
            self.output_path_var.set(short)

    def _cancel_refresh(self):
        """Cancel input refresh job when switching views"""
        if self._input_refresh_job:
            self.after_cancel(self._input_refresh_job)
            self._input_refresh_job = None

    def _show_import(self):
        """Show Import panel with sidebar settings."""
        # Cancel any running refresh job first
        self._cancel_refresh()

        self._current_view = "import"
        self.btn_import.configure(fg_color=C_ACCENT, border_color=C_ACCENT)
        self.btn_process.configure(fg_color=C_CARD, border_color=C_BORDER)

        # Clear main content first to create import_panel
        for w in self.main_content.winfo_children():
            w.destroy()

        # Show import panel in main content
        self.import_panel = ImportPanel(self.main_content, config_manager=self.cm, fg_color=C_BG)
        self.import_panel.pack(fill="both", expand=True)
        
        # Pass reference to import_settings for accessing width/height
        self.import_panel.parent = self

        # Clear sidebar and add settings
        for w in self.sidebar.winfo_children():
            w.destroy()

        # Add import settings to sidebar with reference to import_panel
        from .import_settings_panel import ImportSettingsPanel
        self.import_settings = ImportSettingsPanel(
            self.sidebar,
            config_manager=self.cm,
            import_panel=self.import_panel,  # Pass reference to get image size
            fg_color=C_SURFACE,
            width=258
        )
        self.import_settings.pack(fill="both", expand=True)

        # Load saved capture folder
        capture_folder = self.cm.get("import", "capture_folder")
        if capture_folder and os.path.exists(capture_folder):
            self.import_panel._capture_folder = capture_folder
            short = capture_folder if len(capture_folder) < 35 else "..." + capture_folder[-32:]
            self.import_panel.capture_var.set(short)
            self.import_panel._scan_images()
        
        # Load saved original/resized folder paths to settings
        original_folder = self.cm.get("import", "original_folder")
        resized_folder = self.cm.get("import", "resized_folder")
        if original_folder:
            self.import_settings.original_var.set(str(original_folder))
        if resized_folder:
            self.import_settings.resized_var.set(str(resized_folder))

    def _show_process(self):
        """Show Process panel with settings sidebar."""
        # Cancel any running refresh job first
        self._cancel_refresh()

        self._current_view = "process"
        self.btn_import.configure(fg_color=C_CARD, border_color=C_BORDER)
        self.btn_process.configure(fg_color=C_ACCENT, border_color=C_ACCENT)

        # Clear sidebar
        for w in self.sidebar.winfo_children():
            w.destroy()

        # Add settings to sidebar
        self.settings = SettingsPanel(self.sidebar, config_manager=self.cm, fg_color=C_SURFACE, width=258)
        self.settings.pack(fill="both", expand=True)

        # Clear and rebuild main content
        for w in self.main_content.winfo_children():
            w.destroy()

        self._build_process_content()

        # Load saved input/output folders
        input_folder = self.cm.get("base_folder", "input_folder")
        output_folder = self.cm.get("base_folder", "output_folder")

        if input_folder and os.path.exists(input_folder):
            self._input_folder = input_folder
            short = input_folder if len(input_folder) < 45 else "..." + input_folder[-42:]
            self.input_path_var.set(short)
            self._schedule_input_refresh()

        if output_folder and os.path.exists(output_folder):
            self._output_folder = output_folder
            short = output_folder if len(output_folder) < 45 else "..." + output_folder[-42:]
            self.output_path_var.set(short)

    def _build_process_content(self):
        main = self.main_content
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)
        main.rowconfigure(2, weight=0)
        main.rowconfigure(3, weight=0)

        # IO BAR - compact height
        io_bar = ctk.CTkFrame(main, fg_color=C_CARD, corner_radius=10, border_width=1, border_color=C_BORDER)
        io_bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))
        io_bar.columnconfigure(1, weight=1)
        io_bar.columnconfigure(3, weight=1)
        io_bar.configure(height=52)

        ctk.CTkLabel(io_bar, text="Input", font=("Segoe UI", 10, "bold"), text_color=C_TEXT_DIM).grid(row=0, column=0, padx=(12, 4), pady=8)
        self.input_path_var = ctk.StringVar(value="Select input folder...")
        ctk.CTkEntry(io_bar, textvariable=self.input_path_var, state="readonly", fg_color=C_SURFACE, border_color=C_BORDER, text_color=C_TEXT_DIM, font=("Segoe UI", 10)).grid(row=0, column=1, sticky="ew", padx=2, pady=8)
        ctk.CTkButton(io_bar, text="📂", width=36, height=26, fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER, font=("Segoe UI", 10), corner_radius=6, command=self._select_input).grid(row=0, column=2, padx=(4, 12), pady=8)

        sep = ctk.CTkFrame(io_bar, width=1, fg_color=C_BORDER)
        sep.grid(row=0, column=2, sticky="ns", padx=0, pady=6)

        ctk.CTkLabel(io_bar, text="Output", font=("Segoe UI", 10, "bold"), text_color=C_TEXT_DIM).grid(row=0, column=3, padx=(12, 4), pady=8)
        self.output_path_var = ctk.StringVar(value="Select output folder...")
        ctk.CTkEntry(io_bar, textvariable=self.output_path_var, state="readonly", fg_color=C_SURFACE, border_color=C_BORDER, text_color=C_TEXT_DIM, font=("Segoe UI", 10)).grid(row=0, column=4, sticky="ew", padx=2, pady=8)
        io_bar.columnconfigure(4, weight=1)
        ctk.CTkButton(io_bar, text="📂", width=36, height=26, fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER, font=("Segoe UI", 10), corner_radius=6, command=self._select_output).grid(row=0, column=5, padx=(4, 12), pady=8)

        # CENTER - larger area for images and preview
        center = ctk.CTkFrame(main, fg_color="transparent")
        center.grid(row=1, column=0, sticky="nsew", padx=16, pady=6)
        center.columnconfigure(0, weight=1, minsize=200)
        center.columnconfigure(1, weight=2, minsize=300)
        center.rowconfigure(0, weight=1)

        # File list
        file_card = ctk.CTkFrame(center, fg_color=C_CARD, corner_radius=10, border_width=1, border_color=C_BORDER)
        file_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        file_card.rowconfigure(1, weight=1)
        file_card.columnconfigure(0, weight=1)

        file_header = ctk.CTkFrame(file_card, fg_color="transparent", height=36)
        file_header.grid(row=0, column=0, sticky="ew", padx=12, pady=(8, 2))
        file_header.columnconfigure(0, weight=1)
        ctk.CTkLabel(file_header, text="Images", font=("Segoe UI", 12, "bold"), text_color=C_TEXT).grid(row=0, column=0, sticky="w")
        self.file_count_label = ctk.CTkLabel(file_header, text="0 files", font=("Segoe UI", 10), text_color=C_TEXT_MUTED)
        self.file_count_label.grid(row=0, column=1, sticky="e")

        self.file_list_frame = ctk.CTkScrollableFrame(file_card, fg_color=C_SURFACE, corner_radius=6, scrollbar_button_color=C_BORDER, scrollbar_button_hover_color=C_TEXT_MUTED)
        self.file_list_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(2, 10))
        self.file_list_frame.grid_columnconfigure(1, weight=1)

        # Preview
        self.preview = PreviewPanel(center, fg_color=C_CARD, corner_radius=10, border_width=1, border_color=C_BORDER)
        self.preview.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        # Progress
        self.progress = ProgressPanel(main, fg_color=C_CARD, corner_radius=10, border_width=1, border_color=C_BORDER)
        self.progress.grid(row=2, column=0, sticky="ew", padx=16, pady=(6, 4))

        # Buttons
        btn_row = ctk.CTkFrame(main, fg_color="transparent", height=48)
        btn_row.grid(row=3, column=0, sticky="ew", padx=16, pady=(4, 12))

        self.start_btn = ctk.CTkButton(btn_row, text="▶ Bắt đầu xử lý", width=180, height=36, fg_color=C_SUCCESS, hover_color="#059669", font=("Segoe UI", 12, "bold"), corner_radius=8, command=self._start)
        self.start_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = ctk.CTkButton(btn_row, text="⏹ Dừng", width=90, height=36, fg_color=C_CARD, hover_color=C_DANGER, border_width=1, border_color=C_BORDER, font=("Segoe UI", 12), corner_radius=8, state="disabled", command=self._stop)
        self.stop_btn.pack(side="left")

    # Process methods
    def _make_thumbnail(self, image_path: str, size: int = 52) -> Optional[ctk.CTkImage]:
        img = cv2.imread(image_path)
        if img is None: return None
        h, w = img.shape[:2]
        scale = min(size / w, size / h)
        nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
        resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        from PIL import Image
        pil = Image.fromarray(rgb)
        return ctk.CTkImage(light_image=pil, dark_image=pil, size=(nw, nh))

    def _expected_output_path(self, input_path: str) -> Optional[str]:
        if not self._output_folder: return None
        output_cfg = self.cm.get("output")
        naming = output_cfg.get("naming", "{name}_processed") if isinstance(output_cfg, dict) else "{name}_processed"
        fmt = output_cfg.get("format", "jpg") if isinstance(output_cfg, dict) else "jpg"
        base = os.path.splitext(os.path.basename(input_path))[0]
        output_name = naming.replace("{name}", base)
        return os.path.join(self._output_folder, f"{output_name}.{fmt.lower()}")

    def _refresh_input_images(self):
        if not self._input_folder: return
        current_images = scan_images(self._input_folder)
        current_set = set(current_images)
        previous_set = set(self._image_list)

        for removed in previous_set - current_set:
            self._image_status.pop(removed, None)
            self._processed_output_map.pop(removed, None)
            self._thumb_cache.pop(removed, None)

        for path in current_images:
            if path not in self._image_status:
                expected = self._expected_output_path(path)
                if expected and os.path.exists(expected):
                    self._image_status[path] = "done"
                    self._processed_output_map[path] = expected
                else:
                    self._image_status[path] = "pending"

        self._image_list = current_images
        self.file_count_label.configure(text=f"{len(self._image_list)} files")
        self._render_image_list()

        if self._image_list:
            if self._active_image_path not in current_set:
                self._set_active_image(self._image_list[0])
            elif self._active_image_path:
                self._set_active_image(self._active_image_path)
        else:
            self.preview.clear()

    def _schedule_input_refresh(self):
        if self._input_refresh_job:
            self.after_cancel(self._input_refresh_job)
        self._refresh_input_images()
        self._input_refresh_job = self.after(INPUT_REFRESH_MS, self._schedule_input_refresh)

    def _status_meta(self, status: str):
        if status == "done": return "✅ Đã hoàn thành", C_SUCCESS
        if status == "processing": return "⏳ Đang xử lý", C_WARNING
        if status == "error": return "❌ Lỗi", C_DANGER
        return "🕓 Chờ xử lý", C_TEXT_MUTED

    def _toggle_image_status(self, path: str):
        """Toggle between done and pending status"""
        current = self._image_status.get(path, "pending")
        if current == "done":
            self._image_status[path] = "pending"
        else:
            self._image_status[path] = "done"
        self._render_image_list()

    def _render_image_list(self):
        for w in self.file_list_frame.winfo_children():
            w.destroy()
        self._file_rows.clear()
        self._thumb_cache.clear()

        if not self._image_list:
            ctk.CTkLabel(self.file_list_frame, text="Chưa có ảnh", text_color=C_TEXT_MUTED, font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w", padx=8, pady=8)
            return

        for idx, path in enumerate(self._image_list):
            row = ctk.CTkFrame(self.file_list_frame, fg_color=C_CARD, corner_radius=8)
            row.grid(row=idx, column=0, columnspan=2, sticky="ew", padx=4, pady=4)
            row.grid_columnconfigure(1, weight=1)

            thumb = self._make_thumbnail(path)
            self._thumb_cache[path] = thumb
            ctk.CTkLabel(row, text="", image=thumb, width=56, height=56, fg_color=C_SURFACE, corner_radius=6).grid(row=0, column=0, padx=6, pady=6)

            # Image name
            ctk.CTkLabel(row, text=os.path.basename(path), text_color=C_TEXT, font=("Segoe UI", 11), anchor="w").grid(row=0, column=1, sticky="ew", padx=(2, 6), pady=(8, 2))

            # Toggle switch for done/pending status
            status = self._image_status.get(path, "pending")
            is_done = (status == "done")

            # Create toggle switch
            status_frame = ctk.CTkFrame(row, fg_color="transparent")
            status_frame.grid(row=1, column=1, sticky="w", padx=(2, 6), pady=(0, 6))

            toggle = ctk.CTkSwitch(
                status_frame, text="",
                command=lambda p=path: self._toggle_image_status(p),
                font=("Segoe UI", 10),
                fg_color=C_SUCCESS if is_done else C_TEXT_MUTED,
                progress_color=C_SUCCESS,
                switch_width=40,
                switch_height=20
            )
            toggle.configure(variable=ctk.BooleanVar(value=is_done))
            toggle.pack(side="left")

            status_label = ctk.CTkLabel(
                status_frame,
                text="✅ Hoàn thành" if is_done else "🕓 Chưa hoàn thành",
                text_color=C_SUCCESS if is_done else C_TEXT_MUTED,
                font=("Segoe UI", 9)
            )
            status_label.pack(side="left", padx=(6, 0))

            # Store references
            self._file_rows[path] = {"row": row, "status": status_label, "toggle": toggle}

            for widget in (row,):
                widget.bind("<Button-1>", lambda _e, p=path: self._set_active_image(p))

    def _set_active_image(self, image_path: str):
        self._active_image_path = image_path
        for path, refs in self._file_rows.items():
            refs["row"].configure(fg_color=C_CARD_HOVER if path == image_path else C_CARD)

        before_img = cv2.imread(image_path)
        if before_img is not None:
            self.preview.set_before(before_img)

        out_path = self._processed_output_map.get(image_path)
        if out_path and os.path.exists(out_path):
            after_img = cv2.imread(out_path)
            if after_img is not None:
                self.preview.set_after(after_img)
        else:
            self.preview.set_after_placeholder("Đang chờ xử lý")

        self.preview.set_info(os.path.basename(image_path))

    def _select_input(self):
        folder = filedialog.askdirectory(title="Select input folder")
        if not folder: return
        self._input_folder = folder
        short = folder if len(folder) < 45 else "..." + folder[-42:]
        self.input_path_var.set(short)
        self._schedule_input_refresh()

    def _select_output(self):
        folder = filedialog.askdirectory(title="Select output folder")
        if folder:
            self._output_folder = folder
            short = folder if len(folder) < 45 else "..." + folder[-42:]
            self.output_path_var.set(short)
            self._refresh_input_images()

    def _start(self):
        if not self._input_folder:
            messagebox.showwarning("No input", "Please select an input folder.")
            return
        if not self._output_folder:
            messagebox.showwarning("No output", "Please select an output folder.")
            return
        if not self._image_list:
            messagebox.showwarning("No images", "Input folder has no valid images.")
            return

        pending_images = [p for p in self._image_list if self._image_status.get(p, "pending") != "done"]
        if not pending_images:
            messagebox.showinfo("Không có ảnh cần xử lý", "Tất cả ảnh đã hoàn tất.")
            return

        config = self.settings.apply_to_config()
        total = len(pending_images)

        for p in pending_images:
            self._image_status[p] = "processing"

        self.progress.reset(total)
        self.progress.log(f"Processing {total} images...")
        self._render_image_list()

        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal", fg_color=C_DANGER, hover_color="#DC2626")

        self.runner = BatchRunner(config)
        self._batch_thread = self.runner.run_async(
            self._input_folder, self._output_folder,
            input_images=pending_images,
            on_progress=self._on_progress,
            on_complete=self._on_complete,
            on_error=self._on_error)

    def _stop(self):
        if self.runner and self.runner.is_running:
            self.runner.cancel()
            self.stop_btn.configure(state="disabled")

    def _on_progress(self, current, total, result, elapsed):
        def _update():
            fname = result.input_path if result else None
            self.progress.update_progress(current, total, elapsed, fname)
            if result:
                name = os.path.basename(result.input_path)
                refs = self._file_rows.get(result.input_path)
                if result.success:
                    self._image_status[result.input_path] = "done"
                    self.progress.log(f"Done: {name} ({result.duration:.1f}s)")
                    if refs:
                        refs["status"].configure(text=self._status_meta("done")[0], text_color=self._status_meta("done")[1])
                    if result.output_path and os.path.exists(result.output_path):
                        self._processed_output_map[result.input_path] = result.output_path
                        before_img = cv2.imread(result.input_path)
                        if before_img is not None:
                            self.preview.set_before(before_img)
                        after_img = cv2.imread(result.output_path)
                        if after_img is not None:
                            self.preview.set_after(after_img)
                            self.preview.set_info(name)
                else:
                    self._image_status[result.input_path] = "error"
                    if refs:
                        refs["status"].configure(text=self._status_meta("error")[0], text_color=self._status_meta("error")[1])
                    self.progress.log(f"Error: {name} - {result.error}")

                self._set_active_image(result.input_path)
        self.after(0, _update)

    def _on_complete(self, results: List[BatchResult]):
        def _update():
            success = sum(1 for r in results if r.success)
            total = len(results)
            elapsed = sum(r.duration for r in results)
            self.progress.set_complete(success, total, elapsed)
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled", fg_color=C_CARD)
        self.after(0, _update)

    def _on_error(self, path, error):
        def _update():
            self._image_status[path] = "error"
            self.progress.log(f"Error: {os.path.basename(path)} - {error}")
            refs = self._file_rows.get(path)
            if refs:
                refs["status"].configure(text=self._status_meta("error")[0], text_color=self._status_meta("error")[1])
        self.after(0, _update)

    def _on_close(self):
        if self._input_refresh_job:
            self.after_cancel(self._input_refresh_job)
            self._input_refresh_job = None
        self.destroy()

    def _show_config_menu(self):
        """Show popup menu for config actions"""
        # Create popup window
        popup = ctk.CTkToplevel(self)
        popup.title("Cấu hình")
        popup.geometry("280x270")
        popup.resizable(False, False)
        popup.configure(fg_color=C_SURFACE)
        popup.transient(self)
        popup.grab_set()

        # Center the popup on screen
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (280 // 2)
        y = (popup.winfo_screenheight() // 2) - (270 // 2)
        popup.geometry(f"280x270+{x}+{y}")

        # Title
        ctk.CTkLabel(
            popup, text="⚙️ Cấu hình hệ thống",
            font=("Segoe UI", 14, "bold"), text_color=C_TEXT
        ).pack(pady=(20, 16))

        # Buttons
        def close_popup():
            popup.grab_release()
            popup.destroy()

        ctk.CTkButton(
            popup, text="👁 Xem cấu hình hiện tại", height=36,
            fg_color=C_CARD, border_color=C_BORDER,
            text_color=C_TEXT, font=("Segoe UI", 11),
            command=lambda: [self._view_config(), close_popup()]
        ).pack(fill="x", padx=20, pady=4)

        ctk.CTkButton(
            popup, text="💾 Lưu cấu hình hiện tại", height=36,
            fg_color=C_SUCCESS, hover_color="#059669",
            font=("Segoe UI", 11, "bold"),
            command=lambda: [self._save_config(), close_popup()]
        ).pack(fill="x", padx=20, pady=4)

        ctk.CTkButton(
            popup, text="📥 Import từ file", height=36,
            fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
            font=("Segoe UI", 11),
            command=lambda: [self._import_config(), close_popup()]
        ).pack(fill="x", padx=20, pady=4)

        ctk.CTkButton(
            popup, text="📤 Export ra file", height=36,
            fg_color=C_CARD, border_color=C_BORDER,
            text_color=C_TEXT, font=("Segoe UI", 11),
            command=lambda: [self._export_config(), close_popup()]
        ).pack(fill="x", padx=20, pady=4)

        ctk.CTkButton(
            popup, text="✕ Đóng", height=32,
            fg_color=C_SURFACE, border_color=C_BORDER,
            text_color=C_TEXT_DIM, font=("Segoe UI", 10),
            command=close_popup
        ).pack(fill="x", padx=20, pady=(12, 16))

    def _view_config(self):
        """Show current config in a popup"""
        import json

        popup = ctk.CTkToplevel(self)
        popup.title("Cấu hình hiện tại")
        popup.geometry("450x400")
        popup.configure(fg_color=C_SURFACE)
        popup.transient(self)

        # Center
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (450 // 2)
        y = (popup.winfo_screenheight() // 2) - (400 // 2)
        popup.geometry(f"450x400+{x}+{y}")

        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=16)

        # Get current config
        config_json = json.dumps(self.cm.config, indent=2, ensure_ascii=False)

        ctk.CTkLabel(
            scroll, text=config_json,
            font=("Consolas", 10), text_color=C_TEXT,
            justify="left"
        ).pack(anchor="w")

        ctk.CTkButton(popup, text="✕ Đóng", command=popup.destroy,
                      fg_color=C_CARD, border_color=C_BORDER,
                      text_color=C_TEXT).pack(pady=(0, 16))

    def _save_config(self):
        # Save import settings if on import view
        if hasattr(self, 'import_settings') and self._current_view == "import":
            try:
                import_w = int(self.import_settings.width_var.get())
                import_h = int(self.import_settings.height_var.get())
                self.cm.set("import", "width", import_w)
                self.cm.set("import", "height", import_h)
                self.cm.set("import", "auto_calculate", self.import_settings.auto_calc_var.get())
                # Save capture folder path
                if hasattr(self, 'import_panel') and self.import_panel._capture_folder:
                    self.cm.set("import", "capture_folder", self.import_panel._capture_folder)
                # Save original/resized folder paths
                if hasattr(self.import_settings, 'original_var'):
                    self.cm.set("import", "original_folder", self.import_settings.original_var.get())
                if hasattr(self.import_settings, 'resized_var'):
                    self.cm.set("import", "resized_folder", self.import_settings.resized_var.get())
            except:
                pass

        # Save process settings (including input/output folders)
        if hasattr(self, 'settings') and self._current_view == "process":
            self.settings.apply_to_config()

        # Save input/output folders for process
        if self._input_folder:
            self.cm.set("base_folder", "input_folder", self._input_folder)
        if self._output_folder:
            self.cm.set("base_folder", "output_folder", self._output_folder)

        self.cm.save()
        messagebox.showinfo("Đã lưu", "Đã lưu cấu hình vào config.json")

    def _export_config(self):
        """Export all config to JSON file"""
        import json

        # Get all config sections
        full_config = self.cm.config.copy()

        file_path = filedialog.asksaveasfilename(
            title="Export cấu hình",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="photofit_config.json"
        )

        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(full_config, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Thành công", f"Đã export cấu hình ra:\n{file_path}")

    def _import_config(self):
        """Import config from JSON file"""
        import json
        import sys

        file_path = filedialog.askopenfilename(
            title="Import cấu hình",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Merge with current config
            self.cm._merge(self.cm.config, config_data)
            self.cm.save()

            messagebox.showinfo("Thành công", "Đã import cấu hình!\n\nPhần mềm sẽ khởi động lại để áp dụng cấu hình mới...")

            # Schedule restart after messagebox closes
            self.after(100, self._restart_app)

        except json.JSONDecodeError:
            messagebox.showerror("Lỗi", "File JSON không hợp lệ")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể import: {str(e)}")

    def _restart_app(self):
        """Restart the application to apply new config."""
        try:
            # Get current executable path
            if getattr(sys, 'frozen', False):
                # Running as compiled exe
                exe_path = sys.executable
            else:
                # Running as Python script
                exe_path = sys.executable

            # Close current window
            self.destroy()

            # Start new process
            import subprocess
            subprocess.Popen([exe_path, "main.py"])

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể khởi động lại: {str(e)}")

    def _update_language_buttons(self):
        """Update button styles based on current language."""
        lang = self.lang_var.get()
        if lang == "VI":
            self.btn_vn.configure(fg_color=C_DANGER, hover_color="#DC2626", text_color="#FFFFFF")
            self.btn_en.configure(fg_color=C_CARD, hover_color=C_CARD_HOVER, text_color=C_TEXT_DIM)
        else:
            self.btn_en.configure(fg_color=C_SUCCESS, hover_color="#059669", text_color="#FFFFFF")
            self.btn_vn.configure(fg_color=C_CARD, hover_color=C_CARD_HOVER, text_color=C_TEXT_DIM)

    def _set_language(self, lang: str):
        """Set language and update button styles."""
        self.lang_var.set(lang)
        self._update_language_buttons()
        # Save to config
        self.cm.set("settings", "language", lang)
        self.cm.save()

    def _show_software_info(self):
        """Show software info with version history."""
        popup = ctk.CTkToplevel(self)
        popup.title("Thông tin phần mềm")
        popup.geometry("420x500")
        popup.configure(fg_color=C_SURFACE)
        popup.transient(self)

        # Center popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (420 // 2)
        y = (popup.winfo_screenheight() // 2) - (500 // 2)
        popup.geometry(f"420x500+{x}+{y}")

        # Logo & Title
        ctk.CTkLabel(
            popup, text=f"{APP_LOGO}  {APP_NAME}",
            font=("Segoe UI", 18, "bold"), text_color=C_TEXT
        ).pack(pady=(20, 4))

        ctk.CTkLabel(
            popup, text=f"Phiên bản: {APP_VERSION}",
            font=("Segoe UI", 12), text_color=C_ACCENT
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            popup, text="Công cụ xử lý ảnh thẻ hàng loạt",
            font=("Segoe UI", 11), text_color=C_TEXT_DIM
        ).pack(pady=(0, 16))

        # Separator
        sep = ctk.CTkFrame(popup, height=1, fg_color=C_BORDER)
        sep.pack(fill="x", padx=20, pady=(0, 12))

        # Version history title
        ctk.CTkLabel(
            popup, text="📜 Lịch sử phiên bản",
            font=("Segoe UI", 13, "bold"), text_color=C_TEXT
        ).pack(pady=(0, 8))

        # Scrollable version history
        scroll = ctk.CTkScrollableFrame(popup, fg_color=C_CARD, corner_radius=8)
        scroll.pack(fill="both", expand=True, padx=16, pady=8)

        for log in UPDATE_LOGS:
            if log.startswith("v"):
                ctk.CTkLabel(
                    scroll, text=log,
                    font=("Segoe UI", 11, "bold"), text_color=C_ACCENT,
                    anchor="w"
                ).pack(fill="x", padx=8, pady=(8, 2))
            else:
                ctk.CTkLabel(
                    scroll, text=f"• {log}",
                    font=("Segoe UI", 10), text_color=C_TEXT_DIM,
                    anchor="w"
                ).pack(fill="x", padx=16, pady=1)

        # Close button
        ctk.CTkButton(
            popup, text="✕ Đóng", command=popup.destroy,
            fg_color=C_CARD, border_color=C_BORDER,
            text_color=C_TEXT, width=120
        ).pack(pady=16)

    def _show_update_logs(self):
        # Now just calls _show_software_info for combined view
        self._show_software_info()

    def _show_tools(self):
        """Show Tools panel with new features."""
        self._cancel_refresh()

        self._current_view = "tools"
        self.btn_import.configure(fg_color=C_CARD, border_color=C_BORDER)
        self.btn_process.configure(fg_color=C_CARD, border_color=C_BORDER)

        # Clear sidebar
        for w in self.sidebar.winfo_children():
            w.destroy()

        # Clear main content
        for w in self.main_content.winfo_children():
            w.destroy()

        # Build tools content
        main = self.main_content
        main.columnconfigure(0, weight=1)
        main.rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(main, fg_color=C_CARD, corner_radius=10, border_width=1, border_color=C_BORDER)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 6))

        ctk.CTkLabel(
            header, text="🛠️ Công cụ mở rộng",
            font=("Segoe UI", 16, "bold"), text_color=C_TEXT
        ).pack(pady=16)

        # Tools grid
        tools_scroll = ctk.CTkScrollableFrame(main, fg_color="transparent")
        tools_scroll.grid(row=1, column=0, sticky="nsew", padx=16, pady=6)
        tools_scroll.columnconfigure(0, weight=1)

        # Tool cards
        tools = [
            ("📋", "Template System", "Lưu và quản lý các preset xử lý", self._open_template_manager),
            ("📊", "Statistics", "Xem thống kê xử lý ảnh", self._open_statistics),
            ("🖨️", "Print Layout", "Tạo layout in ấn A4", self._open_print_layout),
            ("📤", "Batch Export", "Export nhiều format", self._open_batch_export),
            ("🌐", "Web Server", "Khởi động web server", self._open_web_server),
            ("🎭", "Face Quality", "Đánh giá chất lượng ảnh", self._open_face_quality),
        ]

        for idx, (icon, title, desc, cmd) in enumerate(tools):
            card = ctk.CTkFrame(tools_scroll, fg_color=C_CARD, corner_radius=10, border_width=1, border_color=C_BORDER)
            card.grid(row=idx, column=0, sticky="ew", pady=6)
            card.columnconfigure(1, weight=1)

            ctk.CTkLabel(card, text=icon, font=("Segoe UI Emoji", 28), text_color=C_ACCENT, width=60).grid(row=0, column=0, padx=16, pady=16)

            info = ctk.CTkFrame(card, fg_color="transparent")
            info.grid(row=0, column=1, sticky="ew", pady=16)
            info.columnconfigure(0, weight=1)

            ctk.CTkLabel(info, text=title, font=("Segoe UI", 14, "bold"), text_color=C_TEXT, anchor="w").grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(info, text=desc, font=("Segoe UI", 11), text_color=C_TEXT_MUTED, anchor="w").grid(row=1, column=0, sticky="w", pady=(4, 0))

            ctk.CTkButton(card, text="Mở", width=80, height=32, fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER, command=cmd).grid(row=0, column=2, padx=16)

    def _open_template_manager(self):
        """Open template manager."""
        try:
            from ui.template_panel import TemplatePanel
            popup = ctk.CTkToplevel(self)
            popup.title("📋 Template Manager")
            popup.geometry("400x500")
            popup.configure(fg_color=C_SURFACE)
            popup.transient(self)

            # Center popup
            popup.update_idletasks()
            x = (popup.winfo_screenwidth() // 2) - (400 // 2)
            y = (popup.winfo_screenheight() // 2) - (500 // 2)
            popup.geometry(f"400x500+{x}+{y}")

            panel = TemplatePanel(popup, config_manager=self.cm, fg_color=C_SURFACE)
            panel.pack(fill="both", expand=True, padx=10, pady=10)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _open_statistics(self):
        """Open statistics panel."""
        try:
            from src.statistics import get_stats, get_import_stats
            import_stats = get_import_stats()
            stats = get_stats()

            import_summary = import_stats.get_summary()
            import_daily = import_stats.get_daily_stats(7)

            summary = stats.get_summary()
            daily = stats.get_daily_stats(7)
            template_usage = stats.get_template_usage()

            popup = ctk.CTkToplevel(self)
            popup.title("📊 Thống kê")
            popup.geometry("550x750")
            popup.configure(fg_color=C_SURFACE)
            popup.transient(self)

            scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
            scroll.pack(fill="both", expand=True, padx=16, pady=16)

            ctk.CTkLabel(scroll, text="📊 Thống kê", font=("Segoe UI", 16, "bold"), text_color=C_TEXT).pack(pady=(0, 16))

            # Import stats
            ctk.CTkLabel(scroll, text="📥 Thống kê Tiếp nhận", font=("Segoe UI", 14, "bold"), text_color=C_ACCENT).pack(anchor="w", pady=(0, 8))

            import_summary_frame = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=10)
            import_summary_frame.pack(fill="x", pady=(0, 12))

            import_row1 = ctk.CTkFrame(import_summary_frame, fg_color="transparent")
            import_row1.pack(fill="x", padx=16, pady=12)

            imp_card1 = ctk.CTkFrame(import_row1, fg_color=C_BG, corner_radius=8)
            imp_card1.pack(side="left", expand=True, fill="both", padx=4)
            ctk.CTkLabel(imp_card1, text="📷 Tổng đã xử lý", font=("Segoe UI", 10), text_color=C_TEXT_MUTED).pack(pady=(8, 4))
            ctk.CTkLabel(imp_card1, text=str(import_summary.get('total_processed', 0)), font=("Segoe UI", 24, "bold"), text_color=C_ACCENT).pack(pady=(0, 8))

            imp_card2 = ctk.CTkFrame(import_row1, fg_color=C_BG, corner_radius=8)
            imp_card2.pack(side="left", expand=True, fill="both", padx=4)
            ctk.CTkLabel(imp_card2, text="✅ Thành công", font=("Segoe UI", 10), text_color=C_TEXT_MUTED).pack(pady=(8, 4))
            ctk.CTkLabel(imp_card2, text=str(import_summary.get('total_success', 0)), font=("Segoe UI", 24, "bold"), text_color=C_SUCCESS).pack(pady=(0, 8))

            imp_card3 = ctk.CTkFrame(import_row1, fg_color=C_BG, corner_radius=8)
            imp_card3.pack(side="left", expand=True, fill="both", padx=4)
            ctk.CTkLabel(imp_card3, text="❌ Thất bại", font=("Segoe UI", 10), text_color=C_TEXT_MUTED).pack(pady=(8, 4))
            ctk.CTkLabel(imp_card3, text=str(import_summary.get('total_errors', 0)), font=("Segoe UI", 24, "bold"), text_color=C_DANGER).pack(pady=(0, 8))

            # Processing stats
            sep = ctk.CTkFrame(popup, height=1, fg_color=C_BORDER)
            sep.pack(fill="x", padx=20, pady=(12, 12))

            ctk.CTkLabel(scroll, text="⚙️ Thống kê Xử lý", font=("Segoe UI", 14, "bold"), text_color=C_SUCCESS).pack(anchor="w", pady=(12, 8))

            summary_frame = ctk.CTkFrame(scroll, fg_color=C_CARD, corner_radius=10)
            summary_frame.pack(fill="x", pady=(0, 12))

            row1 = ctk.CTkFrame(summary_frame, fg_color="transparent")
            row1.pack(fill="x", padx=16, pady=12)

            card1 = ctk.CTkFrame(row1, fg_color=C_BG, corner_radius=8)
            card1.pack(side="left", expand=True, fill="both", padx=4)
            ctk.CTkLabel(card1, text="📷 Tổng ảnh", font=("Segoe UI", 10), text_color=C_TEXT_MUTED).pack(pady=(8, 4))
            ctk.CTkLabel(card1, text=str(summary.get('total_processed', 0)), font=("Segoe UI", 24, "bold"), text_color=C_ACCENT).pack(pady=(0, 8))

            card2 = ctk.CTkFrame(row1, fg_color=C_BG, corner_radius=8)
            card2.pack(side="left", expand=True, fill="both", padx=4)
            ctk.CTkLabel(card2, text="✅ Thành công", font=("Segoe UI", 10), text_color=C_TEXT_MUTED).pack(pady=(8, 4))
            ctk.CTkLabel(card2, text=str(summary.get('total_success', 0)), font=("Segoe UI", 24, "bold"), text_color=C_SUCCESS).pack(pady=(0, 8))

            card3 = ctk.CTkFrame(row1, fg_color=C_BG, corner_radius=8)
            card3.pack(side="left", expand=True, fill="both", padx=4)
            ctk.CTkLabel(card3, text="❌ Lỗi", font=("Segoe UI", 10), text_color=C_TEXT_MUTED).pack(pady=(8, 4))
            ctk.CTkLabel(card3, text=str(summary.get('total_errors', 0)), font=("Segoe UI", 24, "bold"), text_color=C_DANGER).pack(pady=(0, 8))

            ctk.CTkButton(popup, text="✕ Đóng", command=popup.destroy, fg_color=C_CARD, border_color=C_BORDER, text_color=C_TEXT).pack(pady=(0, 16))

        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _open_print_layout(self):
        """Open print layout tool."""
        from src.print_layout import PrintLayout

        popup = ctk.CTkToplevel(self)
        popup.title("🖨️ Print Layout - Tạo trang in")
        popup.geometry("500x550")
        popup.configure(fg_color=C_SURFACE)
        popup.transient(self)

        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (500 // 2)
        y = (popup.winfo_screenheight() // 2) - (550 // 2)
        popup.geometry(f"500x550+{x}+{y}")

        ctk.CTkLabel(popup, text="🖨️ Tạo Layout In Ấn", font=("Segoe UI", 16, "bold"), text_color=C_TEXT).pack(pady=16)

        folder_var = ctk.StringVar(value="Chưa chọn thư mục...")

        def select_folder():
            folder = filedialog.askdirectory(title="Chọn thư mục chứa ảnh")
            if folder:
                folder_var.set(folder)

        ctk.CTkEntry(popup, textvariable=folder_var, state="readonly", fg_color=C_CARD, border_color=C_BORDER, text_color=C_TEXT).pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(popup, text="📂 Chọn thư mục", command=select_folder, fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER).pack(pady=5)

        ctk.CTkLabel(popup, text="📐 Chọn kích thước:", text_color=C_TEXT, font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=20, pady=(15, 5))

        layouts = [
            ("A4 - 4 ảnh 3x4 (2x2)", "3x4", 2, 2),
            ("A4 - 6 ảnh 3x4 (2x3)", "3x4", 2, 3),
            ("A4 - 6 ảnh 4x6 (2x3)", "4x6", 2, 3),
        ]

        layout_var = ctk.StringVar(value=layouts[0][0])

        for text, _, _, _ in layouts:
            ctk.CTkRadioButton(popup, text=text, variable=layout_var, value=text, fg_color=C_ACCENT, text_color=C_TEXT).pack(anchor="w", padx=40, pady=2)

        def generate_layout():
            folder = folder_var.get()
            if folder == "Chưa chọn thư mục..." or not os.path.exists(folder):
                messagebox.showwarning("Chưa chọn thư mục", "Vui lòng chọn thư mục chứa ảnh!")
                return

            selected_layout = None
            for text, size, cols, rows in layouts:
                if text == layout_var.get():
                    selected_layout = (size, cols, rows)
                    break

            if not selected_layout:
                return

            photo_size, columns, rows = selected_layout
            from src.utils import scan_images
            images = scan_images(folder)

            if not images:
                messagebox.showwarning("Không có ảnh", "Thư mục không có ảnh nào!")
                return

            layout = PrintLayout()
            save_path = filedialog.asksaveasfilename(title="Lưu layout", defaultextension=".jpg", filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")])

            if save_path:
                try:
                    layout.create_a4_layout(image_paths=images, photo_size=photo_size, columns=columns, rows=rows, output_path=save_path)
                    messagebox.showinfo("Thành công", f"Đã lưu layout vào:\n{save_path}")
                except Exception as e:
                    messagebox.showerror("Lỗi", str(e))

        ctk.CTkButton(popup, text="🖨️ Tạo Layout", command=generate_layout, fg_color=C_SUCCESS, hover_color="#059669", font=("Segoe UI", 12, "bold"), height=40).pack(pady=20, padx=20, fill="x")
        ctk.CTkButton(popup, text="✕ Đóng", command=popup.destroy, fg_color=C_CARD, border_color=C_BORDER, text_color=C_TEXT).pack(pady=(0, 16))

    def _open_batch_export(self):
        """Open batch export tool."""
        popup = ctk.CTkToplevel(self)
        popup.title("📤 Batch Export")
        popup.geometry("450x400")
        popup.configure(fg_color=C_SURFACE)
        popup.transient(self)

        ctk.CTkLabel(popup, text="📤 Export hàng loạt", font=("Segoe UI", 16, "bold"), text_color=C_TEXT).pack(pady=16)

        folder_var = ctk.StringVar(value="Chưa chọn...")

        def select_folder():
            folder = filedialog.askdirectory(title="Chọn thư mục ảnh")
            if folder:
                folder_var.set(folder)

        ctk.CTkEntry(popup, textvariable=folder_var, state="readonly", fg_color=C_CARD, border_color=C_BORDER, text_color=C_TEXT).pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(popup, text="📂 Chọn thư mục", command=select_folder, fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER).pack(pady=5)

        ctk.CTkLabel(popup, text="Chọn format xuất:", text_color=C_TEXT, font=("Segoe UI", 12, "bold")).pack(pady=10)

        formats = ["JPEG", "PNG"]
        format_vars = {fmt: ctk.BooleanVar(value=True) for fmt in formats}

        for fmt in formats:
            ctk.CTkCheckBox(popup, text=fmt, variable=format_vars[fmt], fg_color=C_ACCENT, text_color=C_TEXT).pack(anchor="w", padx=40)

        def do_export():
            folder = folder_var.get()
            if folder == "Chưa chọn..." or not os.path.exists(folder):
                messagebox.showwarning("Chưa chọn", "Vui lòng chọn thư mục!")
                return

            selected = [f for f, v in format_vars.items() if v.get()]
            if not selected:
                messagebox.showwarning("Chưa chọn", "Vui lòng chọn ít nhất 1 format!")
                return

            save_folder = filedialog.askdirectory(title="Chọn thư mục lưu")
            if not save_folder:
                return

            from src.utils import scan_images
            images = scan_images(folder)

            if not images:
                messagebox.showwarning("Không có ảnh", "Thư mục không có ảnh!")
                return

            import cv2
            count = 0
            for img_path in images:
                base_name = os.path.splitext(os.path.basename(img_path))[0]
                for fmt in selected:
                    ext = fmt.lower()
                    output_path = os.path.join(save_folder, f"{base_name}.{ext}")
                    img = cv2.imread(img_path)
                    if img is not None:
                        cv2.imwrite(output_path, img)
                        count += 1

            messagebox.showinfo("Thành công", f"Đã export {count} file!")

        ctk.CTkButton(popup, text="📤 Export", command=do_export, fg_color=C_SUCCESS, hover_color="#059669", font=("Segoe UI", 12, "bold"), height=40).pack(pady=20, padx=20, fill="x")
        ctk.CTkButton(popup, text="✕ Đóng", command=popup.destroy, fg_color=C_CARD, border_color=C_BORDER, text_color=C_TEXT).pack(pady=(0, 16))

    def _open_web_server(self):
        """Start web server."""
        try:
            from src.web_server import PhotoFitWebServer
            server = PhotoFitWebServer(port=8080, output_folder=self._output_folder or None)
            server.start()
            messagebox.showinfo("Web Server", f"Web server đã khởi động!\n\nTruy cập: http://localhost:8080\n\nTừ điện thoại: http://[IP máy]:8080")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def _open_face_quality(self):
        """Open face quality assessment."""
        popup = ctk.CTkToplevel(self)
        popup.title("🎭 Face Quality")
        popup.geometry("450x400")
        popup.configure(fg_color=C_SURFACE)
        popup.transient(self)

        ctk.CTkLabel(popup, text="🎭 Đánh giá chất lượng ảnh khuôn mặt", font=("Segoe UI", 16, "bold"), text_color=C_TEXT).pack(pady=16)

        folder_var = ctk.StringVar(value="Chưa chọn...")

        def select_folder():
            folder = filedialog.askdirectory(title="Chọn thư mục ảnh")
            if folder:
                folder_var.set(folder)

        ctk.CTkEntry(popup, textvariable=folder_var, state="readonly", fg_color=C_CARD, border_color=C_BORDER, text_color=C_TEXT).pack(fill="x", padx=20, pady=5)
        ctk.CTkButton(popup, text="📂 Chọn thư mục", command=select_folder, fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER).pack(pady=5)

        def analyze():
            folder = folder_var.get()
            if folder == "Chưa chọn..." or not os.path.exists(folder):
                messagebox.showwarning("Chưa chọn", "Vui lòng chọn thư mục!")
                return

            from src.utils import scan_images
            images = scan_images(folder)

            if not images:
                messagebox.showwarning("Không có ảnh", "Thư mục không có ảnh!")
                return

            try:
                from src.face_detector import FaceDetector
                detector = FaceDetector()

                results = []
                for img_path in images:
                    img = cv2.imread(img_path)
                    if img is not None:
                        try:
                            faces = detector.detect_faces(img)
                            quality = "Tốt" if len(faces) == 1 else ("Nhiều khuôn mặt" if len(faces) > 1 else "Không phát hiện khuôn mặt")
                            results.append((os.path.basename(img_path), quality, len(faces)))
                        except Exception as e:
                            results.append((os.path.basename(img_path), "Lỗi", 0))

                result_text = "📊 Kết quả đánh giá:\n\n"
                good = sum(1 for r in results if r[1] == "Tốt")
                result_text += f"Tổng: {len(results)} ảnh\n"
                result_text += f"✅ Chất lượng tốt: {good}\n\n"

                for name, quality, count in results[:10]:
                    result_text += f"- {name}: {quality}\n"

                if len(results) > 10:
                    result_text += f"... và {len(results) - 10} ảnh khác"

                messagebox.showinfo("Kết quả", result_text)
            except Exception as e:
                messagebox.showerror("Lỗi", str(e))

        ctk.CTkButton(popup, text="🔍 Phân tích", command=analyze, fg_color=C_SUCCESS, hover_color="#059669", font=("Segoe UI", 12, "bold"), height=40).pack(pady=20, padx=20, fill="x")
        ctk.CTkButton(popup, text="✕ Đóng", command=popup.destroy, fg_color=C_CARD, border_color=C_BORDER, text_color=C_TEXT).pack(pady=(0, 16))

    def _show_user_guide(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Hướng dẫn sử dụng")
        popup.geometry("500x550")
        popup.resizable(False, False)
        popup.configure(fg_color=C_SURFACE)
        popup.transient(self)

        scroll = ctk.CTkScrollableFrame(popup, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=16)

        guide_text = """📖 HƯỚNG DẪN SỬ DỤNG PHOTOFIT STUDIO v1.0

🟢 MENU TIẾP NHẬN
1. Chọn thư mục Capture
2. Cấu hình kích thước trong sidebar
3. Nhập MSSV và bấm "XỬ LÝ"

🟡 MENU XỬ LÝ
1. Input: Thư mục ảnh đã tiếp nhận
2. Output: Thư mục lưu ảnh đã xử lý
3. Cấu hình trong sidebar
4. Bấm "BẮT ĐẦU XỬ LÝ"

🛠️ CÔNG CỤ MỞ RỘNG
📋 Template System
📊 Statistics
🖨️ Print Layout
📤 Batch Export
🌐 Web Server
🎭 Face Quality"""

        ctk.CTkLabel(scroll, text=guide_text, font=("Segoe UI", 11), text_color=C_TEXT, justify="left").pack(anchor="w")
        ctk.CTkButton(popup, text="✕ Đóng", command=popup.destroy, fg_color=C_CARD, border_color=C_BORDER, text_color=C_TEXT).pack(pady=(0, 16))
