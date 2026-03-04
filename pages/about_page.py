import webbrowser
import customtkinter as ctk

PRIMARY_RED = "#b11226"
BLACK = "#000000"


class AboutPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BLACK)

        container = ctk.CTkFrame(self, fg_color=BLACK)
        container.pack(fill="both", expand=True)

        ctk.CTkLabel(
            container,
            text="GNX PRO - AI STUDIO",
            font=ctk.CTkFont(size=26, weight="bold")
        ).pack(pady=(30, 10))

        ctk.CTkLabel(
            container,
            text="Cinematic Enterprise SaaS Automation Studio",
            font=ctk.CTkFont(size=14)
        ).pack(pady=(0, 25))

        ctk.CTkLabel(
            container,
            text="Developed by",
            font=ctk.CTkFont(size=14)
        ).pack()

        ctk.CTkLabel(
            container,
            text="GENERAL EXPLORER PRODUCTION",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=PRIMARY_RED
        ).pack(pady=(5, 25))

        ctk.CTkButton(
            container,
            text="Instagram",
            fg_color=PRIMARY_RED,
            command=lambda: webbrowser.open("https://www.instagram.com/genexproduction/")
        ).pack(pady=8)

        ctk.CTkButton(
            container,
            text="YouTube",
            fg_color=PRIMARY_RED,
            command=lambda: webbrowser.open("https://www.youtube.com/@GenExProduction")
        ).pack(pady=8)