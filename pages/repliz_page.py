import os
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta, timezone

import customtkinter as ctk
from tkinter import messagebox

from core.services.repliz_service import ReplizService, ReplizAPIError, ReplizAuthError


# optional avatar support
try:
    from PIL import Image  # type: ignore
    PIL_OK = True
except Exception:
    PIL_OK = False


PRIMARY_RED = "#b11226"
GREEN = "#1f8a3b"
GREEN_HOVER = "#196f2f"

BLACK = "#000000"
CARD = "#111111"
CARD2 = "#0b0b0b"
ROW_BG = "#151515"

TEXT_PRIMARY = "#EDEDED"
TEXT_MUTED = "#B8B8B8"

MAX_ACCOUNTS = 100


def _appdata_dir() -> Path:
    base = os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    d = Path(base) / "GNX_PRODUCTION"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _settings_path() -> Path:
    return _appdata_dir() / "repliz_settings.json"


def _avatar_cache_dir() -> Path:
    d = _appdata_dir() / "cache_repliz_avatars"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _tz_local():
    return datetime.now().astimezone().tzinfo


def _iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _parse_lines(text: str) -> List[str]:
    out = []
    for ln in (text or "").splitlines():
        ln = ln.strip()
        if ln:
            out.append(ln)
    return out


def _platform_tag(platform: str) -> str:
    p = (platform or "").lower()
    if "tiktok" in p:
        return "TIKTOK"
    if "instagram" in p or "reels" in p:
        return "INSTAGRAM"
    if "youtube" in p or "yt" in p:
        return "YOUTUBE"
    if "threads" in p:
        return "THREADS"
    return (platform or "SOCIAL").upper()


def _is_short_platform(platform: str) -> bool:
    p = (platform or "").lower()
    return ("tiktok" in p) or ("youtube" in p) or ("short" in p)


def _is_long_platform(platform: str) -> bool:
    p = (platform or "").lower()
    return ("instagram" in p) or ("reels" in p)


class ReplizPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BLACK)

        self.engine = master.master.master.engine
        self.repliz = ReplizService()

        self._accounts: List[Dict[str, Any]] = []
        self._vars: Dict[str, Any] = {}        # id -> BooleanVar
        self._img_refs: Dict[str, Any] = {}    # keep CTkImage alive
        self._saved_selected: set[str] = set()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        self._build_ui()
        self._load_saved()

    # =========================================================
    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=BLACK)
        header.grid(row=0, column=0, sticky="ew", padx=40, pady=(30, 10))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Repliz Settings",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=28, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="Connect → otomatis muncul akun sosmed yang sudah di-auth di web Repliz. Centang akun yang mau di-schedule.",
            text_color=TEXT_MUTED,
            wraplength=980,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        # CONNECT CARD
        connect = ctk.CTkFrame(self, fg_color=CARD, corner_radius=16)
        connect.grid(row=1, column=0, sticky="ew", padx=40, pady=(10, 14))
        connect.grid_columnconfigure(0, weight=1)

        self.base_url = ctk.CTkEntry(connect, placeholder_text="Base URL Public (contoh: https://api.repliz.com/public)", text_color=TEXT_PRIMARY)
        self.base_url.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 6))
        self.base_url.insert(0, "https://api.repliz.com/public")

        self.access_key = ctk.CTkEntry(connect, placeholder_text="Access Key (dari menu Public API Repliz)", text_color=TEXT_PRIMARY)
        self.access_key.grid(row=1, column=0, sticky="ew", padx=18, pady=6)

        self.secret_key = ctk.CTkEntry(connect, placeholder_text="Secret Key", text_color=TEXT_PRIMARY, show="*")
        self.secret_key.grid(row=2, column=0, sticky="ew", padx=18, pady=6)

        row = ctk.CTkFrame(connect, fg_color="transparent")
        row.grid(row=3, column=0, sticky="ew", padx=18, pady=(10, 14))
        row.grid_columnconfigure((0, 1, 2), weight=1)

        self.connect_btn = ctk.CTkButton(
            row, text="Connect",
            fg_color=PRIMARY_RED, hover_color="#7a0d1a", text_color=TEXT_PRIMARY,
            command=self._connect,
        )
        self.connect_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        ctk.CTkButton(
            row, text="Save",
            fg_color="#222222", hover_color="#333333", text_color=TEXT_PRIMARY,
            command=self._save_settings,
        ).grid(row=0, column=1, padx=10, sticky="ew")

        ctk.CTkButton(
            row, text="Apply",
            fg_color="#222222", hover_color="#333333", text_color=TEXT_PRIMARY,
            command=self._apply_to_engine,
        ).grid(row=0, column=2, padx=(10, 0), sticky="ew")

        # ACCOUNTS (compact)
        accounts = ctk.CTkFrame(self, fg_color=CARD2, corner_radius=16)
        accounts.grid(row=2, column=0, sticky="ew", padx=40, pady=(0, 14))
        accounts.grid_columnconfigure(0, weight=1)
        accounts.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(accounts, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 8))
        top.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(top, text="Connected Accounts", text_color=TEXT_PRIMARY,
                     font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w")

        self.search = ctk.CTkEntry(top, placeholder_text="Search nama/username (optional)", text_color=TEXT_PRIMARY)
        self.search.grid(row=0, column=1, padx=10, sticky="ew")

        ctk.CTkButton(top, text="Refresh", fg_color="#222222", hover_color="#333333", text_color=TEXT_PRIMARY,
                      command=self._refresh_accounts).grid(row=0, column=2, padx=10, sticky="ew")

        ctk.CTkButton(top, text="Select All", fg_color="#222222", hover_color="#333333", text_color=TEXT_PRIMARY,
                      command=self._select_all).grid(row=0, column=3, sticky="ew")

        self.info = ctk.CTkLabel(accounts, text="Klik Connect untuk memuat akun.", text_color=TEXT_MUTED, wraplength=980, justify="left")
        self.info.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 8))

        self.acc_scroll = ctk.CTkScrollableFrame(accounts, fg_color="#060606", corner_radius=12, height=260)
        self.acc_scroll.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 14))
        self.acc_scroll.grid_columnconfigure(0, weight=1)

        # AUTO SCHEDULER
        sched = ctk.CTkFrame(self, fg_color=CARD2, corner_radius=16)
        sched.grid(row=3, column=0, sticky="nsew", padx=40, pady=(0, 30))
        sched.grid_columnconfigure(0, weight=1)
        sched.grid_rowconfigure(3, weight=1)

        ctk.CTkLabel(sched, text="AUTO SCHEDULER", text_color=TEXT_PRIMARY,
                     font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 6))

        ctk.CTkLabel(
            sched,
            text="Short URLs (30–60 detik) untuk TikTok + YouTube Shorts. Long URLs (1–3 menit) untuk Instagram/Reels.\n"
                 "Paste URL video (Cloudinary) per baris. Scheduler otomatis sebar ke 30 hari, 5/hari (bisa diubah).",
            text_color=TEXT_MUTED,
            wraplength=980,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 10))

        form = ctk.CTkFrame(sched, fg_color="transparent")
        form.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 10))
        form.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.days_entry = ctk.CTkEntry(form, placeholder_text="Days (contoh: 30)", text_color=TEXT_PRIMARY)
        self.days_entry.insert(0, "30")
        self.days_entry.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        self.per_day_entry = ctk.CTkEntry(form, placeholder_text="Posts/day (contoh: 5)", text_color=TEXT_PRIMARY)
        self.per_day_entry.insert(0, "5")
        self.per_day_entry.grid(row=0, column=1, padx=10, sticky="ew")

        self.start_time_entry = ctk.CTkEntry(form, placeholder_text="Start HH:MM (09:00)", text_color=TEXT_PRIMARY)
        self.start_time_entry.insert(0, "09:00")
        self.start_time_entry.grid(row=0, column=2, padx=10, sticky="ew")

        self.end_time_entry = ctk.CTkEntry(form, placeholder_text="End HH:MM (21:00)", text_color=TEXT_PRIMARY)
        self.end_time_entry.insert(0, "21:00")
        self.end_time_entry.grid(row=0, column=3, padx=(10, 0), sticky="ew")

        self.randomize_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(sched, text="Randomize time (biar natural)", text_color=TEXT_PRIMARY, variable=self.randomize_var)\
            .grid(row=4, column=0, sticky="w", padx=18, pady=(0, 8))

        urls_wrap = ctk.CTkFrame(sched, fg_color="transparent")
        urls_wrap.grid(row=5, column=0, sticky="nsew", padx=18, pady=(0, 12))
        urls_wrap.grid_columnconfigure((0, 1), weight=1)

        left = ctk.CTkFrame(urls_wrap, fg_color="#0b0b0b", corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(left, text="Short URLs (30–60s)", text_color=TEXT_PRIMARY).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 6))
        self.short_box = ctk.CTkTextbox(left, height=160, fg_color="#060606", text_color=TEXT_PRIMARY)
        self.short_box.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        right = ctk.CTkFrame(urls_wrap, fg_color="#0b0b0b", corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(right, text="Long URLs (1–3m)", text_color=TEXT_PRIMARY).grid(row=0, column=0, sticky="w", padx=12, pady=(10, 6))
        self.long_box = ctk.CTkTextbox(right, height=160, fg_color="#060606", text_color=TEXT_PRIMARY)
        self.long_box.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        btns = ctk.CTkFrame(sched, fg_color="transparent")
        btns.grid(row=6, column=0, sticky="ew", padx=18, pady=(0, 18))
        btns.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(btns, text="Load from latest job", fg_color="#222222", hover_color="#333333", text_color=TEXT_PRIMARY,
                      command=self._load_latest_job_urls).grid(row=0, column=0, padx=(0, 10), sticky="ew")

        ctk.CTkButton(btns, text="Preview schedule count", fg_color="#222222", hover_color="#333333", text_color=TEXT_PRIMARY,
                      command=self._preview_schedule).grid(row=0, column=1, padx=10, sticky="ew")

        ctk.CTkButton(btns, text="Create Auto Schedule", fg_color=PRIMARY_RED, hover_color="#7a0d1a", text_color=TEXT_PRIMARY,
                      command=self._create_auto_schedule).grid(row=0, column=2, padx=(10, 0), sticky="ew")

    # =========================================================
    # persistence
    def _load_saved(self):
        p = _settings_path()
        if not p.exists():
            return
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if data.get("base_url"):
                self.base_url.delete(0, "end")
                self.base_url.insert(0, data["base_url"])
            if data.get("access_key"):
                self.access_key.delete(0, "end")
                self.access_key.insert(0, data["access_key"])
            if data.get("secret_key"):
                self.secret_key.delete(0, "end")
                self.secret_key.insert(0, data["secret_key"])

            self._saved_selected = set([str(x) for x in (data.get("selected_account_ids") or []) if x])

            # restore scheduler inputs
            if data.get("scheduler"):
                sch = data["scheduler"]
                self.days_entry.delete(0, "end"); self.days_entry.insert(0, str(sch.get("days", "30")))
                self.per_day_entry.delete(0, "end"); self.per_day_entry.insert(0, str(sch.get("per_day", "5")))
                self.start_time_entry.delete(0, "end"); self.start_time_entry.insert(0, str(sch.get("start_time", "09:00")))
                self.end_time_entry.delete(0, "end"); self.end_time_entry.insert(0, str(sch.get("end_time", "21:00")))
                self.randomize_var.set(bool(sch.get("randomize", True)))

        except Exception:
            pass

    def _save_settings(self):
        try:
            data = {
                "base_url": self.base_url.get().strip(),
                "access_key": self.access_key.get().strip(),
                "secret_key": self.secret_key.get().strip(),
                "selected_account_ids": self._selected_ids(),
                "scheduler": {
                    "days": int(self.days_entry.get().strip() or "30"),
                    "per_day": int(self.per_day_entry.get().strip() or "5"),
                    "start_time": self.start_time_entry.get().strip() or "09:00",
                    "end_time": self.end_time_entry.get().strip() or "21:00",
                    "randomize": bool(self.randomize_var.get()),
                }
            }
            _settings_path().write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            messagebox.showinfo("Saved", "Repliz settings saved.")
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def _apply_to_engine(self):
        ids = self._selected_ids()
        if len(ids) > MAX_ACCOUNTS:
            messagebox.showerror("Limit", f"Maks {MAX_ACCOUNTS} akun. Kamu pilih {len(ids)}.")
            return
        setattr(self.engine, "selected_account_ids", ids)
        setattr(self.engine, "repliz_schedule_enabled", True)
        messagebox.showinfo("Applied", f"Applied {len(ids)} account(s) untuk schedule.")

    # =========================================================
    # accounts
    def _connect(self):
        try:
            base_url = self.base_url.get().strip()
            access = self.access_key.get().strip()
            secret = self.secret_key.get().strip()
            if not base_url or not access or not secret:
                raise ValueError("Base URL, Access Key, dan Secret Key wajib diisi.")

            self.repliz.set_credentials(base_url=base_url, access_key=access, secret_key=secret)

            # set ke engine service juga
            if hasattr(self.engine, "repliz_service") and hasattr(self.engine.repliz_service, "set_credentials"):
                self.engine.repliz_service.set_credentials(base_url=base_url, access_key=access, secret_key=secret)

            # validate
            self.repliz.validate_keys()

            self.connect_btn.configure(text="Connected", fg_color=GREEN, hover_color=GREEN_HOVER)
            self._refresh_accounts()

        except (ReplizAuthError, ReplizAPIError) as e:
            self.connect_btn.configure(text="Connect", fg_color=PRIMARY_RED, hover_color="#7a0d1a")
            messagebox.showerror("Repliz Error", str(e))
        except Exception as e:
            self.connect_btn.configure(text="Connect", fg_color=PRIMARY_RED, hover_color="#7a0d1a")
            messagebox.showerror("Error", str(e))

    def _refresh_accounts(self):
        try:
            search = self.search.get().strip()
            self._accounts = self.repliz.get_social_accounts(page=1, limit=100, search=search)
            self._render_account_rows(self._accounts)
            self.info.configure(text=f"{len(self._accounts)} akun loaded. Centang untuk schedule.")
        except Exception as e:
            messagebox.showerror("Accounts Error", str(e))

    def _render_account_rows(self, accounts: List[Dict[str, Any]]):
        for w in self.acc_scroll.winfo_children():
            w.destroy()
        self._vars.clear()
        self._img_refs.clear()

        for acc in accounts:
            acc_id = acc.get("id")
            if not acc_id:
                continue
            acc_id = str(acc_id)

            platform = _platform_tag(acc.get("platform", ""))
            name = (acc.get("name") or "").strip() or "Unnamed"
            username = (acc.get("username") or "").strip()
            pic = (acc.get("picture") or "").strip()

            row = ctk.CTkFrame(self.acc_scroll, fg_color=ROW_BG, corner_radius=12)
            row.pack(fill="x", padx=10, pady=6)

            # avatar (optional)
            avatar_lbl = ctk.CTkLabel(row, text="", width=34, height=34)
            avatar_lbl.pack(side="left", padx=(10, 8), pady=8)

            if PIL_OK and pic:
                img = self._get_avatar_image(pic, acc_id)
                if img is not None:
                    avatar_lbl.configure(image=img)
                    self._img_refs[acc_id] = img
                else:
                    avatar_lbl.configure(text=platform[:2], text_color=TEXT_PRIMARY)
            else:
                avatar_lbl.configure(text=platform[:2], text_color=TEXT_PRIMARY)

            # text
            txt = f"{platform}  •  {name}"
            if username:
                txt += f"   (@{username})"

            ctk.CTkLabel(row, text=txt, text_color=TEXT_PRIMARY, anchor="w").pack(side="left", fill="x", expand=True, padx=8)

            # checkbox (small)
            var = ctk.BooleanVar(value=(acc_id in self._saved_selected))
            self._vars[acc_id] = var
            ctk.CTkCheckBox(row, text="", width=24, variable=var).pack(side="right", padx=(0, 12))

    def _get_avatar_image(self, url: str, acc_id: str):
        try:
            cache = _avatar_cache_dir() / f"{acc_id}.png"
            if not cache.exists():
                # download
                import urllib.request
                with urllib.request.urlopen(url, timeout=15) as resp:
                    data = resp.read()
                cache.write_bytes(data)

            img = Image.open(cache).convert("RGBA")
            img = img.resize((30, 30))
            return ctk.CTkImage(light_image=img, dark_image=img, size=(30, 30))
        except Exception:
            return None

    def _selected_ids(self) -> List[str]:
        return [acc_id for acc_id, var in self._vars.items() if bool(var.get())]

    def _select_all(self):
        for var in self._vars.values():
            var.set(True)

    # =========================================================
    # auto scheduler
    def _load_latest_job_urls(self):
        """
        Ambil URL upload dari outputs/jobs/latest.json (kalau ada)
        dan masukkan ke Short URLs.
        """
        try:
            latest = Path("outputs") / "jobs" / "latest.json"
            if not latest.exists():
                messagebox.showinfo("Info", "Belum ada outputs/jobs/latest.json. Jalankan 1 job dulu.")
                return
            data = json.loads(latest.read_text(encoding="utf-8"))
            # coba cari uploads di structure umum
            uploads = data.get("uploads") or data.get("data", {}).get("uploads") or {}
            urls = []
            if isinstance(uploads, dict):
                for v in uploads.values():
                    if isinstance(v, dict):
                        u = v.get("url") or v.get("secure_url") or v.get("cloudinary_url")
                        if u:
                            urls.append(str(u))
                    elif isinstance(v, str):
                        urls.append(v)

            if not urls:
                messagebox.showinfo("Info", "Tidak menemukan URL upload di latest.json.")
                return

            self.short_box.delete("1.0", "end")
            self.short_box.insert("1.0", "\n".join(urls))
            messagebox.showinfo("Loaded", f"Loaded {len(urls)} URL(s) ke Short URLs.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _preview_schedule(self):
        try:
            ids = self._selected_ids()
            days = int(self.days_entry.get().strip() or "30")
            per_day = int(self.per_day_entry.get().strip() or "5")
            total_slots = max(0, days * per_day)

            short_urls = _parse_lines(self.short_box.get("1.0", "end"))
            long_urls = _parse_lines(self.long_box.get("1.0", "end"))

            msg = (
                f"Akun dipilih: {len(ids)}\n"
                f"Slot schedule: {total_slots} ({days} hari x {per_day}/hari)\n"
                f"Short URLs: {len(short_urls)} | Long URLs: {len(long_urls)}\n"
                f"Total schedule request (perkiraan): akun x slot = {len(ids)} x {total_slots} = {len(ids) * total_slots}\n"
            )
            messagebox.showinfo("Preview", msg)
        except Exception as e:
            messagebox.showerror("Preview Error", str(e))

    def _build_times(self, days: int, per_day: int, start_hm: str, end_hm: str, randomize: bool) -> List[datetime]:
        tz = _tz_local()
        now_local = datetime.now(tz)
        start_h, start_m = [int(x) for x in start_hm.split(":")]
        end_h, end_m = [int(x) for x in end_hm.split(":")]

        times: List[datetime] = []
        for d in range(days):
            day = (now_local + timedelta(days=d)).date()
            start_dt = datetime(day.year, day.month, day.day, start_h, start_m, tzinfo=tz)
            end_dt = datetime(day.year, day.month, day.day, end_h, end_m, tzinfo=tz)
            if end_dt <= start_dt:
                end_dt = start_dt + timedelta(hours=12)

            window = (end_dt - start_dt).total_seconds()
            step = window / max(1, per_day)

            for i in range(per_day):
                base = start_dt + timedelta(seconds=step * (i + 0.5))
                if randomize:
                    jitter = random.uniform(-step * 0.25, step * 0.25)
                    base = base + timedelta(seconds=jitter)
                times.append(base)

        return times

    def _create_auto_schedule(self):
        """
        Untuk sekarang: schedule langsung ke Repliz dari list URL.
        - TikTok/YT Shorts pakai short_urls
        - IG/Reels pakai long_urls
        """
        try:
            selected_accounts = [a for a in self._accounts if str(a.get("id")) in set(self._selected_ids())]
            if not selected_accounts:
                raise ValueError("Pilih minimal 1 akun (centang).")

            days = int(self.days_entry.get().strip() or "30")
            per_day = int(self.per_day_entry.get().strip() or "5")
            start_hm = self.start_time_entry.get().strip() or "09:00"
            end_hm = self.end_time_entry.get().strip() or "21:00"
            randomize = bool(self.randomize_var.get())

            short_urls = _parse_lines(self.short_box.get("1.0", "end"))
            long_urls = _parse_lines(self.long_box.get("1.0", "end"))

            if not short_urls and not long_urls:
                raise ValueError("Isi minimal 1 URL di Short atau Long URLs.")

            slots = self._build_times(days, per_day, start_hm, end_hm, randomize)
            if not slots:
                raise ValueError("Slot schedule kosong.")

            title = "GNX Auto Schedule"
            desc = "Scheduled by GNX AI Production Studio"

            # Untuk menghindari spam: schedule per akun mengikuti slot yang sama.
            # URL akan diambil berurutan, kalau habis -> stop (tidak repeat) supaya tidak posting video yang sama berkali-kali.
            for acc in selected_accounts:
                acc_id = str(acc["id"])
                platform = str(acc.get("platform") or "")
                use_long = _is_long_platform(platform)
                pool = long_urls if use_long else short_urls
                if not pool:
                    # fallback
                    pool = short_urls or long_urls

                max_posts = min(len(pool), len(slots))
                if max_posts == 0:
                    continue

                for i in range(max_posts):
                    when = _iso_z(slots[i])
                    url = pool[i]
                    self.repliz.schedule_one_video(
                        video_url=url,
                        account_id=acc_id,
                        title=title,
                        description=desc,
                        schedule_at_iso_z=when,
                    )

            messagebox.showinfo("Done", "Auto schedule created. Cek di Repliz → Konten Terjadwal.")
        except (ReplizAuthError, ReplizAPIError) as e:
            messagebox.showerror("Repliz Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", str(e))