import os
import json
from pathlib import Path
import customtkinter as ctk
from tkinter import messagebox


PRIMARY_RED = "#b11226"
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


def _obj_to_dict(obj):
    """Convert job object/dict to a dict safely."""
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj

    d = {}
    # common fields
    for k in ["id", "job_id", "created_at", "updated_at", "payload", "meta", "status"]:
        if hasattr(obj, k):
            d[k] = getattr(obj, k)

    # if job has .to_dict()
    if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
        try:
            return obj.to_dict()
        except Exception:
            pass

    return d


def _status_summary(job_dict: dict):
    st = job_dict.get("status") or {}
    if not isinstance(st, dict):
        # some implementations use object status
        st = _obj_to_dict(st)

    state = st.get("state") or "-"
    stage = st.get("stage") or "-"
    msg = st.get("message") or ""
    return str(state), str(stage), str(msg)


class MonitoringPage(ctk.CTkFrame):
    """
    Monitoring page should NEVER create outputs/ folders (Program Files permission issues).
    It reads jobs from Engine DB/controller only.
    """

    def __init__(self, master):
        super().__init__(master, fg_color=BLACK)

        self.engine = _find_engine(master)
        if self.engine is None:
            raise RuntimeError("Engine not found. Make sure AppShell sets app.engine before building pages.")

        self._job_buttons = []
        self._selected_job = None

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(1, weight=1)

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=BLACK)
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=40, pady=(30, 10))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Monitoring",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=28, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="View jobs from local DB (no filesystem writes).",
            text_color=TEXT_MUTED,
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        btn_row = ctk.CTkFrame(header, fg_color="transparent")
        btn_row.grid(row=0, column=1, rowspan=2, sticky="e")

        ctk.CTkButton(
            btn_row,
            text="Refresh",
            fg_color=PRIMARY_RED,
            hover_color="#7a0d1a",
            text_color=TEXT_PRIMARY,
            command=self.refresh,
            width=120,
        ).pack(side="right")

        # LEFT LIST
        left = ctk.CTkFrame(self, fg_color=CARD, corner_radius=16)
        left.grid(row=1, column=0, sticky="nsew", padx=(40, 12), pady=(0, 30))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left,
            text="Jobs",
            text_color=PRIMARY_RED,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 8))

        self.list_frame = ctk.CTkScrollableFrame(left, fg_color="#060606", corner_radius=12)
        self.list_frame.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        self.list_frame.grid_columnconfigure(0, weight=1)

        # RIGHT DETAILS
        right = ctk.CTkFrame(self, fg_color=CARD2, corner_radius=16)
        right.grid(row=1, column=1, sticky="nsew", padx=(12, 40), pady=(0, 30))
        right.grid_rowconfigure(2, weight=1)
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right,
            text="Job Details",
            text_color=PRIMARY_RED,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 8))

        self.detail_title = ctk.CTkLabel(right, text="Select a job...", text_color=TEXT_PRIMARY)
        self.detail_title.grid(row=1, column=0, sticky="w", padx=18, pady=(0, 8))

        self.detail_box = ctk.CTkTextbox(right, fg_color="#060606", text_color=TEXT_PRIMARY)
        self.detail_box.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 12))
        self.detail_box.insert("1.0", "No job selected.\n")

        action = ctk.CTkFrame(right, fg_color="transparent")
        action.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 18))
        action.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(
            action,
            text="Open Persist Folder",
            fg_color="#222222",
            hover_color="#333333",
            text_color=TEXT_PRIMARY,
            command=self._open_persist_folder,
        ).grid(row=0, column=0, padx=(0, 10), sticky="ew")

        ctk.CTkButton(
            action,
            text="Copy Job JSON",
            fg_color="#222222",
            hover_color="#333333",
            text_color=TEXT_PRIMARY,
            command=self._copy_job_json,
        ).grid(row=0, column=1, padx=(10, 0), sticky="ew")

    def refresh(self):
        # clear list
        for w in self.list_frame.winfo_children():
            w.destroy()
        self._job_buttons.clear()

        try:
            jobs = self.engine.get_jobs() if hasattr(self.engine, "get_jobs") else []
        except Exception:
            jobs = []

        # normalize
        job_dicts = [_obj_to_dict(j) for j in (jobs or [])]

        # sort: newest first (best effort)
        def _sort_key(d):
            return str(d.get("updated_at") or d.get("created_at") or d.get("id") or d.get("job_id") or "")
        job_dicts.sort(key=_sort_key, reverse=True)

        if not job_dicts:
            ctk.CTkLabel(
                self.list_frame,
                text="No jobs found yet. Run Generate once.",
                text_color=TEXT_MUTED,
            ).pack(anchor="w", padx=12, pady=10)
            return

        for d in job_dicts[:200]:
            jid = d.get("id") or d.get("job_id") or "-"
            state, stage, _ = _status_summary(d)

            btn = ctk.CTkButton(
                self.list_frame,
                text=f"{jid}   [{state}]   {stage}",
                fg_color="#111111",
                hover_color="#222222",
                text_color=TEXT_PRIMARY,
                command=lambda dd=d: self._select_job(dd),
                height=36,
            )
            btn.pack(fill="x", padx=10, pady=6)
            self._job_buttons.append(btn)

        # auto-select first
        self._select_job(job_dicts[0])

    def _select_job(self, job_dict: dict):
        self._selected_job = job_dict
        jid = job_dict.get("id") or job_dict.get("job_id") or "-"
        state, stage, msg = _status_summary(job_dict)

        self.detail_title.configure(text=f"Job: {jid}   |   {state} / {stage}")

        self.detail_box.delete("1.0", "end")
        try:
            self.detail_box.insert("1.0", json.dumps(job_dict, ensure_ascii=False, indent=2))
        except Exception:
            self.detail_box.insert("1.0", str(job_dict))

    def _open_persist_folder(self):
        if not self._selected_job:
            return
        meta = self._selected_job.get("meta") or {}
        if not isinstance(meta, dict):
            meta = _obj_to_dict(meta)

        persist_dir = meta.get("persist_dir") or self._selected_job.get("persist_dir")
        if persist_dir and Path(str(persist_dir)).exists():
            _safe_open_path(str(persist_dir))
        else:
            messagebox.showinfo("Info", "No persist folder found for this job yet.")

    def _copy_job_json(self):
        if not self._selected_job:
            return
        try:
            txt = json.dumps(self._selected_job, ensure_ascii=False, indent=2)
            self.clipboard_clear()
            self.clipboard_append(txt)
            messagebox.showinfo("Copied", "Job JSON copied to clipboard.")
        except Exception as e:
            messagebox.showerror("Copy Error", str(e))