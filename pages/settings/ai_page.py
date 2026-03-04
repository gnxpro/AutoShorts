import customtkinter as ctk
from tkinter import messagebox
import openai

from core.config_manager import load_config, save_config


class AISettingsPage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent)

        self.config = load_config()

        ctk.CTkLabel(
            self,
            text="AI Engine Settings",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=20)

        # Provider
        ctk.CTkLabel(self, text="AI Provider").pack(anchor="w", padx=40)

        self.provider_menu = ctk.CTkOptionMenu(
            self,
            values=["disabled", "openai"]
        )
        self.provider_menu.set(self.config.get("ai_provider", "disabled"))
        self.provider_menu.pack(fill="x", padx=40, pady=5)

        # API KEY
        ctk.CTkLabel(self, text="OpenAI API Key").pack(anchor="w", padx=40)

        self.api_entry = ctk.CTkEntry(self, show="*")
        self.api_entry.insert(0, self.config.get("openai_api_key", ""))
        self.api_entry.pack(fill="x", padx=40, pady=5)

        # Buttons
        ctk.CTkButton(
            self,
            text="Save",
            command=self.save_settings
        ).pack(pady=10)

        ctk.CTkButton(
            self,
            text="Test Connection",
            command=self.test_connection
        ).pack()

        self.status_label = ctk.CTkLabel(self, text="")
        self.status_label.pack(pady=10)

    def save_settings(self):
        self.config["ai_provider"] = self.provider_menu.get()
        self.config["openai_api_key"] = self.api_entry.get().strip()

        save_config(self.config)
        messagebox.showinfo("Saved", "AI Settings Saved")

    def test_connection(self):

        provider = self.provider_menu.get()
        key = self.api_entry.get().strip()

        if provider != "openai":
            self.status_label.configure(text="AI Disabled")
            return

        if not key:
            self.status_label.configure(text="No API Key")
            return

        try:
            openai.api_key = key
            openai.Model.list()
            self.status_label.configure(text="Connected ✅")
        except Exception as e:
            self.status_label.configure(text="Connection Failed ❌")