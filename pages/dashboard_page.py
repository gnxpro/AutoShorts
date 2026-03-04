import os
import json
import queue
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog, messagebox


PRIMARY_RED = "#b11226"
DEEP_RED = "#7a0d1a"

GREEN = "#1f8a3b"
BLACK = "#000000"
DARK_CARD = "#111111"
DARKER_CARD = "#0b0b0b"

TEXT_PRIMARY = "#EDEDED"
TEXT_MUTED = "#B8B8B8"
TEXT_SOFT = "#DADADA"


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

        # capabilities (plan gating)
        self.caps = self._read_capabilities()

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()
        self._apply_capabilities_to_ui()

        self.after(120, self._poll_queue)

    # ----------------------------
    # Capabilities
    # ----------------------------
    def _read_capabilities(self) -> dict:
        # Safe fallback if engine doesn't have get_capabilities()
        try:
            if hasattr(self.engine, "get_capabilities"):
                caps = self.engine.get_capabilities() or {}
            else:
                caps = {}
        except Exception:
            caps = {}

        # defaults: full access
        caps.setdefault("plan", "PRO")
        caps.setdefault("allow_youtube", True)
        caps.setdefault("allow_ai", True)
        caps.setdefault("allow_schedule", True)
        caps.setdefault("max_accounts", 100)
        return caps

    def _refresh_capabilities(self):
        self.caps = self._read_capabilities()
        self._apply_capabilities_to_ui()
        self._log(f"[PLAN] {self.caps.get('plan','-')} | YouTube={self.caps.get('allow_youtube')} | AI={self.caps.get('allow_ai')} | Schedule={self.caps.get('allow_schedule')}")

    def _apply_capabilities_to_ui(self):
        plan = str(self.caps.get("plan", "PRO")).upper()
        allow_youtube = bool(self.caps.get("allow_youtube", True))
        allow_ai = bool(self.caps.get("allow_ai", True))

        # Plan badge
        self.plan_badge.configure(text=f"PLAN: {plan}")

        # YouTube gating
        if not allow_youtube:
            self.youtube_entry.configure(state="disabled")
        else:
            self.youtube_entry.configure(state="normal")

        # AI gating
        if not allow_ai:
            # disable checkboxes
            for cb in (self.subtitle_cb, self.hook_cb, self.niche_cb, self.hashtag_cb):
                cb.deselect()
                cb.configure(state="disabled")
            # disable advanced
            self.advanced_btn.configure(state="disabled", text="Advanced AI Control (PRO only)")
            # hide advanced frame if open
            if self.advanced_visible:
                self.advanced_frame.pack_forget()
                self.advanced_visible = False
        else:
            for cb in (self.subtitle_cb, self.hook_cb, self.niche_cb, self.hashtag_cb):
                cb.configure(state="normal")
            self.advanced_btn.configure(state="normal", text="Advanced AI Control (optional)")

        # Update helper text
        if not allow_youtube:
            self.source_hint.configure(
                text="This plan is Offline-only. YouTube input is disabled. Use Offline Video.",
            )
        else:
            self.source_hint.configure(
                text="Choose ONE source: YouTube URL OR Offline Video. Repliz scheduling is configured in the Repliz menu.",
            )

    # ----------------------------
    # UI
    # ----------------------------
    def _build_ui(self):
        # LEFT
        left_wrap = ctk.CTkFrame(self, fg_color=BLACK)
        left_wrap.grid(row=0, column=0, sticky="nsew", padx=40, pady=30)
        left_wrap.grid_rowconfigure(0, weight=1)
        left_wrap.grid_columnconfigure(0, weight=1)

        left = ctk.CTkScrollableFrame(left_wrap, fg_color=BLACK)
        left.grid(row=0, column=0, sticky="nsew")
        left.grid_columnconfigure(0, weight=1)

        title_row = ctk.CTkFrame(left, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        title_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            title_row,
            text="GNX PRO - AI STUDIO",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=28, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self.plan_badge = ctk.CTkLabel(
            title_row,
            text="PLAN: -",
            text_color=TEXT_PRIMARY,
            fg_color="#222222",
            corner_radius=10,
            padx=12,
            pady=6,
        )
        self.plan_badge.grid(row=0, column=1, sticky="e")

        self.source_hint = ctk.CTkLabel(
            left,
            text="Choose ONE source: YouTube URL OR Offline Video. Repliz scheduling is configured in the Repliz menu.",
            text_color=TEXT_MUTED,
            wraplength=520,
            justify="left",
        )
        self.source_hint.grid(row=1, column=0, sticky="w", pady=(0, 14))

        # VIDEO SOURCE CARD
        top_card = ctk.CTkFrame(left, fg_color=DARK_CARD, corner_radius=15)
        top_card.grid(row=2, column=0, sticky="ew", pady=10)
        top_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top_card, text="VIDEO SOURCE", text_color=PRIMARY_RED,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=22, pady=(16, 8))

        self.youtube_entry = ctk.CTkEntry(
            top_card,
            placeholder_text="Example: youtube.com/watch?v=xxxxxxxxxxx",
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_MUTED
        )
        self.youtube_entry.pack(fill="x", padx=22, pady=(0, 10))

        row = ctk.CTkFrame(top_card, fg_color="transparent")
        row.pack(fill="x", padx=22, pady=(0, 10))

        self.offline_entry = ctk.CTkEntry(
            row,
            placeholder_text=r"Example Offline: C:\Users\...\AutoShorts\assets\video.mp4",
            text_color=TEXT_PRIMARY,
            placeholder_text_color=TEXT_MUTED
        )
        self.offline_entry.pack(side="left", fill="x", expand=True)

        ctk.CTkButton(
            row, text="Browse", width=110,
            fg_color=PRIMARY_RED, hover_color=DEEP_RED, text_color=TEXT_PRIMARY,
            command=self._browse_file
        ).pack(side="left", padx=10)

        fmt_row = ctk.CTkFrame(top_card, fg_color="transparent")
        fmt_row.pack(fill="x", padx=22, pady=(0, 12))
        ctk.CTkLabel(fmt_row, text="Format Mode:", text_color=TEXT_SOFT).pack(side="left")

        self.format_mode = ctk.StringVar(value="both")
        self.format_menu = ctk.CTkOptionMenu(
            fmt_row, values=["portrait", "landscape", "both"], variable=self.format_mode,
            fg_color="#222222", button_color="#2a2a2a", button_hover_color="#3a3a3a",
            text_color=TEXT_PRIMARY, dropdown_text_color=TEXT_PRIMARY
        )
        self.format_menu.pack(side="left", padx=10)

        action = ctk.CTkFrame(top_card, fg_color="transparent")
        action.pack(fill="x", padx=22, pady=(0, 10))
        action.grid_columnconfigure((0, 1, 2), weight=1)

        self.generate_btn = ctk.CTkButton(
            action, text="Generate Video", height=46,
            fg_color=PRIMARY_RED, hover_color=DEEP_RED, text_color=TEXT_PRIMARY,
            command=self._on_generate
        )
        self.generate_btn.grid(row=0, column=0, padx=(0, 10), sticky="ew")

        ctk.CTkButton(
            action, text="Open Latest Result", height=46,
            fg_color="#222222", hover_color="#333333", text_color=TEXT_PRIMARY,
            command=self._open_latest_result
        ).grid(row=0, column=1, padx=10, sticky="ew")

        ctk.CTkButton(
            action, text="Refresh Plan", height=46,
            fg_color="#222222", hover_color="#333333", text_color=TEXT_PRIMARY,
            command=self._refresh_capabilities
        ).grid(row=0, column=2, padx=(10, 0), sticky="ew")

        hint = ctk.CTkLabel(
            top_card,
            text="Tip: Configure Cloudinary + Repliz first (Cloudinary/Repliz menus) before scheduling.",
            text_color=TEXT_MUTED,
            wraplength=520,
            justify="left",
        )
        hint.pack(anchor="w", padx=22, pady=(0, 14))

        # AI PROCESSING CARD
        ai_card = ctk.CTkFrame(left, fg_color=DARK_CARD, corner_radius=15)
        ai_card.grid(row=3, column=0, sticky="ew", pady=10)
        ai_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            ai_card, text="AI PROCESSING", text_color=PRIMARY_RED,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(anchor="w", padx=22, pady=(16, 8))

        self.subtitle_cb = ctk.CTkCheckBox(ai_card, text="Subtitle Generation", text_color=TEXT_PRIMARY)
        self.hook_cb = ctk.CTkCheckBox(ai_card, text="Hook Generator", text_color=TEXT_PRIMARY)
        self.niche_cb = ctk.CTkCheckBox(ai_card, text="Niche Analyzer", text_color=TEXT_PRIMARY)
        self.hashtag_cb = ctk.CTkCheckBox(ai_card, text="Auto Hashtag", text_color=TEXT_PRIMARY)
        for cb in (self.subtitle_cb, self.hook_cb, self.niche_cb, self.hashtag_cb):
            cb.pack(anchor="w", padx=22, pady=6)

        self.advanced_btn = ctk.CTkButton(
            ai_card, text="Advanced AI Control (optional)",
            fg_color="#222222", hover_color="#333333", text_color=TEXT_PRIMARY,
            command=self._toggle_advanced
        )
        self.advanced_btn.pack(fill="x", padx=22, pady=(12, 10))

        self.advanced_frame = ctk.CTkFrame(ai_card, fg_color="#0a0a0a")
        self.hook_prompt = self._prompt_box(self.advanced_frame, "Hook Prompt",
                                            "Example: Create 3 short hooks, casual tone, Indonesian.")
        self.subtitle_prompt = self._prompt_box(self.advanced_frame, "Subtitle Prompt",
                                                "Example: Generate clean SRT subtitles in Indonesian.")
        self.niche_prompt = self._prompt_box(self.advanced_frame, "Niche Prompt",
                                             "Example: Analyze niche + recommend target audience.")
        self.hashtag_prompt = self._prompt_box(self.advanced_frame, "Hashtag Prompt",
                                               "Example: Provide 15 hashtags for Instagram Reels.")

        # RIGHT - SYSTEM ACTIVITY
        right = ctk.CTkFrame(self, fg_color=DARK_CARD, corner_radius=15)
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 40), pady=30)
        right.grid_rowconfigure(3, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right, text="SYSTEM ACTIVITY", text_color=PRIMARY_RED,
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=18, pady=(18, 8), sticky="w")

        self.stage_label = ctk.CTkLabel(right, text="Stage: -", text_color=TEXT_SOFT)
        self.stage_label.grid(row=1, column=0, padx=18, pady=(0, 6), sticky="w")

        self.progress_bar = ctk.CTkProgressBar(right)
        self.progress_bar.grid(row=2, column=0, padx=18, pady=(0, 10), sticky="ew")
        self.progress_bar.set(0)

        self.status_box = ctk.CTkTextbox(right, fg_color=DARKER_CARD, text_color=TEXT_PRIMARY)
        self.status_box.grid(row=3, column=0, padx=18, pady=(0, 12), sticky="nsew")
        self.status_box.insert("end", "GNX Engine Ready...\n")

        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.grid(row=4, column=0, padx=18, pady=(0, 18), sticky="ew")
        btn_row.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            btn_row, text="Open outputs/jobs",
            fg_color="#222222", hover_color="#333333", text_color=TEXT_PRIMARY,
            command=self._open_jobs_dir
        ).grid(row=0, column=0, padx=(0, 8), sticky="ew")

        ctk.CTkButton(
            btn_row, text="Open Last Job Folder",
            fg_color="#222222", hover_color="#333333", text_color=TEXT_PRIMARY,
            command=self._open_last_job_folder
        ).grid(row=0, column=1, padx=(8, 0), sticky="ew")

    def _prompt_box(self, parent, title, example_text: str):
        label = ctk.CTkLabel(parent, text=title, text_color=PRIMARY_RED)
        label.pack(anchor="w", padx=22, pady=(10, 6))
        box = ctk.CTkTextbox(parent, height=70, fg_color="#111111", text_color=TEXT_PRIMARY)
        box.pack(fill="x", padx=22, pady=(0, 10))
        box.insert("1.0", example_text)
        return box

    def _toggle_advanced(self):
        if self.advanced_visible:
            self.advanced_frame.pack_forget()
        else:
            self.advanced_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.advanced_visible = not self.advanced_visible

    # ----------------------------
    # Actions
    # ----------------------------
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
                    self._log("Completed ✔" if ok else "Failed ❌")
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
        self._log(f"[{s.get('type','')}] {stage} :: {msg}")
        if s.get("persist_dir"):
            self._last_persist_dir = s["persist_dir"]

    def _jobs_dir(self) -> Path:
        return Path("outputs") / "jobs"

    def _open_jobs_dir(self):
        p = self._jobs_dir()
        p.mkdir(parents=True, exist_ok=True)
        _safe_open_path(str(p.resolve()))

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
            self._open_jobs_dir()
            return
        try:
            data = json.loads(latest.read_text(encoding="utf-8"))
            persist_dir = data.get("persist_dir")
            if persist_dir and Path(persist_dir).exists():
                _safe_open_path(persist_dir)
            else:
                self._open_jobs_dir()
        except Exception as e:
            self._log(f"Failed to read latest.json: {e}")
            self._open_jobs_dir()

    def _on_generate(self):
        allow_youtube = bool(self.caps.get("allow_youtube", True))
        allow_ai = bool(self.caps.get("allow_ai", True))

        youtube = self.youtube_entry.get().strip()
        offline = self.offline_entry.get().strip()

        if youtube and not allow_youtube:
            messagebox.showerror("Plan Restriction", "YouTube mode is disabled on this plan. Use Offline Video only.")
            return

        if not youtube and not offline:
            messagebox.showerror("Error", "Please enter a YouTube URL or choose an offline video file.")
            return

        payload = {
            "youtube_url": youtube,
            "file_path": offline,
            "offline_path": offline,
            "format_mode": self.format_mode.get().strip(),
            "format": self.format_mode.get().strip(),
        }
        if not payload["youtube_url"]:
            payload.pop("youtube_url", None)
        if not payload["file_path"]:
            payload.pop("file_path", None)

        # Include AI options only if plan allows AI
        if allow_ai:
            payload["ai_options"] = {
                "enable_subtitles": bool(self.subtitle_cb.get()),
                "enable_hooks": bool(self.hook_cb.get()),
                "enable_niche": bool(self.niche_cb.get()),
                "enable_hashtags": bool(self.hashtag_cb.get()),
                "prompts": {
                    "hook": self.hook_prompt.get("1.0", "end").strip(),
                    "subtitle": self.subtitle_prompt.get("1.0", "end").strip(),
                    "niche": self.niche_prompt.get("1.0", "end").strip(),
                    "hashtag": self.hashtag_prompt.get("1.0", "end").strip(),
                }
            }

        self._log("Processing...")
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