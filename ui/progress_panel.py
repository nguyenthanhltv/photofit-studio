"""Progress bar and status log panel - Modern dark theme design."""

import customtkinter as ctk
from typing import Optional
from src.utils import format_time

# Color palette (shared with main_window)
C_BG = "#0B0F19"
C_SURFACE = "#131825"
C_CARD = "#1A2035"
C_BORDER = "#2A3352"
C_ACCENT = "#3B82F6"
C_SUCCESS = "#10B981"
C_DANGER = "#EF4444"
C_WARNING = "#F59E0B"
C_TEXT = "#E2E8F0"
C_TEXT_DIM = "#94A3B8"
C_TEXT_MUTED = "#64748B"

FONT = "Segoe UI"

class ProgressPanel(ctk.CTkFrame):
    """Displays batch processing progress, ETA, and status log - modern dark theme."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self._build()
        self._total = 0

    def _build(self):
        self.columnconfigure(0, weight=1)

        # ── Header row ──
        header = ctk.CTkFrame(self, fg_color="transparent", height=32)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        header.columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="Progress", font=(FONT, 13, "bold"),
                     text_color=C_TEXT).grid(row=0, column=0, sticky="w")
        self.pct_label = ctk.CTkLabel(header, text="0 %", font=(FONT, 12, "bold"),
                                       text_color=C_ACCENT)
        self.pct_label.grid(row=0, column=1, sticky="e")

        # ── Progress bar ──
        self.progress_bar = ctk.CTkProgressBar(
            self, height=10, corner_radius=5,
            fg_color=C_SURFACE, progress_color=C_ACCENT,
        )
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 6))
        self.progress_bar.set(0)

        # ── Stats row ──
        stats = ctk.CTkFrame(self, fg_color="transparent")
        stats.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 2))
        stats.columnconfigure(1, weight=1)

        self.count_label = ctk.CTkLabel(stats, text="0 / 0", font=(FONT, 10),
                                         text_color=C_TEXT_DIM)
        self.count_label.grid(row=0, column=0, sticky="w")

        self.status_label = ctk.CTkLabel(stats, text="Sẵn sàng", font=(FONT, 10),
                                          text_color=C_TEXT_MUTED)
        self.status_label.grid(row=0, column=1, sticky="w", padx=12)

        self.eta_label = ctk.CTkLabel(stats, text="ETA: --", font=(FONT, 10),
                                       text_color=C_TEXT_MUTED)
        self.eta_label.grid(row=0, column=2, sticky="e")

        # ── Log textbox ──
        self.log_box = ctk.CTkTextbox(
            self, height=90, font=("Consolas", 10),
            fg_color=C_SURFACE, text_color=C_TEXT_DIM,
            border_width=0, corner_radius=8,
            state="disabled", wrap="word",
            scrollbar_button_color=C_BORDER,
            scrollbar_button_hover_color=C_TEXT_MUTED,
        )
        self.log_box.grid(row=3, column=0, sticky="nsew", padx=16, pady=(4, 12))
        self.rowconfigure(3, weight=1)

    # ── Public API ──────────────────────────────────────────

    def reset(self, total: int = 0) -> None:
        """Reset progress for a new batch."""
        self._total = total
        self.progress_bar.set(0)
        self.pct_label.configure(text="0 %")
        self.count_label.configure(text=f"0 / {total}")
        self.eta_label.configure(text="ETA: --")
        self.status_label.configure(
            text="Đang xử lý..." if total > 0 else "Sẵn sàng",
            text_color=C_WARNING if total > 0 else C_TEXT_MUTED,
        )
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def update_progress(self, current: int, total: int, elapsed: float,
                        last_file: Optional[str] = None) -> None:
        """Update progress display."""
        self._total = total
        pct = current / total if total > 0 else 0
        self.progress_bar.set(pct)
        self.pct_label.configure(text=f"{int(pct * 100)} %")
        self.count_label.configure(text=f"{current} / {total}")

        # ETA
        if current > 0 and current < total:
            avg = elapsed / current
            remaining = (total - current) * avg
            self.eta_label.configure(text=f"ETA: {format_time(remaining)}")
        elif current >= total:
            self.eta_label.configure(text=f"Done: {format_time(elapsed)}")
        else:
            self.eta_label.configure(text="ETA: --")

        if last_file:
            short = last_file.split("\\")[-1].split("/")[-1]
            self.status_label.configure(text=f"Processing: {short}", text_color=C_WARNING)

    def log(self, message: str) -> None:
        """Append a message to the log."""
        self.log_box.configure(state="normal")
        self.log_box.insert("end", message + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def set_complete(self, success: int, total: int, elapsed: float) -> None:
        """Show completion status."""
        failed = total - success
        msg = f"✓ {success}/{total} done"
        if failed > 0:
            msg += f"  ·  {failed} errors"
        msg += f"  ·  {format_time(elapsed)}"
        self.status_label.configure(text=msg, text_color=C_SUCCESS)
        self.progress_bar.configure(progress_color=C_SUCCESS)
        self.progress_bar.set(1.0)
        self.pct_label.configure(text="100 %", text_color=C_SUCCESS)
        self.log(f"\n═══ {msg} ═══")

    def set_cancelled(self, completed: int, total: int) -> None:
        """Show cancellation status."""
        msg = f"Cancelled: {completed}/{total} processed"
        self.status_label.configure(text=msg, text_color=C_DANGER)
        self.progress_bar.configure(progress_color=C_DANGER)
        self.log(f"\n═══ {msg} ═══")