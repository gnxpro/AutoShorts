import os
import sys
import json
from pathlib import Path

import customtkinter as ctk
from tkinter import messagebox
from PIL import Image

from core.services.repliz_service import ReplizService
from core.license_manager import apply_repliz_runtime_state
from core.theme_constants import (
    PRIMARY_RED, PRIMARY_ORANGE,
    GREEN,
    BLACK, CARD_SOFT, ROW, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, TEXT_SOFT,
    BADGE_DARK, BADGE_SUCCESS, BADGE_ERROR,
)
from core.ui_helpers import make_card


class ReplizPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BLACK)

        self.repliz = ReplizService()
        self.accounts = []
        self.vars = {}
        self.icon_cache = {}
        self.queue_vars = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()
        self.load_saved_credentials()

    # ---------------------------------------------------------
    # Paths / config
    # ---------------------------------------------------------

    def _appdata_dir(self) -> Path:
        base = os.getenv("LOCALAPPDATA", "").strip()
        if not base:
            base = str(Path.home() / "AppData" / "Local")
        p = Path(base) / "GNX_PRODUCTION"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _config_path(self) -> Path:
        return self._appdata_dir() / "repliz.json"

    def _icons_base_dir(self) -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent / "assets" / "icons"
        return Path(__file__).resolve().parent.parent / "assets" / "icons"

    def _queue_dir(self) -> Path:
        p = Path.home() / "Documents" / "GNX Production" / "Outputs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------

    def _build_ui(self):
        outer = ctk.CTkScrollableFrame(self, fg_color=BLACK)
        outer.grid(row=0, column=0, sticky="nsew", padx=30, pady=22)
        outer.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Repliz Enterprise Scheduler",
            font=ctk.CTkFont(size=30, weight="bold"),
            text_color=TEXT_PRIMARY,
        ).grid(row=0, column=0, sticky="w")

        self.plan_label = ctk.CTkLabel(
            header,
            text="Plan Support: Basic / Premium / Business",
            text_color=PRIMARY_ORANGE,
        )
        self.plan_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.connect_badge = ctk.CTkLabel(
            header,
            text="NOT CONNECTED",
            text_color=TEXT_PRIMARY,
            fg_color=BADGE_DARK,
            corner_radius=12,
            padx=14,
            pady=7,
        )
        self.connect_badge.grid(row=0, column=1, rowspan=2, sticky="e")

        connect = make_card(
            outer,
            "API Connection",
            "Use your own Repliz account. The Default Account ID becomes the main accountId for scheduling and license lock validation.",
        )
        connect.grid(row=1, column=0, sticky="ew", pady=10)

        self.base_url = ctk.CTkEntry(connect, text_color=TEXT_PRIMARY, height=38)
        self.base_url.pack(fill="x", padx=22, pady=(0, 10))
        self.base_url.insert(0, "https://api.repliz.com/public")

        self.access_key_entry = ctk.CTkEntry(
            connect,
            placeholder_text="Access Key",
            text_color=TEXT_PRIMARY,
            height=38,
        )
        self.access_key_entry.pack(fill="x", padx=22, pady=(0, 10))

        self.secret_key_entry = ctk.CTkEntry(
            connect,
            placeholder_text="Secret Key",
            text_color=TEXT_PRIMARY,
            show="*",
            height=38,
        )
        self.secret_key_entry.pack(fill="x", padx=22, pady=(0, 10))

        self.default_account_id_entry = ctk.CTkEntry(
            connect,
            placeholder_text="Default Account ID",
            text_color=TEXT_PRIMARY,
            height=38,
        )
        self.default_account_id_entry.pack(fill="x", padx=22, pady=(0, 10))

        self.connect_btn = ctk.CTkButton(
            connect,
            text="Connect Repliz",
            fg_color=PRIMARY_RED,
            hover_color="#7a0d1a",
            text_color=TEXT_PRIMARY,
            height=42,
            command=self.connect,
        )
        self.connect_btn.pack(fill="x", padx=22, pady=(0, 16))

        info = make_card(
            outer,
            "Saved Location",
            "Your personal Repliz connection is stored per Windows user in AppData.",
        )
        info.grid(row=2, column=0, sticky="ew", pady=10)

        self.path_label = ctk.CTkLabel(
            info,
            text=f"Config Path: {self._config_path()}",
            text_color=TEXT_SOFT,
            wraplength=920,
            justify="left",
        )
        self.path_label.pack(anchor="w", padx=22, pady=(0, 8))

        self.summary_label = ctk.CTkLabel(
            info,
            text="Summary: -",
            text_color=TEXT_MUTED,
            wraplength=920,
            justify="left",
        )
        self.summary_label.pack(anchor="w", padx=22, pady=(0, 16))

        body = ctk.CTkFrame(outer, fg_color="transparent")
        body.grid(row=3, column=0, sticky="ew", pady=10)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=1)

        accounts_card = make_card(
            body,
            "Connected Social Accounts",
            "If account loading succeeds, tick an account to fill the Default Account ID automatically.",
        )
        accounts_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        self.accounts_scroll = ctk.CTkScrollableFrame(
            accounts_card,
            fg_color="#060606",
            height=360,
            corner_radius=12,
        )
        self.accounts_scroll.pack(fill="both", expand=True, padx=22, pady=(0, 16))

        queue_card = make_card(
            body,
            "Video Queue",
            "Ready-to-send videos from the output folder.",
        )
        queue_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        queue_btn_row = ctk.CTkFrame(queue_card, fg_color="transparent")
        queue_btn_row.pack(fill="x", padx=22, pady=(0, 10))
        queue_btn_row.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            queue_btn_row,
            text="Refresh Queue",
            fg_color=PRIMARY_ORANGE,
            hover_color="#c76600",
            text_color=TEXT_PRIMARY,
            height=38,
            command=self.load_video_queue,
        ).grid(row=0, column=0, padx=(0, 6), sticky="ew")

        ctk.CTkButton(
            queue_btn_row,
            text="Delete Selected",
            fg_color=PRIMARY_RED,
            hover_color="#7a0d1a",
            text_color=TEXT_PRIMARY,
            height=38,
            command=self.delete_selected_queue,
        ).grid(row=0, column=1, padx=6, sticky="ew")

        ctk.CTkButton(
            queue_btn_row,
            text="Open Output Folder",
            fg_color=GREEN,
            hover_color="#1a6b31",
            text_color=TEXT_PRIMARY,
            height=38,
            command=self.open_output_folder,
        ).grid(row=0, column=2, padx=(6, 0), sticky="ew")

        self.queue_scroll = ctk.CTkScrollableFrame(
            queue_card,
            fg_color="#060606",
            height=360,
            corner_radius=12,
        )
        self.queue_scroll.pack(fill="both", expand=True, padx=22, pady=(0, 16))

        sched = make_card(
            outer,
            "Scheduler Settings",
            "The primary Account ID is taken from the Default Account ID field.",
        )
        sched.grid(row=4, column=0, sticky="ew", pady=10)

        row = ctk.CTkFrame(
            sched,
            fg_color=CARD_SOFT,
            corner_radius=12,
            border_width=1,
            border_color=BORDER
        )
        row.pack(fill="x", padx=22, pady=(0, 16))
        row.grid_columnconfigure((1, 3), weight=1)

        ctk.CTkLabel(
            row,
            text="Videos / Day",
            text_color=TEXT_SOFT
        ).grid(row=0, column=0, sticky="w", padx=(12, 8), pady=12)

        self.videos_per_day = ctk.CTkEntry(row, width=100, height=34)
        self.videos_per_day.insert(0, "5")
        self.videos_per_day.grid(row=0, column=1, sticky="ew", pady=12)

        ctk.CTkLabel(
            row,
            text="Days",
            text_color=TEXT_SOFT
        ).grid(row=0, column=2, sticky="w", padx=(16, 8), pady=12)

        self.days_total = ctk.CTkEntry(row, width=100, height=34)
        self.days_total.insert(0, "30")
        self.days_total.grid(row=0, column=3, sticky="ew", pady=12)

        ctk.CTkButton(
            sched,
            text="Generate Schedule",
            fg_color=PRIMARY_ORANGE,
            hover_color="#c76600",
            text_color=TEXT_PRIMARY,
            height=42,
            command=self.generate_schedule,
        ).pack(fill="x", padx=22, pady=(0, 16))

        self.load_video_queue()

    # ---------------------------------------------------------
    # Connection
    # ---------------------------------------------------------

    def connect(self):
        try:
            base = self.base_url.get().strip()
            access_key = self.access_key_entry.get().strip()
            secret_key = self.secret_key_entry.get().strip()
            account_id = self.default_account_id_entry.get().strip()

            self.repliz.set_credentials(
                base_url=base,
                access_key=access_key,
                secret_key=secret_key,
            )
            self.repliz.validate_keys()

            self.connect_btn.configure(text="CONNECTED", fg_color=GREEN)
            self.connect_badge.configure(text="CONNECTED", fg_color=BADGE_SUCCESS)

            self.save_credentials(base, access_key, secret_key, account_id)
            self._apply_runtime_env(base, access_key, secret_key, account_id)
            self.load_accounts()

            apply_repliz_runtime_state(
                repliz_user_id=None,
                repliz_primary_account_id=account_id,
                social_count=len(self.accounts) if self.accounts else 0,
            )

            self._notify_shell_refresh()

            messagebox.showinfo("Repliz", "Connected successfully.")

        except Exception as e:
            self.connect_badge.configure(text="ERROR", fg_color=BADGE_ERROR)
            messagebox.showerror("Repliz Error", str(e))

    def _notify_shell_refresh(self):
        try:
            parent = self.master
            while parent is not None:
                if hasattr(parent, "refresh_plan_status"):
                    parent.refresh_plan_status()
                parent = getattr(parent, "master", None)
        except Exception:
            pass

    def _apply_runtime_env(self, base: str, access_key: str, secret_key: str, account_id: str):
        os.environ["REPLIZ_BASE_URL"] = base
        os.environ["REPLIZ_ACCESS_KEY"] = access_key
        os.environ["REPLIZ_SECRET_KEY"] = secret_key
        os.environ["REPLIZ_ACCOUNT_ID"] = account_id

    # ---------------------------------------------------------
    # Accounts
    # ---------------------------------------------------------

    def load_accounts(self):
        try:
            data = self.repliz.get_social_accounts()
            accounts = data.get("docs", []) if isinstance(data, dict) else data
            self.accounts = accounts or []
        except Exception:
            self.accounts = []

        for w in self.accounts_scroll.winfo_children():
            w.destroy()

        self.vars.clear()

        if not self.accounts:
            ctk.CTkLabel(
                self.accounts_scroll,
                text="Unable to load accounts automatically. Fill Default Account ID manually.",
                text_color=TEXT_MUTED
            ).pack(anchor="w", padx=10, pady=10)
            self._refresh_summary()
            return

        for acc in self.accounts:
            acc_id = str(acc.get("accountId") or acc.get("_id") or acc.get("id") or "")
            name = acc.get("name", "Account")
            username = acc.get("username", "")
            acc_type = acc.get("type", "")

            label = f"{name}"
            if username:
                label += f" (@{username})"
            if acc_type:
                label += f" [{acc_type}]"
            if acc_id:
                label += f" | Account ID: {acc_id}"

            row = ctk.CTkFrame(self.accounts_scroll, fg_color=ROW, corner_radius=10)
            row.pack(fill="x", pady=4, padx=4)

            icon = self.get_social_icon(acc)

            label_kwargs = {
                "master": row,
                "text": "  " + label,
                "text_color": TEXT_PRIMARY,
                "wraplength": 420,
                "justify": "left",
            }

            if icon is not None:
                lbl = ctk.CTkLabel(
                    **label_kwargs,
                    image=icon,
                    compound="left",
                )
            else:
                lbl = ctk.CTkLabel(**label_kwargs)

            lbl.pack(side="left", padx=10, pady=10)

            var = ctk.BooleanVar()
            self.vars[acc_id] = var

            ctk.CTkCheckBox(
                row,
                text="",
                variable=var,
                command=lambda aid=acc_id: self._set_default_account_id(aid),
            ).pack(side="right", padx=10)

        self._refresh_summary()

    def _set_default_account_id(self, account_id: str):
        self.default_account_id_entry.delete(0, "end")
        self.default_account_id_entry.insert(0, account_id)
        os.environ["REPLIZ_ACCOUNT_ID"] = account_id
        self._refresh_summary()

    def get_social_icon(self, account):
        provider = str(account.get("provider") or account.get("platform") or account.get("type") or "").lower()
        name = str(account.get("name") or "").lower()
        username = str(account.get("username") or "").lower()
        hay = f"{provider} {name} {username}"

        if "youtube" in hay:
            icon_name = "youtube"
        elif "instagram" in hay:
            icon_name = "instagram"
        elif "facebook" in hay:
            icon_name = "facebook"
        elif "tiktok" in hay:
            icon_name = "tiktok"
        elif "linkedin" in hay:
            icon_name = "linkedin"
        elif "twitter" in hay or " x " in f" {hay} ":
            icon_name = "twitter"
        elif "threads" in hay:
            icon_name = "threads"
        else:
            icon_name = "default"

        if icon_name in self.icon_cache:
            return self.icon_cache[icon_name]

        try:
            base = self._icons_base_dir()
            path = base / f"{icon_name}.png"
            fallback = base / "default.png"

            if path.exists():
                img = Image.open(path)
            elif fallback.exists():
                img = Image.open(fallback)
            else:
                return None

            icon_img = ctk.CTkImage(img, size=(22, 22))
            self.icon_cache[icon_name] = icon_img
            return icon_img
        except Exception:
            return None

    # ---------------------------------------------------------
    # Queue
    # ---------------------------------------------------------

    def load_video_queue(self):
        folder = self._queue_dir()

        for w in self.queue_scroll.winfo_children():
            w.destroy()

        self.queue_vars.clear()

        files = []
        try:
            files = sorted(
                [f for f in folder.iterdir() if f.is_file() and f.suffix.lower() == ".mp4"],
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
        except Exception:
            files = []

        if not files:
            ctk.CTkLabel(
                self.queue_scroll,
                text="No video files found.",
                text_color=TEXT_MUTED
            ).pack(anchor="w", padx=10, pady=10)
            return

        for f in files:
            row = ctk.CTkFrame(self.queue_scroll, fg_color=ROW, corner_radius=10)
            row.pack(fill="x", pady=4, padx=4)

            var = ctk.BooleanVar(value=False)
            self.queue_vars[str(f)] = var

            ctk.CTkCheckBox(
                row,
                text="",
                variable=var,
            ).pack(side="right", padx=10)

            ctk.CTkLabel(
                row,
                text=f.name,
                text_color=TEXT_PRIMARY,
                wraplength=300,
                justify="left",
            ).pack(side="left", padx=10, pady=10)

    def delete_selected_queue(self):
        selected = [Path(p) for p, var in self.queue_vars.items() if bool(var.get())]

        if not selected:
            messagebox.showwarning("Queue", "Select at least one video to delete.")
            return

        if not messagebox.askyesno("Delete Queue", f"Delete {len(selected)} selected video(s)?"):
            return

        deleted = 0
        failed = 0

        for p in selected:
            try:
                if p.exists():
                    p.unlink()
                    deleted += 1
            except Exception:
                failed += 1

        self.load_video_queue()

        if failed == 0:
            messagebox.showinfo("Queue", f"Deleted {deleted} video(s).")
        else:
            messagebox.showwarning("Queue", f"Deleted {deleted} video(s), failed {failed}.")

    def open_output_folder(self):
        try:
            path = self._queue_dir().resolve()
            if os.name == "nt":
                os.startfile(str(path))
            else:
                import subprocess
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as e:
            messagebox.showerror("Open Folder Error", str(e))

    # ---------------------------------------------------------
    # Selection / schedule
    # ---------------------------------------------------------

    def get_selected_account_ids(self):
        manual = self.default_account_id_entry.get().strip()
        if manual:
            return [manual]

        selected = [acc_id for acc_id, var in self.vars.items() if bool(var.get())]
        return selected

    def generate_schedule(self):
        try:
            v = int(self.videos_per_day.get())
            d = int(self.days_total.get())
        except Exception:
            messagebox.showerror("Scheduler", "Videos / Day and Days must be numeric.")
            return

        total = v * d
        selected = self.get_selected_account_ids()

        messagebox.showinfo(
            "Scheduler",
            f"{total} videos will be scheduled.\nPrimary Account ID: {selected[0] if selected else '-'}"
        )

    # ---------------------------------------------------------
    # Save / load config
    # ---------------------------------------------------------

    def save_credentials(self, base, access_key, secret_key, account_id):
        payload = {
            "base": base,
            "access_key": access_key,
            "secret_key": secret_key,
            "account_id": account_id,
            "repliz_primary_account_id": account_id,
        }
        self._config_path().write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._refresh_summary(payload)

    def load_saved_credentials(self):
        path = self._config_path()
        self.path_label.configure(text=f"Config Path: {path}")

        if not path.exists():
            self.summary_label.configure(text="Summary: No saved Repliz config found.")
            return

        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            self.summary_label.configure(text=f"Summary: Failed to read Repliz config: {e}")
            return

        base = data.get("base", "")
        access_key = data.get("access_key", "")
        secret_key = data.get("secret_key", "")
        account_id = data.get("account_id", "") or data.get("repliz_primary_account_id", "")

        self.base_url.delete(0, "end")
        self.base_url.insert(0, base or "https://api.repliz.com/public")

        self.access_key_entry.delete(0, "end")
        self.access_key_entry.insert(0, access_key)

        self.secret_key_entry.delete(0, "end")
        self.secret_key_entry.insert(0, secret_key)

        self.default_account_id_entry.delete(0, "end")
        self.default_account_id_entry.insert(0, account_id)

        if base and access_key and secret_key:
            self.repliz.set_credentials(
                base_url=base,
                access_key=access_key,
                secret_key=secret_key,
            )
            self._apply_runtime_env(base, access_key, secret_key, account_id)

        self._refresh_summary(data)

    def _mask(self, value: str) -> str:
        value = value or ""
        if len(value) <= 8:
            return "*" * len(value)
        return value[:4] + "*" * (len(value) - 8) + value[-4:]

    def _refresh_summary(self, data=None):
        if data is None:
            data = {
                "base": self.base_url.get().strip(),
                "access_key": self.access_key_entry.get().strip(),
                "secret_key": self.secret_key_entry.get().strip(),
                "account_id": self.default_account_id_entry.get().strip(),
            }

        self.path_label.configure(text=f"Config Path: {self._config_path()}")
        self.summary_label.configure(
            text=(
                f"Summary: base={data.get('base','')} | "
                f"access_key={self._mask(str(data.get('access_key','')))} | "
                f"secret_key={self._mask(str(data.get('secret_key','')))} | "
                f"account_id={data.get('account_id','') or data.get('repliz_primary_account_id','') or '-'}"
            )
        )