import os
import sys
import customtkinter as ctk

# --- 1. SYSTEM PATH CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# --- 2. CORE IMPORTS ---
from core.engine import Engine
from scripts.auto_debug import log_error, format_for_ai

try:
    from ui.pages.dashboard_v2 import DashboardV2 as DashboardPage
    from ui.pages.social_accounts_page import SocialAccountsPage
    from ui.pages.cloudinary_page import CloudinaryPage
    from ui.pages.ai_settings_page import AISettingsPage
    from ui.pages.calendar_page import CalendarPage
    from ui.pages.about_page import AboutPage
    from ui.pages.license_page import LicensePage
    print("✅ SUCCESS: All pages found and loaded!")
except Exception as e:
    print(f"❌ CRITICAL ERROR DURING IMPORT: {e}")
    sys.exit(1)

# --- 3. MAIN APPLICATION CLASS ---
class GNXStudio(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Window Setup
        self.title("GNX Studio v3 - AI Automation")
        self.geometry("1200x800")
        ctk.set_appearance_mode("dark")
        
        # Initialize Engine
        self.engine = Engine()
        
        # Grid Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        self._build_sidebar()
        
        # Container untuk halaman-halaman (dengan grid layout)
        self.container = ctk.CTkFrame(self, fg_color="#101010", corner_radius=0)
        self.container.grid(row=0, column=1, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(0, weight=1)
        
        self.pages = {}
        self.show_page("dashboard")

    def refresh_account_list(self):
        """Refresh social account list if the social page is loaded."""
        social_page = self.pages.get("social")
        if social_page and hasattr(social_page, "_refresh_ui"):
            social_page._refresh_ui()

    def _build_sidebar(self):
        """Membangun menu navigasi di sisi kiri"""
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color="#0a0a0a")
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="GNX\nSTUDIO", font=("Arial", 28, "bold"), 
                     text_color="#FF0000").pack(pady=35)

        # Navigasi
        menu_items = [
            ("📊 DASHBOARD", "dashboard"),
            ("👥 ACCOUNTS", "social"),
            ("☁️ CLOUD", "cloudinary"),
            ("🤖 AI CONFIG", "ai_settings"),
            ("📅 SCHEDULE", "calendar"),
            ("🔑 LICENSE", "license"),
            ("ℹ️ ABOUT", "about")
        ]

        for text, page_id in menu_items:
            btn = ctk.CTkButton(self.sidebar, text=text, anchor="w", height=45,
                                fg_color="transparent", hover_color="#222",
                                command=lambda p=page_id: self.show_page(p))
            btn.pack(fill="x", padx=15, pady=3)

    def show_page(self, page_id):
        """Logika perpindahan halaman (Lazy Loading)"""
        # Sembunyikan halaman yang sedang aktif
        for p in self.pages.values():
            p.grid_remove()
        
        # Buat halaman jika belum ada
        if page_id not in self.pages:
            try:
                if page_id == "dashboard": self.pages[page_id] = DashboardPage(self.container)
                elif page_id == "social": self.pages[page_id] = SocialAccountsPage(self.container)
                elif page_id == "cloudinary": self.pages[page_id] = CloudinaryPage(self.container)
                elif page_id == "ai_settings": self.pages[page_id] = AISettingsPage(self.container)
                elif page_id == "calendar": self.pages[page_id] = CalendarPage(self.container)
                elif page_id == "license": self.pages[page_id] = LicensePage(self.container)
                elif page_id == "about": self.pages[page_id] = AboutPage(self.container)
                
                # Grid setup untuk page agar fill container
                self.pages[page_id].grid(row=0, column=0, sticky="nsew")
            except Exception as e:
                print(f"❌ Error loading page {page_id}: {e}")
                return

        # Tampilkan halaman
        self.pages[page_id].grid()

# --- 4. RUN APPLICATION ---
from scripts.auto_debug import log_error, format_for_ai

if __name__ == "__main__":
    try:
        app = GNXStudio()
        app.mainloop()
    except Exception as e:
        log_error(e)

        print("\n===== COPY KE AI =====\n")
        print(format_for_ai())

