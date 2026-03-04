import customtkinter as ctk
import webbrowser

PRIMARY_RED = "#b11226"
BG_BLACK = "#0d0d0d"
CARD_BLACK = "#141414"


class AboutPage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, fg_color=BG_BLACK)

        # Important: do NOT use self.pack() here
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(
            self,
            fg_color=CARD_BLACK,
            corner_radius=12
        )
        container.grid(row=0, column=0, padx=60, pady=40, sticky="nsew")

        ctk.CTkLabel(
            container,
            text="GNX PRODUCTION",
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
            hover_color="#8f0e1e",
            command=lambda: webbrowser.open(
                "https://www.instagram.com/genexproduction/"
            )
        ).pack(pady=8)

        ctk.CTkButton(
            container,
            text="YouTube",
            fg_color=PRIMARY_RED,
            hover_color="#8f0e1e",
            command=lambda: webbrowser.open(
                "https://www.youtube.com/@GenExProduction"
            )
        ).pack(pady=8)

        ctk.CTkLabel(
            container,
            text="Version 5.0 Global SaaS",
            font=ctk.CTkFont(size=12)
        ).pack(pady=(30, 20))