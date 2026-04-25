import sys
import webbrowser
from pathlib import Path
import customtkinter as ctk

from core.theme_constants import (
    PRIMARY_ORANGE, PRIMARY_RED, DEEP_RED, GREEN, BLACK, CARD, CARD_SOFT, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, TEXT_SOFT,
    BADGE_DARK, BADGE_SUCCESS, BADGE_WARNING,
)
from core.ui_helpers import make_card

def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent

def _default_pricing():
    return {
        "basic": {
            "title": "Basic",
            "badge": "Free Forever",
            "price_label": "FREE",
            "subtitle": "Starter pack for marketing testing and basic workflow.",
            "items": [
                "2 social media accounts limit",
                "2 videos generation per day",
                "1080p maximum quality",
                "Manual AI Tools access",
                "Locked by PC Hardware (HWID)"
            ],
            "action_label": "",
            "action_url": ""
        },
        "premium": {
            "title": "Premium",
            "badge": "🔥 GLOBAL SALE - 80% OFF",
            "price_label": "$29",
            "subtitle": "CLEARANCE SALE! Get full automation at a fraction of the cost.",
            "items": [
                "100 social media accounts limit",
                "24 videos generation per day",
                "Up to 1440p (2K) quality",
                "Full AI Auto-Copywriting",
                "Smart Social Scheduler",
                "Strictly locked to 1 PC (HWID)"
            ],
            "action_label": "Grab Discount Now",
            "action_url": "https://www.instagram.com/genexproduction/"
        },
        "business": {
            "title": "Business",
            "badge": "Enterprise",
            "price_label": "Contact Admin",
            "subtitle": "Unlimited scale for agencies and multi-PC deployment.",
            "items": [
                "Multi-PC installation allowed",
                "100 accounts limit PER PC",
                "24 videos daily PER PC",
                "Up to 4K Master Quality",
                "Admin-managed configuration",
                "Special pricing based on scale"
            ],
            "action_label": "Contact via WhatsApp",
            "action_url": "https://wa.me/6287828541944"
        },
        "notes": [
            "Global Clearance Promo: The 80% discount is applied globally for a limited time.",
            "Hardware ID (HWID) Locking: Your Premium license is bound to your motherboard serial.",
            "Security: Using a Premium license on unauthorized PCs will trigger an automatic security block."
        ]
    }

def _load_pricing():
    # FIX: Paksa aplikasi untuk SELALU membaca dari kode Python (_default_pricing)
    # Abaikan file pricing.json lama yang masih nyangkut di cache komputer.
    return _default_pricing()

def _open_url(url: str):
    try:
        url = str(url or "").strip()
        if url: webbrowser.open(url)
    except Exception: pass

class AboutPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BLACK)
        self.grid_columnconfigure(0, weight=1)
        self.pricing = _load_pricing()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_ui()

    def _build_ui(self):
        outer = ctk.CTkScrollableFrame(self, fg_color=BLACK)
        outer.grid(row=0, column=0, sticky="nsew", padx=30, pady=22)
        outer.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(outer, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        
        ctk.CTkLabel(header, text="About GNX Production Studio", text_color=TEXT_PRIMARY, font=ctk.CTkFont(size=30, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(header, text="High-performance AI pipeline for viral short-form video production.", text_color=TEXT_MUTED).grid(row=1, column=0, sticky="w", pady=(6, 0))

        pricing_wrap = ctk.CTkFrame(outer, fg_color="transparent")
        pricing_wrap.grid(row=1, column=0, sticky="ew", pady=10)
        pricing_wrap.grid_columnconfigure((0, 1, 2), weight=1)

        self._build_plan_card(pricing_wrap, row=0, column=0, data=self.pricing.get("basic", {}), badge_color=BADGE_DARK, accent_color=TEXT_PRIMARY, pad=(0, 8))
        self._build_plan_card(pricing_wrap, row=0, column=1, data=self.pricing.get("premium", {}), badge_color=PRIMARY_RED, accent_color=PRIMARY_ORANGE, pad=8)
        self._build_plan_card(pricing_wrap, row=0, column=2, data=self.pricing.get("business", {}), badge_color=BADGE_SUCCESS, accent_color=GREEN, pad=(8, 0))

        notes_card = make_card(outer, "Promotion & Security Notes", "Limited time offers and runtime rules.")
        notes_card.grid(row=2, column=0, sticky="ew", pady=10)

        notes = self.pricing.get("notes", [])
        notes_text = "\n\n".join([f"• {item}" for item in notes]) if notes else "No notes available."

        ctk.CTkLabel(notes_card, text=notes_text, text_color=TEXT_SOFT, justify="left", anchor="w", wraplength=920).pack(fill="x", padx=22, pady=(0, 16))

    def _build_plan_card(self, parent, row, column, data, badge_color, accent_color, pad):
        card = ctk.CTkFrame(parent, fg_color=CARD, corner_radius=18, border_width=1, border_color=BORDER)
        card.grid(row=row, column=column, sticky="nsew", padx=pad, pady=0)
        
        badge = ctk.CTkLabel(card, text=str(data.get("badge", "")), text_color=TEXT_PRIMARY, fg_color=badge_color, corner_radius=12, padx=12, pady=6)
        badge.pack(anchor="w", padx=18, pady=(18, 10))

        ctk.CTkLabel(card, text=str(data.get("title", "Plan")), text_color=accent_color, font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", padx=18)
        
        # Price Label dengan coretan diskon
        price_f = ctk.CTkFrame(card, fg_color="transparent")
        price_f.pack(anchor="w", padx=18, pady=(8, 4))
        
        if data.get("title") == "Premium":
            ctk.CTkLabel(price_f, text="$145", text_color=TEXT_MUTED, font=ctk.CTkFont(size=14, slant="italic", overstrike=True)).pack(side="left", padx=(0, 5))
            
        ctk.CTkLabel(price_f, text=str(data.get("price_label", "-")), text_color=TEXT_PRIMARY, font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")

        ctk.CTkLabel(card, text=str(data.get("subtitle", "")), text_color=TEXT_MUTED, wraplength=260, justify="left").pack(anchor="w", padx=18, pady=(0, 12))

        items_box = ctk.CTkFrame(card, fg_color=CARD_SOFT, corner_radius=12)
        items_box.pack(fill="both", expand=True, padx=18, pady=(0, 12))

        for item in data.get("items", []):
            ctk.CTkLabel(items_box, text=f"• {item}", text_color=TEXT_SOFT, justify="left", anchor="w", wraplength=250).pack(fill="x", padx=14, pady=6)

        action_label, action_url = str(data.get("action_label", "")).strip(), str(data.get("action_url", "")).strip()
        if action_label and action_url:
            ctk.CTkButton(card, text=action_label, fg_color=PRIMARY_RED if data.get("title") == "Premium" else accent_color, hover_color=DEEP_RED, text_color=TEXT_PRIMARY, height=40, command=lambda u=action_url: _open_url(u)).pack(fill="x", padx=18, pady=(0, 18))
        else:
            ctk.CTkFrame(card, fg_color="transparent", height=10).pack(fill="x", padx=18, pady=(0, 18))