import os
import sys
import subprocess
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox


PRIMARY_RED = "#b11226"
DEEP_RED = "#7a0d1a"
BLACK = "#000000"
CARD = "#111111"
CARD2 = "#0b0b0b"
TEXT_PRIMARY = "#EDEDED"
TEXT_MUTED = "#B8B8B8"


def _safe_open_path(p: str):
    try:
        if not p:
            return
        if os.name == "nt":
            os.startfile(p)
        else:
            import subprocess as sp
            sp.Popen(["xdg-open", p])
    except Exception as e:
        messagebox.showerror("Open Error", str(e))


def _appdata_dir() -> Path:
    base = os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    d = Path(base) / "GNX_PRODUCTION"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _outputs_dir() -> Path:
    d = _appdata_dir() / "outputs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _jobs_dir() -> Path:
    d = _outputs_dir() / "jobs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parents[1]


def _find_worker_exe() -> Path | None:
    base = _base_dir()
    p = base / "gnx_worker.exe"
    if p.exists():
        return p
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        mp = Path(meipass) / "gnx_worker.exe"
        if mp.exists():
            return mp
    return None


def _find_worker_entry_py() -> Path | None:
    base = _base_dir()
    candidates = [
        base / "worker_entry.py",
        base / "gnx" / "worker_entry.py",
        base / "core" / "worker_entry.py",
    ]
    for p in candidates:
        if p.exists():
            return p
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        mp = Path(meipass) / "worker_entry.py"
        if mp.exists():
            return mp
    return None


class WorkerControlPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BLACK)
        self.worker_proc: subprocess.Popen | None = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_ui()
        self._log("Worker Control ready.")

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=BLACK)
        header.grid(row=0, column=0, sticky="ew", padx=40, pady=(30, 10))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Worker Control",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=28, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="Start/Stop background worker. Worker lock/log saved in LocalAppData (safe).",
            text_color=TEXT_MUTED,
            wraplength=980,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        card = ctk.CTkFrame(self, fg_color=CARD, corner_radius=16)
        card.grid(row=1, column=0, sticky="ew", padx=40, pady=(10, 14))
        card.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            card,
            text="Worker Status: STOPPED",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=16, weight="bold"),
        )
        self.status_label.grid(row=0, column=0, sticky="w", padx=18, pady=(16, 10))

        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 16))
        btn_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkButton(
            btn_row,
            text="Start Worker",
            fg_color=PRIMARY_RED,
            hover_color=DEEP_RED,
            text_color=TEXT_PRIMARY,
            command=self._start_worker,
        ).grid(row=0, column=0, padx=(0, 10), sticky="ew")

        ctk.CTkButton(
            btn_row,
            text="Stop Worker (Graceful)",
            fg_color="#222222",
            hover_color="#333333",
            text_color=TEXT_PRIMARY,
            command=self._stop_worker,
        ).grid(row=0, column=1, padx=10, sticky="ew")

        ctk.CTkButton(
            btn_row,
            text="Open outputs",
            fg_color="#222222",
            hover_color="#333333",
            text_color=TEXT_PRIMARY,
            command=lambda: _safe_open_path(str(_outputs_dir())),
        ).grid(row=0, column=2, padx=10, sticky="ew")

        ctk.CTkButton(
            btn_row,
            text="Open AppData",
            fg_color="#222222",
            hover_color="#333333",
            text_color=TEXT_PRIMARY,
            command=lambda: _safe_open_path(str(_appdata_dir())),
        ).grid(row=0, column=3, padx=(10, 0), sticky="ew")

        log_card = ctk.CTkFrame(self, fg_color=CARD2, corner_radius=16)
        log_card.grid(row=2, column=0, sticky="nsew", padx=40, pady=(0, 30))
        log_card.grid_rowconfigure(1, weight=1)
        log_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_card,
            text="ACTIVITY LOG",
            text_color=PRIMARY_RED,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 8))

        self.log_box = ctk.CTkTextbox(log_card, fg_color="#060606", text_color=TEXT_PRIMARY)
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        self.log_box.insert("end", "Worker Control ready.\n")

    def _log(self, msg: str):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")

    def _start_worker(self):
        if self.worker_proc and self.worker_proc.poll() is None:
            messagebox.showinfo("Worker", "Worker is already running.")
            return

        exe = _find_worker_exe()
        entry = _find_worker_entry_py()

        workdir = _appdata_dir()
        env = os.environ.copy()
        env["GNX_APPDATA_DIR"] = str(workdir)

        # clear stop flag before starting
        for p in (workdir / "stop.flag", workdir / "stop.falg"):
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass

        try:
            if exe:
                self._log(f"Starting worker EXE: {exe}")
                self.worker_proc = subprocess.Popen(
                    [str(exe)],
                    cwd=str(workdir),
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
                )
            elif entry:
                self._log(f"Starting worker PY: {entry}")
                self.worker_proc = subprocess.Popen(
                    [sys.executable, str(entry)],
                    cwd=str(workdir),
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
                )
            else:
                messagebox.showerror(
                    "Worker",
                    "Could not find gnx_worker.exe or worker_entry.py.\n"
                    "Fix: rebuild Premium installer to include worker."
                )
                return

            self.status_label.configure(text="Worker Status: RUNNING")
            self._log(f"Worker started (cwd={workdir}).")

        except Exception as e:
            messagebox.showerror("Worker Error", str(e))

    def _stop_worker(self):
        workdir = _appdata_dir()
        stop_flag = workdir / "stop.flag"

        # create stop flag (graceful stop)
        try:
            stop_flag.write_text("stop", encoding="utf-8")
            self._log(f"stop.flag created: {stop_flag}")
        except Exception as e:
            messagebox.showerror("Worker Stop Error", f"Cannot create stop.flag: {e}")
            return

        # wait for graceful exit
        if self.worker_proc and self.worker_proc.poll() is None:
            self._log("Waiting for worker to exit gracefully...")
            try:
                self.worker_proc.wait(timeout=6)
            except Exception:
                self._log("Graceful stop timeout. Terminating worker...")
                try:
                    self.worker_proc.terminate()
                    self.worker_proc.wait(timeout=3)
                except Exception:
                    try:
                        self.worker_proc.kill()
                    except Exception:
                        pass

        self.worker_proc = None
        self.status_label.configure(text="Worker Status: STOPPED")
        self._log("Worker stopped.")