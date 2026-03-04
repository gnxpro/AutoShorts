import os
from pathlib import Path
import customtkinter as ctk

from pages.dashboard_page import DashboardPage
from pages.monitoring_page import MonitoringPage
from pages.worker_control_page import WorkerControlPage
from pages.settings_page import SettingsPage
from pages.repliz_page import ReplizPage
from pages.cloudinary_page import CloudinaryPage
from pages.ai_settings_page import AISettingsPage
from pages.about_page import AboutPage

# admin page (optional)
try:
    from pages.admin_page import AdminPage
    ADMIN_PAGE_OK = True
except Exception:
    ADMIN_PAGE_OK = False


PRIMARY_RED = "#b11226"
SIDEBAR_BG = "#0c0c0c"
MAIN_BG = "#070707"
CARD_BG = "#111111"


def _appdata_dir() -> Path:
    base = os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    d = Path(base) / "GNX_PRODUCTION"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _is_admin_enabled() -> bool:
    if os.getenv("GNX_ADMIN", "").strip() == "1":
        return True
    flag = _appdata_dir() / "admin.flag"
    return flag.exists()


class AppShell(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=MAIN_BG)
        self.pack(fill="both", expand=True)

        self.master = master

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.admin_enabled = _is_admin_enabled() and ADMIN_PAGE_OK

        self._build_sidebar()
        self._build_pages()

        self._show_page("dashboard")

    # =====================================================

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=220, fg_color=SIDEBAR_BG)
        sidebar.grid(row=0, column=0, sticky="ns")
        sidebar.grid_propagate(False)

        buttons = [
            ("Dashboard", "dashboard"),
            ("Monitoring", "monitoring"),
            ("Worker Control", "worker"),
            ("AI Settings", "ai_settings"),
            ("Cloudinary", "cloudinary"),
            ("Repliz", "repliz"),
            ("About", "about"),
        ]

        if self.admin_enabled:
            buttons.append(("Admin", "admin"))

        for text, key in buttons:
            btn = ctk.CTkButton(
                sidebar,
                text=text,
                fg_color=CARD_BG,
                hover_color=PRIMARY_RED,
                command=lambda k=key: self._show_page(k)
            )
            btn.pack(fill="x", padx=15, pady=8)

    # =====================================================

    def _build_pages(self):
        container = ctk.CTkFrame(self, fg_color=MAIN_BG)
        container.grid(row=0, column=1, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self.pages = {
            "dashboard": DashboardPage(container),
            "monitoring": MonitoringPage(container),
            "worker": WorkerControlPage(container),
            "ai_settings": AISettingsPage(container),
            "cloudinary": CloudinaryPage(container),
            "repliz": ReplizPage(container),
            "about": AboutPage(container),
        }

        if self.admin_enabled:
            self.pages["admin"] = AdminPage(container)

        for page in self.pages.values():
            page.grid(row=0, column=0, sticky="nsew")

    # =====================================================

    def _show_page(self, name):
        self.pages[name].tkraise()