import customtkinter as ctk
import threading
import os
import sys
import json
import time
import requests
from pathlib import Path
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime
from tkinter import messagebox

from core.theme_constants import BLACK, CARD, PRIMARY_RED, BTN_DARK
from services.youtube_auth import start_auth
from core.tiktok_auth import TikTokAuth
from core.logger import log_info, log_error


class SocialAccountsPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BLACK)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        if getattr(sys, "frozen", False):
            self.base_dir = Path(sys.executable).parent
        else:
            self.base_dir = Path(os.getcwd())

        self.db_path = self.base_dir / "data" / "tokens" / "social_accounts.json"
        self.member_config_path = self.base_dir / "config" / "gnx_member.json"
        self.member_id = self._load_or_ask_member_id()

        self.api_session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.api_session.mount("https://", adapter)

        self._build_ui()

    def _default_db(self):
        return {
            "FACEBOOK": [],
            "INSTAGRAM": [],
            "YOUTUBE": [],
            "TIKTOK": []
        }

    def _load_or_ask_member_id(self):
        if not self.member_config_path.parent.exists():
            self.member_config_path.parent.mkdir(parents=True, exist_ok=True)

        if self.member_config_path.exists():
            try:
                with open(self.member_config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("member_id"):
                        return data["member_id"]
            except Exception:
                pass

        dialog = ctk.CTkInputDialog(
            text="Enter your GNX Username / Email:",
            title="GNX Member Activation"
        )
        user_input = dialog.get_input()
        if not user_input or user_input.strip() == "":
            user_input = f"GNX_GUEST_{int(time.time())}"

        with open(self.member_config_path, "w", encoding="utf-8") as f:
            json.dump({"member_id": user_input.strip()}, f, indent=4)

        return user_input.strip()

    def _load_db(self):
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        if self.db_path.exists():
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        db = self._default_db()
                        for key in db.keys():
                            value = data.get(key, [])
                            db[key] = value if isinstance(value, list) else []
                        return db
            except Exception as e:
                log_error(f"Load DB Error: {e}")

        return self._default_db()

    def _save_db(self, db):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(db, f, indent=4, ensure_ascii=False)

    def _build_ui(self):
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=30, pady=(30, 10))

        ctk.CTkLabel(
            self.header,
            text="SOCIAL ACCOUNTS MANAGER",
            font=("Arial", 22, "bold"),
            text_color=PRIMARY_RED
        ).pack(side="left")

        self.btn_refresh = ctk.CTkButton(
            self.header,
            text="REFRESH",
            width=100,
            fg_color="#333",
            hover_color=PRIMARY_RED,
            command=self._refresh_ui
        )
        self.btn_refresh.pack(side="right", padx=10)

        self.login_panel = ctk.CTkFrame(self, fg_color=CARD, corner_radius=15)
        self.login_panel.pack(fill="x", padx=30, pady=10)

        self.plat_var = ctk.StringVar(value="YouTube")
        ctk.CTkOptionMenu(
            self.login_panel,
            values=["YouTube", "TikTok"],
            variable=self.plat_var,
            fg_color=BTN_DARK
        ).pack(side="left", padx=20, pady=20)

        self.btn_login = ctk.CTkButton(
            self.login_panel,
            text="+ ADD NEW ACCOUNT",
            fg_color=PRIMARY_RED,
            font=("Arial", 12, "bold"),
            command=self._on_login_click
        )
        self.btn_login.pack(side="right", padx=20)

        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=30, pady=10)

        self._refresh_ui()

    def _on_login_click(self):
        platform = self.plat_var.get()
        self.btn_login.configure(state="disabled", text="PROCESSING...")
        threading.Thread(target=self._auth_process, args=(platform,), daemon=True).start()

    def _auth_process(self, platform):
        try:
            if platform == "YouTube":
                account = start_auth(self.member_id)
                self._save_account_to_db(
                    platform="YOUTUBE",
                    user=account["user"],
                    token_path=account["token_path"],
                    channel_id=account["channel_id"]
                )
                self.after(0, lambda: messagebox.showinfo(
                    "Success",
                    f"Akun YouTube '{account['user']}' berhasil ditambahkan."
                ))
            elif platform == "TikTok":
                tk = TikTokAuth()
                tk.open_browser()
                log_info("TikTok Browser Opened. Waiting for token...")
                success, name = tk.finalize_login()
                if success:
                    self._save_account_to_db(
                        platform="TIKTOK",
                        user=name,
                        token_path=str(self.base_dir / "data" / "tokens" / "tiktok_token.json")
                    )
                    self.after(0, self._refresh_ui)
                    if hasattr(self.master.master, "refresh_account_list"):
                        self.after(0, self.master.master.refresh_account_list)
        except Exception as e:
            log_error(f"Auth Error: {str(e)}")
            self.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.after(0, lambda: self.btn_login.configure(
                state="normal",
                text="+ ADD NEW ACCOUNT"
            ))

    def _save_account_to_db(self, platform, user, token_path, channel_id=None):
        db = self._load_db()
        platform = platform.upper()

        if platform not in db:
            db[platform] = []

        for acc in db[platform]:
            if acc.get("user") == user or (
                channel_id and acc.get("channel_id") == channel_id
            ):
                acc["status"] = "ACTIVE"
                acc["token_path"] = token_path
                acc["channel_id"] = channel_id
                acc["member_id"] = self.member_id
                acc["last_login"] = datetime.now().strftime("%Y-%m-%d")
                self._save_db(db)
                return

        db[platform].append({
            "user": user,
            "status": "ACTIVE",
            "token_path": token_path,
            "channel_id": channel_id,
            "member_id": self.member_id,
            "last_login": datetime.now().strftime("%Y-%m-%d")
        })
        self._save_db(db)

    def _refresh_ui(self):
        for w in self.scroll_frame.winfo_children():
            w.destroy()

        db = self._load_db()
        for platform, accounts in db.items():
            if not accounts:
                continue
            for i, account in enumerate(accounts):
                self._create_account_card(platform, account, i)

    def _create_account_card(self, platform, account, index):
        card = ctk.CTkFrame(self.scroll_frame, fg_color=CARD, height=60)
        card.pack(fill="x", pady=5)

        label_text = f"{platform} | {account.get('user', '-')}"
        if account.get("status"):
            label_text += f" | {account['status']}"

        ctk.CTkLabel(
            card,
            text=label_text,
            font=("Arial", 13, "bold")
        ).pack(side="left", padx=20)

        btn_logout = ctk.CTkButton(
            card,
            text="LOGOUT",
            width=80,
            fg_color="#333",
            hover_color=PRIMARY_RED,
            command=lambda p=platform, idx=index: self._on_logout(p, idx)
        )
        btn_logout.pack(side="right", padx=15)

    def _on_logout(self, platform, index):
        if messagebox.askyesno("Confirm", f"Logout from {platform} account?"):
            db = self._load_db()
            db[platform.upper()].pop(index)
            self._save_db(db)
            self._refresh_ui()
            log_info(f"SUCCESS: Logged out from {platform} account.")