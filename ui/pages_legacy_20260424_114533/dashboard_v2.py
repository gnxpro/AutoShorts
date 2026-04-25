import os
import threading
import customtkinter as ctk
import cv2
from PIL import Image
from pathlib import Path
from datetime import datetime
from tkinter import filedialog
from core.theme_constants import BLACK, PRIMARY_RED, CARD, GREEN, BTN_DARK

class DashboardV2(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=BLACK, **kwargs)
        self.output_dir = Path.home() / "Desktop" / "GNX Production" / "Outputs"
        self.selected_local_file = None
        self.style_ref_image = None  # Reference image path
        self.queue_list = []
        self.current_video_cap = None
        self.current_preview_image = None
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self._build_left_panel()
        self._build_right_panel()

    def _build_left_panel(self):
        self.left_panel = ctk.CTkFrame(self, fg_color=CARD, corner_radius=15)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        ctk.CTkLabel(self.left_panel, text="GNX AI STUDIO v3", font=("Arial", 20, "bold"), text_color=PRIMARY_RED).pack(pady=15)

        # 1. VIDEO SOURCE
        self.tab_input = ctk.CTkTabview(self.left_panel, height=80)
        self.tab_input.pack(fill="x", padx=15)
        self.tab_yt = self.tab_input.add("YOUTUBE")
        self.tab_local = self.tab_input.add("LOCAL")
        self.yt_url = ctk.CTkEntry(self.tab_yt, placeholder_text="Paste Link...")
        self.yt_url.pack(fill="x", padx=10, pady=2)
        ctk.CTkButton(self.tab_local, text="📁 BROWSE SOURCE", height=24, command=self._browse_file).pack()

        # 2. IMAGE-TO-VIDEO STYLE REF (BARU)
        ctk.CTkLabel(self.left_panel, text="🖼️ STYLE REFERENCE (IMAGE)", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.style_btn = ctk.CTkButton(self.left_panel, text="Select Style Image (Optional)", fg_color="#222", height=30, command=self._browse_style_image)
        self.style_btn.pack(fill="x", padx=15, pady=5)

        # 3. TEXT-TO-EDIT PROMPT
        ctk.CTkLabel(self.left_panel, text="✍️ AI EDITING INSTRUCTION", font=("Arial", 11, "bold")).pack(anchor="w", padx=20, pady=(10, 0))
        self.ai_prompt = ctk.CTkTextbox(self.left_panel, height=60, fg_color="#111", border_width=1, border_color="#333")
        self.ai_prompt.pack(fill="x", padx=15, pady=5)
        self.ai_prompt.insert("1.0", "Make it cinematic, add auto-captions, and center face...")

        # 4. STRATEGY SELECTION
        self.strategy_var = ctk.StringVar(value="shorts_60s")
        ctk.CTkRadioButton(self.left_panel, text="Shorts/TikTok (60s)", variable=self.strategy_var, value="shorts_60s").pack(anchor="w", padx=25, pady=2)
        ctk.CTkRadioButton(self.left_panel, text="Reels FB/IG (3m)", variable=self.strategy_var, value="reels_3m").pack(anchor="w", padx=25, pady=2)
        ctk.CTkRadioButton(self.left_panel, text="FB Page Long (10m+)", variable=self.strategy_var, value="long_form").pack(anchor="w", padx=25, pady=2)

        self.log_area = ctk.CTkTextbox(self.left_panel, height=120, fg_color="#000", font=("Consolas", 10))
        self.log_area.pack(fill="both", expand=True, padx=15, pady=10)

        self.btn_start = ctk.CTkButton(self.left_panel, text="🔥 START AI PRODUCTION", fg_color=PRIMARY_RED, font=("Arial", 14, "bold"), height=40, command=self.start_pipeline)
        self.btn_start.pack(fill="x", padx=20, pady=(0, 20))

    def _build_right_panel(self):
        self.right_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        
        self.monitor = ctk.CTkFrame(self.right_panel, fg_color="#000", border_width=2, border_color="#222")
        self.monitor.pack(fill="both", expand=True, pady=(0, 15))
        self.video_canvas = ctk.CTkLabel(self.monitor, text="AI ENGINE STANDBY", text_color="#444")
        self.video_canvas.pack(fill="both", expand=True)

        self.video_library = ctk.CTkScrollableFrame(self.right_panel, height=200, fg_color=CARD)
        self.video_library.pack(fill="x")

    def _browse_style_image(self):
        """Memilih gambar referensi gaya"""
        f = filedialog.askopenfilename(filetypes=[("Image", "*.jpg *.png *.jpeg")])
        if f:
            self.style_ref_image = f
            self.style_btn.configure(text=f"Selected: {Path(f).name}", text_color=GREEN)
            self.write_log(f"STYLE >> Image reference set: {Path(f).name}")

    def write_log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert("end", f"[{timestamp}] {msg}\n")
        self.log_area.see("end")

    def _browse_file(self):
        f = filedialog.askopenfilename()
        if f: 
            self.selected_local_file = f
            self.write_log(f"SOURCE >> Local video: {Path(f).name}")

    def start_pipeline(self):
        source = self.yt_url.get() if self.tab_input.get() == "YOUTUBE" else self.selected_local_file
        prompt = self.ai_prompt.get("1.0", "end-1c")
        
        if not source:
            self.write_log("CRITICAL >> Missing video source!")
            return

        self.btn_start.configure(state="disabled", text="AI PROCESSING...")
        # Kirim source, prompt, dan style image ke engine
        threading.Thread(target=self._run_engine, args=(source, prompt, self.style_ref_image), daemon=True).start()

    def _run_engine(self, source, prompt, style_img):
        stype = "YOUTUBE" if self.tab_input.get() == "YOUTUBE" else "LOCAL"
        # Format command lengkap untuk AI Engine
        cmd = f"STRATEGY:{self.strategy_var.get()}|PROMPT:{prompt}|STYLE:{style_img}"
        self.master.master.engine.process_full_pipeline(source, stype, cmd, self.write_log, self.receive_production_data)
        self.after(0, lambda: self.btn_start.configure(state="normal", text="🔥 START AI PRODUCTION"))

    def receive_production_data(self, data):
        self.queue_list.append(data)
        self.after(0, self.refresh_library)
        self.after(0, lambda: self.play_video_preview(data['local_path']))

    def play_video_preview(self, video_path):
        if not video_path or not os.path.exists(video_path): return
        try:
            if self.current_video_cap: self.current_video_cap.release()
            cap = cv2.VideoCapture(str(video_path))
            cap.set(cv2.CAP_PROP_POS_FRAMES, 5) 
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                self.update_idletasks()
                w, h = self.video_canvas.winfo_width(), self.video_canvas.winfo_height()
                img.thumbnail((w if w > 50 else 600, h if h > 50 else 400), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                self.current_preview_image = ctk_img
                self.video_canvas.configure(image=ctk_img, text="")
            if self.current_video_cap:
                self.current_video_cap.release()
            self.current_video_cap = cap
        except Exception:
            pass

    def refresh_library(self):
        for w in self.video_library.winfo_children(): w.destroy()
        for vid in self.queue_list:
            item = ctk.CTkFrame(self.video_library, fg_color="#1a1a1a", height=55)
            item.pack(fill="x", padx=5, pady=2)
            item.pack_propagate(False)
            ctk.CTkButton(item, text="▶", width=40, command=lambda v=vid: self.play_video_preview(v['local_path'])).pack(side="left", padx=10)
            ctk.CTkLabel(item, text=vid.get('title', 'Video')[:40], anchor="w").pack(side="left")