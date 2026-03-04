from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple


APP_NAME = "GNX_PRODUCTION"
LICENSE_FILE_NAME = "license.json"

DEFAULT_LICENSE_SECRET = "GNX_SECRET_CHANGE_ME_BEFORE_RELEASE_2026"
GLOBAL_MAX_ACCOUNTS_CAP = 100  # ✅ hard cap for safety


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + pad).encode("utf-8"))


def _json_dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_iso(s: str) -> datetime:
    if s.endswith("Z"):
        s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s).astimezone(timezone.utc)


def _appdata_dir() -> Path:
    base = os.getenv("LOCALAPPDATA")
    if base:
        d = Path(base) / APP_NAME
    else:
        d = Path.home() / "AppData" / "Local" / APP_NAME
    d.mkdir(parents=True, exist_ok=True)
    return d


@dataclass
class LicenseStatus:
    ok: bool
    mode: str          # trial | license | free
    plan: str          # FREE | BASIC | PRO | TRIAL
    days_left: int
    expires_at: Optional[str]
    max_accounts: int
    message: str


class LicenseManager:
    """
    QUICK OFFLINE licensing:
    - Trial auto-start (default 7 days)
    - After trial expires => FREE mode (offline-only, no AI, no schedule, 5 accounts)
    - License key = HMAC signature GNX1.<payload>.<sig>
    """

    def __init__(self):
        self.storage_dir = _appdata_dir()
        self.license_path = self.storage_dir / LICENSE_FILE_NAME

        self.secret = os.getenv("GNX_LICENSE_SECRET", "").strip() or DEFAULT_LICENSE_SECRET
        self.default_trial_days = int(os.getenv("GNX_TRIAL_DAYS", "7") or "7")

        self._ensure_initialized()

    # ------------------------------
    # Storage
    # ------------------------------
    def _read(self) -> Dict[str, Any]:
        if not self.license_path.exists():
            return {}
        try:
            return json.loads(self.license_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write(self, data: Dict[str, Any]) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.license_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _ensure_initialized(self) -> None:
        data = self._read()
        if data.get("mode") in ("trial", "license"):
            return
        self.start_trial(self.default_trial_days)

    # ------------------------------
    # Trial
    # ------------------------------
    def start_trial(self, days: int) -> LicenseStatus:
        days = int(days)
        if days <= 0:
            days = 7
        now = _utcnow()
        data = {
            "mode": "trial",
            "trial_start": _iso(now),
            "trial_days": days,
            "max_accounts": GLOBAL_MAX_ACCOUNTS_CAP,
            "last_seen_utc": _iso(now),
        }
        self._write(data)
        return self.get_status()

    # ------------------------------
    # License key (HMAC)
    # ------------------------------
    @classmethod
    def create_license_key(cls, payload: Dict[str, Any], secret: str) -> str:
        payload_json = _json_dumps(payload).encode("utf-8")
        p = _b64url_encode(payload_json)
        sig = hmac.new(secret.encode("utf-8"), p.encode("utf-8"), hashlib.sha256).digest()
        s = _b64url_encode(sig)
        return f"GNX1.{p}.{s}"

    @classmethod
    def verify_license_key(cls, key: str, secret: str) -> Dict[str, Any]:
        key = (key or "").strip()
        if not key.startswith("GNX1."):
            raise ValueError("Invalid license format (must start with GNX1.)")
        parts = key.split(".")
        if len(parts) != 3:
            raise ValueError("Invalid license format (GNX1.<payload>.<sig>)")

        _, p, s = parts
        expected = hmac.new(secret.encode("utf-8"), p.encode("utf-8"), hashlib.sha256).digest()
        got = _b64url_decode(s)

        if not hmac.compare_digest(expected, got):
            raise ValueError("Invalid license signature")

        payload_json = _b64url_decode(p).decode("utf-8")
        payload = json.loads(payload_json)

        if "exp" not in payload:
            raise ValueError("License payload must contain exp (YYYY-MM-DD)")
        if "plan" not in payload:
            payload["plan"] = "PRO"
        if "max_accounts" not in payload:
            payload["max_accounts"] = GLOBAL_MAX_ACCOUNTS_CAP

        # ✅ hard cap 100
        payload["max_accounts"] = min(int(payload.get("max_accounts", GLOBAL_MAX_ACCOUNTS_CAP)), GLOBAL_MAX_ACCOUNTS_CAP)

        return payload

    def activate_license(self, key: str) -> LicenseStatus:
        payload = self.verify_license_key(key, self.secret)
        now = _utcnow()
        data = {
            "mode": "license",
            "license_key": key.strip(),
            "payload": payload,
            "activated_at": _iso(now),
            "last_seen_utc": _iso(now),
        }
        self._write(data)
        return self.get_status()

    # ------------------------------
    # Capabilities (plan rules)
    # ------------------------------
    def get_capabilities(self) -> Dict[str, Any]:
        st = self.get_status()
        plan = (st.plan or "FREE").upper()

        # Defaults
        caps = {
            "plan": plan,
            "allow_youtube": False,
            "allow_ai": False,
            "allow_schedule": False,
            "max_accounts": min(int(st.max_accounts), GLOBAL_MAX_ACCOUNTS_CAP),
        }

        # FREE: offline only, no AI, no schedule, max 5 accounts (for safety display)
        if plan == "FREE":
            caps.update({"allow_youtube": False, "allow_ai": False, "allow_schedule": False, "max_accounts": 5})
            return caps

        # BASIC: offline only, no AI, schedule allowed but max 5 accounts
        if plan == "BASIC":
            caps.update({"allow_youtube": False, "allow_ai": False, "allow_schedule": True, "max_accounts": 5})
            return caps

        # TRIAL: treat as PRO but still cap 100
        if plan == "TRIAL":
            caps.update({"allow_youtube": True, "allow_ai": True, "allow_schedule": True, "max_accounts": GLOBAL_MAX_ACCOUNTS_CAP})
            return caps

        # PRO (default)
        caps.update({"allow_youtube": True, "allow_ai": True, "allow_schedule": True, "max_accounts": GLOBAL_MAX_ACCOUNTS_CAP})
        return caps

    # ------------------------------
    # Status / checks
    # ------------------------------
    def get_status(self) -> LicenseStatus:
        data = self._read()
        now = _utcnow()

        mode = data.get("mode", "free")

        # update last_seen
        if mode in ("trial", "license"):
            data["last_seen_utc"] = _iso(now)
            self._write(data)

        # TRIAL
        if mode == "trial":
            start = _parse_iso(data.get("trial_start", _iso(now)))
            days = int(data.get("trial_days", 7))
            exp = start + timedelta(days=days)
            days_left = max(0, (exp - now).days)

            if now < exp:
                return LicenseStatus(
                    ok=True,
                    mode="trial",
                    plan="TRIAL",
                    days_left=days_left,
                    expires_at=_iso(exp),
                    max_accounts=GLOBAL_MAX_ACCOUNTS_CAP,
                    message=f"TRIAL active. {days_left} day(s) left.",
                )

            # ✅ Trial expired -> FREE mode (still usable offline)
            return LicenseStatus(
                ok=True,
                mode="free",
                plan="FREE",
                days_left=0,
                expires_at=_iso(exp),
                max_accounts=5,
                message="TRIAL expired. Switched to FREE mode (Offline only, AI disabled).",
            )

        # LICENSE
        if mode == "license":
            payload = data.get("payload") or {}
            plan = str(payload.get("plan", "PRO")).upper()
            max_accounts = min(int(payload.get("max_accounts", GLOBAL_MAX_ACCOUNTS_CAP)), GLOBAL_MAX_ACCOUNTS_CAP)

            exp_date = str(payload.get("exp", "")).strip()  # YYYY-MM-DD
            if not exp_date:
                # fallback to FREE
                return LicenseStatus(True, "free", "FREE", 0, None, 5, "Invalid license. Switched to FREE mode.")

            exp_dt = datetime.fromisoformat(exp_date).replace(tzinfo=timezone.utc) + timedelta(days=1)
            days_left = max(0, (exp_dt - now).days)

            if now < exp_dt:
                return LicenseStatus(
                    ok=True,
                    mode="license",
                    plan=plan,
                    days_left=days_left,
                    expires_at=_iso(exp_dt),
                    max_accounts=max_accounts,
                    message=f"LICENSE active ({plan}). {days_left} day(s) left.",
                )

            # ✅ License expired -> FREE mode
            return LicenseStatus(
                ok=True,
                mode="free",
                plan="FREE",
                days_left=0,
                expires_at=_iso(exp_dt),
                max_accounts=5,
                message="LICENSE expired. Switched to FREE mode (Offline only, AI disabled).",
            )

        # default: FREE
        return LicenseStatus(
            ok=True,
            mode="free",
            plan="FREE",
            days_left=0,
            expires_at=None,
            max_accounts=5,
            message="FREE mode (Offline only, AI disabled).",
        )

    def check_allowed(self, *, required_accounts: int = 0) -> Tuple[bool, str, LicenseStatus]:
        st = self.get_status()
        caps = self.get_capabilities()

        # enforce max accounts (hard cap 100, and plan cap 5 for FREE/BASIC)
        if required_accounts > int(caps["max_accounts"]):
            return False, f"Account limit exceeded: {required_accounts}/{caps['max_accounts']}", st

        return True, "OK", st

    def info_paths(self) -> Dict[str, str]:
        return {
            "storage_dir": str(self.storage_dir),
            "license_path": str(self.license_path),
        }