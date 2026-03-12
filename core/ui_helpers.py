# core/ui_helpers.py

import customtkinter as ctk

from core.theme_constants import (
    CARD,
    CARD_SOFT,
    BORDER,
    PRIMARY_RED,
    TEXT_PRIMARY,
    TEXT_MUTED,
)


def make_card(parent, title, subtitle=None):
    card = ctk.CTkFrame(
        parent,
        fg_color=CARD,
        corner_radius=18,
        border_width=1,
        border_color=BORDER,
    )
    card.grid_columnconfigure(0, weight=1)

    ctk.CTkLabel(
        card,
        text=title,
        text_color=PRIMARY_RED,
        font=ctk.CTkFont(size=15, weight="bold"),
    ).pack(anchor="w", padx=22, pady=(16, 6))

    if subtitle:
        ctk.CTkLabel(
            card,
            text=subtitle,
            text_color=TEXT_MUTED,
            wraplength=820,
            justify="left",
        ).pack(anchor="w", padx=22, pady=(0, 12))

    return card


def make_stat_card(parent, title, value="-"):
    card = ctk.CTkFrame(
        parent,
        fg_color=CARD_SOFT,
        corner_radius=14,
        border_width=1,
        border_color=BORDER,
    )

    ctk.CTkLabel(
        card,
        text=title,
        text_color=TEXT_MUTED,
        font=ctk.CTkFont(size=11),
    ).pack(anchor="w", padx=12, pady=(10, 4))

    value_label = ctk.CTkLabel(
        card,
        text=value,
        text_color=TEXT_PRIMARY,
        font=ctk.CTkFont(size=18, weight="bold"),
    )
    value_label.pack(anchor="w", padx=12, pady=(0, 10))

    return card, value_label


def make_section_badge(parent, text):
    return ctk.CTkLabel(
        parent,
        text=text,
        text_color=TEXT_PRIMARY,
        fg_color="#1f1f1f",
        corner_radius=12,
        padx=14,
        pady=7,
    )