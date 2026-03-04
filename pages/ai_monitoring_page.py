import customtkinter as ctk


class MonitoringPage(ctk.CTkFrame):

    def __init__(self, master, engine):
        super().__init__(master, fg_color="transparent")

        self.engine = engine

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.textbox = ctk.CTkTextbox(self)
        self.textbox.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        self._load_existing_jobs()
        self.engine.add_status_listener(self._on_engine_status)

    # =========================================================

    def _load_existing_jobs(self):
        jobs = self.engine.get_jobs()
        for job in jobs:
            self.textbox.insert("end", f"{job.status} - {job.payload}\n")

    def _on_engine_status(self, message):
        self.textbox.insert("end", f"{message}\n")
        self.textbox.see("end")