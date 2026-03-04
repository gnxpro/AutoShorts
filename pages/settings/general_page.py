import customtkinter as ctk
from tkinter import messagebox
from core.config_manager import load_config, save_config

PRIMARY_RED = "#b11226"
BG_BLACK = "#0d0d0d"


class GeneralPage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, fg_color=BG_BLACK)

        self.grid_columnconfigure(0, weight=1)

        self.config = load_config()

        ctk.CTkLabel(
            self,
            text="General Settings",
            font=ctk.CTkFont(size=18, weight="bold")
        ).grid(row=0, column=0, pady=30)

        # Engine Mode
        ctk.CTkLabel(
            self,
            text="Engine Mode"
        ).grid(row=1, column=0, sticky="w", padx=40)

        self.engine_menu = ctk.CTkOptionMenu(
            self,
            values=["basic", "premium", "high level"]
        )
        self.engine_menu.set(
            self.config.get("engine_mode", "basic")
        )
        self.engine_menu.grid(row=2, column=0, padx=40, pady=5, sticky="ew")

        # Performance Mode
        ctk.CTkLabel(
            self,
            text="Performance Mode"
        ).grid(row=3, column=0, sticky="w", padx=40)

        self.performance_menu = ctk.CTkOptionMenu(
            self,
            values=["balanced", "fast", "high quality"]
        )
        self.performance_menu.set(
            self.config.get("performance_mode", "balanced")
        )
        self.performance_menu.grid(row=4, column=0, padx=40, pady=5, sticky="ew")

        # Watermark toggle
        self.watermark_switch = ctk.CTkSwitch(
            self,
            text="Enable Watermark"
        )
        if self.config.get("watermark_enabled", False):
            self.watermark_switch.select()
        self.watermark_switch.grid(row=5, column=0, pady=20)

        # Save Button
        ctk.CTkButton(
            self,
            text="Save Settings",
            fg_color=PRIMARY_RED,
            command=self.save_settings
        ).grid(row=6, column=0, pady=10)

    def save_settings(self):

        self.config["engine_mode"] = self.engine_menu.get()
        self.config["performance_mode"] = self.performance_menu.get()
        self.config["watermark_enabled"] = self.watermark_switch.get()

        save_config(self.config)

        messagebox.showinfo("Saved", "General settings saved successfully.")