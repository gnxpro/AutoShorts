import customtkinter as ctk
import webbrowser

PRIMARY_RED = "#c1121f"


class UpgradePage(ctk.CTkFrame):

    def __init__(self, parent, engine=None):
        super().__init__(parent)

        self.engine = engine

        container = ctk.CTkFrame(self)
        container.pack(fill="both", expand=True, padx=40, pady=40)

        # TITLE
        ctk.CTkLabel(
            container,
            text="GNX PRO - Upgrade Plan",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(pady=(10, 10))

        ctk.CTkLabel(
            container,
            text="Choose the best plan for your automation workflow",
            font=ctk.CTkFont(size=14)
        ).pack(pady=(0, 25))

        # PRICING AREA
        cards_frame = ctk.CTkFrame(container)
        cards_frame.pack(pady=20)

        # =========================
        # FREE PLAN
        # =========================

        free_card = ctk.CTkFrame(cards_frame, width=240, height=260)
        free_card.grid(row=0, column=0, padx=20, pady=10)
        free_card.grid_propagate(False)

        ctk.CTkLabel(
            free_card,
            text="FREE",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            free_card,
            text="$0",
            font=ctk.CTkFont(size=20)
        ).pack(pady=(0, 10))

        ctk.CTkLabel(free_card, text="• 2 Social Accounts").pack(pady=2)
        ctk.CTkLabel(free_card, text="• AI Tools Enabled").pack(pady=2)
        ctk.CTkLabel(free_card, text="• Offline Video Processing").pack(pady=2)
        ctk.CTkLabel(free_card, text="• Basic Scheduler").pack(pady=2)

        ctk.CTkButton(
            free_card,
            text="Current Plan",
            state="disabled"
        ).pack(pady=20)

        # =========================
        # PREMIUM PLAN
        # =========================

        premium_card = ctk.CTkFrame(cards_frame, width=240, height=260)
        premium_card.grid(row=0, column=1, padx=20, pady=10)
        premium_card.grid_propagate(False)

        ctk.CTkLabel(
            premium_card,
            text="PREMIUM",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            premium_card,
            text="$49",
            font=ctk.CTkFont(size=20)
        ).pack(pady=(0, 10))

        ctk.CTkLabel(premium_card, text="• 100 Social Accounts").pack(pady=2)
        ctk.CTkLabel(premium_card, text="• Full AI Tools").pack(pady=2)
        ctk.CTkLabel(premium_card, text="• Cloudinary Upload").pack(pady=2)
        ctk.CTkLabel(premium_card, text="• Repliz Automation").pack(pady=2)
        ctk.CTkLabel(premium_card, text="• Priority Updates").pack(pady=2)

        ctk.CTkButton(
            premium_card,
            text="Upgrade to Premium",
            fg_color=PRIMARY_RED,
            command=self.buy_premium
        ).pack(pady=20)

        # =========================
        # BUSINESS PLAN
        # =========================

        business_card = ctk.CTkFrame(cards_frame, width=240, height=260)
        business_card.grid(row=0, column=2, padx=20, pady=10)
        business_card.grid_propagate(False)

        ctk.CTkLabel(
            business_card,
            text="BUSINESS",
            font=ctk.CTkFont(size=22, weight="bold")
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            business_card,
            text="$199",
            font=ctk.CTkFont(size=20)
        ).pack(pady=(0, 10))

        ctk.CTkLabel(business_card, text="• 100 Social Accounts").pack(pady=2)
        ctk.CTkLabel(business_card, text="• Full Automation").pack(pady=2)
        ctk.CTkLabel(business_card, text="• Deployment Support").pack(pady=2)
        ctk.CTkLabel(business_card, text="• Onboarding Session").pack(pady=2)
        ctk.CTkLabel(business_card, text="• Priority Maintenance").pack(pady=2)

        ctk.CTkButton(
            business_card,
            text="Contact Sales",
            fg_color=PRIMARY_RED,
            command=self.contact_sales
        ).pack(pady=20)

        # FOOTER
        footer = ctk.CTkFrame(container)
        footer.pack(pady=30)

        ctk.CTkLabel(
            footer,
            text="Developed by GENERAL EXPLORER PRODUCTION",
            font=ctk.CTkFont(size=13)
        ).pack()

    # =========================
    # ACTIONS
    # =========================

    def buy_premium(self):

        webbrowser.open(
            "https://wa.me/628000000000"
        )

    def contact_sales(self):

        webbrowser.open(
            "https://wa.me/628000000000"
        )