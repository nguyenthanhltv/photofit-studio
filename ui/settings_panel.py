"""Settings panel - Modern dark theme design."""

import customtkinter as ctk
from src.config_manager import ConfigManager, SIZE_PRESETS, BG_COLOR_PRESETS

# Color palette (shared with main_window)
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

FONT = "Segoe UI"


class SettingsPanel(ctk.CTkScrollableFrame):
    """Panel with all processing configuration options - modern dark theme."""

    def __init__(self, master, config_manager: ConfigManager, **kwargs):
        super().__init__(master, **kwargs)
        self.cm = config_manager
        self.configure(
            scrollbar_button_color=C_BORDER,
            scrollbar_button_hover_color=C_TEXT_MUTED,
        )
        self._build()

    # ── Helpers ──────────────────────────────────────────────
    def _section_label(self, parent, text: str, row: int, **grid_kw):
        lbl = ctk.CTkLabel(
            parent, text=text,
            font=(FONT, 13, "bold"), text_color=C_TEXT,
        )
        lbl.grid(row=row, column=0, columnspan=2, sticky="w",
                 padx=14, pady=(18, 6), **grid_kw)
        return lbl

    def _separator(self, parent, row: int):
        sep = ctk.CTkFrame(parent, height=1, fg_color=C_BORDER)
        sep.grid(row=row, column=0, columnspan=2, sticky="ew", padx=14, pady=(4, 0))

    def _checkbox(self, parent, text: str, variable, row: int):
        cb = ctk.CTkCheckBox(
            parent, text=text, variable=variable,
            font=(FONT, 11), text_color=C_TEXT_DIM,
            fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
            border_color=C_BORDER, checkmark_color="#FFFFFF",
            corner_radius=4,
        )
        cb.grid(row=row, column=0, columnspan=2, sticky="w", padx=14, pady=3)
        return cb

    def _small_label(self, parent, text: str, row: int, col: int = 0, **kw):
        lbl = ctk.CTkLabel(
            parent, text=text,
            font=(FONT, 11), text_color=C_TEXT_MUTED,
        )
        lbl.grid(row=row, column=col, sticky="w", padx=14, pady=(6, 2), **kw)
        return lbl

    def _option_menu(self, parent, variable, values, row: int, command=None, width=210):
        om = ctk.CTkOptionMenu(
            parent, variable=variable, values=values,
            command=command, width=width, height=30,
            font=(FONT, 11), text_color=C_TEXT,
            fg_color=C_CARD, button_color=C_BORDER,
            button_hover_color=C_CARD_HOVER,
            dropdown_fg_color=C_CARD,
            dropdown_hover_color=C_CARD_HOVER,
            dropdown_text_color=C_TEXT,
            corner_radius=8,
        )
        om.grid(row=row, column=0, columnspan=2, sticky="w", padx=14, pady=2)
        return om

    def _entry(self, parent, variable, width=70, placeholder=""):
        return ctk.CTkEntry(
            parent, textvariable=variable, width=width, height=30,
            font=(FONT, 11), text_color=C_TEXT,
            fg_color=C_CARD, border_color=C_BORDER,
            placeholder_text=placeholder, corner_radius=8,
        )

    # ── Build UI ────────────────────────────────────────────
    def _build(self):
        r = 0

        # ═══ BEAUTIFY ═══
        self._section_label(self, "✨  Làm đẹp", r); r += 1

        self.beautify_enabled = ctk.BooleanVar(value=self.cm.get("beautify", "enabled"))
        self._checkbox(self, "Bật làm đẹp", self.beautify_enabled, r); r += 1

        self._small_label(self, "Mức độ", r); r += 1
        self.beautify_level = ctk.StringVar(value=self.cm.get("beautify", "level"))
        level_frame = ctk.CTkFrame(self, fg_color="transparent")
        level_frame.grid(row=r, column=0, columnspan=2, sticky="w", padx=14, pady=2); r += 1
        for i, (val, lbl) in enumerate([("light", "Nhẹ"), ("medium", "Vừa"), ("strong", "Mạnh")]):
            ctk.CTkRadioButton(
                level_frame, text=lbl, variable=self.beautify_level, value=val,
                font=(FONT, 11), text_color=C_TEXT_DIM,
                fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
                border_color=C_BORDER,
                width=64,
            ).grid(row=0, column=i, padx=(0, 6), sticky="w")

        self.skin_smooth = ctk.BooleanVar(value=self.cm.get("beautify", "skin_smoothing"))
        self._checkbox(self, "Làm mịn da", self.skin_smooth, r); r += 1

        self.brightness_auto = ctk.BooleanVar(value=self.cm.get("beautify", "brightness_auto"))
        self._checkbox(self, "Auto sáng / tương phản", self.brightness_auto, r); r += 1

        self.hair_smooth = ctk.BooleanVar(value=self.cm.get("beautify", "hair_smoothing"))
        self._checkbox(self, "Làm mịn rìa tóc", self.hair_smooth, r); r += 1

        self.eye_enhance = ctk.BooleanVar(value=self.cm.get("beautify", "eye_enhancement"))
        self._checkbox(self, "Tăng sáng mắt", self.eye_enhance, r); r += 1

        self.teeth_whiten = ctk.BooleanVar(value=self.cm.get("beautify", "teeth_whitening"))
        self._checkbox(self, "Làm trắng răng", self.teeth_whiten, r); r += 1

        self._separator(self, r); r += 1

        # ═══ BACKGROUND ═══
        self._section_label(self, "🎨  Nền ảnh", r); r += 1

        self.bg_enabled = ctk.BooleanVar(value=self.cm.get("background", "enabled"))
        self._checkbox(self, "Xóa / Thay nền", self.bg_enabled, r); r += 1

        self._small_label(self, "Màu nền", r); r += 1
        bg_names = list(BG_COLOR_PRESETS.keys())
        current_hex = self.cm.get("background", "color")
        current_bg = "white"
        for k, v in BG_COLOR_PRESETS.items():
            if v["hex"].upper() == current_hex.upper():
                current_bg = k
                break
        self.bg_color_name = ctk.StringVar(value=current_bg)
        self.bg_dropdown = self._option_menu(self, self.bg_color_name, bg_names, r,
                                              command=self._on_bg_change); r += 1

        self._small_label(self, "Custom Hex", r); r += 1
        self.custom_hex = ctk.StringVar(value=current_hex)
        hex_entry = self._entry(self, self.custom_hex, width=120, placeholder="#FFFFFF")
        hex_entry.grid(row=r, column=0, columnspan=2, sticky="w", padx=14, pady=2); r += 1

        self.edge_refine = ctk.BooleanVar(value=self.cm.get("background", "edge_refinement"))
        self._checkbox(self, "Làm mịn viền", self.edge_refine, r); r += 1

        self._separator(self, r); r += 1

        # ═══ AI ENHANCE ═══
        self._section_label(self, "🤖  AI Nâng cao", r); r += 1

        self.ai_enabled = ctk.BooleanVar(value=self.cm.get("ai_enhance", "enabled"))
        self._checkbox(self, "Bật AI nâng cao chất lượng", self.ai_enabled, r); r += 1

        self._small_label(self, "Mức độ AI", r); r += 1
        self.ai_level = ctk.StringVar(value=self.cm.get("ai_enhance", "level"))
        ai_level_frame = ctk.CTkFrame(self, fg_color="transparent")
        ai_level_frame.grid(row=r, column=0, columnspan=2, sticky="w", padx=14, pady=2); r += 1
        for i, (val, lbl) in enumerate([("light", "Nhẹ"), ("medium", "Vừa"), ("strong", "Mạnh")]):
            ctk.CTkRadioButton(
                ai_level_frame, text=lbl, variable=self.ai_level, value=val,
                font=(FONT, 11), text_color=C_TEXT_DIM,
                fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
                border_color=C_BORDER,
                width=64,
            ).grid(row=0, column=i, padx=(0, 6), sticky="w")

        self.ai_sharpen = ctk.BooleanVar(value=self.cm.get("ai_enhance", "enhance_sharpness"))
        self._checkbox(self, "Tăng độ nét (Sharpness)", self.ai_sharpen, r); r += 1

        self.ai_colors = ctk.BooleanVar(value=self.cm.get("ai_enhance", "enhance_colors"))
        self._checkbox(self, "Cải thiện màu sắc (Colors)", self.ai_colors, r); r += 1

        self.ai_denoise = ctk.BooleanVar(value=self.cm.get("ai_enhance", "denoise"))
        self._checkbox(self, "Khử nhiễu (Denoise)", self.ai_denoise, r); r += 1

        self.ai_sr = ctk.BooleanVar(value=self.cm.get("ai_enhance", "super_resolution"))
        self._checkbox(self, "Super Resolution (Phóng to nét)", self.ai_sr, r); r += 1

        self._separator(self, r); r += 1

        # ═══ RESIZE ═══
        self._section_label(self, "📐  Kích thước", r); r += 1

        self.resize_enabled = ctk.BooleanVar(value=self.cm.get("resize", "enabled"))
        self._checkbox(self, "Resize ảnh", self.resize_enabled, r); r += 1

        self.auto_subject_fit = ctk.BooleanVar(value=self.cm.get("resize", "auto_subject_fit"))
        self._checkbox(self, "Tự canh chủ thể vào khung", self.auto_subject_fit, r); r += 1

        self._small_label(self, "Khoảng cách", r); r += 1
        self.distance_level = ctk.StringVar(value=self.cm.get("resize", "distance_level"))
        distance_frame = ctk.CTkFrame(self, fg_color="transparent")
        distance_frame.grid(row=r, column=0, columnspan=2, sticky="w", padx=14, pady=2); r += 1
        for i, (val, lbl) in enumerate([("near", "Gần"), ("medium", "Vừa"), ("far", "Xa")]):
            ctk.CTkRadioButton(
                distance_frame, text=lbl, variable=self.distance_level, value=val,
                font=(FONT, 11), text_color=C_TEXT_DIM,
                fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
                border_color=C_BORDER,
                width=64,
            ).grid(row=0, column=i, padx=(0, 6), sticky="w")

        self._small_label(self, "Preset", r); r += 1
        size_names = list(SIZE_PRESETS.keys())
        self.size_preset = ctk.StringVar(value=self.cm.get("resize", "preset"))
        self.size_dropdown = self._option_menu(self, self.size_preset, size_names, r,
                                                command=self._on_size_change); r += 1

        # Width × Height
        size_frame = ctk.CTkFrame(self, fg_color="transparent")
        size_frame.grid(row=r, column=0, columnspan=2, sticky="w", padx=14, pady=4); r += 1

        self.width_var = ctk.StringVar(value=str(self.cm.get("resize", "width_px")))
        self.height_var = ctk.StringVar(value=str(self.cm.get("resize", "height_px")))

        ctk.CTkLabel(size_frame, text="W", font=(FONT, 10), text_color=C_TEXT_MUTED).grid(row=0, column=0)
        self._entry(size_frame, self.width_var, 58).grid(row=0, column=1, padx=4)
        ctk.CTkLabel(size_frame, text="×", font=(FONT, 11), text_color=C_TEXT_MUTED).grid(row=0, column=2)
        ctk.CTkLabel(size_frame, text="H", font=(FONT, 10), text_color=C_TEXT_MUTED).grid(row=0, column=3, padx=(4, 0))
        self._entry(size_frame, self.height_var, 58).grid(row=0, column=4, padx=4)
        ctk.CTkLabel(size_frame, text="px", font=(FONT, 10), text_color=C_TEXT_MUTED).grid(row=0, column=5)

        # DPI
        dpi_frame = ctk.CTkFrame(self, fg_color="transparent")
        dpi_frame.grid(row=r, column=0, columnspan=2, sticky="w", padx=14, pady=2); r += 1
        ctk.CTkLabel(dpi_frame, text="DPI", font=(FONT, 10), text_color=C_TEXT_MUTED).grid(row=0, column=0, padx=(0, 6))
        self.dpi_var = ctk.StringVar(value=str(self.cm.get("resize", "dpi")))
        ctk.CTkOptionMenu(
            dpi_frame, variable=self.dpi_var, values=["72", "150", "300"],
            width=80, height=28, font=(FONT, 11), text_color=C_TEXT,
            fg_color=C_CARD, button_color=C_BORDER,
            button_hover_color=C_CARD_HOVER,
            dropdown_fg_color=C_CARD, dropdown_hover_color=C_CARD_HOVER,
            dropdown_text_color=C_TEXT, corner_radius=8,
        ).grid(row=0, column=1)

        self._separator(self, r); r += 1

        # ═══ OUTPUT ═══
        self._section_label(self, "💾  Output", r); r += 1

        self._small_label(self, "Format", r); r += 1
        self.format_var = ctk.StringVar(value=self.cm.get("output", "format"))
        fmt_frame = ctk.CTkFrame(self, fg_color="transparent")
        fmt_frame.grid(row=r, column=0, columnspan=2, sticky="w", padx=14, pady=2); r += 1
        for i, (val, lbl) in enumerate([("jpg", "JPG"), ("png", "PNG")]):
            ctk.CTkRadioButton(
                fmt_frame, text=lbl, variable=self.format_var, value=val,
                font=(FONT, 11), text_color=C_TEXT_DIM,
                fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
                border_color=C_BORDER,
            ).grid(row=0, column=i, padx=(0, 16))

        # Quality slider
        quality_frame = ctk.CTkFrame(self, fg_color="transparent")
        quality_frame.grid(row=r, column=0, columnspan=2, sticky="ew", padx=14, pady=4); r += 1
        ctk.CTkLabel(quality_frame, text="Quality", font=(FONT, 10),
                     text_color=C_TEXT_MUTED).grid(row=0, column=0, padx=(0, 8))
        self.quality_var = ctk.IntVar(value=self.cm.get("output", "quality"))
        ctk.CTkSlider(
            quality_frame, from_=50, to=100, variable=self.quality_var,
            width=120, height=16,
            fg_color=C_BORDER, progress_color=C_ACCENT,
            button_color=C_TEXT, button_hover_color="#FFFFFF",
        ).grid(row=0, column=1, padx=4)
        self.quality_label = ctk.CTkLabel(quality_frame, text=str(self.quality_var.get()),
                                           font=(FONT, 11, "bold"), text_color=C_ACCENT, width=30)
        self.quality_label.grid(row=0, column=2)
        self.quality_var.trace_add("write", lambda *_: self.quality_label.configure(
            text=str(self.quality_var.get())))

        self.overwrite_var = ctk.BooleanVar(value=self.cm.get("output", "overwrite"))
        self._checkbox(self, "Ghi đè file trùng tên", self.overwrite_var, r); r += 1

        self._separator(self, r); r += 1

        # ═══ PROCESSING ═══
        self._section_label(self, "⚙️  Xử lý", r); r += 1

        workers_frame = ctk.CTkFrame(self, fg_color="transparent")
        workers_frame.grid(row=r, column=0, columnspan=2, sticky="w", padx=14, pady=4); r += 1
        ctk.CTkLabel(workers_frame, text="Workers", font=(FONT, 10),
                     text_color=C_TEXT_MUTED).grid(row=0, column=0, padx=(0, 8))
        self.workers_var = ctk.StringVar(value=str(self.cm.get("processing", "parallel_workers")))
        ctk.CTkOptionMenu(
            workers_frame, variable=self.workers_var, values=["1", "2", "4", "8"],
            width=72, height=28, font=(FONT, 11), text_color=C_TEXT,
            fg_color=C_CARD, button_color=C_BORDER,
            button_hover_color=C_CARD_HOVER,
            dropdown_fg_color=C_CARD, dropdown_hover_color=C_CARD_HOVER,
            dropdown_text_color=C_TEXT, corner_radius=8,
        ).grid(row=0, column=1)

        self.skip_error = ctk.BooleanVar(value=self.cm.get("processing", "skip_on_error"))
        self._checkbox(self, "Bỏ qua ảnh lỗi, tiếp tục", self.skip_error, r); r += 1

        # Bottom padding
        ctk.CTkFrame(self, fg_color="transparent", height=16).grid(
            row=r, column=0, columnspan=2)

    # ── Callbacks ───────────────────────────────────────────
    def _on_bg_change(self, name):
        preset = BG_COLOR_PRESETS.get(name, BG_COLOR_PRESETS["white"])
        if name != "custom":
            self.custom_hex.set(preset["hex"])

    def _on_size_change(self, name):
        preset = SIZE_PRESETS.get(name, SIZE_PRESETS["3x4"])
        if name != "custom":
            self.width_var.set(str(preset["width_px"]))
            self.height_var.set(str(preset["height_px"]))

    def apply_to_config(self) -> dict:
        """Read all UI values and update config manager. Returns config dict."""
        self.cm.set("beautify", "enabled", self.beautify_enabled.get())
        self.cm.set("beautify", "level", self.beautify_level.get())
        self.cm.set("beautify", "skin_smoothing", self.skin_smooth.get())
        self.cm.set("beautify", "brightness_auto", self.brightness_auto.get())
        self.cm.set("beautify", "hair_smoothing", self.hair_smooth.get())
        self.cm.set("beautify", "eye_enhancement", self.eye_enhance.get())
        self.cm.set("beautify", "teeth_whitening", self.teeth_whiten.get())

        self.cm.set("background", "enabled", self.bg_enabled.get())
        self.cm.set("background", "color", self.custom_hex.get())
        self.cm.set("background", "edge_refinement", self.edge_refine.get())

        # AI Enhancement settings
        self.cm.set("ai_enhance", "enabled", self.ai_enabled.get())
        self.cm.set("ai_enhance", "level", self.ai_level.get())
        self.cm.set("ai_enhance", "enhance_sharpness", self.ai_sharpen.get())
        self.cm.set("ai_enhance", "enhance_colors", self.ai_colors.get())
        self.cm.set("ai_enhance", "denoise", self.ai_denoise.get())
        self.cm.set("ai_enhance", "super_resolution", self.ai_sr.get())

        self.cm.set("resize", "enabled", self.resize_enabled.get())
        self.cm.set("resize", "auto_subject_fit", self.auto_subject_fit.get())
        self.cm.set("resize", "distance_level", self.distance_level.get())
        self.cm.set("resize", "preset", self.size_preset.get())
        try:
            self.cm.set("resize", "width_px", int(self.width_var.get()))
            self.cm.set("resize", "height_px", int(self.height_var.get()))
        except ValueError:
            pass
        try:
            self.cm.set("resize", "dpi", int(self.dpi_var.get()))
        except ValueError:
            pass

        self.cm.set("output", "format", self.format_var.get())
        self.cm.set("output", "quality", self.quality_var.get())
        self.cm.set("output", "overwrite", self.overwrite_var.get())

        try:
            self.cm.set("processing", "parallel_workers", int(self.workers_var.get()))
        except ValueError:
            pass
        self.cm.set("processing", "skip_on_error", self.skip_error.get())

        return self.cm.config
