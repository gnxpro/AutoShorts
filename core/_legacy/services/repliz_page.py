import customtkinter as ctk
from core.config_manager import load_config, save_config


class ReplizPage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent)

        self.config_data = load_config()

        ctk.CTkLabel(
            self,
            text="Repliz Integration",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=15)

        self.api_url = ctk.CTkEntry(self, placeholder_text="Repliz API URL")
        self.api_url.pack(fill="x", padx=40, pady=5)
        self.api_url.insert(0, self.config_data.get("repliz_api_url"))

        self.api_key = ctk.CTkEntry(self, placeholder_text="Repliz API Key")
        self.api_key.pack(fill="x", padx=40, pady=5)
        self.api_key.insert(0, self.config_data.get("repliz_api_key"))

        ctk.CTkLabel(self, text="Accounts").pack(pady=10)

        self.checkboxes = []

        for account in self.config_data.get("repliz_accounts", []):
            var = ctk.BooleanVar(value=account.get("enabled", False))

            cb = ctk.CTkCheckBox(
                self,
                text=account["name"],
                variable=var
            )
            cb.pack(anchor="w", padx=60)

            self.checkboxes.append((account, var))

        ctk.CTkButton(
            self,
            text="Save",
            command=self.save_settings
        ).pack(pady=20)

    def save_settings(self):

        self.config_data["repliz_api_url"] = self.api_url.get()
        self.config_data["repliz_api_key"] = self.api_key.get()

        for account, var in self.checkboxes:
            account["enabled"] = var.get()

        save_config(self.config_data)