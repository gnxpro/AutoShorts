import os
import queue
import threading
import asyncio
from datetime import datetime
from pathlib import Path

import customtkinter as ctk
from tkinter import filedialog, messagebox

from core.theme_constants import (
    PRIMARY_RED, DEEP_RED, BLACK, CARD, CARD_SOFT, CARD_DARK, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, TEXT_SOFT, BTN_DARK
)
from core.ui_helpers import make_card
from core.gnx_pipeline_adapter import run_gnx_job

def _find_engine(widget):
    w = widget
    for _ in range(12):
        if hasattr(w, "engine"): return w.engine
        w = getattr(w, "master", None)
        if w is None: break
    return None

class DashboardPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BLACK)
        self.engine = _find_engine(master)
        self._q = queue.Queue()

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self._build_ui()
        self.after(120, self._poll_queue)

    def _build_ui(self):
        # --- LEFT AREA (Controls) ---
        left_wrap = ctk.CTkFrame(self, fg_color=BLACK)
        left_wrap.grid(row=0, column=0, sticky="nsew", padx=28, pady=20)
        left = ctk.CTkScrollableFrame(left_wrap, fg_color=BLACK); left.pack(fill="both", expand=True)

        ctk.CTkLabel(left, text="GNX Studio", font=("Arial", 30, "bold")).pack(anchor="w", pady=(0, 20))

        # 1. VIDEO SOURCE
        src_card = make_card(left, "VIDEO SOURCE", "Input Link YouTube atau File Lokal.")
        src_card.pack(fill="x", pady=10)
        self.youtube_entry = ctk.CTkEntry(src_card, placeholder_text="Paste YouTube URL here...", height=40, fg_color=BLACK, border_color=BORDER)
        self.youtube_entry.pack(fill="x", padx=20, pady=(15, 10))
        self.offline_entry = ctk.CTkEntry(src_card, placeholder_text="Select local video...", height=40, fg_color=BLACK, border_color=BORDER)
        self.offline_entry.pack(fill="x", padx=20, pady=(0, 15))

        # 2. FACE TRACKER & QUALITY
        face_card = make_card(left, "PRODUCTION SETTINGS", "Konfigurasi Face Tracker & Kualitas.")
        face_card.pack(fill="x", pady=10)
        
        self.face_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(face_card, text="Enable Face Tracker (Auto-Centering)", variable=self.face_var, font=("Arial", 12)).pack(anchor="w", padx=20, pady=10)
        
        self.quality_var = ctk.StringVar(value="1080p")
        ctk.CTkOptionMenu(face_card, values=["720p", "1080p", "1440p", "4k"], variable=self.quality_var, fg_color=BTN_DARK).pack(anchor="w", padx=20, pady=(0, 15))

        # 3. AI CONTENT & DURATION (Hooks, Captions, etc.)
        ai_card = make_card(left, "AI & DURATION", "Atur AI Hooks dan Durasi Maksimal.")
        ai_card.pack(fill="x", pady=10)
        
        self.hooks_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(ai_card, text="Auto AI Hooks & Captioning", variable=self.hooks_var, font=("Arial", 12)).pack(anchor="w", padx=20, pady=10)
        
        self.duration_var = ctk.StringVar(value="60")
        ctk.CTkLabel(ai_card, text="Max Duration (Seconds):", font=("Arial", 11)).pack(anchor="w", padx=20)
        ctk.CTkSegmentedButton(ai_card, values=["30", "60", "90", "180"], variable=self.duration_var).pack(fill="x", padx=20, pady=(5, 15))

        # 4. START BUTTON
        self.generate_btn = ctk.CTkButton(left, text="🚀 START PRODUCTION", height=60, fg_color=PRIMARY_RED, hover_color=DEEP_RED, font=("Arial", 16, "bold"), command=self._on_generate)
        self.generate_btn.pack(fill="x", pady=30)

        # --- RIGHT AREA (Console/Log) ---
        right = ctk.CTkFrame(self, fg_color=CARD, corner_radius=15)
        right.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        ctk.CTkLabel(right, text="SYSTEM LOG", font=("Arial", 12, "bold"), text_color=TEXT_SOFT).pack(anchor="w", padx=15, pady=(15, 5))
        self.status_box = ctk.CTkTextbox(right, fg_color=BLACK, text_color="#00FF00", font=("Consolas", 11), border_width=1, border_color=BORDER)
        self.status_box.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def _on_generate(self):
        yt_url = self.youtube_entry.get().strip()
        loc_path = self.offline_entry.get().strip()
        
        payload = {
            "youtube_url": yt_url if yt_url else None,
            "offline_path": loc_path if loc_path else None,
            "format": "portrait",
            "quality": self.quality_var.get(),
            "face_centering": {"enabled": self.face_var.get()},
            "ai_options": {"enable_hooks": self.hooks_var.get()},
            "duration_limit": int(self.duration_var.get()),
            "enable_upload": True
        }
        
        self.generate_btn.configure(state="disabled", text="RUNNING...")
        self.status_box.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] 🚀 Initiating Full Production...\n")
        threading.Thread(target=self._run_async_job, args=(payload,), daemon=True).start()

    def _run_async_job(self, payload):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(run_gnx_job(
                payload=payload,
                job_id=f"JOB-{datetime.now().strftime('%M%S')}",
                youtube_service=self.engine.youtube_service, 
                cloudinary_service=self.engine.cloudinary_service,
                event_handler=lambda e: self._q.put(("log", e.message))
            ))
        except Exception as e:
            self._q.put(("log", f"❌ ERROR: {str(e)}"))
        finally:
            self._q.put(("done", True))

    def _poll_queue(self):
        try:
            while True:
                k, d = self._q.get_nowait()
                if k == "log": 
                    self.status_box.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {d}\n")
                    self.status_box.see("end")
                elif k == "done": 
                    self.generate_btn.configure(state="normal", text="🚀 START PRODUCTION")
        except: pass
        self.after(120, self._poll_queue)