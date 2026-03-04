import customtkinter as ctk
from tkinter import messagebox
from core.config_manager import ConfigManager
from core.services.cloudinary_service import CloudinaryService


class CloudinaryPage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.grid_columnconfigure(0, weight=1)

        self.config = ConfigManager()

        self._build_ui()
        self._load_saved()

    # =========================
    # UI
    # =========================

    def _build_ui(self):

        ctk.CTkLabel(
            self,
            text="Cloudinary Settings",
            font=ctk.CTkFont(size=22, weight="bold")
        ).grid(row=0, column=0, pady=(40, 20))

        self.cloud_name = ctk.CTkEntry(self, placeholder_text="Cloud Name")
        self.cloud_name.grid(row=1, column=0, padx=80, pady=8, sticky="ew")

        self.api_key = ctk.CTkEntry(self, placeholder_text="API Key")
        self.api_key.grid(row=2, column=0, padx=80, pady=8, sticky="ew")

        self.api_secret = ctk.CTkEntry(self, placeholder_text="API Secret", show="*")
        self.api_secret.grid(row=3, column=0, padx=80, pady=8, sticky="ew")

        ctk.CTkButton(
            self,
            text="Test Connection",
            command=self.test_connection
        ).grid(row=4, column=0, pady=10)

        ctk.CTkButton(
            self,
            text="Save Settings",
            fg_color="#16a34a",
            command=self.save_settings
        ).grid(row=5, column=0, pady=10)

    # =========================
    # LOAD CONFIG
    # =========================

    def _load_saved(self):

        cloud_conf = self.config.get_cloudinary()

        if cloud_conf:
            self.cloud_name.insert(0, cloud_conf.get("cloud_name", ""))
            self.api_key.insert(0, cloud_conf.get("api_key", ""))
            self.api_secret.insert(0, cloud_conf.get("api_secret", ""))

    # =========================
    # SAVE
    # =========================

    def save_settings(self):

        cloud_name = self.cloud_name.get().strip()
        api_key = self.api_key.get().strip()
        api_secret = self.api_secret.get().strip()

        if not cloud_name or not api_key or not api_secret:
            messagebox.showerror("Error", "All fields are required.")
            return

        self.config.set_cloudinary(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )

        messagebox.showinfo("Saved", "Cloudinary settings saved.")

    # =========================
    # TEST CONNECTION
    # =========================

    def test_connection(self):

        try:
            service = CloudinaryService()
            service.test_connection()
            messagebox.showinfo("Success", "Cloudinary connected successfully.")
        except Exception as e:
            messagebox.showerror("Error", str(e))