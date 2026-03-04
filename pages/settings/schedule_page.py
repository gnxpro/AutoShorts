import customtkinter as ctk
from core.config_manager import ConfigManager


class SchedulePage(ctk.CTkFrame):

    def __init__(self, parent):
        super().__init__(parent)

        self.config = ConfigManager()

        self.pack(fill="both", expand=True)

        ctk.CTkLabel(self, text="Schedule Settings",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        self.platform_var = ctk.StringVar(value="instagram")
        self.videos_var = ctk.StringVar(value="1")
        self.start_time_var = ctk.StringVar(value="14:00:00")

        ctk.CTkOptionMenu(
            self,
            values=["instagram", "youtube", "tiktok"],
            variable=self.platform_var
        ).pack(pady=10)

        ctk.CTkOptionMenu(
            self,
            values=["1", "2", "3", "4", "5"],
            variable=self.videos_var
        ).pack(pady=10)

        ctk.CTkEntry(
            self,
            textvariable=self.start_time_var,
            placeholder_text="Start Time HH:MM:SS"
        ).pack(pady=10)

        ctk.CTkButton(
            self,
            text="Save Schedule",
            command=self.save_schedule
        ).pack(pady=20)

    def save_schedule(self):
        self.config.set_schedule(
            mode="daily",
            videos_per_day=int(self.videos_var.get()),
            platform=self.platform_var.get(),
            start_time=self.start_time_var.get()
        )