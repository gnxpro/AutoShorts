import customtkinter as ctk


class SplashScreen(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.geometry("500x300")
        self.overrideredirect(True)
        self.configure(fg_color="#0f172a")

        ctk.CTkLabel(
            self,
            text="GNX PRODUCTION",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color="white"
        ).pack(expand=True)

        ctk.CTkLabel(
            self,
            text="AI Powered Short Generator",
            text_color="#94a3b8"
        ).pack(pady=10)
