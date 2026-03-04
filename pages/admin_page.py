import os
import customtkinter as ctk
from tkinter import messagebox

from core.licensing.license_manager import LicenseManager


PRIMARY_RED = #b11226
BLACK = #000000
CARD = #111111
TEXT_PRIMARY = #EDEDED
TEXT_MUTED = #B8B8B8


class AdminPage(ctk.CTkFrame)
    
    ADMIN ONLY
    - Generate license keys inside the app
    - Copy to clipboard
    

    def __init__(self, master)
        super().__init__(master, fg_color=BLACK)
        self.engine = master.master.master.engine
        self.lm = LicenseManager()

        self.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(self, fg_color=BLACK)
        header.grid(row=0, column=0, sticky=ew, padx=40, pady=(30, 10))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=Admin • License Generator,
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=28, weight=bold),
        ).grid(row=0, column=0, sticky=w)

        ctk.CTkLabel(
            header,
            text=Generate membership keys (offline). Keep this page hidden from members.,
            text_color=TEXT_MUTED,
        ).grid(row=1, column=0, sticky=w, pady=(6, 0))

        card = ctk.CTkFrame(self, fg_color=CARD, corner_radius=16)
        card.grid(row=1, column=0, sticky=ew, padx=40, pady=(10, 14))
        card.grid_columnconfigure(0, weight=1)

        self.plan_var = ctk.StringVar(value=PRO)

        row1 = ctk.CTkFrame(card, fg_color=transparent)
        row1.grid(row=0, column=0, sticky=ew, padx=18, pady=(14, 8))
        row1.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(row1, text=Plan, text_color=TEXT_PRIMARY).grid(row=0, column=0, sticky=w)
        self.plan_menu = ctk.CTkOptionMenu(
            row1, values=[BASIC, PRO], variable=self.plan_var,
            fg_color=#222222, button_color=#2a2a2a, button_hover_color=#3a3a3a,
            text_color=TEXT_PRIMARY, dropdown_text_color=TEXT_PRIMARY
        )
        self.plan_menu.grid(row=0, column=1, padx=10, sticky=ew)

        self.days_entry = ctk.CTkEntry(card, placeholder_text=Days (e.g. 30), text_color=TEXT_PRIMARY)
        self.days_entry.grid(row=1, column=0, sticky=ew, padx=18, pady=6)
        self.days_entry.insert(0, 30)

        self.max_entry = ctk.CTkEntry(card, placeholder_text=Max accounts (BASIC=5, PRO=100), text_color=TEXT_PRIMARY)
        self.max_entry.grid(row=2, column=0, sticky=ew, padx=18, pady=6)
        self.max_entry.insert(0, 100)

        self.name_entry = ctk.CTkEntry(card, placeholder_text='Client name (e.g. Client A)', text_color=TEXT_PRIMARY)
        self.name_entry.grid(row=3, column=0, sticky=ew, padx=18, pady=6)

        btn_row = ctk.CTkFrame(card, fg_color=transparent)
        btn_row.grid(row=4, column=0, sticky=ew, padx=18, pady=(10, 14))
        btn_row.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(
            btn_row, text=Generate,
            fg_color=PRIMARY_RED, hover_color=#7a0d1a, text_color=TEXT_PRIMARY,
            command=self._generate
        ).grid(row=0, column=0, padx=(0, 10), sticky=ew)

        ctk.CTkButton(
            btn_row, text=Copy Key,
            fg_color=#222222, hover_color=#333333, text_color=TEXT_PRIMARY,
            command=self._copy
        ).grid(row=0, column=1, padx=10, sticky=ew)

        ctk.CTkButton(
            btn_row, text=Clear,
            fg_color=#222222, hover_color=#333333, text_color=TEXT_PRIMARY,
            command=self._clear
        ).grid(row=0, column=2, padx=(10, 0), sticky=ew)

        self.out = ctk.CTkTextbox(card, height=160, fg_color=#0b0b0b, text_color=TEXT_PRIMARY)
        self.out.grid(row=5, column=0, sticky=ew, padx=18, pady=(0, 18))
        self.out.insert(1.0, Generated license key will appear here...n)

    def _generate(self)
        try
            plan = (self.plan_var.get() or PRO).strip().upper()
            days = int(self.days_entry.get().strip() or 30)

            # Max accounts rules
            # - Global cap is 100 for safety
            # - BASIC should be 5
            if plan == BASIC
                max_accounts = 5
            else
                max_accounts = int(self.max_entry.get().strip() or 100)
                if max_accounts  100
                    max_accounts = 100
                if max_accounts = 0
                    max_accounts = 100

            name = self.name_entry.get().strip()

            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)
            exp_dt = now + timedelta(days=days)

            payload = {
                plan plan,
                exp exp_dt.strftime(%Y-%m-%d),
                max_accounts max_accounts,
                iat now.isoformat().replace(+0000, Z),
                name name,
            }

            key = LicenseManager.create_license_key(payload, self.lm.secret)

            self.out.delete(1.0, end)
            self.out.insert(1.0, fPAYLOADn{payload}nnLICENSE KEYn{key}n)
            messagebox.showinfo(OK, License generated. Click Copy Key.)

        except Exception as e
            messagebox.showerror(Generate Error, str(e))

    def _copy(self)
        try
            txt = self.out.get(1.0, end).strip()
            if GNX1. not in txt
                messagebox.showerror(Copy, No license key found. Generate first.)
                return
            # get the last GNX1 line
            key = 
            for line in txt.splitlines()[-1]
                if line.strip().startswith(GNX1.)
                    key = line.strip()
                    break
            if not key
                messagebox.showerror(Copy, No license key found.)
                return

            self.clipboard_clear()
            self.clipboard_append(key)
            messagebox.showinfo(Copied, License key copied to clipboard.)
        except Exception as e
            messagebox.showerror(Copy Error, str(e))

    def _clear(self)
        self.out.delete(1.0, end)
        self.out.insert(1.0, Generated license key will appear here...n)