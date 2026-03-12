import json
import os
import webbrowser
from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk

from core.theme_constants import (
    PRIMARY_RED,
    GREEN,
    BLACK,
    BORDER,
    TEXT_PRIMARY,
    TEXT_MUTED,
    TEXT_SOFT,
    BADGE_DARK,
    BADGE_SUCCESS,
    BADGE_ERROR,
    BTN_DARK,
    BTN_DARK_HOVER,
)
from core.ui_helpers import make_card


class CloudinaryPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BLACK)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()
        self.load_saved_config()

    # ---------------------------------------------------------
    # Paths / config
    # ---------------------------------------------------------

    def _appdata_dir(self) -> Path:
        base = os.getenv("LOCALAPPDATA", "").strip()
        if not base:
            base = str(Path.home() / "AppData" / "Local")
        p = Path(base) / "GNX_PRODUCTION"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _config_path(self) -> Path:
        return self._appdata_dir() / "cloudinary.json"

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def _build_ui(self):
        outer = ctk.CTkScrollableFrame(self, fg_color=BLACK)
        outer.grid(row=0, column=0, sticky="nsew", padx=30, pady=22)
        outer.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Cloudinary Configuration",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="Connect your own Cloudinary account to upload and manage your generated videos.",
            text_color=TEXT_MUTED,
            wraplength=900,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.status_badge = ctk.CTkLabel(
            header,
            text="NOT SAVED",
            text_color=TEXT_PRIMARY,
            fg_color=BADGE_DARK,
            corner_radius=12,
            padx=14,
            pady=7,
        )
        self.status_badge.grid(row=0, column=1, rowspan=2, sticky="e")

        card = make_card(
            outer,
            "Connection Settings",
            "Fill your own Cloudinary account settings. Upload Preset must be the real Cloudinary upload preset name, not API Key.",
        )
        card.grid(row=1, column=0, sticky="ew", pady=10)

        self.cloud_name_entry = ctk.CTkEntry(
            card,
            placeholder_text="Cloud Name",
            text_color=TEXT_PRIMARY,
            height=40,
        )
        self.cloud_name_entry.pack(fill="x", padx=22, pady=(0, 10))

        self.upload_preset_entry = ctk.CTkEntry(
            card,
            placeholder_text="Upload Preset (example: gnx_unsigned_upload)",
            text_color=TEXT_PRIMARY,
            height=40,
        )
        self.upload_preset_entry.pack(fill="x", padx=22, pady=(0, 10))

        self.folder_entry = ctk.CTkEntry(
            card,
            placeholder_text="Folder (optional, example: gnx_uploads)",
            text_color=TEXT_PRIMARY,
            height=40,
        )
        self.folder_entry.pack(fill="x", padx=22, pady=(0, 10))

        self.secure_delivery_var = ctk.BooleanVar(value=True)
        self.secure_delivery_cb = ctk.CTkCheckBox(
            card,
            text="Prefer secure delivery URL",
            variable=self.secure_delivery_var,
            text_color=TEXT_PRIMARY,
        )
        self.secure_delivery_cb.pack(anchor="w", padx=22, pady=(0, 8))

        ctk.CTkLabel(
            card,
            text=(
                "Tips:\n"
                "- Cloud Name is your Cloudinary cloud name\n"
                "- Upload Preset is the preset name from Cloudinary Upload Settings\n"
                "- Use an unsigned upload preset for easiest setup\n"
                "- Folder is optional and can be something simple like gnx_uploads"
            ),
            text_color=TEXT_MUTED,
            justify="left",
            anchor="w",
            wraplength=860,
        ).pack(fill="x", padx=22, pady=(0, 14))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=22, pady=(0, 16))
        btn_row.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        ctk.CTkButton(
            btn_row,
            text="Save Config",
            fg_color=PRIMARY_RED,
            hover_color="#7a0d1a",
            text_color=TEXT_PRIMARY,
            height=42,
            command=self.save_config,
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            btn_row,
            text="Reload",
            fg_color=BTN_DARK,
            hover_color=BTN_DARK_HOVER,
            text_color=TEXT_PRIMARY,
            height=42,
            command=self.load_saved_config,
        ).grid(row=0, column=1, padx=8, sticky="ew")

        ctk.CTkButton(
            btn_row,
            text="Open Config Folder",
            fg_color=BTN_DARK,
            hover_color=BTN_DARK_HOVER,
            text_color=TEXT_PRIMARY,
            height=42,
            command=self.open_config_folder,
        ).grid(row=0, column=2, padx=8, sticky="ew")

        ctk.CTkButton(
            btn_row,
            text="Open Dashboard",
            fg_color=BTN_DARK,
            hover_color=BTN_DARK_HOVER,
            text_color=TEXT_PRIMARY,
            height=42,
            command=self.open_cloudinary_dashboard,
        ).grid(row=0, column=3, padx=8, sticky="ew")

        ctk.CTkButton(
            btn_row,
            text="Open Media Library",
            fg_color=GREEN,
            hover_color="#1a6b31",
            text_color=TEXT_PRIMARY,
            height=42,
            command=self.open_media_library,
        ).grid(row=0, column=4, padx=(8, 0), sticky="ew")

        info_card = make_card(
            outer,
            "Saved Location",
            "Your personal Cloudinary config is stored per Windows user in AppData.",
        )
        info_card.grid(row=2, column=0, sticky="ew", pady=10)

        self.path_label = ctk.CTkLabel(
            info_card,
            text=f"Config Path: {self._config_path()}",
            text_color=TEXT_SOFT,
            wraplength=920,
            justify="left",
        )
        self.path_label.pack(anchor="w", padx=22, pady=(0, 8))

        self.summary_label = ctk.CTkLabel(
            info_card,
            text="Summary: -",
            text_color=TEXT_MUTED,
            wraplength=920,
            justify="left",
        )
        self.summary_label.pack(anchor="w", padx=22, pady=(0, 16))

        preview_card = make_card(
            outer,
            "Config Preview",
            "Stored JSON preview.",
        )
        preview_card.grid(row=3, column=0, sticky="ew", pady=10)

        self.preview_box = ctk.CTkTextbox(
            preview_card,
            height=240,
            fg_color="#060606",
            text_color=TEXT_PRIMARY,
            border_width=1,
            border_color=BORDER,
        )
        self.preview_box.pack(fill="x", padx=22, pady=(0, 16))

    # ---------------------------------------------------------
    # Runtime env
    # ---------------------------------------------------------

    def _apply_runtime_env(self, data: dict):
        os.environ["CLOUDINARY_CLOUD_NAME"] = str(data.get("cloud_name", "")).strip()
        os.environ["CLOUDINARY_UPLOAD_PRESET"] = str(data.get("upload_preset", "")).strip()

        folder = str(data.get("folder", "")).strip()
        if folder:
            os.environ["CLOUDINARY_FOLDER"] = folder
        else:
            os.environ.pop("CLOUDINARY_FOLDER", None)

        os.environ["CLOUDINARY_SECURE_DELIVERY"] = "1" if bool(data.get("secure_delivery", True)) else "0"

    # ---------------------------------------------------------
    # Actions
    # ---------------------------------------------------------

    def save_config(self):
        cloud_name = self.cloud_name_entry.get().strip()
        upload_preset = self.upload_preset_entry.get().strip()
        folder = self.folder_entry.get().strip()
        secure_delivery = bool(self.secure_delivery_var.get())

        if not cloud_name or not upload_preset:
            self.status_badge.configure(text="ERROR", fg_color=BADGE_ERROR)
            messagebox.showerror(
                "Cloudinary",
                "Cloud Name and Upload Preset are required.",
            )
            return

        data = {
            "cloud_name": cloud_name,
            "upload_preset": upload_preset,
            "folder": folder,
            "secure_delivery": secure_delivery,
        }

        try:
            self._config_path().write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            self._apply_runtime_env(data)
            self.status_badge.configure(text="SAVED", fg_color=BADGE_SUCCESS)
            self._refresh_preview(data)
            messagebox.showinfo("Cloudinary", "Cloudinary config saved successfully.")
        except Exception as e:
            self.status_badge.configure(text="ERROR", fg_color=BADGE_ERROR)
            messagebox.showerror("Cloudinary Error", str(e))

    def load_saved_config(self):
        path = self._config_path()

        if not path.exists():
            self.status_badge.configure(text="NOT SAVED", fg_color=BADGE_DARK)
            self.path_label.configure(text=f"Config Path: {path}")
            self.summary_label.configure(text="Summary: No saved Cloudinary config found.")
            self.preview_box.delete("1.0", "end")
            self.preview_box.insert("1.0", "{}")
            return

        try:
            data = json.loads(path.read_text(encoding="utf-8"))

            self.cloud_name_entry.delete(0, "end")
            self.cloud_name_entry.insert(0, str(data.get("cloud_name", "")))

            self.upload_preset_entry.delete(0, "end")
            self.upload_preset_entry.insert(0, str(data.get("upload_preset", "")))

            self.folder_entry.delete(0, "end")
            self.folder_entry.insert(0, str(data.get("folder", "")))

            self.secure_delivery_var.set(bool(data.get("secure_delivery", True)))

            self._apply_runtime_env(data)
            self.status_badge.configure(text="LOADED", fg_color=GREEN)
            self._refresh_preview(data)

        except Exception as e:
            self.status_badge.configure(text="ERROR", fg_color=BADGE_ERROR)
            self.summary_label.configure(text=f"Summary: Failed to read config: {e}")
            self.preview_box.delete("1.0", "end")
            self.preview_box.insert("1.0", f"Failed to read config: {e}")

    def _refresh_preview(self, data: dict):
        self.path_label.configure(text=f"Config Path: {self._config_path()}")

        cloud_name = str(data.get("cloud_name", "")).strip()
        upload_preset = str(data.get("upload_preset", "")).strip()
        folder = str(data.get("folder", "")).strip() or "-"
        secure_delivery = bool(data.get("secure_delivery", True))

        self.summary_label.configure(
            text=(
                f"Summary: cloud_name={cloud_name} | "
                f"upload_preset={upload_preset} | "
                f"folder={folder} | "
                f"secure_delivery={secure_delivery}"
            )
        )

        self.preview_box.delete("1.0", "end")
        self.preview_box.insert(
            "1.0",
            json.dumps(data, ensure_ascii=False, indent=2),
        )

    def open_config_folder(self):
        try:
            path = self._appdata_dir().resolve()
            if os.name == "nt":
                os.startfile(str(path))
            else:
                import subprocess
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as e:
            messagebox.showerror("Open Folder Error", str(e))

    def open_cloudinary_dashboard(self):
        try:
            cloud_name = self.cloud_name_entry.get().strip()
            if cloud_name:
                webbrowser.open(f"https://console.cloudinary.com/console/{cloud_name}")
            else:
                webbrowser.open("https://console.cloudinary.com/")
        except Exception:
            pass

    def open_media_library(self):
        try:
            cloud_name = self.cloud_name_entry.get().strip()
            if cloud_name:
                webbrowser.open(f"https://console.cloudinary.com/console/{cloud_name}/media_library/home")
            else:
                webbrowser.open("https://console.cloudinary.com/")
        except Exception:
            pass