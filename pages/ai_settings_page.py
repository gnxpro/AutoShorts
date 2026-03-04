import os
import json
from pathlib import Path
from urllib import request, error

import customtkinter as ctk
from tkinter import messagebox


PRIMARY_RED = "#b11226"
GREEN = "#1f8a3b"
GREEN_HOVER = "#196f2f"

BLACK = "#000000"
CARD = "#111111"

TEXT_PRIMARY = "#EDEDED"
TEXT_MUTED = "#B8B8B8"


def _appdata_dir() -> Path:
    base = os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    d = Path(base) / "GNX_PRODUCTION"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _settings_path() -> Path:
    return _appdata_dir() / "openai_settings.json"


def _openai_test(api_key: str) -> bool:
    url = "https://api.openai.com/v1/models"
    req = request.Request(
        url=url,
        method="GET",
        headers={
            "Authorization": f"Bearer {api_key}",
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
        raise RuntimeError(f"OpenAI HTTP {getattr(e, 'code', None)}: {body[:400]}")
    except Exception as e:
        raise RuntimeError(str(e))


class AISettingsPage(ctk.CTkFrame):
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
            text="AI Login (OpenAI)",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=28, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="Masukkan OpenAI API Key → Test → Save & Apply.",
            text_color=TEXT_MUTED,
            wraplength=900,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        card = ctk.CTkFrame(self, fg_color=CARD, corner_radius=16)
        card.grid(row=1, column=0, sticky="ew", padx=40, pady=(10, 30))
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="OPENAI",
            text_color=PRIMARY_RED,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 8))

        self.key_entry = ctk.CTkEntry(
            card,
            placeholder_text="OpenAI API Key (sk-...)",
            text_color=TEXT_PRIMARY,
            show="*",
        )
        self.key_entry.grid(row=1, column=0, sticky="ew", padx=18, pady=6)

        self.status_label = ctk.CTkLabel(card, text="", text_color=TEXT_MUTED)
        self.status_label.grid(row=2, column=0, sticky="w", padx=18, pady=(6, 0))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="ew", padx=18, pady=(10, 14))
        btn_row.grid_columnconfigure((0, 1), weight=1)

        self.test_btn = ctk.CTkButton(
            btn_row,
            text="Test Connection",
            fg_color="#222222",
            hover_color="#333333",
            text_color=TEXT_PRIMARY,
            command=self._test,
        )
        self.test_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.save_btn = ctk.CTkButton(
            btn_row,
            text="Save & Apply",
            fg_color=PRIMARY_RED,
            hover_color="#7a0d1a",
            text_color=TEXT_PRIMARY,
            command=self._save_apply,
        )
        self.save_btn.grid(row=0, column=1, padx=(10, 0), sticky="ew")

    def _load_saved(self):
        p = _settings_path()
        if not p.exists():
            # coba env existing
            k = os.getenv("OPENAI_API_KEY", "").strip()
            if k:
                self.key_entry.insert(0, k)
            return
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            k = (data.get("openai_api_key") or "").strip()
            if k:
                self.key_entry.insert(0, k)
                os.environ["OPENAI_API_KEY"] = k
        except Exception:
            pass

    def _collect(self) -> str:
        k = self.key_entry.get().strip()
        if not k:
            raise ValueError("OpenAI API Key wajib diisi.")
        return k

    def _test(self):
        try:
            k = self._collect()
            ok = _openai_test(k)
            if ok:
                self.status_label.configure(text="✅ OpenAI Connected")
                self.save_btn.configure(fg_color=GREEN, hover_color=GREEN_HOVER)
            else:
                self.status_label.configure(text="❌ OpenAI Test Failed")
        except Exception as e:
            messagebox.showerror("OpenAI Error", str(e))

    def _save_apply(self):
        try:
            k = self._collect()
            _settings_path().write_text(json.dumps({"openai_api_key": k}, ensure_ascii=False, indent=2), encoding="utf-8")

            os.environ["OPENAI_API_KEY"] = k

            # kalau ada modul AI manager yang baca env di runtime, ini cukup.
            self.status_label.configure(text="✅ Saved. (Key applied to runtime)")
            messagebox.showinfo("AI Settings", "Saved & applied.")
        except Exception as e:
            messagebox.showerror("AI Settings Error", str(e))