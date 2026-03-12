import customtkinter as ctk

from core.theme_constants import (
    PRIMARY_RED,
    DEEP_RED,
    BLACK,
    CARD,
    BORDER,
    TEXT_PRIMARY,
    TEXT_MUTED,
    TEXT_SOFT,
    BTN_DARK,
    BTN_DARK_HOVER,
)
from core.license_manager import load_effective_capabilities

from pages.dashboard_page import DashboardPage
from pages.cloudinary_page import CloudinaryPage
from pages.repliz_page import ReplizPage
from pages.ai_settings_page import AISettingsPage
from pages.license_page import LicensePage
from pages.about_page import AboutPage


class AppShell(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BLACK)
        self.pack(fill="both", expand=True)

        self.app = master
        self.engine = getattr(master, "engine", None)

        self.current_page = None
        self.nav_buttons = {}
        self.pages = {}

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content()
        self._build_pages()

        self.show_page("dashboard")
        self.refresh_plan_status()

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=CARD,
            corner_radius=0,
            border_width=1,
            border_color=BORDER,
            width=240,
        )
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(7, weight=1)

        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 14))
        brand.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            brand,
            text="GNX",
            text_color=PRIMARY_RED,
            font=ctk.CTkFont(size=28, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            brand,
            text="Production Studio",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        ctk.CTkLabel(
            brand,
            text="Desktop workflow for AI video production and Repliz scheduling",
            text_color=TEXT_MUTED,
            wraplength=190,
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(6, 0))

        nav = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav.grid(row=1, column=0, sticky="new", padx=12, pady=(0, 0))
        nav.grid_columnconfigure(0, weight=1)

        items = [
            ("dashboard", "Dashboard"),
            ("cloudinary", "Cloudinary"),
            ("repliz", "Repliz"),
            ("ai_settings", "AI Settings"),
            ("license", "License"),
            ("about", "About"),
        ]

        for idx, (key, label) in enumerate(items):
            btn = ctk.CTkButton(
                nav,
                text=label,
                height=42,
                corner_radius=12,
                fg_color=BTN_DARK,
                hover_color=BTN_DARK_HOVER,
                text_color=TEXT_PRIMARY,
                anchor="w",
                command=lambda k=key: self.show_page(k),
            )
            btn.grid(row=idx, column=0, sticky="ew", pady=5)
            self.nav_buttons[key] = btn

        footer = ctk.CTkFrame(
            self.sidebar,
            fg_color="#0d0d0d",
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
        )
        footer.grid(row=8, column=0, sticky="sew", padx=12, pady=12)
        footer.grid_columnconfigure(0, weight=1)

        self.sidebar_plan_label = ctk.CTkLabel(
            footer,
            text="Plan: BASIC",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.sidebar_plan_label.grid(row=0, column=0, sticky="w", padx=12, pady=(12, 4))

        self.sidebar_runtime_label = ctk.CTkLabel(
            footer,
            text="Runtime: Basic",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=12),
            wraplength=180,
            justify="left",
        )
        self.sidebar_runtime_label.grid(row=1, column=0, sticky="w", padx=12, pady=(0, 6))

        self.sidebar_meta_label = ctk.CTkLabel(
            footer,
            text="Accounts: 2 | Quality: 480p",
            text_color=TEXT_SOFT,
            font=ctk.CTkFont(size=11),
            wraplength=180,
            justify="left",
        )
        self.sidebar_meta_label.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 12))

    def _build_content(self):
        self.content = ctk.CTkFrame(self, fg_color=BLACK)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    def _build_pages(self):
        self.pages["dashboard"] = DashboardPage(self.content)
        self.pages["cloudinary"] = CloudinaryPage(self.content)
        self.pages["repliz"] = ReplizPage(self.content)
        self.pages["ai_settings"] = AISettingsPage(self.content)
        self.pages["license"] = LicensePage(self.content)
        self.pages["about"] = AboutPage(self.content)

        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")
            page.grid_remove()

    def show_page(self, key: str):
        if key not in self.pages:
            return

        if self.current_page is not None:
            self.pages[self.current_page].grid_remove()

        self.pages[key].grid()
        self.current_page = key

        self._update_nav_state()
        self.refresh_plan_status()

    def _update_nav_state(self):
        for key, btn in self.nav_buttons.items():
            if key == self.current_page:
                btn.configure(
                    fg_color=PRIMARY_RED,
                    hover_color=DEEP_RED,
                    text_color=TEXT_PRIMARY,
                )
            else:
                btn.configure(
                    fg_color=BTN_DARK,
                    hover_color=BTN_DARK_HOVER,
                    text_color=TEXT_PRIMARY,
                )

    def refresh_plan_status(self):
        try:
            caps = load_effective_capabilities() or {}
        except Exception:
            caps = {}

        licensed_plan = str(caps.get("plan", "BASIC")).upper()
        effective_plan = str(caps.get("effective_plan", licensed_plan)).upper()

        max_accounts = caps.get("max_social_accounts")
        accounts_text = "Unlimited" if max_accounts is None else str(max_accounts)

        qualities = caps.get("quality_options") or ["480p"]
        quality_text = ", ".join([str(q) for q in qualities])

        self.sidebar_plan_label.configure(text=f"Plan: {effective_plan}")

        runtime_text = f"Runtime: {effective_plan}"
        runtime_color = TEXT_MUTED

        if effective_plan == "BASIC" and licensed_plan != "BASIC" and not bool(caps.get("binding_valid", True)):
            runtime_text = "Runtime: Basic fallback (Repliz mismatch)"
            runtime_color = PRIMARY_RED
        elif bool(caps.get("blocked_for_social_limit", False)):
            runtime_text = "Runtime: Social account limit exceeded"
            runtime_color = PRIMARY_RED
        elif effective_plan == "PREMIUM":
            runtime_text = "Runtime: Premium active"
            runtime_color = TEXT_PRIMARY
        elif effective_plan == "BUSINESS":
            units = caps.get("business_charge_units_this_device", 0)
            runtime_text = f"Runtime: Business active | Units: {units}"
            runtime_color = TEXT_PRIMARY

        self.sidebar_runtime_label.configure(
            text=runtime_text,
            text_color=runtime_color,
        )

        self.sidebar_meta_label.configure(
            text=f"Accounts: {accounts_text} | Quality: {quality_text}"
        )