import customtkinter as ctk
import webbrowser


class UpgradeDialog(ctk.CTkToplevel):

    def __init__(self, parent):
        super().__init__(parent)

        self.title("Upgrade GNX PRO")
        self.geometry("520x420")

        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            container,
            text="Upgrade GNX PRO",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=(10, 20))

        ctk.CTkLabel(
            container,
            text="Choose your plan",
            font=ctk.CTkFont(size=14)
        ).pack(pady=(0, 20))

        self.plan_card(container, "FREE", "2 Social Accounts\nFull AI Tools\nOffline Video")
        self.plan_card(container, "PREMIUM", "100 Accounts\nAuto Scheduler\nAI Hooks + Caption")
        self.plan_card(container, "BUSINESS", "100 Accounts\nOnboarding Support\nPriority Update")

        ctk.CTkButton(
            container,
            text="View Pricing",
            command=self.open_pricing
        ).pack(pady=20)

    def plan_card(self, parent, title, desc):

        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=6)

        ctk.CTkLabel(
            frame,
            text=title,
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(anchor="w", padx=10)

        ctk.CTkLabel(
            frame,
            text=desc,
            font=ctk.CTkFont(size=13)
        ).pack(anchor="w", padx=10)

    def open_pricing(self):
        webbrowser.open("https://your-pricing-link.com")