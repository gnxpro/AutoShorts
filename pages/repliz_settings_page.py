import customtkinter as ctk
import requests
from tkinter import messagebox

from core.config_manager import ConfigManager

PRIMARY = "#b11226"
DEEP_RED = "#7a0d1a"

BLACK = "#000000"
CARD_BG = "#101010"
CARD_SOFT = "#151515"
BORDER = "#242424"

TEXT_PRIMARY = "#F2F2F2"
TEXT_MUTED = "#AFAFAF"
TEXT_SOFT = "#DADADA"


class ReplizSettingsPage(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=BLACK)

        self.config = ConfigManager()
        self.repliz_conf = self.config.get_repliz()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()

    def _make_card(self, parent, title, subtitle=None):
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD_BG,
            corner_radius=18,
            border_width=1,
            border_color=BORDER
        )
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=PRIMARY
        ).pack(anchor="w", padx=22, pady=(16, 6))

        if subtitle:
            ctk.CTkLabel(
                card,
                text=subtitle,
                text_color=TEXT_MUTED,
                wraplength=760,
                justify="left",
            ).pack(anchor="w", padx=22, pady=(0, 12))

        return card

    def _build_ui(self):
        outer = ctk.CTkScrollableFrame(self, fg_color=BLACK)
        outer.grid(row=0, column=0, sticky="nsew", padx=30, pady=22)
        outer.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Repliz Integration Settings",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=TEXT_PRIMARY
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="Configure base URL and API keys for Repliz integration.",
            text_color=TEXT_MUTED
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.status_badge = ctk.CTkLabel(
            header,
            text="NOT TESTED",
            text_color=TEXT_PRIMARY,
            fg_color="#1f1f1f",
            corner_radius=12,
            padx=14,
            pady=7,
        )
        self.status_badge.grid(row=0, column=1, rowspan=2, sticky="e")

        card = self._make_card(
            outer,
            "Credentials",
            "Use Test Connection before saving to ensure your API keys are valid."
        )
        card.grid(row=1, column=0, sticky="ew", pady=10)

        ctk.CTkLabel(card, text="API Base URL", text_color=TEXT_SOFT).pack(anchor="w", padx=22)
        self.base_url = ctk.CTkEntry(card, height=38)
        self.base_url.insert(0, self.repliz_conf.get("base_url", "https://api.repliz.com/public"))
        self.base_url.pack(fill="x", padx=22, pady=(4, 10))

        ctk.CTkLabel(card, text="Access Key", text_color=TEXT_SOFT).pack(anchor="w", padx=22)
        self.access_key = ctk.CTkEntry(card, height=38)
        self.access_key.insert(0, self.repliz_conf.get("access_key", ""))
        self.access_key.pack(fill="x", padx=22, pady=(4, 10))

        ctk.CTkLabel(card, text="Secret Key", text_color=TEXT_SOFT).pack(anchor="w", padx=22)
        self.secret_key = ctk.CTkEntry(card, show="*", height=38)
        self.secret_key.insert(0, self.repliz_conf.get("secret_key", ""))
        self.secret_key.pack(fill="x", padx=22, pady=(4, 10))

        self.status_label = ctk.CTkLabel(card, text="", text_color=TEXT_MUTED)
        self.status_label.pack(anchor="w", padx=22, pady=(0, 10))

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(fill="x", padx=22, pady=(0, 16))
        actions.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            actions,
            text="Test Connection",
            fg_color="#222222",
            hover_color="#333333",
            text_color=TEXT_PRIMARY,
            height=42,
            command=self._test_connection
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            actions,
            text="Save Configuration",
            fg_color=PRIMARY,
            hover_color=DEEP_RED,
            text_color=TEXT_PRIMARY,
            height=42,
            command=self._save_config
        ).grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def _save_config(self):
        new_conf = {
            "base_url": self.base_url.get().strip(),
            "access_key": self.access_key.get().strip(),
            "secret_key": self.secret_key.get().strip()
        }

        self.config.save_repliz(new_conf)
        self.status_badge.configure(text="SAVED", fg_color="#143322")
        messagebox.showinfo("Success", "Repliz configuration saved.")

    def _test_connection(self):
        url = self.base_url.get().strip()
        headers = {
            "X-Access-Key": self.access_key.get().strip(),
            "X-Secret-Key": self.secret_key.get().strip()
        }

        try:
            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 200:
                self.status_label.configure(
                    text="✓ Connected to Repliz",
                    text_color="green"
                )
                self.status_badge.configure(text="CONNECTED", fg_color="#143322")
            else:
                self.status_label.configure(
                    text=f"⚠ Error {response.status_code}",
                    text_color="orange"
                )
                self.status_badge.configure(text="WARNING", fg_color="#3a2a12")

        except Exception:
            self.status_label.configure(
                text="✕ Connection Failed",
                text_color="red"
            )
            self.status_badge.configure(text="ERROR", fg_color="#3a1717")