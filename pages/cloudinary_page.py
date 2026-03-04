import os
import json
import base64
from pathlib import Path
from urllib import request, error

import customtkinter as ctk
from tkinter import messagebox


PRIMARY_RED = "#b11226"
GREEN = "#1f8a3b"
GREEN_HOVER = "#196f2f"

BLACK = "#000000"
CARD = "#111111"
CARD2 = "#0b0b0b"

TEXT_PRIMARY = "#EDEDED"
TEXT_MUTED = "#B8B8B8"


def _appdata_dir() -> Path:
    base = os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    d = Path(base) / "GNX_PRODUCTION"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _settings_path() -> Path:
    return _appdata_dir() / "cloudinary_settings.json"


def _basic_auth(api_key: str, api_secret: str) -> str:
    token = base64.b64encode(f"{api_key}:{api_secret}".encode("utf-8")).decode("utf-8")
    return f"Basic {token}"


def _cloudinary_test_usage(cloud_name: str, api_key: str, api_secret: str) -> bool:
    """
    Test paling sederhana: GET /usage (Admin API).
    Jika 200 -> OK.
    """
    url = f"https://api.cloudinary.com/v1_1/{cloud_name}/usage"
    req = request.Request(
        url=url,
        method="GET",
        headers={
            "Authorization": _basic_auth(api_key, api_secret),
            "Accept": "application/json",
        },
    )
    try:
        with request.urlopen(req, timeout=20) as resp:
            return resp.status == 200
    except error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        raise RuntimeError(f"Cloudinary HTTP {getattr(e, 'code', None)}: {body[:400]}")
    except Exception as e:
        raise RuntimeError(str(e))


class CloudinaryPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BLACK)
        self.engine = master.master.master.engine

        self.grid_columnconfigure(0, weight=1)

        self._build_ui()
        self._load_saved()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=BLACK)
        header.grid(row=0, column=0, sticky="ew", padx=40, pady=(30, 10))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Cloudinary Connection",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=28, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="Isi Cloud Name (User ID), API Key, API Secret → Test → Save & Connect.",
            text_color=TEXT_MUTED,
            wraplength=900,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        card = ctk.CTkFrame(self, fg_color=CARD, corner_radius=16)
        card.grid(row=1, column=0, sticky="ew", padx=40, pady=(10, 14))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="CREDENTIALS",
            text_color=PRIMARY_RED,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 8))

        self.cloud_name_entry = ctk.CTkEntry(
            card,
            placeholder_text="Cloud Name / User ID (contoh: dlcfc8xjy)",
            text_color=TEXT_PRIMARY,
        )
        self.cloud_name_entry.grid(row=1, column=0, sticky="ew", padx=18, pady=6)

        self.api_key_entry = ctk.CTkEntry(
            card,
            placeholder_text="API Key",
            text_color=TEXT_PRIMARY,
        )
        self.api_key_entry.grid(row=2, column=0, sticky="ew", padx=18, pady=6)

        self.api_secret_entry = ctk.CTkEntry(
            card,
            placeholder_text="API Secret",
            text_color=TEXT_PRIMARY,
            show="*",
        )
        self.api_secret_entry.grid(row=3, column=0, sticky="ew", padx=18, pady=6)

        self.status_label = ctk.CTkLabel(card, text="", text_color=TEXT_MUTED)
        self.status_label.grid(row=4, column=0, sticky="w", padx=18, pady=(6, 0))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.grid(row=5, column=0, sticky="ew", padx=18, pady=(10, 14))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        self.test_btn = ctk.CTkButton(
            btn_row,
            text="Test Connection",
            fg_color="#222222",
            hover_color="#333333",
            text_color=TEXT_PRIMARY,
            command=self._test_connection,
        )
        self.test_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.save_btn = ctk.CTkButton(
            btn_row,
            text="Save & Connect",
            fg_color=PRIMARY_RED,
            hover_color="#7a0d1a",
            text_color=TEXT_PRIMARY,
            command=self._save_and_connect,
        )
        self.save_btn.grid(row=0, column=1, padx=(10, 0), sticky="ew")

        info = ctk.CTkFrame(self, fg_color=CARD2, corner_radius=16)
        info.grid(row=2, column=0, sticky="ew", padx=40, pady=(0, 30))
        info.grid_columnconfigure(0, weight=1)

        box = ctk.CTkTextbox(info, fg_color="#060606", text_color=TEXT_PRIMARY, height=140)
        box.grid(row=0, column=0, sticky="ew", padx=18, pady=18)
        box.insert(
            "1.0",
            "Setelah Connected:\n"
            "- Upload video dari Dashboard akan jalan ke Cloudinary.\n"
            "- Kalau gagal, cek Cloud Name / API Key / API Secret.\n"
        )

    def _load_saved(self):
        p = _settings_path()
        if not p.exists():
            return
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if data.get("cloud_name"):
                self.cloud_name_entry.insert(0, data["cloud_name"])
            if data.get("api_key"):
                self.api_key_entry.insert(0, data["api_key"])
            if data.get("api_secret"):
                self.api_secret_entry.insert(0, data["api_secret"])
        except Exception:
            pass

    def _collect(self):
        cloud = self.cloud_name_entry.get().strip()
        key = self.api_key_entry.get().strip()
        secret = self.api_secret_entry.get().strip()
        if not cloud or not key or not secret:
            raise ValueError("Cloud Name, API Key, dan API Secret wajib diisi.")
        return cloud, key, secret

    def _apply_env(self, cloud: str, key: str, secret: str):
        os.environ["CLOUDINARY_CLOUD_NAME"] = cloud
        os.environ["CLOUDINARY_API_KEY"] = key
        os.environ["CLOUDINARY_API_SECRET"] = secret

        # Re-init cloudinary service jika ada
        try:
            from core.services.cloudinary_service import CloudinaryService
            self.engine.cloudinary_service = CloudinaryService()
        except Exception:
            pass

    def _test_connection(self):
        try:
            cloud, key, secret = self._collect()
            ok = _cloudinary_test_usage(cloud, key, secret)
            if ok:
                self.status_label.configure(text="✅ Cloudinary Connected")
                self.save_btn.configure(fg_color=GREEN, hover_color=GREEN_HOVER)
            else:
                self.status_label.configure(text="❌ Cloudinary Test Failed")
        except Exception as e:
            messagebox.showerror("Cloudinary Error", str(e))

    def _save_and_connect(self):
        try:
            cloud, key, secret = self._collect()

            data = {"cloud_name": cloud, "api_key": key, "api_secret": secret}
            _settings_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

            self._apply_env(cloud, key, secret)

            # auto test setelah save
            ok = _cloudinary_test_usage(cloud, key, secret)
            if ok:
                self.status_label.configure(text="✅ Saved & Connected")
                self.save_btn.configure(fg_color=GREEN, hover_color=GREEN_HOVER)
                messagebox.showinfo("Cloudinary", "Saved & Connected.")
            else:
                self.status_label.configure(text="⚠ Saved, tapi test gagal")
                messagebox.showwarning("Cloudinary", "Saved, tapi test gagal. Cek credential.")

        except Exception as e:
            messagebox.showerror("Cloudinary Error", str(e))