import requests
import customtkinter as ctk
from tkinter import messagebox

from core.settings_store import load_config, save_config, get as cfg_get, set as cfg_set
from core.theme_constants import (
    PRIMARY_RED,
    DEEP_RED,
    BLACK,
    CARD_SOFT,
    TEXT_PRIMARY,
    TEXT_MUTED,
    TEXT_SOFT,
    BADGE_DARK,
    BADGE_SUCCESS,
    BADGE_ERROR,
    BTN_DARK,
    BTN_DARK_HOVER,
)
from core.ui_helpers import make_card, make_stat_card


OPENAI_MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
]

GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash",
]


class AISettingsPage(ctk.CTkFrame):
    """
    AI Settings:
    - Provider: OpenAI / OpenRouter / Gemini
    - Model selection
    - Auto Prompt toggle
    - Provider-specific API settings
    """

    def __init__(self, master):
        super().__init__(master, fg_color=BLACK)

        self.cfg = load_config()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()
        self._load_from_config()
        self._refresh_provider_ui()

    # ---------------------------------------------------------
    # Build UI
    # ---------------------------------------------------------

    def _build_ui(self):
        outer = ctk.CTkScrollableFrame(self, fg_color=BLACK)
        outer.grid(row=0, column=0, sticky="nsew", padx=30, pady=22)
        outer.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="AI Settings",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=30, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="Choose provider, model, and prompt behavior. Settings are saved locally.",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=13),
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.status_badge = ctk.CTkLabel(
            header,
            text="NOT TESTED",
            text_color=TEXT_PRIMARY,
            fg_color=BADGE_DARK,
            corner_radius=12,
            padx=14,
            pady=7,
        )
        self.status_badge.grid(row=0, column=1, rowspan=2, sticky="e")

        # Stats
        stats = ctk.CTkFrame(outer, fg_color="transparent")
        stats.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        for i in range(3):
            stats.grid_columnconfigure(i, weight=1)

        stat1, self.stat_provider_value = make_stat_card(stats, "Provider")
        stat1.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        stat2, self.stat_model_value = make_stat_card(stats, "Selected Model")
        stat2.grid(row=0, column=1, sticky="ew", padx=8)

        stat3, self.stat_prompt_value = make_stat_card(stats, "Prompt Mode")
        stat3.grid(row=0, column=2, sticky="ew", padx=(8, 0))

        # Main settings
        settings_card = make_card(
            outer,
            "AI Provider Configuration",
            "Set your provider, choose a model, then test and save the configuration.",
        )
        settings_card.grid(row=2, column=0, sticky="ew", pady=10)

        # Provider row
        provider_row = ctk.CTkFrame(settings_card, fg_color="transparent")
        provider_row.pack(fill="x", padx=22, pady=(0, 10))
        provider_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            provider_row,
            text="Provider",
            text_color=TEXT_SOFT,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))

        self.provider_var = ctk.StringVar(value="openai")
        self.provider_menu = ctk.CTkOptionMenu(
            provider_row,
            values=["openai", "openrouter", "gemini"],
            variable=self.provider_var,
            fg_color=BTN_DARK,
            button_color="#2a2a2a",
            button_hover_color="#3a3a3a",
            text_color=TEXT_PRIMARY,
            dropdown_text_color=TEXT_PRIMARY,
            width=220,
            command=lambda _=None: self._refresh_provider_ui(),
        )
        self.provider_menu.grid(row=0, column=1, sticky="e")

        # Model row
        model_row = ctk.CTkFrame(settings_card, fg_color="transparent")
        model_row.pack(fill="x", padx=22, pady=(0, 10))
        model_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            model_row,
            text="Model",
            text_color=TEXT_SOFT,
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))

        self.model_var = ctk.StringVar(value="gpt-4o-mini")
        self.model_menu = ctk.CTkOptionMenu(
            model_row,
            values=OPENAI_MODELS,
            variable=self.model_var,
            fg_color=BTN_DARK,
            button_color="#2a2a2a",
            button_hover_color="#3a3a3a",
            text_color=TEXT_PRIMARY,
            dropdown_text_color=TEXT_PRIMARY,
            width=320,
            command=lambda _=None: self._update_summary_cards(),
        )
        self.model_menu.grid(row=0, column=1, sticky="e")

        # Prompt mode card
        prompt_card = ctk.CTkFrame(
            settings_card,
            fg_color=CARD_SOFT,
            corner_radius=14,
            border_width=1,
            border_color="#242424",
        )
        prompt_card.pack(fill="x", padx=22, pady=(0, 12))

        self.auto_prompt_var = ctk.BooleanVar(value=True)
        self.auto_prompt_cb = ctk.CTkCheckBox(
            prompt_card,
            text="Enable Auto Prompt (recommended) — uncheck to use manual prompts in tool pages",
            variable=self.auto_prompt_var,
            text_color=TEXT_PRIMARY,
            command=self._update_summary_cards,
        )
        self.auto_prompt_cb.pack(anchor="w", padx=14, pady=12)

        # Provider credentials card
        provider_card = make_card(
            outer,
            "Provider Credentials",
            "This section changes automatically based on the selected provider.",
        )
        provider_card.grid(row=3, column=0, sticky="ew", pady=10)

        self.provider_frame = ctk.CTkFrame(
            provider_card,
            fg_color=CARD_SOFT,
            corner_radius=14,
            border_width=1,
            border_color="#242424",
        )
        self.provider_frame.pack(fill="x", padx=22, pady=(0, 16))
        self.provider_frame.grid_columnconfigure(0, weight=1)

        # OpenAI widgets
        self.openai_key = ctk.CTkEntry(
            self.provider_frame,
            placeholder_text="OpenAI API Key",
            text_color=TEXT_PRIMARY,
            height=38,
            show="*",
        )

        # OpenRouter widgets
        self.or_key = ctk.CTkEntry(
            self.provider_frame,
            placeholder_text="OpenRouter API Key",
            text_color=TEXT_PRIMARY,
            height=38,
            show="*",
        )
        self.or_base = ctk.CTkEntry(
            self.provider_frame,
            placeholder_text="OpenRouter Base URL (default: https://openrouter.ai/api/v1)",
            text_color=TEXT_PRIMARY,
            height=38,
        )
        self.or_load_btn = ctk.CTkButton(
            self.provider_frame,
            text="Load Models (OpenRouter)",
            fg_color=PRIMARY_RED,
            hover_color=DEEP_RED,
            text_color=TEXT_PRIMARY,
            height=38,
            command=self._load_openrouter_models,
        )

        # Gemini widgets
        self.gemini_key = ctk.CTkEntry(
            self.provider_frame,
            placeholder_text="Gemini API Key",
            text_color=TEXT_PRIMARY,
            height=38,
            show="*",
        )

        # Actions
        actions_card = make_card(
            outer,
            "Actions",
            "Test your connection first, then save the configuration.",
        )
        actions_card.grid(row=4, column=0, sticky="ew", pady=10)

        actions = ctk.CTkFrame(actions_card, fg_color="transparent")
        actions.pack(fill="x", padx=22, pady=(0, 16))
        actions.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            actions,
            text="Test Connection",
            fg_color=BTN_DARK,
            hover_color=BTN_DARK_HOVER,
            text_color=TEXT_PRIMARY,
            height=42,
            command=self._test_connection,
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            actions,
            text="Save Settings",
            fg_color=PRIMARY_RED,
            hover_color=DEEP_RED,
            text_color=TEXT_PRIMARY,
            height=42,
            command=self._save,
        ).grid(row=0, column=1, padx=8, sticky="ew")

        ctk.CTkButton(
            actions,
            text="Reset Defaults",
            fg_color=BTN_DARK,
            hover_color=BTN_DARK_HOVER,
            text_color=TEXT_PRIMARY,
            height=42,
            command=self._reset_defaults,
        ).grid(row=0, column=2, padx=(8, 0), sticky="ew")

    # ---------------------------------------------------------
    # Provider UI
    # ---------------------------------------------------------

    def _clear_provider_frame(self):
        for w in self.provider_frame.winfo_children():
            w.grid_forget()

    def _refresh_provider_ui(self):
        provider = (self.provider_var.get() or "openai").lower()
        self._clear_provider_frame()

        if provider == "openai":
            self.model_menu.configure(values=OPENAI_MODELS)
            if self.model_var.get() not in OPENAI_MODELS:
                self.model_var.set(OPENAI_MODELS[0])

            self.openai_key.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 14))

        elif provider == "openrouter":
            cached = cfg_get(self.cfg, "ai.openrouter.cached_models", []) or []
            values = cached if cached else [
                "openai/gpt-4o-mini",
                "openai/gpt-4o",
                "google/gemini-2.5-flash",
                "anthropic/claude-3.7-sonnet",
                "meta-llama/llama-3.3-70b-instruct",
                "deepseek/deepseek-chat",
            ]
            self.model_menu.configure(values=values)
            if self.model_var.get() not in values:
                self.model_var.set(values[0])

            self.or_key.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 8))
            self.or_base.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 8))
            self.or_load_btn.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 14))

        elif provider == "gemini":
            self.model_menu.configure(values=GEMINI_MODELS)
            if self.model_var.get() not in GEMINI_MODELS:
                self.model_var.set(GEMINI_MODELS[0])

            self.gemini_key.grid(row=0, column=0, sticky="ew", padx=14, pady=(14, 14))

        else:
            messagebox.showerror("Error", f"Unknown provider: {provider}")

        self._update_summary_cards()

    # ---------------------------------------------------------
    # Load / Save config
    # ---------------------------------------------------------

    def _load_from_config(self):
        self.provider_var.set(cfg_get(self.cfg, "ai.provider", "openai"))
        self.model_var.set(cfg_get(self.cfg, "ai.model", "gpt-4o-mini"))
        self.auto_prompt_var.set(bool(cfg_get(self.cfg, "ai.auto_prompt", True)))

        self.openai_key.delete(0, "end")
        self.openai_key.insert(0, cfg_get(self.cfg, "ai.openai.api_key", "") or "")

        self.or_key.delete(0, "end")
        self.or_key.insert(0, cfg_get(self.cfg, "ai.openrouter.api_key", "") or "")

        self.or_base.delete(0, "end")
        self.or_base.insert(
            0,
            cfg_get(self.cfg, "ai.openrouter.base_url", "https://openrouter.ai/api/v1")
            or "https://openrouter.ai/api/v1"
        )

        self.gemini_key.delete(0, "end")
        self.gemini_key.insert(0, cfg_get(self.cfg, "ai.gemini.api_key", "") or "")

        self._update_summary_cards()

    def _save(self):
        provider = (self.provider_var.get() or "openai").lower()

        cfg_set(self.cfg, "ai.provider", provider)
        cfg_set(self.cfg, "ai.model", self.model_var.get())
        cfg_set(self.cfg, "ai.auto_prompt", bool(self.auto_prompt_var.get()))

        cfg_set(self.cfg, "ai.openai.api_key", self.openai_key.get().strip())
        cfg_set(self.cfg, "ai.openrouter.api_key", self.or_key.get().strip())
        cfg_set(
            self.cfg,
            "ai.openrouter.base_url",
            (self.or_base.get().strip() or "https://openrouter.ai/api/v1")
        )
        cfg_set(self.cfg, "ai.gemini.api_key", self.gemini_key.get().strip())

        save_config(self.cfg)
        self.status_badge.configure(text="SAVED", fg_color=BADGE_SUCCESS)
        messagebox.showinfo("Saved", "AI settings saved successfully.")
        self._update_summary_cards()

    def _reset_defaults(self):
        self.provider_var.set("openai")
        self.model_var.set("gpt-4o-mini")
        self.auto_prompt_var.set(True)

        self.openai_key.delete(0, "end")
        self.or_key.delete(0, "end")
        self.gemini_key.delete(0, "end")
        self.or_base.delete(0, "end")
        self.or_base.insert(0, "https://openrouter.ai/api/v1")

        self.status_badge.configure(text="DEFAULTS", fg_color="#3a2a12")
        self._refresh_provider_ui()
        messagebox.showinfo("Reset", "Defaults applied. Click Save to persist.")

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    def _update_summary_cards(self):
        provider = (self.provider_var.get() or "openai").upper()
        model = self.model_var.get().strip() or "-"
        prompt_mode = "AUTO" if bool(self.auto_prompt_var.get()) else "MANUAL"

        self.stat_provider_value.configure(text=provider)
        self.stat_model_value.configure(text=model)
        self.stat_prompt_value.configure(text=prompt_mode)

    # ---------------------------------------------------------
    # Actions
    # ---------------------------------------------------------

    def _test_connection(self):
        provider = (self.provider_var.get() or "openai").lower()
        model = self.model_var.get().strip()

        try:
            if provider == "openai":
                key = self.openai_key.get().strip()
                if not key:
                    raise Exception("OpenAI API Key is empty.")

                r = requests.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {key}"},
                    timeout=20,
                )
                if r.status_code >= 400:
                    raise Exception(f"OpenAI test failed: {r.status_code} {r.text[:200]}")

                self.status_badge.configure(text="CONNECTED", fg_color=BADGE_SUCCESS)
                messagebox.showinfo("OK", f"OpenAI connected.\nModel selected: {model}")
                return

            if provider == "openrouter":
                key = self.or_key.get().strip()
                base = (self.or_base.get().strip() or "https://openrouter.ai/api/v1").rstrip("/")
                if not key:
                    raise Exception("OpenRouter API Key is empty.")

                r = requests.get(
                    f"{base}/models",
                    headers={"Authorization": f"Bearer {key}"},
                    timeout=20,
                )
                if r.status_code >= 400:
                    raise Exception(f"OpenRouter test failed: {r.status_code} {r.text[:200]}")

                self.status_badge.configure(text="CONNECTED", fg_color=BADGE_SUCCESS)
                messagebox.showinfo("OK", f"OpenRouter connected.\nModel selected: {model}")
                return

            if provider == "gemini":
                key = self.gemini_key.get().strip()
                if not key:
                    raise Exception("Gemini API Key is empty.")

                self.status_badge.configure(text="CONNECTED", fg_color=BADGE_SUCCESS)
                messagebox.showinfo("OK", f"Gemini key saved.\nModel selected: {model}")
                return

            raise Exception(f"Unknown provider: {provider}")

        except Exception as e:
            self.status_badge.configure(text="ERROR", fg_color=BADGE_ERROR)
            messagebox.showerror("Connection Error", str(e))

    def _load_openrouter_models(self):
        try:
            key = self.or_key.get().strip()
            base = (self.or_base.get().strip() or "https://openrouter.ai/api/v1").rstrip("/")

            if not key:
                messagebox.showerror("Error", "OpenRouter API Key is empty.")
                return

            r = requests.get(
                f"{base}/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=30,
            )
            if r.status_code >= 400:
                raise Exception(f"{r.status_code} {r.text[:250]}")

            data = r.json()
            models = [m.get("id") for m in (data.get("data") or []) if m.get("id")]
            if not models:
                raise Exception("No models returned from OpenRouter.")

            cfg_set(self.cfg, "ai.openrouter.cached_models", models)
            save_config(self.cfg)

            self.model_menu.configure(values=models)
            self.model_var.set(models[0])
            self._update_summary_cards()

            messagebox.showinfo("Loaded", f"Loaded {len(models)} OpenRouter models.")
        except Exception as e:
            messagebox.showerror("Load Models Error", str(e))