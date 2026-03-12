import shutil
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.theme_constants import (
    PRIMARY_RED,
    DEEP_RED,
    BLACK,
    BORDER,
    TEXT_PRIMARY,
    TEXT_MUTED,
    TEXT_SOFT,
    BADGE_DARK,
    BADGE_SUCCESS,
    BTN_DARK,
    BTN_DARK_HOVER,
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
            text="Import a signed .gnxlic file to upgrade your plan without reinstalling the application.",
            text_color=TEXT_MUTED,
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.plan_badge = ctk.CTkLabel(
            header,
            text="PLAN: -",
            text_color=TEXT_PRIMARY,
            fg_color=BADGE_DARK,
            corner_radius=12,
            padx=14,
            pady=7,
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

        stat3, self.daily_value = make_stat_card(stats, "Daily Limit")
        stat3.grid(row=0, column=2, sticky="ew", padx=8)

        stat4, self.quality_value = make_stat_card(stats, "Quality")
        stat4.grid(row=0, column=3, sticky="ew", padx=(8, 0))

        info_card = make_card(
            outer,
            "Current License",
            "The installer places a default Basic signed license. Upgrading only requires importing a new .gnxlic file.",
        )
        info_card.grid(row=2, column=0, sticky="ew", pady=10)

        self.license_path_label = ctk.CTkLabel(
            info_card,
            text="License Path: -",
            text_color=TEXT_SOFT,
            wraplength=760,
            justify="left",
        )
        self.license_path_label.pack(anchor="w", padx=22, pady=(0, 8))

        self.summary_label = ctk.CTkLabel(
            info_card,
            text="Summary: -",
            text_color=TEXT_MUTED,
            wraplength=760,
            justify="left",
        )
        self.summary_label.pack(anchor="w", padx=22, pady=(0, 12))

        btn_row = ctk.CTkFrame(info_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=22, pady=(0, 16))
        btn_row.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            btn_row,
            text="Refresh",
            fg_color=BTN_DARK,
            hover_color=BTN_DARK_HOVER,
            text_color=TEXT_PRIMARY,
            height=42,
            command=self._refresh,
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            btn_row,
            text="Open License Folder",
            fg_color=BTN_DARK,
            hover_color=BTN_DARK_HOVER,
            text_color=TEXT_PRIMARY,
            height=42,
            command=self._open_license_folder,
        ).grid(row=0, column=1, padx=8, sticky="ew")

        ctk.CTkButton(
            btn_row,
            text="Import .gnxlic",
            fg_color=PRIMARY_RED,
            hover_color=DEEP_RED,
            text_color=TEXT_PRIMARY,
            height=42,
            command=self._import_license,
        ).grid(row=0, column=2, padx=(8, 0), sticky="ew")

        viewer_card = make_card(
            outer,
            "License Preview",
            "Active signed license file preview.",
        )
        viewer_card.grid(row=3, column=0, sticky="ew", pady=10)

        self.viewer = ctk.CTkTextbox(
            viewer_card,
            height=280,
            fg_color="#060606",
            text_color=TEXT_PRIMARY,
            border_width=1,
            border_color=BORDER,
        )
        self.viewer.pack(fill="x", padx=22, pady=(0, 16))

    def _refresh(self):
        raw_caps = load_license_capabilities()
        caps = load_effective_capabilities()

        licensed_plan = str(raw_caps.get("plan", "BASIC")).upper()
        effective_plan = str(caps.get("effective_plan", licensed_plan)).upper()
        quality = ", ".join(caps.get("quality_options", []))
        path = Path(get_license_path())

        self.plan_badge.configure(
            text=f"PLAN: {effective_plan}",
            fg_color=BADGE_SUCCESS if effective_plan != "BASIC" else BADGE_DARK,
        )
        self.plan_value.configure(text=effective_plan)
        self.accounts_value.configure(
            text="Unlimited" if caps.get("max_social_accounts") is None else str(caps.get("max_social_accounts", 0))
        )
        self.daily_value.configure(
            text="Unlimited" if caps.get("daily_video_limit") is None else str(caps.get("daily_video_limit", 0))
        )
        self.quality_value.configure(text=quality or "-")

        runtime_note = ""
        if effective_plan == "BASIC" and licensed_plan != "BASIC" and not bool(caps.get("binding_valid", True)):
            runtime_note = " | Runtime fallback: Repliz mismatch"
        elif bool(caps.get("blocked_for_social_limit", False)):
            runtime_note = " | Runtime warning: Social account limit exceeded"

        self.license_path_label.configure(text=f"License Path: {path}")
        self.summary_label.configure(
            text=(
                f"License ID={caps.get('license_id', '-')} | "
                f"Licensed Plan={licensed_plan} | "
                f"Runtime={effective_plan}{runtime_note} | "
                f"AI={caps.get('allow_ai')} | "
                f"Schedule={caps.get('allow_schedule')} | "
                f"30Days={caps.get('monthly_video_limit')} | "
                f"Default Quality={caps.get('default_quality')}"
            )
        )

        try:
            self.viewer.delete("1.0", "end")
            self.viewer.insert("1.0", path.read_text(encoding="utf-8"))
        except Exception as e:
            self.viewer.delete("1.0", "end")
            self.viewer.insert("1.0", f"Failed to read license: {e}")

    def _open_license_folder(self):
        path = Path(get_license_path()).parent
        _safe_open_path(str(path))

    def _import_license(self):
        src = filedialog.askopenfilename(
            filetypes=[
                ("GNX License", "*.gnxlic"),
                ("JSON files", "*.json"),
                ("All files", "*.*"),
            ]
        )
        if not src:
            return

        try:
            dst = Path(get_license_path())
            shutil.copyfile(src, dst)
            load_license_capabilities()
            self._refresh()
            messagebox.showinfo(
                "License",
                "License imported successfully. Restart the app if another page has not updated yet."
            )
        except Exception as e:
            messagebox.showerror("Import Error", str(e))