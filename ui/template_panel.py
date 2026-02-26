"""Template panel UI for PhotoFit Studio.

Template selection and management interface.
"""

import customtkinter as ctk
from tkinter import messagebox
from src.template_manager import TemplateManager
from src.config_manager import ConfigManager

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

FONT = "Segoe UI"


class TemplatePanel(ctk.CTkFrame):
    """Template management panel UI."""

    def __init__(self, master, config_manager: ConfigManager, **kwargs):
        super().__init__(master, **kwargs)
        self.cm = config_manager
        self.template_manager = TemplateManager()
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Header
        header = ctk.CTkFrame(self, fg_color="transparent", height=48)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 8))
        ctk.CTkLabel(
            header, text="📋 Quản lý Template",
            font=(FONT, 16, "bold"), text_color=C_TEXT
        ).pack(side="left")

        # Template list container
        list_container = ctk.CTkFrame(self, fg_color=C_CARD, corner_radius=10, border_width=1, border_color=C_BORDER)
        list_container.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 12))
        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(1, weight=1)

        # Title
        ctk.CTkLabel(
            list_container, text="Chọn Template:",
            font=(FONT, 12, "bold"), text_color=C_TEXT
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 8))

        # Scrollable frame for templates
        self.template_frame = ctk.CTkScrollableFrame(
            list_container, 
            fg_color="transparent",
            scrollbar_button_color=C_BORDER,
            scrollbar_button_hover_color=C_TEXT_MUTED
        )
        self.template_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.template_frame.columnconfigure(0, weight=1)

        # Action buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent", height=48)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))
        btn_frame.columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            btn_frame, text="💾 Lưu Template",
            fg_color=C_SUCCESS, hover_color="#059669",
            font=(FONT, 11, "bold"), height=36,
            command=self._save_current_as_template
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            btn_frame, text="📥 Import",
            fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
            font=(FONT, 11), height=36,
            command=self._import_template
        ).grid(row=0, column=1, padx=3, sticky="ew")

        ctk.CTkButton(
            btn_frame, text="📤 Export",
            fg_color=C_CARD, border_color=C_BORDER,
            text_color=C_TEXT, font=(FONT, 11), height=36,
            command=self._export_template
        ).grid(row=0, column=2, padx=(6, 0), sticky="ew")

        # Load templates
        self._load_templates()

    def _load_templates(self):
        """Load and display all templates."""
        # Clear existing
        for widget in self.template_frame.winfo_children():
            widget.destroy()

        templates = self.template_manager.list_templates()
        
        if not templates:
            ctk.CTkLabel(
                self.template_frame, text="Chưa có template nào",
                text_color=C_TEXT_MUTED, font=(FONT, 11)
            ).grid(row=0, column=0, sticky="w", padx=8, pady=8)
            return

        # Current template from config
        current_template = self.cm.get("resize", "preset")

        for idx, template in enumerate(templates):
            is_builtin = template.get("type") == "builtin"
            template_type = "🏢" if is_builtin else "📁"
            
            # Template card
            card = ctk.CTkFrame(self.template_frame, fg_color=C_SURFACE, corner_radius=8)
            card.grid(row=idx, column=0, sticky="ew", padx=4, pady=4)
            card.columnconfigure(1, weight=1)

            # Radio button
            var = ctk.StringVar(value=template["id"])
            rb = ctk.CTkRadioButton(
                card, text="", variable=var, value=template["id"],
                font=(FONT, 11), 
                fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
                border_color=C_BORDER,
                command=lambda t=template["id"]: self._on_template_selected(t)
            )
            rb.grid(row=0, column=0, padx=8, pady=8)

            # Template info
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=8)
            info_frame.columnconfigure(0, weight=1)

            ctk.CTkLabel(
                info_frame, 
                text=f"{template_type} {template['name']}",
                font=(FONT, 12, "bold"), text_color=C_TEXT,
                anchor="w"
            ).grid(row=0, column=0, sticky="w")

            ctk.CTkLabel(
                info_frame,
                text=template.get("description", ""),
                font=(FONT, 10), text_color=C_TEXT_MUTED,
                anchor="w"
            ).grid(row=1, column=0, sticky="w")

            # Delete button for custom templates
            if not is_builtin:
                del_btn = ctk.CTkButton(
                    card, text="🗑️", width=32, height=32,
                    fg_color="transparent", hover_color=C_DANGER,
                    font=(FONT, 12),
                    command=lambda t=template["id"]: self._delete_template(t)
                )
                del_btn.grid(row=0, column=2, padx=8)

    def _on_template_selected(self, template_id: str):
        """Handle template selection."""
        # Apply template to config
        template_config = self.template_manager.load_template(template_id)
        if template_config:
            # Update config manager
            for key, value in template_config.items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        self.cm.set(key, subkey, subvalue)
            
            messagebox.showinfo("Thành công", f"Đã áp dụng template: {template_id}")

    def _save_current_as_template(self):
        """Save current config as a new template."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Lưu Template")
        dialog.geometry("400x250")
        dialog.configure(fg_color=C_SURFACE)
        dialog.transient(self)
        dialog.grab_set()

        # Center
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 200
        y = (dialog.winfo_screenheight() // 2) - 125
        dialog.geometry(f"400x250+{x}+{y}")

        ctk.CTkLabel(
            dialog, text="Lưu cấu hình hiện tại thành Template",
            font=(FONT, 14, "bold"), text_color=C_TEXT
        ).pack(pady=(20, 16))

        # Name input
        ctk.CTkLabel(dialog, text="Tên Template:", text_color=C_TEXT_DIM).pack(anchor="w", padx=24)
        name_var = ctk.StringVar()
        ctk.CTkEntry(
            dialog, textvariable=name_var, width=350, height=36,
            fg_color=C_CARD, border_color=C_BORDER, text_color=C_TEXT
        ).pack(pady=(4, 12), padx=24)

        # Description input
        ctk.CTkLabel(dialog, text="Mô tả:", text_color=C_TEXT_DIM).pack(anchor="w", padx=24)
        desc_var = ctk.StringVar()
        ctk.CTkEntry(
            dialog, textvariable=desc_var, width=350, height=36,
            fg_color=C_CARD, border_color=C_BORDER, text_color=C_TEXT
        ).pack(pady=(4, 16), padx=24)

        # Buttons
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=(0, 16))

        def save():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("Cảnh báo", "Vui lòng nhập tên template!")
                return
            
            self.template_manager.save_template(name, self.cm.config, desc_var.get())
            dialog.destroy()
            self._load_templates()
            messagebox.showinfo("Thành công", f"Đã lưu template: {name}")

        ctk.CTkButton(
            btn_frame, text="Lưu", width=100, height=36,
            fg_color=C_SUCCESS, hover_color="#059669",
            font=(FONT, 11, "bold"), command=save
        ).pack(side="left", padx=8)

        ctk.CTkButton(
            btn_frame, text="Hủy", width=100, height=36,
            fg_color=C_CARD, border_color=C_BORDER,
            text_color=C_TEXT, command=dialog.destroy
        ).pack(side="left", padx=8)

    def _import_template(self):
        """Import template from file."""
        from tkinter import filedialog
        
        filepath = filedialog.askopenfilename(
            title="Import Template",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filepath:
            result = self.template_manager.import_template(filepath)
            if result:
                self._load_templates()
                messagebox.showinfo("Thành công", "Đã import template!")
            else:
                messagebox.showerror("Lỗi", "Không thể import template!")

    def _export_template(self):
        """Export selected template to file."""
        from tkinter import filedialog
        
        templates = self.template_manager.list_templates()
        if not templates:
            messagebox.showwarning("Cảnh báo", "Không có template nào để export!")
            return
        
        # Show template selection dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Export Template")
        dialog.geometry("350x400")
        dialog.configure(fg_color=C_SURFACE)
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog, text="Chọn Template để Export:",
            font=(FONT, 14, "bold"), text_color=C_TEXT
        ).pack(pady=16)

        var = ctk.StringVar()

        for t in templates:
            rb = ctk.CTkRadioButton(
                dialog, text=f"{t['name']} ({t.get('type', 'custom')})",
                variable=var, value=t["id"],
                font=(FONT, 11), text_color=C_TEXT,
                fg_color=C_ACCENT, border_color=C_BORDER
            ).pack(anchor="w", padx=24, pady=4)

        def do_export():
            tid = var.get()
            if not tid:
                return
            
            filepath = filedialog.asksaveasfilename(
                title="Export Template",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json")],
                initialfile=f"{tid}.json"
            )
            
            if filepath:
                if self.template_manager.export_template(tid, filepath):
                    dialog.destroy()
                    messagebox.showinfo("Thành công", "Đã export template!")
                else:
                    messagebox.showerror("Lỗi", "Không thể export template!")

        ctk.CTkButton(
            dialog, text="Export", width=100, height=36,
            fg_color=C_SUCCESS, hover_color="#059669",
            font=(FONT, 11, "bold"), command=do_export
        ).pack(pady=16)

    def _delete_template(self, template_id: str):
        """Delete a custom template."""
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa template này?"):
            if self.template_manager.delete_template(template_id):
                self._load_templates()
                messagebox.showinfo("Thành công", "Đã xóa template!")
            else:
                messagebox.showerror("Lỗi", "Không thể xóa template!")
