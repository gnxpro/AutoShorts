import customtkinter as ctk
from tkinter import messagebox
import os
import webbrowser
import cloudinary
import cloudinary.api
from core.theme_constants import BLACK, CARD, PRIMARY_RED, TEXT_PRIMARY, TEXT_MUTED, GREEN, BTN_DARK
from core.settings_store import load_config, save_config

class CloudinaryPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BLACK)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.raw_cfg = load_config()
        self.c_cfg = self.raw_cfg.get("cloudinary", {})
        self._build_ui()

    def _build_ui(self):
        # --- MAIN CONTAINER ---
        self.main_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_scroll.pack(fill="both", expand=True, padx=40, pady=20)

        # Header
        ctk.CTkLabel(self.main_scroll, text="Cloudinary Integration", font=("Arial", 28, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w")
        ctk.CTkLabel(self.main_scroll, text="Connect your Cloudinary account to enable the automatic rendering system.", font=("Arial", 14), text_color=TEXT_MUTED).pack(anchor="w", pady=(5, 20))

        # ==========================================
        # 📘 TUTORIAL SECTION FOR MEMBERS (GLOBAL LANGUAGE)
        # ==========================================
        tutorial_frame = ctk.CTkFrame(self.main_scroll, fg_color="#1a1a2e", corner_radius=10, border_width=1, border_color="#3a3a5e")
        tutorial_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(tutorial_frame, text="ℹ️ How to Get Your API Key (Free)", font=("Arial", 14, "bold"), text_color="#66b3ff").pack(anchor="w", padx=20, pady=(15, 5))
        
        tutorial_text = (
            "1. Click the 'Open Cloudinary Website' button below to open your browser.\n"
            "2. Create a new account for free (Sign Up).\n"
            "3. After successfully logging in, go to the 'Dashboard' or 'Programmable Media' menu.\n"
            "4. Find the 'Product Environment Credentials' section.\n"
            "5. Copy your Cloud Name, API Key, and API Secret, then Paste them into the boxes below."
        )
        ctk.CTkLabel(tutorial_frame, text=tutorial_text, font=("Arial", 12), text_color="#cccccc", justify="left").pack(anchor="w", padx=20, pady=(0, 15))
        
        # Open Web Button
        ctk.CTkButton(tutorial_frame, text="🌐 Open Cloudinary Website", width=180, fg_color="#0066cc", hover_color="#004c99",
                      command=lambda: webbrowser.open("https://cloudinary.com/users/register/free")).pack(anchor="w", padx=20, pady=(0, 20))

        # ==========================================
        # ⚙️ API INPUT SECTION
        # ==========================================
        card = ctk.CTkFrame(self.main_scroll, fg_color=CARD, corner_radius=10, border_width=1, border_color="#222")
        card.pack(fill="x")

        # --- Cloud Name ---
        ctk.CTkLabel(card, text="Cloud Name", font=("Arial", 12, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(20, 5))
        self.cname_entry = ctk.CTkEntry(card, width=400, fg_color="#111", border_color="#333")
        self.cname_entry.pack(anchor="w", padx=20)
        if self.c_cfg.get("cloud_name"):
            self.cname_entry.insert(0, self.c_cfg.get("cloud_name"))

        # --- API Key ---
        ctk.CTkLabel(card, text="API Key", font=("Arial", 12, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(15, 5))
        self.apikey_entry = ctk.CTkEntry(card, width=400, fg_color="#111", border_color="#333")
        self.apikey_entry.pack(anchor="w", padx=20)
        if self.c_cfg.get("api_key"):
            self.apikey_entry.insert(0, self.c_cfg.get("api_key"))

        # --- API Secret ---
        ctk.CTkLabel(card, text="API Secret", font=("Arial", 12, "bold"), text_color=TEXT_PRIMARY).pack(anchor="w", padx=20, pady=(15, 5))
        self.secret_entry = ctk.CTkEntry(card, width=400, fg_color="#111", border_color="#333", show="•")
        self.secret_entry.pack(anchor="w", padx=20)
        if self.c_cfg.get("api_secret"):
            self.secret_entry.insert(0, self.c_cfg.get("api_secret"))

        # --- Action Buttons ---
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=30)

        ctk.CTkButton(btn_frame, text="SAVE SETTINGS", width=140, fg_color=PRIMARY_RED, hover_color="#cc0000",
                      command=self._save_settings).pack(side="left", padx=(0, 15))
                      
        ctk.CTkButton(btn_frame, text="TEST CONNECTION", width=140, fg_color="#2b2b2b", hover_color="#444", text_color="#fff",
                      command=self._test_connection).pack(side="left")

    # ==========================================
    # 🧠 FUNCTION LOGIC
    # ==========================================
    def _save_settings(self):
        cname = self.cname_entry.get().strip()
        apikey = self.apikey_entry.get().strip()
        secret = self.secret_entry.get().strip()

        if not cname or not apikey or not secret:
            messagebox.showwarning("Incomplete", "All Cloudinary fields must be filled!")
            return

        self.raw_cfg["cloudinary"] = {
            "cloud_name": cname,
            "api_key": apikey,
            "api_secret": secret
        }
        save_config(self.raw_cfg)
        messagebox.showinfo("Saved", "Settings saved successfully! Please click Test Connection to verify.")

    def _test_connection(self):
        cname = self.cname_entry.get().strip()
        apikey = self.apikey_entry.get().strip()
        secret = self.secret_entry.get().strip()

        if not cname or not apikey or not secret:
            messagebox.showwarning("Warning", "Please fill in all fields before testing the connection!")
            return

        try:
            cloudinary.config(
                cloud_name=cname,
                api_key=apikey,
                api_secret=secret,
                secure=True
            )
            response = cloudinary.api.ping()
            
            if response.get("status") == "ok":
                messagebox.showinfo("Connection Success!", "✅ API Valid!\nSuccessfully connected to your Cloudinary account.")
            else:
                messagebox.showerror("Connection Failed", "❌ Failed to connect. Please check your API Key and Secret.")
                
        except Exception as e:
            messagebox.showerror("Authentication Error", f"❌ Access denied!\nMake sure your Cloud Name and API Keys are correct.\n\nDetails: {str(e)}")