import os
import json
import queue
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from core.engine import Engine


APP_ROOT = Path(__file__).resolve().parents[1]  # .../AutoShorts
OUTPUTS_DIR = APP_ROOT / "outputs"
JOBS_DIR = OUTPUTS_DIR / "jobs"


def safe_open_path(p: str):
    try:
        if not p:
            return
        if os.name == "nt":
            os.startfile(p)  # Windows
        else:
            # fallback mac/linux
            import subprocess
            subprocess.Popen(["xdg-open", p])
    except Exception as e:
        messagebox.showerror("Open Error", str(e))


class GNXDemoApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        self.title("GNX Pipeline Demo (CustomTkinter)")
        self.geometry("980x640")

        self.engine = Engine()

        # Queue untuk kirim status dari thread engine -> UI main thread
        self.q = queue.Queue()

        self._build_ui()
        self.after(100, self._poll_queue)

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        top.grid_columnconfigure(1, weight=1)

        # Source type
        self.source_type = ctk.StringVar(value="file")
        self.source_switch = ctk.CTkSegmentedButton(
            top,
            values=["file", "youtube"],
            variable=self.source_type,
            command=self._on_source_type_change
        )
        self.source_switch.grid(row=0, column=0, padx=(12, 8), pady=10, sticky="w")

        # Source value entry + browse
        self.source_entry = ctk.CTkEntry(top, placeholder_text="assets\\video.mp4 atau URL YouTube")
        self.source_entry.grid(row=0, column=1, padx=8, pady=10, sticky="ew")
        self.source_entry.insert(0, "assets\\video.mp4")

        self.browse_btn = ctk.CTkButton(top, text="Browse", width=90, command=self._browse_file)
        self.browse_btn.grid(row=0, column=2, padx=(8, 12), pady=10, sticky="e")

        # Format mode
        self.format_mode = ctk.StringVar(value="both")
        self.format_menu = ctk.CTkOptionMenu(top, values=["portrait", "landscape", "both"], variable=self.format_mode)
        self.format_menu.grid(row=1, column=0, padx=(12, 8), pady=(0, 10), sticky="w")

        # Enable schedule
        self.enable_schedule = tk.BooleanVar(value=True)
        self.schedule_chk = ctk.CTkCheckBox(top, text="Enable Repliz Schedule", variable=self.enable_schedule)
        self.schedule_chk.grid(row=1, column=1, padx=8, pady=(0, 10), sticky="w")

        # Account IDs entry (comma-separated)
        self.account_ids_entry = ctk.CTkEntry(top, placeholder_text="Repliz Account IDs (pisahkan dengan koma)")
        self.account_ids_entry.grid(row=2, column=0, columnspan=2, padx=(12, 8), pady=(0, 10), sticky="ew")
        self.account_ids_entry.insert(0, "680affa5ce12f2f72916f67e")  # ganti dengan account kamu

        # Start button
        self.start_btn = ctk.CTkButton(top, text="Run Job", command=self._start_job, width=120)
        self.start_btn.grid(row=2, column=2, padx=(8, 12), pady=(0, 10), sticky="e")

        # Progress + stage label
        mid = ctk.CTkFrame(self)
        mid.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        mid.grid_columnconfigure(0, weight=1)
        mid.grid_rowconfigure(1, weight=1)

        self.stage_label = ctk.CTkLabel(mid, text="Stage: -", anchor="w")
        self.stage_label.grid(row=0, column=0, padx=12, pady=(12, 6), sticky="ew")

        self.progress = ctk.CTkProgressBar(mid)
        self.progress.grid(row=0, column=1, padx=12, pady=(12, 6), sticky="ew")
        self.progress.set(0)

        # Log textbox
        self.log = ctk.CTkTextbox(mid, wrap="word")
        self.log.grid(row=1, column=0, columnspan=2, padx=12, pady=(6, 12), sticky="nsew")

        # Bottom buttons
        bottom = ctk.CTkFrame(self)
        bottom.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))
        bottom.grid_columnconfigure(0, weight=1)

        self.open_latest_btn = ctk.CTkButton(bottom, text="Open Latest Result", command=self._open_latest_result)
        self.open_latest_btn.grid(row=0, column=0, padx=12, pady=10, sticky="w")

        self.open_jobs_btn = ctk.CTkButton(bottom, text="Open outputs/jobs", command=lambda: safe_open_path(str(JOBS_DIR)))
        self.open_jobs_btn.grid(row=0, column=1, padx=12, pady=10, sticky="e")

        self._on_source_type_change(self.source_type.get())

    def _on_source_type_change(self, value: str):
        if value == "file":
            self.browse_btn.configure(state="normal")
            if "http" in self.source_entry.get().lower():
                self.source_entry.delete(0, "end")
                self.source_entry.insert(0, "assets\\video.mp4")
        else:
            self.browse_btn.configure(state="disabled")
            if "http" not in self.source_entry.get().lower():
                self.source_entry.delete(0, "end")
                self.source_entry.insert(0, "https://youtube.com/watch?v=dQw4w9WgXcQ")

    def _browse_file(self):
        p = filedialog.askopenfilename(
            title="Select Video",
            filetypes=[("Video Files", "*.mp4 *.mov *.mkv *.webm *.m4v *.avi"), ("All Files", "*.*")]
        )
        if p:
            self.source_entry.delete(0, "end")
            self.source_entry.insert(0, p)

    def _parse_account_ids(self):
        raw = self.account_ids_entry.get().strip()
        if not raw:
            return []
        return [x.strip() for x in raw.split(",") if x.strip()]

    def _build_payload(self) -> dict:
        src_type = self.source_type.get().strip()
        src_val = self.source_entry.get().strip()

        payload = {
            "format_mode": self.format_mode.get().strip(),
            "enable_schedule": bool(self.enable_schedule.get()),
        }

        if src_type == "file":
            payload["file_path"] = src_val
        else:
            payload["youtube_url"] = src_val

        # Multi-account (Repliz account IDs)
        payload["account_ids"] = self._parse_account_ids()

        return payload

    def _append_log(self, text: str):
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def _start_job(self):
        payload = self._build_payload()

        # Validasi cepat
        if "file_path" in payload:
            fp = payload["file_path"]
            if not Path(fp).exists():
                messagebox.showerror("Error", f"File tidak ditemukan:\n{fp}")
                return

        if payload.get("enable_schedule", True) and not payload.get("account_ids"):
            messagebox.showerror("Error", "Schedule ON, tapi account_ids kosong. Masukkan Repliz Account ID.")
            return

        self.start_btn.configure(state="disabled")
        self.progress.set(0)
        self.stage_label.configure(text="Stage: -")
        self._append_log("=== RUN JOB ===")
        self._append_log(f"Payload: {payload}")

        def on_status(status: dict):
            # Dipanggil dari thread background -> jangan update UI langsung
            self.q.put(("status", status))

        def on_done(ok: bool):
            self.q.put(("done", ok))

        self.engine.start(payload, on_status, on_done)

    def _poll_queue(self):
        try:
            while True:
                kind, data = self.q.get_nowait()

                if kind == "status":
                    self._handle_status(data)
                elif kind == "done":
                    self.start_btn.configure(state="normal")
                    self._append_log(f"=== DONE: {data} ===")
        except queue.Empty:
            pass

        self.after(120, self._poll_queue)

    def _handle_status(self, s: dict):
        # Format status dari Engine (event_handler pipeline)
        stype = s.get("type", "")
        stage = s.get("stage") or "-"
        msg = s.get("message") or ""

        # Progress: bisa None untuk STAGE_START, jadi guard
        p = s.get("progress")
        if isinstance(p, (int, float)):
            # clamp 0..1
            p = max(0.0, min(1.0, float(p)))
            self.progress.set(p)

        self.stage_label.configure(text=f"Stage: {stage}")
        self._append_log(f"[{stype}] {stage} :: {msg}")

        # Kalau final sudah ada persist_dir, tampilkan hint
        if stype == "FINAL":
            persist_dir = s.get("persist_dir")
            if persist_dir:
                self._append_log(f"[RESULT] {persist_dir}")

    def _open_latest_result(self):
        try:
            latest = JOBS_DIR / "latest.json"
            if not latest.exists():
                messagebox.showinfo("Info", "Belum ada latest.json. Jalankan 1 job dulu.")
                return
            data = json.loads(latest.read_text(encoding="utf-8"))
            persist_dir = data.get("persist_dir")
            if not persist_dir:
                messagebox.showinfo("Info", "latest.json tidak punya persist_dir.")
                return
            safe_open_path(persist_dir)
        except Exception as e:
            messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    app = GNXDemoApp()
    app.mainloop()