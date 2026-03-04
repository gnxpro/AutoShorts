import customtkinter as ctk
from tkinter import messagebox
import webbrowser
import platform
import sys

from core.config_manager import ConfigManager
from core.ai.provider_router import ProviderRouter


PRIMARY = "#b11226"
CARD_BG = "#111111"
TEXT_MUTED = "#aaaaaa"


class SettingsPage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")

        self.config = ConfigManager()
        self.ai_conf = self.config.get_ai()

        self._build_tabs()

    # =====================================================
    # TABS
    # =====================================================

    def _build_tabs(self):
        tabview = ctk.CTkTabview(self)
        tabview.pack(fill="both", expand=True, padx=20, pady=20)

        tabview.add("AI Settings")
        tabview.add("About")

        self._build_ai_tab(tabview.tab("AI Settings"))
        self._build_about_tab(tabview.tab("About"))

    # =====================================================
    # AI SETTINGS PRO
    # =====================================================

    def _build_ai_tab(self, parent):

        frame = ctk.CTkFrame(parent, fg_color=CARD_BG)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            frame,
            text="AI CONFIGURATION PANEL",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=PRIMARY
        ).pack(pady=(15, 10))

        # Provider
        ctk.CTkLabel(frame, text="AI Provider").pack(anchor="w", padx=15)
        self.provider_option = ctk.CTkOptionMenu(
            frame,
            values=["openai", "gemini"]
        )
        self.provider_option.set(self.ai_conf.get("provider", "openai"))
        self.provider_option.pack(fill="x", padx=15, pady=5)

        # OpenAI Key
        ctk.CTkLabel(frame, text="OpenAI API Key").pack(anchor="w", padx=15)
        self.openai_entry = ctk.CTkEntry(frame)
        self.openai_entry.insert(0, self.ai_conf.get("openai_api_key", ""))
        self.openai_entry.pack(fill="x", padx=15, pady=5)

        # Gemini Key
        ctk.CTkLabel(frame, text="Gemini API Key").pack(anchor="w", padx=15)
        self.gemini_entry = ctk.CTkEntry(frame)
        self.gemini_entry.insert(0, self.ai_conf.get("gemini_api_key", ""))
        self.gemini_entry.pack(fill="x", padx=15, pady=5)

        # Model
        ctk.CTkLabel(frame, text="Default Model").pack(anchor="w", padx=15)
        self.model_option = ctk.CTkOptionMenu(
            frame,
            values=["gpt-4o", "gpt-4o-mini", "gpt-4.1"]
        )
        self.model_option.set(self.ai_conf.get("model", "gpt-4o"))
        self.model_option.pack(fill="x", padx=15, pady=5)

        # Tone
        ctk.CTkLabel(frame, text="Default Tone").pack(anchor="w", padx=15)
        self.tone_option = ctk.CTkOptionMenu(
            frame,
            values=["Viral", "Emotional", "Professional", "Aggressive"]
        )
        self.tone_option.set(self.ai_conf.get("tone", "Viral"))
        self.tone_option.pack(fill="x", padx=15, pady=5)

        # Hook Style
        ctk.CTkLabel(frame, text="Hook Style").pack(anchor="w", padx=15)
        self.hook_style_option = ctk.CTkOptionMenu(
            frame,
            values=["Emotional", "Curiosity", "Controversy", "Question"]
        )
        self.hook_style_option.set(self.ai_conf.get("hook_style", "Emotional"))
        self.hook_style_option.pack(fill="x", padx=15, pady=5)

        # Subtitle Style
        ctk.CTkLabel(frame, text="Subtitle Style").pack(anchor="w", padx=15)
        self.subtitle_option = ctk.CTkOptionMenu(
            frame,
            values=["tiktok", "instagram", "youtube"]
        )
        self.subtitle_option.set(self.ai_conf.get("subtitle_style", "tiktok"))
        self.subtitle_option.pack(fill="x", padx=15, pady=5)

        # Language
        ctk.CTkLabel(frame, text="Language").pack(anchor="w", padx=15)
        self.language_option = ctk.CTkOptionMenu(
            frame,
            values=["id", "en"]
        )
        self.language_option.set(self.ai_conf.get("language", "id"))
        self.language_option.pack(fill="x", padx=15, pady=5)

        # Daily Credit Limit
        ctk.CTkLabel(frame, text="Daily AI Credit Limit").pack(anchor="w", padx=15)
        self.credit_entry = ctk.CTkEntry(frame)
        self.credit_entry.insert(0, str(self.ai_conf.get("daily_credit_limit", 1000)))
        self.credit_entry.pack(fill="x", padx=15, pady=5)

        # Buttons
        ctk.CTkButton(
            frame,
            text="Test AI Connection",
            command=self._test_ai
        ).pack(pady=(15, 5))

        ctk.CTkButton(
            frame,
            text="Save AI Settings",
            command=self._save_ai
        ).pack(pady=10)

        self.status_label = ctk.CTkLabel(frame, text="")
        self.status_label.pack(pady=5)

    # =====================================================
    # SAVE
    # =====================================================

    def _save_ai(self):

        new_conf = {
            "provider": self.provider_option.get(),
            "openai_api_key": self.openai_entry.get(),
            "gemini_api_key": self.gemini_entry.get(),
            "model": self.model_option.get(),
            "tone": self.tone_option.get(),
            "hook_style": self.hook_style_option.get(),
            "subtitle_style": self.subtitle_option.get(),
            "language": self.language_option.get(),
            "daily_credit_limit": int(self.credit_entry.get() or 1000)
        }

        self.config.save_ai(new_conf)
        messagebox.showinfo("Success", "AI settings saved.")

    # =====================================================
    # TEST API
    # =====================================================

    def _test_ai(self):

        try:
            test_conf = {
                "provider": self.provider_option.get(),
                "openai_api_key": self.openai_entry.get(),
                "gemini_api_key": self.gemini_entry.get(),
                "model": self.model_option.get()
            }

            router = ProviderRouter(test_conf)

            result = router.generate(
                system_prompt="You are a test bot.",
                user_prompt="Say OK.",
                model_override=self.model_option.get()
            )

            if result:
                self.status_label.configure(
                    text="✓ AI Connected Successfully",
                    text_color="green"
                )
            else:
                self.status_label.configure(
                    text="⚠ No response",
                    text_color="orange"
                )

        except Exception as e:
            self.status_label.configure(
                text="✕ AI Connection Failed",
                text_color="red"
            )

    # =====================================================
    # ABOUT
    # =====================================================

    def _build_about_tab(self, parent):

        frame = ctk.CTkFrame(parent, fg_color=CARD_BG)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            frame,
            text="GNX PRODUCTION",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=PRIMARY
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            frame,
            text="Developed by General Explorer Production / GNX Profesional",
            text_color=TEXT_MUTED
        ).pack(pady=(0, 15))

        desktop_info = f"""
Desktop Version: 2.0.0
Python: {platform.python_version()}
Platform: {platform.system()} {platform.release()}
Mode: {"PyInstaller" if getattr(sys, "frozen", False) else "Development"}
"""

        ctk.CTkLabel(
            frame,
            text=desktop_info.strip(),
            justify="left",
            text_color=TEXT_MUTED
        ).pack(pady=10)

        self._link_button(
            frame,
            "GenEx Production YouTube",
            "https://www.youtube.com/@GenExProduction"
        )

        self._link_button(
            frame,
            "GNX Profesional YouTube",
            "https://www.youtube.com/@gnxprofesional"
        )

    # =====================================================

    def _link_button(self, parent, text, url):
        ctk.CTkButton(
            parent,
            text=text,
            command=lambda: webbrowser.open(url)
        ).pack(pady=4)