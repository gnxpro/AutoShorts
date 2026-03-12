# core/licensing/license_manager.py
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional
import os

try:
    # optional: use your existing settings store if available
    from core.settings_store import load_config, get as cfg_get  # type: ignore
except Exception:
    load_config = None
    cfg_get = None


@dataclass
class LicenseStatus:
    ok: bool = True
    mode: str = "disabled"            # licensing disabled
    plan: str = "PREMIUM"             # BASIC / PREMIUM / BUSINESS
    days_left: Optional[int] = None
    expires_at: Optional[str] = None
    message: str = "Licensing is disabled (plan-based access)."


class LicenseManager:
    """
    Licensing disabled.
    Capabilities are determined by plan:
    - BASIC: lifetime, max 2 accounts (IG + YouTube only), AI enabled
    - PREMIUM: max 100 accounts, all services enabled
    - BUSINESS: max 100 accounts, all services enabled (+ support handled commercially, not in app)
    """

    def __init__(self):
        self._status = LicenseStatus(plan=self._get_plan())

    # ---------------------------
    # Plan source
    # ---------------------------
    def _get_plan(self) -> str:
        # 1) Env override (recommended for different installers)
        env_plan = (os.getenv("GNX_PLAN") or "").strip().upper()
        if env_plan in ("BASIC", "PREMIUM", "BUSINESS"):
            return env_plan

        # 2) Config fallback (AppData gnx_config.json if you store it)
        if load_config and cfg_get:
            try:
                cfg = load_config()
                cfg_plan = str(cfg_get(cfg, "app.plan", "PREMIUM")).strip().upper()
                if cfg_plan in ("BASIC", "PREMIUM", "BUSINESS"):
                    return cfg_plan
            except Exception:
                pass

        return "PREMIUM"

    # ---------------------------
    # Status & capabilities
    # ---------------------------
    def get_status(self) -> LicenseStatus:
        # refresh plan dynamically
        self._status.plan = self._get_plan()
        return self._status

    def get_capabilities(self) -> Dict[str, Any]:
        plan = self._get_plan()

        # Defaults = premium-like
        caps: Dict[str, Any] = {
            "plan": plan,
            "allow_youtube": True,     # YouTube as source video
            "allow_ai": True,          # hooks/subtitle/niche/hashtags
            "allow_schedule": True,    # schedule to Repliz
            "max_accounts": 100,       # safety cap
            # Optional: used by Repliz page to filter visible accounts
            "allowed_repliz_types": None,  # None = all
            # Optional: show in About/Business plan
            "support_level": "standard",
        }

        if plan == "BASIC":
            caps["max_accounts"] = 2
            caps["allow_youtube"] = True
            caps["allow_ai"] = True
            caps["allow_schedule"] = True
            # Only IG + YouTube (enforced best at UI selection)
            caps["allowed_repliz_types"] = ["instagram", "youtube"]
            caps["support_level"] = "basic"

        elif plan == "PREMIUM":
            caps["max_accounts"] = 100
            caps["allowed_repliz_types"] = None
            caps["support_level"] = "premium"

        elif plan == "BUSINESS":
            caps["max_accounts"] = 100
            caps["allowed_repliz_types"] = None
            caps["support_level"] = "business"

        return caps

    # ---------------------------
    # No-op license API (kept for compatibility)
    # ---------------------------
    def activate_license(self, key: str) -> LicenseStatus:
        # licensing disabled
        st = self.get_status()
        st.message = "License activation is disabled (plan-based access)."
        return st

    def start_trial(self, days: int) -> LicenseStatus:
        # licensing disabled
        st = self.get_status()
        st.message = "Trial is disabled (plan-based access)."
        return st

    def check_allowed(self, required_accounts: int = 0) -> tuple[bool, str, Dict[str, Any]]:
        caps = self.get_capabilities()
        max_accounts = int(caps.get("max_accounts", 100))

        if required_accounts > max_accounts:
            return (
                False,
                f"Plan limit reached: max {max_accounts} accounts, requested {required_accounts}.",
                caps,
            )

        return True, "OK", caps