import shutil
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.theme_constants import (
    PRIMARY_RED, DEEP_RED, BLACK, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, TEXT_SOFT,
    BADGE_DARK, BADGE_SUCCESS, BTN_DARK, BTN_DARK_HOVER,
)
from core.ui_helpers import make_card, make_stat_card
from core.license_manager import (
    load_license_capabilities,
    load_effective_capabilities,
    get_license_path,
)

def _safe_open_path(p: str):
    try:
        if not p:
            return
        import os
        if os.name == "nt":
            os.startfile(p)
        else:
            import subprocess
            subprocess.Popen(["xdg-open", p])
    except Exception as e:
        messagebox.showerror("Open Error", str(e))

class LicensePage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BLACK)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()
        self._refresh()

    def _build_ui(self):
        outer = ctk.CTkScrollableFrame(self, fg_color=BLACK)
        outer.grid(row=0, column=0, sticky="nsew", padx=30, pady=22)
        outer.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="License Management",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=30, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="View or import your active GNX license.",
            text_color=TEXT_MUTED,
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.plan_badge = ctk.CTkLabel(
            header, text="PLAN: -", text_color=TEXT_PRIMARY,
            fg_color=BADGE_DARK, corner_radius=12, padx=14, pady=7,
        )
        self.plan_badge.grid(row=0, column=1, rowspan=2, sticky="e")

        stats = ctk.CTkFrame(outer, fg_color="transparent")
        stats.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        for i in range(4):
            stats.grid_columnconfigure(i, weight=1)

        stat1, self.plan_value = make_stat_card(stats, "Current Plan")
        stat1.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        stat2, self.accounts_value = make_stat_card(stats, "Max Accounts")
        stat2.grid(row=0, column=1, sticky="ew", padx=8)

        stat3, self.daily_value = make_stat_card(stats, "Daily Video Limit")
        stat3.grid(row=0, column=2, sticky="ew", padx=8)

        stat4, self.quality_value = make_stat_card(stats, "Max Resolution")
        stat4.grid(row=0, column=3, sticky="ew", padx=(8, 0))

        info_card = make_card(
            outer,
            "Current License",
            "This app runs on Business mode by default for Admins when no license is found.",
        )
        info_card.grid(row=2, column=0, sticky="ew", pady=10)

        self.license_path_label = ctk.CTkLabel(
            info_card, text="License Path: -", text_color=TEXT_SOFT, wraplength=760, justify="left",
        )
        self.license_path_label.pack(anchor="w", padx=22, pady=(0, 8))

        self.summary_label = ctk.CTkLabel(
            info_card, text="Summary: -", text_color=TEXT_MUTED, wraplength=760, justify="left",
        )
        self.summary_label.pack(anchor="w", padx=22, pady=(0, 12))

        btn_row = ctk.CTkFrame(info_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=22, pady=(0, 16))
        btn_row.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            btn_row, text="Refresh", fg_color=BTN_DARK, hover_color=BTN_DARK_HOVER,
            text_color=TEXT_PRIMARY, height=42, command=self._refresh,
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            btn_row, text="Open License Folder", fg_color=BTN_DARK, hover_color=BTN_DARK_HOVER,
            text_color=TEXT_PRIMARY, height=42, command=self._open_license_folder,
        ).grid(row=0, column=1, padx=8, sticky="ew")

        ctk.CTkButton(
            btn_row, text="Import .json License", fg_color=PRIMARY_RED, hover_color=DEEP_RED,
            text_color=TEXT_PRIMARY, height=42, command=self._import_license,
        ).grid(row=0, column=2, padx=(8, 0), sticky="ew")

        viewer_card = make_card(outer, "License Data Preview", "Raw data inside the license file.")
        viewer_card.grid(row=3, column=0, sticky="ew", pady=10)

        self.viewer = ctk.CTkTextbox(
            viewer_card, height=280, fg_color="#060606", text_color=TEXT_PRIMARY,
            border_width=1, border_color=BORDER,
        )
        self.viewer.pack(fill="x", padx=22, pady=(0, 16))

    def _refresh(self):
        caps = load_effective_capabilities()

        effective_plan = str(caps.get("effective_plan", "BASIC")).upper()
        quality = caps.get("max_resolution", "1080p")
        path = Path(get_license_path())

        self.plan_badge.configure(
            text=f"PLAN: {effective_plan}",
            fg_color=BADGE_SUCCESS if effective_plan != "BASIC" else BADGE_DARK,
        )
        self.plan_value.configure(text=effective_plan)
        
        self.accounts_value.configure(text=str(caps.get("max_social_accounts", 2)))
        self.daily_value.configure(text=str(caps.get("daily_video_limit", 2)))
        self.quality_value.configure(text=quality)

        self.license_path_label.configure(text=f"File: {path}")
        self.summary_label.configure(
            text=(f"Effective Runtime Plan: {effective_plan} | Multi-PC Allowed: {str(not caps.get('pc_lock', True))}")
        )

        try:
            if path.exists():
                self.viewer.delete("1.0", "end")
                self.viewer.insert("1.0", path.read_text(encoding="utf-8"))
            else:
                self.viewer.delete("1.0", "end")
                self.viewer.insert("1.0", "No license file found. Running in default Admin mode (BUSINESS).")
        except Exception as e:
            self.viewer.delete("1.0", "end")
            self.viewer.insert("1.0", f"Failed to read license: {e}")

    def _open_license_folder(self):
        path = Path(get_license_path()).parent
        _safe_open_path(str(path))

    def _import_license(self):
        src = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not src:
            return

        try:
            dst = Path(get_license_path())
            shutil.copyfile(src, dst)
            self._refresh()
            messagebox.showinfo("License", "License imported successfully.")
        except Exception as e:
            messagebox.showerror("Import Error", str(e))