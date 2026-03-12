import os
import json
import queue
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog, messagebox

from core.theme_constants import (
    PRIMARY_RED, DEEP_RED,
    BLACK, CARD, CARD_SOFT, CARD_DARK, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, TEXT_SOFT,
    BTN_DARK, BTN_DARK_HOVER,
)
from core.ui_helpers import make_card, make_stat_card


def _safe_open_path(p: str):
    try:
        if not p:
            return
        if os.name == "nt":
            os.startfile(p)
        else:
            import subprocess
            subprocess.Popen(["xdg-open", p])
    except Exception as e:
        messagebox.showerror("Open Error", str(e))


def _find_engine(widget):
    w = widget
    for _ in range(12):
        if hasattr(w, "engine"):
            return w.engine
        w = getattr(w, "master", None)
        if w is None:
            break
    return None


class DashboardPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BLACK)

        self.engine = _find_engine(master)
        if self.engine is None:
            raise RuntimeError("Engine not found. Make sure AppShell sets app.engine before building pages.")

        self._q = queue.Queue()
        self._last_persist_dir = None
        self.advanced_visible = False

        self.cloudinary_enabled = ctk.BooleanVar(value=True)
        self.cloudinary_mode = ctk.StringVar(value="manual")

        self.repliz_enabled = ctk.BooleanVar(value=True)
        self.repliz_mode = ctk.StringVar(value="manual")

        self.face_center_enabled = ctk.BooleanVar(value=True)
        self.face_center_mode = ctk.StringVar(value="best_face_center")
        self.face_center_strategy = ctk.StringVar(value="podcast_dual_speaker")
        self.face_debug_overlay = ctk.BooleanVar(value=False)

        self.duration_mode = ctk.StringVar(value="auto")
        self.portrait_min_seconds = ctk.StringVar(value="30")
        self.portrait_max_seconds = ctk.StringVar(value="120")
        self.landscape_max_seconds = ctk.StringVar(value="180")

        self.caps = self._read_capabilities()
        self.quality_profile = ctk.StringVar(value=self.caps.get("default_quality", "480p"))

        self.subtitle_mode = ctk.StringVar(value="auto")
        self.hook_mode = ctk.StringVar(value="auto")
        self.niche_mode = ctk.StringVar(value="auto")
        self.hashtag_mode = ctk.StringVar(value="auto")

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()
        self._apply_capabilities_to_ui()
        self._on_duration_mode_change()

        self.after(120, self._poll_queue)

    def _documents_root(self) -> Path:
        env = os.getenv("GNX_OUTPUT_ROOT", "").strip()
        if env:
            p = Path(env)
            p.mkdir(parents=True, exist_ok=True)
            return p

        root = Path.home() / "Documents" / "GNX Production"
        root.mkdir(parents=True, exist_ok=True)
        return root

    def _outputs_dir(self) -> Path:
        p = self._documents_root() / "Outputs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _jobs_dir(self) -> Path:
        p = self._documents_root() / "Jobs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _temp_dir(self) -> Path:
        p = self._documents_root() / "Temp"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _usage_file(self) -> Path:
        return self._jobs_dir() / "usage.json"

    def _read_capabilities(self) -> dict:
        try:
            if hasattr(self.engine, "get_capabilities"):
                caps = self.engine.get_capabilities() or {}
            else:
                caps = {}
        except Exception:
            caps = {}

        effective_plan = str(caps.get("effective_plan") or caps.get("plan") or "BASIC").upper()

        caps.setdefault("plan", effective_plan)
        caps.setdefault("effective_plan", effective_plan)
        caps.setdefault("allow_youtube", True)
        caps.setdefault("allow_ai", True)
        caps.setdefault("allow_schedule", True)
        caps.setdefault("max_accounts", caps.get("max_social_accounts", 2 if effective_plan == "BASIC" else 100))
        caps.setdefault("daily_video_limit", 2 if effective_plan == "BASIC" else 8)
        caps.setdefault("monthly_video_limit", 60 if effective_plan == "BASIC" else 240)
        caps.setdefault("quality_options", ["480p"])
        caps.setdefault("default_quality", "480p")
        caps.setdefault("binding_valid", True)
        caps.setdefault("blocked_for_social_limit", False)
        caps.setdefault("business_charge_units_this_device", 0)
        return caps

    def _read_usage_stats(self):
        p = self._usage_file()
        if not p.exists():
            return 0, 0

        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return 0, 0

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        today_key = now.strftime("%Y-%m-%d")
        days = data.get("days", {})

        daily = int(days.get(today_key, 0))
        rolling = 0
        for day_str, count in days.items():
            try:
                dt = datetime.strptime(day_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                age = (now - dt).days
                if 0 <= age < 30:
                    rolling += int(count)
            except Exception:
                continue
        return daily, rolling

    def _refresh_capabilities(self):
        self.caps = self._read_capabilities()

        current_quality = self.quality_profile.get().strip()
        allowed = list(self.caps.get("quality_options", ["480p"]))
        if current_quality not in allowed:
            self.quality_profile.set(self.caps.get("default_quality", allowed[0]))

        self.quality_menu.configure(values=allowed)
        self._apply_capabilities_to_ui()
        self._log(
            f"[PLAN] {self.caps.get('effective_plan','-')} | "
            f"Daily={self.caps.get('daily_video_limit')} | "
            f"30Days={self.caps.get('monthly_video_limit')} | "
            f"Accounts={self.caps.get('max_accounts')} | "
            f"Quality={', '.join(self.caps.get('quality_options', []))}"
        )

    def _apply_capabilities_to_ui(self):
        licensed_plan = str(self.caps.get("plan", "BASIC")).upper()
        effective_plan = str(self.caps.get("effective_plan", licensed_plan)).upper()

        allow_youtube = bool(self.caps.get("allow_youtube", True))
        allow_ai = bool(self.caps.get("allow_ai", True))
        allow_schedule = bool(self.caps.get("allow_schedule", True))
        binding_valid = bool(self.caps.get("binding_valid", True))
        blocked_for_social_limit = bool(self.caps.get("blocked_for_social_limit", False))

        daily_used, rolling_used = self._read_usage_stats()
        self.stat_daily_value.configure(text=f"{daily_used}/{self.caps.get('daily_video_limit')}")
        self.stat_month_value.configure(text=f"{rolling_used}/{self.caps.get('monthly_video_limit')}")
        accounts_text = self.caps.get("max_accounts")
        self.stat_account_value.configure(text="Unlimited" if accounts_text is None else str(accounts_text))

        self.footer_plan_label.configure(text=f"Plan: {effective_plan}")

        runtime_text = f"Runtime: {effective_plan}"
        runtime_color = TEXT_MUTED

        if effective_plan == "BASIC" and licensed_plan != "BASIC" and not binding_valid:
            runtime_text = "Runtime: Basic fallback (Repliz mismatch)"
            runtime_color = PRIMARY_RED
        elif blocked_for_social_limit:
            runtime_text = "Runtime: Social account limit exceeded"
            runtime_color = PRIMARY_RED
        elif effective_plan == "BUSINESS":
            units = self.caps.get("business_charge_units_this_device", 0)
            runtime_text = f"Runtime: Business | Device Units: {units}"
            runtime_color = TEXT_PRIMARY
        elif effective_plan == "PREMIUM":
            runtime_text = "Runtime: Premium active"
            runtime_color = TEXT_PRIMARY

        self.footer_runtime_label.configure(text=runtime_text, text_color=runtime_color)

        if not allow_youtube:
            self.source_hint.configure(text="This plan is offline-only. YouTube input is disabled. Use Offline Video only.")
        else:
            self.source_hint.configure(text="Choose one source only: YouTube URL or Offline Video.")

        if not allow_ai:
            for cb in (self.subtitle_cb, self.hook_cb, self.niche_cb, self.hashtag_cb):
                cb.deselect()
                cb.configure(state="disabled")
            for menu in (self.subtitle_mode_menu, self.hook_mode_menu, self.niche_mode_menu, self.hashtag_mode_menu):
                menu.configure(state="disabled")
            self.advanced_btn.configure(state="disabled", text="Advanced AI Control (disabled by plan)")
            if self.advanced_visible:
                self.advanced_frame.pack_forget()
                self.advanced_visible = False
        else:
            for cb in (self.subtitle_cb, self.hook_cb, self.niche_cb, self.hashtag_cb):
                cb.configure(state="normal")
            for menu in (self.subtitle_mode_menu, self.hook_mode_menu, self.niche_mode_menu, self.hashtag_mode_menu):
                menu.configure(state="normal")
            self.advanced_btn.configure(state="normal", text="Advanced AI Control")

        if not allow_schedule:
            self.repliz_mode.set("manual")
            self.repliz_mode_menu.configure(state="disabled")
            self.repliz_cb.deselect()
            self.repliz_cb.configure(state="disabled")
        else:
            self.repliz_mode_menu.configure(state="normal")
            self.repliz_cb.configure(state="normal")

        self.quality_menu.configure(values=list(self.caps.get("quality_options", ["480p"])))
        if self.quality_profile.get() not in self.caps.get("quality_options", []):
            self.quality_profile.set(self.caps.get("default_quality", "480p"))

    def _build_ai_tool_row(self, parent, label_text, mode_var):
        row = ctk.CTkFrame(parent, fg_color=CARD_SOFT, corner_radius=12, border_width=1, border_color=BORDER)
        row.pack(fill="x", padx=22, pady=6)
        row.grid_columnconfigure(1, weight=1)

        cb = ctk.CTkCheckBox(row, text=label_text, text_color=TEXT_PRIMARY)
        cb.grid(row=0, column=0, sticky="w", padx=12, pady=10)

        menu = ctk.CTkOptionMenu(
            row,
            values=["auto", "manual_prompt"],
            variable=mode_var,
            fg_color=BTN_DARK,
            button_color="#2a2a2a",
            button_hover_color="#3a3a3a",
            text_color=TEXT_PRIMARY,
            dropdown_text_color=TEXT_PRIMARY,
            width=170,
        )
        menu.grid(row=0, column=1, sticky="e", padx=12, pady=10)
        return cb, menu

    def _prompt_box(self, parent, title, example_text: str):
        ctk.CTkLabel(parent, text=title, text_color=PRIMARY_RED).pack(anchor="w", padx=22, pady=(10, 6))
        box = ctk.CTkTextbox(
            parent,
            height=78,
            fg_color="#111111",
            text_color=TEXT_PRIMARY,
            border_width=1,
            border_color=BORDER,
        )
        box.pack(fill="x", padx=22, pady=(0, 10))
        box.insert("1.0", example_text)
        return box

    def _build_ui(self):
        left_wrap = ctk.CTkFrame(self, fg_color=BLACK)
        left_wrap.grid(row=0, column=0, sticky="nsew", padx=28, pady=20)
        left_wrap.grid_rowconfigure(0, weight=1)
        left_wrap.grid_columnconfigure(0, weight=1)

        left = ctk.CTkScrollableFrame(left_wrap, fg_color=BLACK)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(left, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="GNX Production Workspace",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=30, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self.source_hint = ctk.CTkLabel(left, text="", text_color=TEXT_MUTED, wraplength=700, justify="left")
        self.source_hint.grid(row=1, column=0, sticky="w", pady=(0, 12))

        stats_wrap = ctk.CTkFrame(left, fg_color="transparent")
        stats_wrap.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        for i in range(3):
            stats_wrap.grid_columnconfigure(i, weight=1)

        stat2, self.stat_daily_value = make_stat_card(stats_wrap, "Daily Usage")
        stat2.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        stat3, self.stat_month_value = make_stat_card(stats_wrap, "30 Days Usage")
        stat3.grid(row=0, column=1, sticky="ew", padx=8)

        stat4, self.stat_account_value = make_stat_card(stats_wrap, "Max Accounts")
        stat4.grid(row=0, column=2, sticky="ew", padx=(8, 0))

        top_card = make_card(left, "VIDEO SOURCE", "Choose the source video, output format, and target quality.")
        top_card.grid(row=3, column=0, sticky="ew", pady=10)

        self.youtube_entry = ctk.CTkEntry(
            top_card,
            placeholder_text="Example: youtube.com/watch?v=xxxxxxxxxxx",
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_MUTED,
            height=38,
        )
        self.youtube_entry.pack(fill="x", padx=22, pady=(0, 10))

        row = ctk.CTkFrame(top_card, fg_color="transparent")
        row.pack(fill="x", padx=22, pady=(0, 10))

        self.offline_entry = ctk.CTkEntry(
            row,
            placeholder_text=r"Example Offline: C:\Users\...\Videos\sample.mp4",
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_MUTED,
            height=38,
        )
        self.offline_entry.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            row,
            text="Browse",
            width=110,
            height=38,
            fg_color=PRIMARY_RED,
            hover_color=DEEP_RED,
            text_color=TEXT_PRIMARY,
            command=self._browse_file,
        ).pack(side="left", padx=10)

        options_row = ctk.CTkFrame(top_card, fg_color="transparent")
        options_row.pack(fill="x", padx=22, pady=(0, 12))

        ctk.CTkLabel(options_row, text="Format Mode:", text_color=TEXT_SOFT).pack(side="left")
        self.format_mode = ctk.StringVar(value="both")
        self.format_menu = ctk.CTkOptionMenu(
            options_row,
            values=["portrait", "landscape", "both"],
            variable=self.format_mode,
            fg_color=BTN_DARK,
            button_color="#2a2a2a",
            button_hover_color="#3a3a3a",
            text_color=TEXT_PRIMARY,
            dropdown_text_color=TEXT_PRIMARY,
            width=150,
        )
        self.format_menu.pack(side="left", padx=10)

        ctk.CTkLabel(options_row, text="Quality:", text_color=TEXT_SOFT).pack(side="left", padx=(20, 0))
        self.quality_menu = ctk.CTkOptionMenu(
            options_row,
            values=list(self.caps.get("quality_options", ["480p"])),
            variable=self.quality_profile,
            fg_color=BTN_DARK,
            button_color="#2a2a2a",
            button_hover_color="#3a3a3a",
            text_color=TEXT_PRIMARY,
            dropdown_text_color=TEXT_PRIMARY,
            width=150,
        )
        self.quality_menu.pack(side="left", padx=10)

        action = ctk.CTkFrame(top_card, fg_color="transparent")
        action.pack(fill="x", padx=22, pady=(0, 14))
        action.grid_columnconfigure((0, 1, 2), weight=1)

        self.generate_btn = ctk.CTkButton(
            action,
            text="Generate Video",
            height=46,
            fg_color=PRIMARY_RED,
            hover_color=DEEP_RED,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._on_generate,
        )
        self.generate_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        ctk.CTkButton(
            action,
            text="Open Latest Result",
            height=46,
            fg_color=BTN_DARK,
            hover_color=BTN_DARK_HOVER,
            text_color=TEXT_PRIMARY,
            command=self._open_latest_result,
        ).grid(row=0, column=1, padx=10, sticky="ew")

        ctk.CTkButton(
            action,
            text="Refresh Runtime",
            height=46,
            fg_color=BTN_DARK,
            hover_color=BTN_DARK_HOVER,
            text_color=TEXT_PRIMARY,
            command=self._refresh_capabilities,
        ).grid(row=0, column=2, padx=(10, 0), sticky="ew")

        duration_card = make_card(left, "DURATION POLICY", "Use auto for platform defaults or manual for custom ranges.")
        duration_card.grid(row=4, column=0, sticky="ew", pady=10)

        duration_mode_row = ctk.CTkFrame(duration_card, fg_color="transparent")
        duration_mode_row.pack(fill="x", padx=22, pady=(0, 10))

        ctk.CTkLabel(duration_mode_row, text="Mode:", text_color=TEXT_SOFT).pack(side="left")
        self.duration_mode_menu = ctk.CTkOptionMenu(
            duration_mode_row,
            values=["auto", "manual"],
            variable=self.duration_mode,
            command=lambda _value: self._on_duration_mode_change(),
            fg_color=BTN_DARK,
            button_color="#2a2a2a",
            button_hover_color="#3a3a3a",
            text_color=TEXT_PRIMARY,
            dropdown_text_color=TEXT_PRIMARY,
            width=150,
        )
        self.duration_mode_menu.pack(side="left", padx=10)

        self.duration_manual_frame = ctk.CTkFrame(duration_card, fg_color=CARD_SOFT, corner_radius=12, border_width=1, border_color=BORDER)
        self.duration_manual_frame.pack(fill="x", padx=22, pady=(0, 14))
        self.duration_manual_frame.grid_columnconfigure((1, 3, 5), weight=1)

        ctk.CTkLabel(self.duration_manual_frame, text="Portrait Min:", text_color=TEXT_SOFT).grid(row=0, column=0, sticky="w", padx=(12, 8), pady=12)
        self.portrait_min_entry = ctk.CTkEntry(self.duration_manual_frame, textvariable=self.portrait_min_seconds, height=34)
        self.portrait_min_entry.grid(row=0, column=1, sticky="ew", pady=12)

        ctk.CTkLabel(self.duration_manual_frame, text="Portrait Max:", text_color=TEXT_SOFT).grid(row=0, column=2, sticky="w", padx=(16, 8), pady=12)
        self.portrait_max_entry = ctk.CTkEntry(self.duration_manual_frame, textvariable=self.portrait_max_seconds, height=34)
        self.portrait_max_entry.grid(row=0, column=3, sticky="ew", pady=12)

        ctk.CTkLabel(self.duration_manual_frame, text="Landscape Max:", text_color=TEXT_SOFT).grid(row=0, column=4, sticky="w", padx=(16, 8), pady=12)
        self.landscape_max_entry = ctk.CTkEntry(self.duration_manual_frame, textvariable=self.landscape_max_seconds, height=34)
        self.landscape_max_entry.grid(row=0, column=5, sticky="ew", pady=12)

        ctk.CTkLabel(
            duration_card,
            text="Platform-safe rule: Shorts/TikTok 30–120 sec, Reels 60–180 sec, mixed workflow is safest around 60–120 sec.",
            text_color=TEXT_MUTED,
            wraplength=650,
            justify="left",
        ).pack(anchor="w", padx=22, pady=(0, 14))

        face_card = make_card(left, "SMART FACE CENTER", "Use best_face_center + podcast_dual_speaker for dual-speaker podcast framing.")
        face_card.grid(row=5, column=0, sticky="ew", pady=10)

        self.face_center_cb = ctk.CTkCheckBox(face_card, text="Enable Smart Face Center", variable=self.face_center_enabled, text_color=TEXT_PRIMARY)
        self.face_center_cb.pack(anchor="w", padx=22, pady=(0, 10))

        face_mode_row = ctk.CTkFrame(face_card, fg_color="transparent")
        face_mode_row.pack(fill="x", padx=22, pady=(0, 10))
        ctk.CTkLabel(face_mode_row, text="Mode:", text_color=TEXT_SOFT).pack(side="left")

        self.face_mode_menu = ctk.CTkOptionMenu(
            face_mode_row,
            values=["off", "auto_fast", "best_face_center"],
            variable=self.face_center_mode,
            fg_color=BTN_DARK,
            button_color="#2a2a2a",
            button_hover_color="#3a3a3a",
            text_color=TEXT_PRIMARY,
            dropdown_text_color=TEXT_PRIMARY,
            width=180,
        )
        self.face_mode_menu.pack(side="left", padx=10)

        face_strategy_row = ctk.CTkFrame(face_card, fg_color="transparent")
        face_strategy_row.pack(fill="x", padx=22, pady=(0, 10))
        ctk.CTkLabel(face_strategy_row, text="Strategy:", text_color=TEXT_SOFT).pack(side="left")

        self.face_strategy_menu = ctk.CTkOptionMenu(
            face_strategy_row,
            values=["center_face", "eyes_priority", "speaker_priority", "podcast_dual_speaker"],
            variable=self.face_center_strategy,
            fg_color=BTN_DARK,
            button_color="#2a2a2a",
            button_hover_color="#3a3a3a",
            text_color=TEXT_PRIMARY,
            dropdown_text_color=TEXT_PRIMARY,
            width=220,
        )
        self.face_strategy_menu.pack(side="left", padx=10)

        self.face_debug_cb = ctk.CTkCheckBox(face_card, text="Debug Face Overlay", variable=self.face_debug_overlay, text_color=TEXT_PRIMARY)
        self.face_debug_cb.pack(anchor="w", padx=22, pady=(0, 12))

        delivery_card = make_card(left, "DELIVERY / DISTRIBUTION", "Auto sends immediately after the job is completed. Manual keeps results ready without immediate delivery.")
        delivery_card.grid(row=6, column=0, sticky="ew", pady=10)

        cloud_row = ctk.CTkFrame(delivery_card, fg_color=CARD_SOFT, corner_radius=12, border_width=1, border_color=BORDER)
        cloud_row.pack(fill="x", padx=22, pady=(0, 10))
        cloud_row.grid_columnconfigure(1, weight=1)

        self.cloudinary_cb = ctk.CTkCheckBox(cloud_row, text="Send to Cloudinary", variable=self.cloudinary_enabled, text_color=TEXT_PRIMARY)
        self.cloudinary_cb.grid(row=0, column=0, sticky="w", padx=12, pady=10)

        self.cloudinary_mode_menu = ctk.CTkOptionMenu(
            cloud_row,
            values=["auto", "manual"],
            variable=self.cloudinary_mode,
            fg_color=BTN_DARK,
            button_color="#2a2a2a",
            button_hover_color="#3a3a3a",
            text_color=TEXT_PRIMARY,
            dropdown_text_color=TEXT_PRIMARY,
            width=140,
        )
        self.cloudinary_mode_menu.grid(row=0, column=1, sticky="e", padx=12, pady=10)

        repliz_row = ctk.CTkFrame(delivery_card, fg_color=CARD_SOFT, corner_radius=12, border_width=1, border_color=BORDER)
        repliz_row.pack(fill="x", padx=22, pady=(0, 14))
        repliz_row.grid_columnconfigure(1, weight=1)

        self.repliz_cb = ctk.CTkCheckBox(repliz_row, text="Send to Repliz", variable=self.repliz_enabled, text_color=TEXT_PRIMARY)
        self.repliz_cb.grid(row=0, column=0, sticky="w", padx=12, pady=10)

        self.repliz_mode_menu = ctk.CTkOptionMenu(
            repliz_row,
            values=["auto", "manual"],
            variable=self.repliz_mode,
            fg_color=BTN_DARK,
            button_color="#2a2a2a",
            button_hover_color="#3a3a3a",
            text_color=TEXT_PRIMARY,
            dropdown_text_color=TEXT_PRIMARY,
            width=140,
        )
        self.repliz_mode_menu.grid(row=0, column=1, sticky="e", padx=12, pady=10)

        ai_card = make_card(left, "AI PROCESSING", "Enable the AI tools you want to use. Each tool can run in auto or manual_prompt mode.")
        ai_card.grid(row=7, column=0, sticky="ew", pady=10)

        self.subtitle_cb, self.subtitle_mode_menu = self._build_ai_tool_row(ai_card, "Subtitle Generation", self.subtitle_mode)
        self.hook_cb, self.hook_mode_menu = self._build_ai_tool_row(ai_card, "Hook Generator", self.hook_mode)
        self.niche_cb, self.niche_mode_menu = self._build_ai_tool_row(ai_card, "Niche Analyzer", self.niche_mode)
        self.hashtag_cb, self.hashtag_mode_menu = self._build_ai_tool_row(ai_card, "Auto Hashtag", self.hashtag_mode)

        self.advanced_btn = ctk.CTkButton(
            ai_card,
            text="Advanced AI Control",
            fg_color=BTN_DARK,
            hover_color=BTN_DARK_HOVER,
            text_color=TEXT_PRIMARY,
            command=self._toggle_advanced,
        )
        self.advanced_btn.pack(fill="x", padx=22, pady=(12, 10))

        self.advanced_frame = ctk.CTkFrame(
            ai_card,
            fg_color="#0a0a0a",
            corner_radius=12,
            border_width=1,
            border_color=BORDER,
        )

        self.hook_prompt = self._prompt_box(self.advanced_frame, "Hook Prompt", "Example: Create 3 short hooks, casual tone, Indonesian.")
        self.subtitle_prompt = self._prompt_box(self.advanced_frame, "Subtitle Prompt", "Example: Generate clean SRT subtitles in Indonesian.")
        self.niche_prompt = self._prompt_box(self.advanced_frame, "Niche Prompt", "Example: Analyze niche and recommend target audience.")
        self.hashtag_prompt = self._prompt_box(self.advanced_frame, "Hashtag Prompt", "Example: Provide 15 hashtags for Instagram Reels.")

        ctk.CTkLabel(
            self.advanced_frame,
            text="Notes:\n- auto = engine runs the workflow automatically\n- manual_prompt = engine must use the prompt you provide",
            text_color=TEXT_MUTED,
            wraplength=650,
            justify="left",
        ).pack(anchor="w", padx=22, pady=(0, 14))

        footer_card = ctk.CTkFrame(
            left,
            fg_color=CARD_SOFT,
            corner_radius=14,
            border_width=1,
            border_color=BORDER,
        )
        footer_card.grid(row=8, column=0, sticky="ew", pady=(12, 4))
        footer_card.grid_columnconfigure(0, weight=1)

        self.footer_plan_label = ctk.CTkLabel(
            footer_card,
            text="Plan: BASIC",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.footer_plan_label.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))

        self.footer_runtime_label = ctk.CTkLabel(
            footer_card,
            text="Runtime: Basic",
            text_color=TEXT_MUTED,
            font=ctk.CTkFont(size=12),
        )
        self.footer_runtime_label.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

        right = ctk.CTkFrame(self, fg_color=CARD, corner_radius=18, border_width=1, border_color=BORDER)
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 28), pady=20)
        right.grid_rowconfigure(4, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right,
            text="SYSTEM ACTIVITY",
            text_color=PRIMARY_RED,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, padx=18, pady=(18, 8), sticky="w")

        self.stage_label = ctk.CTkLabel(right, text="Stage: -", text_color=TEXT_SOFT, font=ctk.CTkFont(size=13, weight="bold"))
        self.stage_label.grid(row=1, column=0, padx=18, pady=(0, 6), sticky="w")

        self.progress_bar = ctk.CTkProgressBar(right)
        self.progress_bar.grid(row=2, column=0, padx=18, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)

        self.quick_info = ctk.CTkLabel(right, text="Ready to process.", text_color=TEXT_MUTED)
        self.quick_info.grid(row=3, column=0, padx=18, pady=(0, 10), sticky="w")

        self.status_box = ctk.CTkTextbox(
            right,
            fg_color=CARD_DARK,
            text_color=TEXT_PRIMARY,
            border_width=1,
            border_color=BORDER,
        )
        self.status_box.grid(row=4, column=0, padx=18, pady=(0, 12), sticky="nsew")
        self.status_box.insert("end", "GNX Engine Ready...\n")

        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.grid(row=5, column=0, padx=18, pady=(0, 18), sticky="ew")
        btn_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_row,
            text="Open outputs/jobs",
            fg_color=BTN_DARK,
            hover_color=BTN_DARK_HOVER,
            text_color=TEXT_PRIMARY,
            command=self._open_outputs_and_jobs,
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            btn_row,
            text="Open Last Job Folder",
            fg_color=BTN_DARK,
            hover_color=BTN_DARK_HOVER,
            text_color=TEXT_PRIMARY,
            command=self._open_last_job_folder,
        ).grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def _on_duration_mode_change(self):
        mode = self.duration_mode.get().strip().lower()
        if mode == "manual":
            self.duration_manual_frame.pack(fill="x", padx=22, pady=(0, 14))
        else:
            self.duration_manual_frame.pack_forget()

    def _toggle_advanced(self):
        if self.advanced_visible:
            self.advanced_frame.pack_forget()
        else:
            self.advanced_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.advanced_visible = not self.advanced_visible

    def _browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mov *.mkv *.webm *.m4v *.avi")])
        if path:
            self.offline_entry.delete(0, "end")
            self.offline_entry.insert(0, path)

    def _log(self, msg: str):
        self.status_box.insert("end", msg + "\n")
        self.status_box.see("end")

    def _poll_queue(self):
        try:
            while True:
                kind, data = self._q.get_nowait()
                if kind == "log":
                    self._log(str(data))
                elif kind == "status_dict":
                    self._handle_status_dict(data)
                elif kind == "done":
                    ok = bool(data)
                    self.generate_btn.configure(state="normal")
                    self.quick_info.configure(text="Job completed successfully." if ok else "Job failed. Check logs.")
                    self._log("Completed ✔" if ok else "Failed ❌")
                    self._refresh_capabilities()
        except queue.Empty:
            pass
        self.after(120, self._poll_queue)

    def _handle_status_dict(self, s: dict):
        stage = s.get("stage") or "-"
        msg = s.get("message") or ""
        p = s.get("progress")
        if isinstance(p, (int, float)):
            p = max(0.0, min(1.0, float(p)))
            self.progress_bar.set(p)
        self.stage_label.configure(text=f"Stage: {stage}")
        self.quick_info.configure(text=msg or "Running...")
        self._log(f"[{s.get('type','')}] {stage} :: {msg}")
        if s.get("persist_dir"):
            self._last_persist_dir = s["persist_dir"]

    def _open_outputs_and_jobs(self):
        _safe_open_path(str(self._outputs_dir().resolve()))
        _safe_open_path(str(self._jobs_dir().resolve()))

    def _open_last_job_folder(self):
        if self._last_persist_dir and Path(self._last_persist_dir).exists():
            _safe_open_path(self._last_persist_dir)
        else:
            self._open_latest_result()

    def _open_latest_result(self):
        jobs_dir = self._jobs_dir()
        latest = jobs_dir / "latest.json"
        if not latest.exists():
            self._log("No latest.json yet. Run one job first.")
            _safe_open_path(str(jobs_dir.resolve()))
            return

        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
            persist_dir = data.get("persist_dir")
            if persist_dir and Path(persist_dir).exists():
                _safe_open_path(persist_dir)
            else:
                self._log("latest.json found, but persist_dir is missing. Opening Outputs folder.")
                _safe_open_path(str(self._outputs_dir().resolve()))
        except Exception as e:
            self._log(f"Failed to read latest.json: {e}")
            _safe_open_path(str(jobs_dir.resolve()))

    def _safe_int(self, value: str, default_value: int):
        try:
            return int(str(value).strip())
        except Exception:
            return default_value

    def _on_generate(self):
        allow_youtube = bool(self.caps.get("allow_youtube", True))
        allow_ai = bool(self.caps.get("allow_ai", True))
        blocked_for_social_limit = bool(self.caps.get("blocked_for_social_limit", False))

        if blocked_for_social_limit:
            messagebox.showerror("Plan Restriction", "Connected social account count exceeds the allowed plan limit.")
            return

        youtube = self.youtube_entry.get().strip()
        offline = self.offline_entry.get().strip()

        if youtube and offline:
            messagebox.showerror("Input Error", "Choose only one source: YouTube URL or Offline Video.")
            return

        if youtube and not allow_youtube:
            messagebox.showerror("Plan Restriction", "YouTube mode is disabled on this plan. Use Offline Video only.")
            return

        if not youtube and not offline:
            messagebox.showerror("Error", "Please enter a YouTube URL or choose an offline video file.")
            return

        face_mode = self.face_center_mode.get().strip()
        face_enabled = bool(self.face_center_enabled.get())
        if not face_enabled:
            face_mode = "off"

        duration_mode = self.duration_mode.get().strip().lower()
        duration_policy = {"mode": duration_mode}

        if duration_mode == "manual":
            portrait_min = self._safe_int(self.portrait_min_seconds.get(), 30)
            portrait_max = self._safe_int(self.portrait_max_seconds.get(), 120)
            landscape_max = self._safe_int(self.landscape_max_seconds.get(), 180)

            if portrait_min <= 0 or portrait_max <= 0 or landscape_max <= 0:
                messagebox.showerror("Duration Error", "All manual durations must be greater than 0.")
                return
            if portrait_min > portrait_max:
                messagebox.showerror("Duration Error", "Portrait Min cannot be greater than Portrait Max.")
                return

            duration_policy = {
                "mode": "manual",
                "portrait_min_seconds": portrait_min,
                "portrait_max_seconds": portrait_max,
                "landscape_max_seconds": landscape_max,
            }

        payload = {
            "youtube_url": youtube,
            "file_path": offline,
            "offline_path": offline,
            "format_mode": self.format_mode.get().strip(),
            "format": self.format_mode.get().strip(),
            "quality_profile": self.quality_profile.get().strip(),
            "quality": self.quality_profile.get().strip(),
            "output_dir": str(self._outputs_dir()),
            "temp_dir": str(self._temp_dir()),
            "duration_policy": duration_policy,
            "face_centering": {
                "enabled": face_enabled,
                "mode": face_mode,
                "strategy": self.face_center_strategy.get().strip(),
                "fallback": "center_face",
                "debug_overlay": bool(self.face_debug_overlay.get()),
            },
            "delivery_options": {
                "cloudinary": {
                    "enabled": bool(self.cloudinary_enabled.get()),
                    "mode": self.cloudinary_mode.get().strip().lower(),
                },
                "repliz": {
                    "enabled": bool(self.repliz_enabled.get()),
                    "mode": self.repliz_mode.get().strip().lower(),
                },
            },
        }

        if not payload["youtube_url"]:
            payload.pop("youtube_url", None)
        if not payload["file_path"]:
            payload.pop("file_path", None)

        if allow_ai:
            payload["ai_options"] = {
                "enable_subtitles": bool(self.subtitle_cb.get()),
                "enable_hooks": bool(self.hook_cb.get()),
                "enable_niche": bool(self.niche_cb.get()),
                "enable_hashtags": bool(self.hashtag_cb.get()),
                "subtitle_mode": self.subtitle_mode.get().strip(),
                "hook_mode": self.hook_mode.get().strip(),
                "niche_mode": self.niche_mode.get().strip(),
                "hashtag_mode": self.hashtag_mode.get().strip(),
                "prompts": {
                    "hook": self.hook_prompt.get("1.0", "end").strip(),
                    "subtitle": self.subtitle_prompt.get("1.0", "end").strip(),
                    "niche": self.niche_prompt.get("1.0", "end").strip(),
                    "hashtag": self.hashtag_prompt.get("1.0", "end").strip(),
                },
            }

        self._log("Processing...")
        self._log(
            f"[PLAN] {self.caps.get('effective_plan')} | "
            f"quality={payload['quality_profile']} | "
            f"daily={self.caps.get('daily_video_limit')} | "
            f"30days={self.caps.get('monthly_video_limit')} | "
            f"accounts={self.caps.get('max_accounts')}"
        )
        self._log(
            f"[DURATION] mode={duration_policy['mode']} | "
            f"portrait_min={duration_policy.get('portrait_min_seconds', 'auto')} | "
            f"portrait_max={duration_policy.get('portrait_max_seconds', 'auto')} | "
            f"landscape_max={duration_policy.get('landscape_max_seconds', 'auto')}"
        )
        self._log(
            f"[FACE] enabled={payload['face_centering']['enabled']} | "
            f"mode={payload['face_centering']['mode']} | "
            f"strategy={payload['face_centering']['strategy']} | "
            f"debug={payload['face_centering']['debug_overlay']}"
        )

        if allow_ai:
            self._log(
                f"[AI] subtitle={self.subtitle_cb.get()}:{self.subtitle_mode.get()} | "
                f"hooks={self.hook_cb.get()}:{self.hook_mode.get()} | "
                f"niche={self.niche_cb.get()}:{self.niche_mode.get()} | "
                f"hashtag={self.hashtag_cb.get()}:{self.hashtag_mode.get()}"
            )

        self.quick_info.configure(text="Starting pipeline...")
        self.stage_label.configure(text="Stage: -")
        self.progress_bar.set(0)
        self.generate_btn.configure(state="disabled")

        def on_status(msg):
            if isinstance(msg, dict):
                self._q.put(("status_dict", msg))
            else:
                self._q.put(("log", str(msg)))

        def on_done(success):
            self._q.put(("done", bool(success)))

        self.engine.start(payload, on_status, on_done)