import customtkinter as ctk
import requests
from tkinter import messagebox

from core.config_manager import ConfigManager

PRIMARY = "#b11226"
CARD_BG = "#111111"
TEXT_MUTED = "#aaaaaa"


class ReplizPage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.config = ConfigManager()
        self.repliz_conf = self.config.get_repliz()

        self._build_ui()

    # =====================================================
    # UI
    # =====================================================

    def _build_ui(self):

        title = ctk.CTkLabel(
            self,
            text="REPLIZ INTEGRATION",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=PRIMARY
        )
        title.pack(pady=(20, 10))

        frame = ctk.CTkFrame(self, fg_color=CARD_BG)
        frame.pack(fill="x", padx=20, pady=20)

        # Base URL
        ctk.CTkLabel(frame, text="API Base URL").pack(anchor="w", padx=15)
        self.base_url = ctk.CTkEntry(frame)
        self.base_url.insert(0, self.repliz_conf.get("base_url", "https://api.repliz.com/public"))
        self.base_url.pack(fill="x", padx=15, pady=5)

        # Access Key
        ctk.CTkLabel(frame, text="Access Key").pack(anchor="w", padx=15)
        self.access_key = ctk.CTkEntry(frame)
        self.access_key.insert(0, self.repliz_conf.get("access_key", ""))
        self.access_key.pack(fill="x", padx=15, pady=5)

        # Secret Key
        ctk.CTkLabel(frame, text="Secret Key").pack(anchor="w", padx=15)
        self.secret_key = ctk.CTkEntry(frame, show="*")
        self.secret_key.insert(0, self.repliz_conf.get("secret_key", ""))
        self.secret_key.pack(fill="x", padx=15, pady=5)

        # Buttons
        ctk.CTkButton(
            frame,
            text="Test Connection",
            command=self._test_connection
        ).pack(pady=10)

        ctk.CTkButton(
            frame,
            text="Save Configuration",
            command=self._save_config
        ).pack(pady=10)

        self.status_label = ctk.CTkLabel(frame, text="")
        self.status_label.pack(pady=10)

    # =====================================================
    # SAVE
    # =====================================================

    def _save_config(self):

        new_conf = {
            "base_url": self.base_url.get(),
            "access_key": self.access_key.get(),
            "secret_key": self.secret_key.get()
        }

        self.config.save_repliz(new_conf)

        messagebox.showinfo("Success", "Repliz configuration saved.")

    # =====================================================
    # TEST CONNECTION
    # =====================================================

    def _test_connection(self):

        url = self.base_url.get()
        headers = {
            "X-Access-Key": self.access_key.get(),
            "X-Secret-Key": self.secret_key.get()
        }

        try:
            response = requests.get(url, headers=headers, timeout=5)

            if response.status_code == 200:
                self.status_label.configure(
                    text="✓ Connected to Repliz",
                    text_color="green"
                )
            else:
                self.status_label.configure(
                    text=f"⚠ Error {response.status_code}",
                    text_color="orange"
                )

        except Exception:
            self.status_label.configure(
                text="✕ Connection Failed",
                text_color="red"
            )