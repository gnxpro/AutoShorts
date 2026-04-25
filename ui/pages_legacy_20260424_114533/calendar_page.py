import customtkinter as ctk
import tkinter.messagebox as messagebox
from pathlib import Path
from core.theme_constants import (
    PRIMARY_RED, DEEP_RED, BLACK, BORDER, CARD, CARD_SOFT,
    TEXT_PRIMARY, TEXT_MUTED, TEXT_SOFT,
    BTN_DARK, BTN_DARK_HOVER
)
from core.ui_helpers import make_card
from core.scheduler_engine import GNXScheduler

class CalendarPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BLACK)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.scheduler = GNXScheduler()
        self._build_ui()
        self.load_data()

    def _build_ui(self):
        # --- HEADER AREA ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=30, pady=(30, 10))
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="Production Calendar", 
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        title_label.pack(side="left")

        # Tombol Refresh
        self.btn_refresh = ctk.CTkButton(
            header_frame, 
            text="🔄 Refresh List", 
            width=120,
            height=35,
            fg_color=BTN_DARK,
            hover_color=BTN_DARK_HOVER,
            text_color=TEXT_PRIMARY,
            command=self.load_data
        )
        self.btn_refresh.pack(side="right")

        # --- SCROLLABLE LIST AREA ---
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, 
            fg_color=BLACK,
            scrollbar_button_color=CARD_SOFT,
            scrollbar_button_hover_color=BORDER
        )
        self.scroll_frame.grid(row=1, column=0, sticky="nsew", padx=25, pady=10)

    def load_data(self):
        """Membersihkan UI dan memuat ulang antrean dari database"""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        queue_list = self.scheduler.load_queue()

        if not queue_list:
            empty_lbl = ctk.CTkLabel(
                self.scroll_frame, 
                text="Tidak ada antrean video saat ini.", 
                text_color=TEXT_SOFT,
                font=ctk.CTkFont(size=14, slant="italic")
            )
            empty_lbl.pack(pady=50)
            return

        for item in queue_list:
            title = item.get("title", "Untitled Video")
            status = item.get("status", "Pending")
            
            card = ctk.CTkFrame(self.scroll_frame, fg_color=CARD, corner_radius=12, border_width=1, border_color=BORDER)
            card.pack(fill="x", pady=8, padx=5)

            info_box = ctk.CTkFrame(card, fg_color="transparent")
            info_box.pack(side="left", fill="both", expand=True, padx=20, pady=15)

            ctk.CTkLabel(
                info_box, 
                text=title, 
                text_color=TEXT_PRIMARY, 
                font=ctk.CTkFont(size=15, weight="bold"),
                anchor="w"
            ).pack(fill="x")

            ctk.CTkLabel(
                info_box, 
                text=f"Status: {status} • Ready for production", 
                text_color=TEXT_MUTED, 
                font=ctk.CTkFont(size=12),
                anchor="w"
            ).pack(fill="x")

            btn_box = ctk.CTkFrame(card, fg_color="transparent")
            btn_box.pack(side="right", padx=20)

            btn_post = ctk.CTkButton(
                btn_box, 
                text="🚀 POST", 
                width=85, 
                height=32,
                fg_color=PRIMARY_RED, 
                hover_color=DEEP_RED,
                command=lambda t=title: self._execute_post(t)
            )
            btn_post.pack(side="right", padx=5)

            btn_del = ctk.CTkButton(
                btn_box, 
                text="🗑️ Hapus", 
                width=75, 
                height=32,
                fg_color="transparent",
                border_width=1,
                border_color=DEEP_RED,
                text_color=PRIMARY_RED,
                hover_color=CARD_SOFT,
                command=lambda t=title: self._confirm_delete(t)
            )
            btn_del.pack(side="right", padx=5)

    def _execute_post(self, title):
        """Memicu proses upload dengan radar pencarian super agresif"""
        import threading
        import os
        import re
        from pathlib import Path
        from core.uploader import GNXUploader
        from core.logger import log_info, log_error

        # 1. Ambil data dari antrean
        queue_list = self.scheduler.load_queue()
        video_data = next((item for item in queue_list if item.get("title") == title), None)

        if not video_data:
            messagebox.showerror("Error", f"Data '{title}' tidak ditemukan!")
            return

        output_dir = Path(r"C:\Users\GenEx\Desktop\GNX Production\Outputs")
        video_path = ""

        # 2. RADAR SCAN SUPER AGRESIF
        if output_dir.exists():
            # Bersihkan judul antrean untuk pencocokan (ignore P1, P2, dll)
            title_clean = re.sub(r'p\d+$', '', title.lower().strip())
            title_clean = re.sub(r'[^a-z0-9]', '', title_clean)
            
            semua_mp4 = list(output_dir.glob("*.mp4"))
            for mp4 in semua_mp4:
                file_clean = re.sub(r'[^a-z0-9]', '', mp4.stem.lower())
                if title_clean in file_clean or file_clean in title_clean:
                    video_path = str(mp4)
                    break

        # 3. VERIFIKASI FILE
        if not video_path or not os.path.exists(video_path):
            files = [f.name for f in output_dir.glob("*.mp4")]
            list_file = "\n- ".join(files[:5]) if files else "(Folder Kosong)"
            msg = f"Radar gagal menemukan file video!\n\nJudul: {title}\nFolder: {output_dir}\n\nFile tersedia:\n- {list_file}"
            messagebox.showerror("File Tidak Ditemukan", msg)
            return

        desc = video_data.get("description") or f"Video: {title}"

        # 4. JALANKAN MESIN UPLOAD
        def run_upload_engine():
            log_info(f"CALENDAR >> Radar menemukan file: {Path(video_path).name}")
            uploader = GNXUploader()
            
            # Kita jalankan per platform secara berurutan
            # Jalur FB akan tetap lokal, Jalur IG otomatis lewat Cloudinary
            platforms = ["YOUTUBE", "TIKTOK", "FACEBOOK", "INSTAGRAM"]
            all_success = True
            
            for plat in platforms:
                # Sekarang post_video sangat simpel, parameter 'video_url' ditangani di uploader
                success = uploader.post_video(plat, video_path, title, desc)
                if not success: all_success = False
            
            if all_success:
                log_info(f"✅ CALENDAR >> '{title}' sukses terkirim ke semua platform!")
            else:
                log_error(f"❌ CALENDAR >> '{title}' selesai, tapi ada beberapa kendala. Cek Log.")

        threading.Thread(target=run_upload_engine, daemon=True).start()
        messagebox.showinfo("Proses Dimulai", f"Video ditemukan!\nFile: {Path(video_path).name}\n\nCek log terminal untuk progres.")

    def _confirm_delete(self, title):
        """Pop-up konfirmasi hapus antrean"""
        ans = messagebox.askyesno("Hapus Antrean", f"Hapus '{title}' dari daftar kalender?")
        if ans:
            if self.scheduler.remove_from_queue(title):
                self.load_data()
            else:
                messagebox.showerror("Error", "Gagal menghapus data dari database.")