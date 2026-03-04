import customtkinter as ctk
from tkinter import messagebox
import asyncio

from core.config_manager import ConfigManager
from core.services.repliz_service_async import AsyncReplizService
from core.services.async_runner import AsyncRunner


class ReplizPage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.config = ConfigManager()
        self.async_runner = AsyncRunner()

        self.accounts = []

        self.build_ui()
        self.load_saved_config()

    # ==================================================
    # UI
    # ==================================================

    def build_ui(self):

        self.grid_columnconfigure(0, weight=1)

        container = ctk.CTkFrame(self, fg_color="#111111", corner_radius=15)
        container.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        container.grid_columnconfigure(0, weight=1)

        # ACCESS KEY
        ctk.CTkLabel(container, text="Access Key").grid(
            row=0, column=0, sticky="w", padx=20, pady=(20, 5)
        )

        self.access_entry = ctk.CTkEntry(container, height=40)
        self.access_entry.grid(row=1, column=0, sticky="ew", padx=20)

        # SECRET KEY
        ctk.CTkLabel(container, text="Secret Key").grid(
            row=2, column=0, sticky="w", padx=20, pady=(20, 5)
        )

        self.secret_entry = ctk.CTkEntry(container, height=40, show="*")
        self.secret_entry.grid(row=3, column=0, sticky="ew", padx=20)

        # BUTTONS
        ctk.CTkButton(
            container,
            text="Validate Keys",
            command=self.validate_keys
        ).grid(row=4, column=0, pady=15)

        ctk.CTkButton(
            container,
            text="Save Settings",
            fg_color="#28a745",
            hover_color="#2ecc71",
            command=self.save_settings
        ).grid(row=5, column=0, pady=10)

        # ACCOUNTS SECTION
        self.accounts_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="#1b1b1b",
            corner_radius=15,
            height=400
        )
        self.accounts_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=20,
            pady=(10, 20)
        )

        self.accounts_frame.grid_columnconfigure((0, 1, 2), weight=1)

    # ==================================================
    # LOAD SAVED CONFIG
    # ==================================================

    def load_saved_config(self):

        repliz_conf = self.config.get_repliz()

        if repliz_conf:
            self.access_entry.insert(0, repliz_conf.get("access_key", ""))
            self.secret_entry.insert(0, repliz_conf.get("secret_key", ""))

    # ==================================================
    # SAVE SETTINGS
    # ==================================================

    def save_settings(self):

        access = self.access_entry.get().strip()
        secret = self.secret_entry.get().strip()

        if not access or not secret:
            messagebox.showerror("Error", "Both keys are required.")
            return

        self.config.set_repliz(
            base_url="https://api.repliz.com/public",
            access_key=access,
            secret_key=secret
        )

        messagebox.showinfo("Success", "Repliz settings saved.")

    # ==================================================
    # VALIDATE KEYS
    # ==================================================

    def validate_keys(self):

        access = self.access_entry.get().strip()
        secret = self.secret_entry.get().strip()

        if not access or not secret:
            messagebox.showerror("Error", "Both keys are required.")
            return

        service = AsyncReplizService(
            base_url="https://api.repliz.com/public",
            access_key=access,
            secret_key=secret
        )

        async def fetch_accounts():
            try:
                result = await service.get_accounts()
                self.accounts = result.get("docs", [])
                self.render_accounts()
                messagebox.showinfo("Success", "Keys validated successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Invalid keys:\n{e}")

        self.async_runner.start(fetch_accounts())

    # ==================================================
    # RENDER ACCOUNT CARDS
    # ==================================================

    def render_accounts(self):

        for widget in self.accounts_frame.winfo_children():
            widget.destroy()

        for index, acc in enumerate(self.accounts):

            card = ctk.CTkFrame(
                self.accounts_frame,
                fg_color="#2b2b2b",
                corner_radius=10,
                height=200
            )

            row = index // 3
            col = index % 3

            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")

            # PLATFORM
            platform = acc.get("type", "unknown").upper()

            ctk.CTkLabel(
                card,
                text=platform,
                text_color="#00bcd4"
            ).pack(pady=(10, 5))

            # NAME
            ctk.CTkLabel(
                card,
                text=acc.get("name", ""),
                font=ctk.CTkFont(size=14, weight="bold")
            ).pack()

            # USERNAME
            ctk.CTkLabel(
                card,
                text=f"@{acc.get('username', '')}",
                text_color="gray"
            ).pack()

            # STATUS
            status_text = "Connected" if acc.get("isConnected") else "Not Connected"
            status_color = "#28a745" if acc.get("isConnected") else "#dc3545"

            ctk.CTkLabel(
                card,
                text=status_text,
                text_color=status_color
            ).pack(pady=10)