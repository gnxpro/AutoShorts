import requests
import customtkinter as ctk
from tkinter import messagebox
import webbrowser

from core.ai.settings_service import get_ai_settings, save_ai_settings
from core.theme_constants import (
    PRIMARY_RED, BLACK, TEXT_PRIMARY, TEXT_MUTED, 
    BADGE_DARK, BADGE_SUCCESS, BTN_DARK, CARD
)
from core.ui_helpers import make_card, make_section_badge
from core.ai.model_registry import get_models_by_provider
from core.ai.connection_tester import test_connection
from services.youtube_auth import start_auth
class AISettingsPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BLACK)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_ui()
        self._load_from_config()
        self._refresh_provider_ui()

    def _build_ui(self):
        # Container utama dengan Scroll agar semua tab tutorial kelihatan
        outer = ctk.CTkScrollableFrame(self, fg_color=BLACK)
        outer.pack(fill="both", expand=True, padx=30, pady=22)

        # --- HEADER ---
        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="AI & AUTOMATION HUB", font=("Arial", 30, "bold"), text_color=TEXT_PRIMARY).pack(side="left")
        self.status_badge = make_section_badge(header, "READY")
        self.status_badge.pack(side="right")

        # --- TUTORIAL SECTION (KEMBALI HADIR) ---
        tut_card = make_card(outer, "API Setup & Tutorials", "How to get your API keys for free or paid models.")
        tut_card.pack(fill="x", pady=(0, 20))

        self.tut_tabs = ctk.CTkTabview(tut_card, height=180, fg_color="transparent")
        self.tut_tabs.pack(fill="x", padx=20, pady=(5, 15))

        # Tab Gemini
        t_gem = self.tut_tabs.add("Google Gemini")
        ctk.CTkLabel(t_gem, text="1. Login to aistudio.google.com\n2. Create a new API Key.\n3. Best high-quality free tier option.", justify="left", text_color=TEXT_MUTED).pack(anchor="w", pady=5)
        ctk.CTkButton(t_gem, text="🌐 Get Gemini Key", width=160, command=lambda: webbrowser.open("https://aistudio.google.com/app/apikey")).pack(anchor="w")

        # Tab Groq
        t_groq = self.tut_tabs.add("Groq Cloud (Free)")
        ctk.CTkLabel(t_groq, text="1. Go to console.groq.com/keys\n2. Create an API Key for Llama 3.\n3. Fastest inference with generous free tier.", justify="left", text_color=TEXT_MUTED).pack(anchor="w", pady=5)
        ctk.CTkButton(t_groq, text="🌐 Get Groq Key", width=160, fg_color="#f55036", hover_color="#d4442e", command=lambda: webbrowser.open("https://console.groq.com/keys")).pack(anchor="w")

        # Tab OpenAI
        t_oai = self.tut_tabs.add("OpenAI")
        ctk.CTkLabel(t_oai, text="1. Login to platform.openai.com\n2. Add min $5 billing balance.\n3. Required for GPT-4o models.", justify="left", text_color=TEXT_MUTED).pack(anchor="w", pady=5)
        ctk.CTkButton(t_oai, text="🌐 Get OpenAI Key", width=160, command=lambda: webbrowser.open("https://platform.openai.com/api-keys")).pack(anchor="w")

        # --- CONFIGURATION SECTION ---
        conf_card = make_card(outer, "Engine Configuration", "Configure your AI provider and active model.")
        conf_card.pack(fill="x", pady=(0, 20))
        
        sel_f = ctk.CTkFrame(conf_card, fg_color="transparent")
        sel_f.pack(fill="x", padx=20, pady=10)

        self.provider_var = ctk.StringVar(value="Gemini AI")
        self.provider_menu = ctk.CTkOptionMenu(sel_f, values=["OFF (Manual)", "Gemini AI", "Groq Cloud", "OpenAI"], 
                                               variable=self.provider_var, command=lambda _: self._refresh_provider_ui())
        self.provider_menu.pack(side="left", expand=True, padx=5)

        self.model_var = ctk.StringVar(value="gemini-2.0-flash")
        self.model_menu = ctk.CTkOptionMenu(sel_f, values=get_models_by_provider("Gemini AI"), variable=self.model_var)
        self.model_menu.pack(side="left", expand=True, padx=5)

        self.key_entry = ctk.CTkEntry(conf_card, placeholder_text="Enter API Key here...", show="*", height=45)
        self.key_entry.pack(fill="x", padx=20, pady=15)

        # --- BUTTONS ---
        btn_f = ctk.CTkFrame(conf_card, fg_color="transparent")
        btn_f.pack(fill="x", padx=20, pady=20)
        self.test_btn = ctk.CTkButton(btn_f, text="Test Connection", fg_color=BTN_DARK, command=self._test_connection)
        self.test_btn.pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btn_f, text="Save Settings", fg_color=PRIMARY_RED, command=self._save).pack(side="left", expand=True, padx=5)

    def _refresh_provider_ui(self):
        models = get_models_by_provider(self.provider_var.get())

        self.model_menu.configure(values=models)

        if self.model_var.get() not in models:
            self.model_var.set(models[0] if models else "")

    def _load_from_config(self):
        data = get_ai_settings()
        self.provider_var.set(data["provider"])
        self.model_var.set(data["model"])
        if data["api_key"]:
            self.key_entry.insert(0, data["api_key"])
        self._refresh_provider_ui()

    def _save(self):
        save_ai_settings(
            self.provider_var.get(),
            self.model_var.get(),
            self.key_entry.get().strip()
        )
        self.status_badge.configure(text="SAVED", fg_color=BADGE_SUCCESS)
        messagebox.showinfo("Success", "Settings Saved Successfully!")

    def _test_connection(self):
        provider = self.provider_var.get()
        api_key = self.key_entry.get().strip()
        model = self.model_var.get()

        success, msg = test_connection(provider, api_key, model)

        if success:
            messagebox.showinfo("Success", msg)
        else:
            messagebox.showerror("Error", msg)
