import json
import sys
import webbrowser
from pathlib import Path

import customtkinter as ctk

from core.theme_constants import (
    PRIMARY_ORANGE,
    GREEN,
    BLACK,
    CARD,
    CARD_SOFT,
    BORDER,
    TEXT_PRIMARY,
    TEXT_MUTED,
    TEXT_SOFT,
    BADGE_DARK,
    BADGE_SUCCESS,
    BADGE_WARNING,
)
from core.ui_helpers import make_card


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def config_dir() -> Path:
    p = app_base_dir() / "config"
    p.mkdir(parents=True, exist_ok=True)
    return p


def pricing_path() -> Path:
    return config_dir() / "pricing.json"


def _default_pricing():
    return {
        "basic": {
            "title": "Basic",
            "badge": "Free",
            "price_label": "Free",
            "subtitle": "Full workflow access for early marketing and product trial",
            "items": [
                "2 social media accounts",
                "2 videos per day",
                "60 videos per 30 days",
                "480p quality",
                "AI tools enabled",
                "Upload to Repliz enabled"
            ],
            "action_label": "",
            "action_url": ""
        },
        "premium": {
            "title": "Premium",
            "badge": "Most Popular",
            "price_label": "499k",
            "subtitle": "100 social media accounts, locked by Repliz",
            "items": [
                "100 social media accounts",
                "Locked by Repliz",
                "8 videos per day",
                "240 videos per 30 days",
                "Up to 1080p quality",
                "AI tools enabled",
                "Scheduling enabled",
                "Multi-PC usage allowed with the same registered Repliz account"
            ],
            "action_label": "Open Website",
            "action_url": "https://www.instagram.com/genexproduction/"
        },
        "business": {
            "title": "Business",
            "badge": "Custom Enterprise",
            "price_label": "Contact Admin",
            "subtitle": "Multi-PC and multi-account business deployment",
            "items": [
                "Multi-PC deployment",
                "Multi social media accounts",
                "Admin-managed configuration",
                "Custom billing",
                "Custom capacity",
                "Special pricing based on business needs"
            ],
            "action_label": "Contact via WhatsApp",
            "action_url": "https://wa.me/6287828541944"
        },
        "notes": [
            "Premium remains active only when the connected Repliz account matches the registered licensed account.",
            "If a different Repliz account is used, the application automatically runs in Basic mode.",
            "Business plans are managed directly by admin for multi-PC and large-scale account usage."
        ]
    }


def _load_pricing():
    path = pricing_path()
    if not path.exists():
        return _default_pricing()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return _default_pricing()
        return data
    except Exception:
        return _default_pricing()


def _open_url(url: str):
    try:
        url = str(url or "").strip()
        if url:
            webbrowser.open(url)
    except Exception:
        pass


class AboutPage(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=BLACK)

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
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="About GNX Production Studio",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=30, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text="AI-powered production workflow for video generation, scheduling, and scalable Repliz-based publishing.",
            text_color=TEXT_MUTED,
            wraplength=900,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))

        overview = make_card(
            outer,
            "Platform Overview",
            "GNX Production Studio helps creators, marketers, and teams produce videos faster, organize publishing, and scale their Repliz workflow with better account safety and scheduling discipline."
        )
        overview.grid(row=1, column=0, sticky="ew", pady=10)

        ctk.CTkLabel(
            overview,
            text=(
                "Core modules:\n"
                "- AI-assisted content workflow\n"
                "- Smart video processing\n"
                "- Cloudinary delivery\n"
                "- Repliz scheduling\n"
                "- License-based plan control"
            ),
            text_color=TEXT_SOFT,
            justify="left",
            anchor="w",
        ).pack(fill="x", padx=22, pady=(0, 16))

        pricing_wrap = ctk.CTkFrame(outer, fg_color="transparent")
        pricing_wrap.grid(row=2, column=0, sticky="ew", pady=10)
        pricing_wrap.grid_columnconfigure((0, 1, 2), weight=1)

        self._build_plan_card(
            pricing_wrap,
            row=0,
            column=0,
            data=self.pricing.get("basic", {}),
            badge_color=BADGE_DARK,
            accent_color=TEXT_PRIMARY,
            pad=(0, 8),
        )

        self._build_plan_card(
            pricing_wrap,
            row=0,
            column=1,
            data=self.pricing.get("premium", {}),
            badge_color=BADGE_WARNING,
            accent_color=PRIMARY_ORANGE,
            pad=8,
        )

        self._build_plan_card(
            pricing_wrap,
            row=0,
            column=2,
            data=self.pricing.get("business", {}),
            badge_color=BADGE_SUCCESS,
            accent_color=GREEN,
            pad=(8, 0),
        )

        notes_card = make_card(
            outer,
            "Plan Policy Notes",
            "Important runtime policy and account-lock rules."
        )
        notes_card.grid(row=3, column=0, sticky="ew", pady=10)

        notes = self.pricing.get("notes", [])
        notes_text = "\n".join([f"- {item}" for item in notes]) if notes else "- No notes available."

        ctk.CTkLabel(
            notes_card,
            text=notes_text,
            text_color=TEXT_SOFT,
            justify="left",
            anchor="w",
            wraplength=920,
        ).pack(fill="x", padx=22, pady=(0, 16))

        footer = make_card(
            outer,
            "Support",
            "For Business onboarding, multi-PC deployment, and custom pricing, please contact admin."
        )
        footer.grid(row=4, column=0, sticky="ew", pady=10)

        ctk.CTkLabel(
            footer,
            text=(
                f"Config path: {pricing_path()}\n"
                "GNX Production Studio is designed to balance growth, automation, and account safety."
            ),
            text_color=TEXT_MUTED,
            wraplength=900,
            justify="left",
        ).pack(anchor="w", padx=22, pady=(0, 16))

    def _build_plan_card(self, parent, row, column, data, badge_color, accent_color, pad):
        title = str(data.get("title", "Plan"))
        badge_text = str(data.get("badge", ""))
        price_label = str(data.get("price_label", "-"))
        subtitle = str(data.get("subtitle", ""))
        items = data.get("items", [])
        action_label = str(data.get("action_label", "")).strip()
        action_url = str(data.get("action_url", "")).strip()

        card = ctk.CTkFrame(
            parent,
            fg_color=CARD,
            corner_radius=18,
            border_width=1,
            border_color=BORDER,
        )
        card.grid(row=row, column=column, sticky="nsew", padx=pad, pady=0)
        card.grid_columnconfigure(0, weight=1)

        badge = ctk.CTkLabel(
            card,
            text=badge_text,
            text_color=TEXT_PRIMARY,
            fg_color=badge_color,
            corner_radius=12,
            padx=12,
            pady=6,
        )
        badge.pack(anchor="w", padx=18, pady=(18, 10))

        ctk.CTkLabel(
            card,
            text=title,
            text_color=accent_color,
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(anchor="w", padx=18)

        ctk.CTkLabel(
            card,
            text=price_label,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=20, weight="bold"),
        ).pack(anchor="w", padx=18, pady=(8, 4))

        ctk.CTkLabel(
            card,
            text=subtitle,
            text_color=TEXT_MUTED,
            wraplength=260,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 12))

        items_box = ctk.CTkFrame(card, fg_color=CARD_SOFT, corner_radius=12)
        items_box.pack(fill="both", expand=True, padx=18, pady=(0, 12))

        if not isinstance(items, list):
            items = []

        for item in items:
            ctk.CTkLabel(
                items_box,
                text=f"• {item}",
                text_color=TEXT_SOFT,
                justify="left",
                anchor="w",
                wraplength=250,
            ).pack(fill="x", padx=14, pady=6)

        if action_label and action_url:
            ctk.CTkButton(
                card,
                text=action_label,
                fg_color=accent_color,
                hover_color=accent_color,
                text_color=TEXT_PRIMARY,
                height=40,
                command=lambda u=action_url: _open_url(u),
            ).pack(fill="x", padx=18, pady=(0, 18))
        else:
            ctk.CTkFrame(card, fg_color="transparent", height=10).pack(fill="x", padx=18, pady=(0, 18))