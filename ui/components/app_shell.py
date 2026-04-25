import customtkinter as ctk

from core.theme_constants import (
    PRIMARY_RED, DEEP_RED, BLACK, CARD, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, TEXT_SOFT, BTN_DARK, BTN_DARK_HOVER,
)
from core.license_manager import load_effective_capabilities

# Impor Halaman
from ui.pages.dashboard_v2 import DashboardV2 as DashboardPage
from ui.pages.calendar_page import CalendarPage
from ui.pages.social_accounts_page import SocialAccountsPage
from ui.pages.cloudinary_page import CloudinaryPage
from ui.pages.ai_settings_page import AISettingsPage
from ui.pages.about_page import AboutPage
from ui.pages.license_page import LicensePage

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

        # Refresh plan sebelum menampilkan halaman pertama
        self.refresh_plan_status()
        self.show_page("dashboard")

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, fg_color=CARD, corner_radius=0, border_width=1, border_color=BORDER, width=240)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(8, weight=1)

        # Branding
        brand = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 14))
        
        ctk.CTkLabel(brand, text="GNX", text_color=PRIMARY_RED, font=ctk.CTkFont(size=28, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(brand, text="Production Studio", text_color=TEXT_PRIMARY, font=ctk.CTkFont(size=16, weight="bold")).grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Navigasi Menu
        nav = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav.grid(row=1, column=0, sticky="new", padx=12, pady=(0, 0))
        nav.grid_columnconfigure(0, weight=1)

        items = [
            ("dashboard", "Dashboard"),
            ("cloudinary", "Cloud Storage"),
            ("social", "Social Accounts"),
            ("calendar", "Schedule & Calendar"),
            ("ai_settings", "AI Configuration"),
            ("license", "License & Billing"),
            ("about", "About GNX"),
        ]

        for idx, (key, label) in enumerate(items):
            btn = ctk.CTkButton(
                nav, text=label, height=42, corner_radius=12,
                fg_color=BTN_DARK, hover_color=BTN_DARK_HOVER,
                text_color=TEXT_PRIMARY, anchor="w",
                command=lambda k=key: self.show_page(k),
            )
            btn.grid(row=idx, column=0, sticky="ew", pady=5)
            self.nav_buttons[key] = btn

        # Footer Info (Realtime License Status)
        footer = ctk.CTkFrame(self.sidebar, fg_color="#0d0d0d", corner_radius=14, border_width=1, border_color=BORDER)
        footer.grid(row=9, column=0, sticky="sew", padx=12, pady=12)
        
        self.sidebar_plan_label = ctk.CTkLabel(footer, text="Plan: LOADING...", text_color=TEXT_PRIMARY, font=ctk.CTkFont(size=13, weight="bold"))
        self.sidebar_plan_label.grid(row=0, column=0, sticky="w", padx=16, pady=12)

    def _build_content(self):
        self.content = ctk.CTkFrame(self, fg_color=BLACK)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.grid_rowconfigure(0, weight=1)
        self.content.grid_columnconfigure(0, weight=1)

    def _build_pages(self):
        self.pages["dashboard"] = DashboardPage(self.content)
        self.pages["cloudinary"] = CloudinaryPage(self.content)
        self.pages["social"] = SocialAccountsPage(self.content)
        self.pages["calendar"] = CalendarPage(self.content)
        self.pages["ai_settings"] = AISettingsPage(self.content)
        self.pages["license"] = LicensePage(self.content)
        self.pages["about"] = AboutPage(self.content)

        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")
            page.grid_remove()

    def show_page(self, key: str):
        if key not in self.pages: return
        if self.current_page is not None: self.pages[self.current_page].grid_remove()
        self.pages[key].grid()
        self.current_page = key
        self._update_nav_state()
        if key == "dashboard": self.refresh_plan_status() # Auto-refresh saat buka dashboard

    def _update_nav_state(self):
        for key, btn in self.nav_buttons.items():
            if key == self.current_page: btn.configure(fg_color=PRIMARY_RED, hover_color=DEEP_RED)
            else: btn.configure(fg_color=BTN_DARK, hover_color=BTN_DARK_HOVER)

    def refresh_plan_status(self):
        try:
            caps = load_effective_capabilities() or {}
            plan = str(caps.get("effective_plan", "BUSINESS")).upper() # Memaksa baca backend
            self.sidebar_plan_label.configure(text=f"Plan: {plan}")
            
            # Update Dashboard badge if exists
            if "dashboard" in self.pages and hasattr(self.pages["dashboard"], "badge_lbl"):
                self.pages["dashboard"].badge_lbl.configure(text=f"{plan} MEMBER")
        except Exception:
            pass