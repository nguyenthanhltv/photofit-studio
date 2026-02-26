"""Import Settings Panel - Sidebar for Import menu - Modern dark theme design."""

import os
import json
import customtkinter as ctk
from tkinter import filedialog, messagebox

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


class ImportSettingsPanel(ctk.CTkFrame):
    """Settings panel for Import menu - placed in sidebar."""

    def __init__(self, master, config_manager, import_panel=None, **kwargs):
        super().__init__(master, **kwargs)
        self.cm = config_manager
        self.import_panel = import_panel  # Reference to ImportPanel for getting image size
        self._build()
        
        # Load saved config
        self._load_config()

    def _build(self):
        self.columnconfigure(0, weight=1)
        
        # Title
        ctk.CTkLabel(
            self, text="⚙️ CẤU HÌNH",
            font=(FONT, 13, "bold"), text_color=C_TEXT
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(16, 12))

        # Folder Paths Section
        folder_card = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=10,
                                   border_width=1, border_color=C_BORDER)
        folder_card.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        folder_card.columnconfigure(1, weight=1)

        ctk.CTkLabel(folder_card, text="📁 Đường dẫn thư mục",
                      font=(FONT, 11, "bold"), text_color=C_TEXT
                      ).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 8))

        # Original folder - with folder picker
        ctk.CTkLabel(folder_card, text="📂 Gốc:",
                      font=(FONT, 10), text_color=C_TEXT_DIM
                      ).grid(row=1, column=0, padx=12, pady=4, sticky="w")
        
        self.original_var = ctk.StringVar(value="")
        ctk.CTkEntry(
            folder_card, textvariable=self.original_var,
            fg_color=C_SURFACE, border_color=C_BORDER,
            text_color=C_TEXT, font=(FONT, 10)
        ).grid(row=1, column=1, sticky="ew", padx=12, pady=4)
        
        ctk.CTkButton(folder_card, text="📂", width=36, height=28,
                       fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
                       font=(FONT, 10), corner_radius=6,
                       command=self._select_original_folder
                       ).grid(row=1, column=2, padx=(4, 12), pady=4)

        # Resized folder - with folder picker
        ctk.CTkLabel(folder_card, text="📂 Resize:",
                      font=(FONT, 10), text_color=C_TEXT_DIM
                      ).grid(row=2, column=0, padx=12, pady=4, sticky="w")
        
        self.resized_var = ctk.StringVar(value="")
        ctk.CTkEntry(
            folder_card, textvariable=self.resized_var,
            fg_color=C_SURFACE, border_color=C_BORDER,
            text_color=C_TEXT, font=(FONT, 10)
        ).grid(row=2, column=1, sticky="ew", padx=12, pady=4)
        
        ctk.CTkButton(folder_card, text="📂", width=36, height=28,
                       fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
                       font=(FONT, 10), corner_radius=6,
                       command=self._select_resized_folder
                       ).grid(row=2, column=2, padx=(4, 12), pady=(4, 12))

        # Size Configuration Section
        size_card = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=10,
                                  border_width=1, border_color=C_BORDER)
        size_card.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        size_card.columnconfigure(1, weight=1)

        ctk.CTkLabel(size_card, text="📏 Kích thước Resize",
                      font=(FONT, 11, "bold"), text_color=C_TEXT
                      ).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(12, 8))

        # Width
        ctk.CTkLabel(size_card, text="Width:",
                      font=(FONT, 10), text_color=C_TEXT_DIM
                      ).grid(row=1, column=0, padx=12, pady=4, sticky="w")
        
        self.width_var = ctk.StringVar(value="800")
        self.width_entry = ctk.CTkEntry(
            size_card, textvariable=self.width_var,
            fg_color=C_SURFACE, border_color=C_BORDER,
            text_color=C_TEXT, font=(FONT, 10)
        )
        self.width_entry.grid(row=1, column=1, sticky="ew", padx=12, pady=4)
        self.width_entry.bind("<KeyRelease>", lambda e: self._on_width_change())

        # Height
        ctk.CTkLabel(size_card, text="Height:",
                      font=(FONT, 10), text_color=C_TEXT_DIM
                      ).grid(row=2, column=0, padx=12, pady=4, sticky="w")
        
        self.height_var = ctk.StringVar(value="600")
        self.height_entry = ctk.CTkEntry(
            size_card, textvariable=self.height_var,
            fg_color=C_SURFACE, border_color=C_BORDER,
            text_color=C_TEXT, font=(FONT, 10)
        )
        self.height_entry.grid(row=2, column=1, sticky="ew", padx=12, pady=4)
        self.height_entry.bind("<KeyRelease>", lambda e: self._on_height_change())

        # Auto calculate
        self.auto_calc_var = ctk.BooleanVar(value=True)
        self.auto_calc_check = ctk.CTkCheckBox(
            size_card, text="Auto tính theo tỷ lệ ảnh",
            variable=self.auto_calc_var,
            font=(FONT, 9), text_color=C_TEXT_DIM,
            fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER
        )
        self.auto_calc_check.grid(row=3, column=0, columnspan=2, sticky="w", padx=12, pady=(8, 12))

        # Info text - at bottom of sidebar
        ctk.CTkLabel(
            self, text="💡 Sử dụng nút ⚙️ Cấu hình\ntrên header để lưu",
            font=(FONT, 9), text_color=C_TEXT_MUTED, justify="left"
        ).grid(row=3, column=0, sticky="w", padx=16, pady=(16, 16))

    def _load_config(self):
        """Load config from config manager"""
        try:
            import_width = self.cm.get("import", "width")
            import_height = self.cm.get("import", "height")
            auto_calc = self.cm.get("import", "auto_calculate")
            original_folder = self.cm.get("import", "original_folder")
            resized_folder = self.cm.get("import", "resized_folder")
            
            if import_width:
                self.width_var.set(str(import_width))
            if import_height:
                self.height_var.set(str(import_height))
            if auto_calc is not None:
                self.auto_calc_var.set(auto_calc)
            if original_folder:
                self.original_var.set(str(original_folder))
            if resized_folder:
                self.resized_var.set(str(resized_folder))
        except:
            pass

    def _on_width_change(self):
        """Auto-calculate height when width changes - like Paint"""
        if not self.auto_calc_var.get():
            return
        
        # Get image size from import panel if available
        img_w, img_h = 0, 0
        if self.import_panel and hasattr(self.import_panel, '_selected_image_size'):
            img_w, img_h = self.import_panel._selected_image_size
        
        # If no image selected, use default ratio 4:3
        if img_w == 0 or img_h == 0:
            img_w, img_h = 4, 3
        
        try:
            width_val = int(self.width_var.get())
            if width_val > 0:
                # Calculate height maintaining aspect ratio
                ratio = img_h / img_w
                height_val = int(width_val * ratio)
                self.height_var.set(str(height_val))
        except ValueError:
            pass

    def _on_height_change(self):
        """Auto-calculate width when height changes - like Paint"""
        if not self.auto_calc_var.get():
            return
        
        # Get image size from import panel if available
        img_w, img_h = 0, 0
        if self.import_panel and hasattr(self.import_panel, '_selected_image_size'):
            img_w, img_h = self.import_panel._selected_image_size
        
        # If no image selected, use default ratio 4:3
        if img_w == 0 or img_h == 0:
            img_w, img_h = 4, 3
        
        try:
            height_val = int(self.height_var.get())
            if height_val > 0:
                # Calculate width maintaining aspect ratio
                ratio = img_w / img_h
                width_val = int(height_val * ratio)
                self.width_var.set(str(width_val))
        except ValueError:
            pass

    def _save_config(self):
        """Save config to config.json"""
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            
            if width <= 0 or height <= 0:
                messagebox.showwarning("Lỗi", "Kích thước phải lớn hơn 0")
                return
            
            # Save to config manager
            self.cm.set("import", "width", width)
            self.cm.set("import", "height", height)
            self.cm.set("import", "auto_calculate", self.auto_calc_var.get())
            self.cm.set("import", "original_folder", self.original_var.get())
            self.cm.set("import", "resized_folder", self.resized_var.get())
            self.cm.save()
            
            messagebox.showinfo("Thành công", f"Đã lưu cấu hình:\nWidth: {width}\nHeight: {height}")
        except ValueError:
            messagebox.showwarning("Lỗi", "Vui lòng nhập số hợp lệ")

    def get_folders(self):
        """Get folder paths"""
        return self.original_var.get(), self.resized_var.get()

    def _export_config(self):
        """Export config to JSON file"""
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            
            config_data = {
                "import": {
                    "width": width,
                    "height": height,
                    "auto_calculate": self.auto_calc_var.get()
                }
            }
            
            file_path = filedialog.asksaveasfilename(
                title="Export cấu hình",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile="photofit_import_config.json"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Thành công", f"Đã export cấu hình ra:\n{file_path}")
        except ValueError:
            messagebox.showwarning("Lỗi", "Vui lòng nhập số hợp lệ")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể export: {str(e)}")

    def _import_config(self):
        """Import config from JSON file"""
        try:
            file_path = filedialog.askopenfilename(
                title="Import cấu hình",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            if "import" in config_data:
                import_config = config_data["import"]
                
                if "width" in import_config:
                    self.width_var.set(str(import_config["width"]))
                
                if "height" in import_config:
                    self.height_var.set(str(import_config["height"]))
                
                if "auto_calculate" in import_config:
                    self.auto_calc_var.set(import_config["auto_calculate"])
                
                messagebox.showinfo("Thành công", "Đã import cấu hình!")
            else:
                messagebox.showwarning("Lỗi", "File cấu hình không hợp lệ")
        except json.JSONDecodeError:
            messagebox.showerror("Lỗi", "File JSON không hợp lệ")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể import: {str(e)}")

    def get_size(self):
        """Get current size settings"""
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            return width, height
        except:
            return 800, 600

    def get_auto_calculate(self):
        """Get auto calculate setting"""
        return self.auto_calc_var.get()

    def _select_original_folder(self):
        """Select original folder path"""
        folder = filedialog.askdirectory(title="Chọn thư mục lưu ảnh gốc")
        if folder:
            self.original_var.set(folder)

    def _select_resized_folder(self):
        """Select resized folder path"""
        folder = filedialog.askdirectory(title="Chọn thư mục lưu ảnh đã resize")
        if folder:
            self.resized_var.set(folder)
