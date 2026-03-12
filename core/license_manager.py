import os
import json
import base64
import hashlib
import hmac
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional


APP_DIR_NAME = "GNX_PRODUCTION"
LICENSE_FILENAME = "license.gnxlic"
RUNTIME_STATE_FILENAME = "runtime_state.json"

LICENSE_SECRET = "GNX_PRODUCTION_LICENSE_SECRET_V2_2026_REPLIZ_LOCK"


# =========================================================
# PATHS
# =========================================================

def _appdata_dir() -> Path:
    base = os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    p = Path(base) / APP_DIR_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def _license_path() -> Path:
    return _appdata_dir() / LICENSE_FILENAME


def _runtime_state_path() -> Path:
    return _appdata_dir() / RUNTIME_STATE_FILENAME


def _repliz_config_path() -> Path:
    return _appdata_dir() / "repliz.json"


def get_license_path() -> str:
    return str(_license_path())


def get_runtime_state_path() -> str:
    return str(_runtime_state_path())


# =========================================================
# JSON SIGNATURE
# =========================================================

def _canonical_json(data: Dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sign_payload(payload: Dict[str, Any]) -> str:
    raw = _canonical_json(payload).encode("utf-8")
    sig = hmac.new(LICENSE_SECRET.encode("utf-8"), raw, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).decode("utf-8")


def _verify_signature(payload: Dict[str, Any], signature: str) -> bool:
    expected = _sign_payload(payload)
    return hmac.compare_digest(expected, signature or "")


# =========================================================
# TIME
# =========================================================

def _utc_now():
    return datetime.now(timezone.utc)


def _parse_iso_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


# =========================================================
# FEATURES
# =========================================================

def _basic_features():
    return {
        "max_social_accounts": 2,
        "daily_video_limit": 2,
        "monthly_video_limit": 60,
        "quality_options": ["480p"],
        "default_quality": "480p",
        "allow_youtube": True,
        "allow_ai": True,
        "allow_schedule": True,
    }


def _premium_features():
    return {
        "max_social_accounts": 100,
        "daily_video_limit": 8,
        "monthly_video_limit": 240,
        "quality_options": ["480p", "720p", "1080p"],
        "default_quality": "1080p",
        "allow_youtube": True,
        "allow_ai": True,
        "allow_schedule": True,
    }


def _business_features():
    return {
        "max_social_accounts": None,
        "daily_video_limit": None,
        "monthly_video_limit": None,
        "quality_options": ["480p", "720p", "1080p", "4K"],
        "default_quality": "1080p",
        "allow_youtube": True,
        "allow_ai": True,
        "allow_schedule": True,
        "per_device_social_block": 100,
    }


# =========================================================
# BASIC LICENSE
# =========================================================

def _default_basic_license():
    payload = {
        "license_id": "GNX-BASIC-LOCAL",
        "plan": "BASIC",
        "issued_to": "local_user",
        "repliz_user_id": None,
        "repliz_primary_account_id": None,
        "expires_at": None,
        "features": _basic_features(),
        "issued_at": _utc_now().isoformat(),
    }
    return {**payload, "signature": _sign_payload(payload)}


# =========================================================
# NORMALIZATION
# =========================================================

def _normalize_caps_from_license(license_data: Dict[str, Any]) -> Dict[str, Any]:
    plan = str(license_data.get("plan", "BASIC")).upper().strip()
    features = dict(license_data.get("features") or {})

    base_features = _basic_features()
    if plan == "PREMIUM":
        base_features = _premium_features()
    elif plan == "BUSINESS":
        base_features = _business_features()

    merged_features = dict(base_features)
    merged_features.update(features)

    return {
        "license_id": str(license_data.get("license_id", "")),
        "plan": plan,
        "issued_to": str(license_data.get("issued_to", "")),
        "repliz_user_id": license_data.get("repliz_user_id"),
        "repliz_primary_account_id": license_data.get("repliz_primary_account_id"),
        "expires_at": license_data.get("expires_at"),
        "max_social_accounts": merged_features.get("max_social_accounts"),
        "daily_video_limit": merged_features.get("daily_video_limit"),
        "monthly_video_limit": merged_features.get("monthly_video_limit"),
        "quality_options": merged_features.get("quality_options"),
        "default_quality": merged_features.get("default_quality"),
        "allow_youtube": merged_features.get("allow_youtube"),
        "allow_ai": merged_features.get("allow_ai"),
        "allow_schedule": merged_features.get("allow_schedule"),
        "per_device_social_block": merged_features.get("per_device_social_block"),
    }


# =========================================================
# LICENSE LOAD
# =========================================================

def ensure_license_exists():
    p = _license_path()

    if not p.exists():
        basic = _default_basic_license()
        p.write_text(json.dumps(basic, indent=2), encoding="utf-8")

    return p


def load_raw_license():
    p = ensure_license_exists()
    return json.loads(p.read_text(encoding="utf-8"))


def validate_license_data(license_data: Dict[str, Any]):
    required = ["license_id", "plan", "issued_to", "features", "issued_at", "signature"]
    for key in required:
        if key not in license_data:
            raise ValueError(f"License field missing: {key}")

    signature = license_data.get("signature")
    payload = dict(license_data)
    payload.pop("signature", None)

    if not _verify_signature(payload, signature):
        raise ValueError("Invalid license signature")

    expires_at = _parse_iso_datetime(license_data.get("expires_at"))
    if expires_at and _utc_now() > expires_at:
        raise ValueError("License expired")

    return _normalize_caps_from_license(payload)


def load_license_capabilities():
    try:
        raw = load_raw_license()
        return validate_license_data(raw)
    except Exception as e:
        print("[LICENSE] invalid license, fallback to BASIC:", e)
        return _normalize_caps_from_license(_default_basic_license())


# =========================================================
# SAVE LICENSE
# =========================================================

def save_signed_license(
    license_id: str,
    plan: str,
    issued_to: str,
    repliz_user_id=None,
    repliz_primary_account_id=None,
    expires_at=None,
    features: Optional[Dict[str, Any]] = None,
):
    plan = str(plan or "BASIC").upper().strip()

    if plan == "PREMIUM":
        default_features = _premium_features()
    elif plan == "BUSINESS":
        default_features = _business_features()
    else:
        default_features = _basic_features()

    merged_features = dict(default_features)
    merged_features.update(features or {})

    payload = {
        "license_id": license_id,
        "plan": plan,
        "issued_to": issued_to,
        "repliz_user_id": repliz_user_id,
        "repliz_primary_account_id": repliz_primary_account_id,
        "expires_at": expires_at,
        "features": merged_features,
        "issued_at": _utc_now().isoformat(),
    }

    signed = {**payload, "signature": _sign_payload(payload)}

    p = _license_path()
    p.write_text(json.dumps(signed, indent=2), encoding="utf-8")
    return p


def export_signed_license_file(
    output_path: str,
    license_id: str,
    plan: str,
    issued_to: str,
    repliz_user_id=None,
    repliz_primary_account_id=None,
    expires_at=None,
    features: Optional[Dict[str, Any]] = None,
):
    plan = str(plan or "BASIC").upper().strip()

    if plan == "PREMIUM":
        default_features = _premium_features()
    elif plan == "BUSINESS":
        default_features = _business_features()
    else:
        default_features = _basic_features()

    merged_features = dict(default_features)
    merged_features.update(features or {})

    payload = {
        "license_id": str(license_id).strip(),
        "plan": plan,
        "issued_to": str(issued_to).strip(),
        "repliz_user_id": repliz_user_id,
        "repliz_primary_account_id": repliz_primary_account_id,
        "expires_at": expires_at,
        "features": merged_features,
        "issued_at": _utc_now().isoformat(),
    }

    signed_license = {**payload, "signature": _sign_payload(payload)}

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(signed_license, ensure_ascii=False, indent=2), encoding="utf-8")


# =========================================================
# RUNTIME STATE
# =========================================================

def _default_runtime_state() -> Dict[str, Any]:
    return {
        "effective_plan": "BASIC",
        "last_repliz_user_id": None,
        "last_repliz_primary_account_id": None,
        "last_social_count": 0,
        "business_charge_units_this_device": 0,
    }


def load_runtime_state() -> Dict[str, Any]:
    p = _runtime_state_path()
    if not p.exists():
        state = _default_runtime_state()
        p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return state

    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        state = _default_runtime_state()
        p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        return state


def save_runtime_state(state: Dict[str, Any]) -> Path:
    merged = _default_runtime_state()
    merged.update(state or {})
    p = _runtime_state_path()
    p.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


# =========================================================
# REPLIZ CONFIG
# =========================================================

def _load_repliz_runtime():
    path = _repliz_config_path()

    if not path.exists():
        return {
            "repliz_user_id": None,
            "repliz_primary_account_id": None,
        }

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "repliz_user_id": None,
            "repliz_primary_account_id": None,
        }

    return {
        "repliz_user_id": (
            data.get("repliz_user_id")
            or data.get("user_id")
            or data.get("connected_user_id")
        ),
        "repliz_primary_account_id": (
            data.get("repliz_primary_account_id")
            or data.get("account_id")
        ),
    }


# =========================================================
# RUNTIME PLAN
# =========================================================

def calculate_business_charge_units(social_count: int, per_device_block: Optional[int]) -> int:
    try:
        social_count = int(social_count or 0)
    except Exception:
        social_count = 0

    try:
        per_device_block = int(per_device_block or 100)
    except Exception:
        per_device_block = 100

    if social_count <= 0:
        return 0
    return (social_count + per_device_block - 1) // per_device_block


def validate_repliz_binding(license_caps, repliz_user_id, repliz_primary_account_id, social_count: int = 0):
    plan = str(license_caps.get("plan", "BASIC")).upper().strip()

    result = dict(license_caps)
    result["effective_plan"] = plan
    result["binding_valid"] = True
    result["blocked_for_social_limit"] = False
    result["repliz_connected_user_id"] = repliz_user_id
    result["repliz_connected_primary_account_id"] = repliz_primary_account_id
    result["social_count"] = int(social_count or 0)
    result["business_charge_units_this_device"] = 0

    if plan == "BASIC":
        return result

    licensed_user_id = license_caps.get("repliz_user_id")
    licensed_primary_account_id = license_caps.get("repliz_primary_account_id")

    def _fallback(reason: str):
        fallback = _normalize_caps_from_license(_default_basic_license())
        fallback["license_id"] = result.get("license_id", "")
        fallback["issued_to"] = result.get("issued_to", "")
        fallback["effective_plan"] = "BASIC"
        fallback["binding_valid"] = False
        fallback["blocked_for_social_limit"] = False
        fallback["repliz_connected_user_id"] = repliz_user_id
        fallback["repliz_connected_primary_account_id"] = repliz_primary_account_id
        fallback["social_count"] = int(social_count or 0)
        fallback["fallback_reason"] = reason
        fallback["repliz_user_id"] = licensed_user_id
        fallback["repliz_primary_account_id"] = licensed_primary_account_id
        return fallback

    # Main lock = primary account
    if licensed_primary_account_id:
        if not repliz_primary_account_id:
            return _fallback("repliz_not_connected")

        if str(repliz_primary_account_id).strip() != str(licensed_primary_account_id).strip():
            return _fallback("repliz_primary_account_mismatch")

    # Optional extra validation only when current app has user id
    if licensed_user_id and repliz_user_id:
        if str(repliz_user_id).strip() != str(licensed_user_id).strip():
            return _fallback("repliz_user_mismatch")

    if plan == "PREMIUM":
        max_social_accounts = result.get("max_social_accounts")
        if max_social_accounts is not None and int(social_count or 0) > int(max_social_accounts):
            result["blocked_for_social_limit"] = True
        return result

    if plan == "BUSINESS":
        block = result.get("per_device_social_block") or 100
        result["business_charge_units_this_device"] = calculate_business_charge_units(
            social_count=int(social_count or 0),
            per_device_block=block,
        )
        return result

    return result


# =========================================================
# EFFECTIVE CAPABILITIES
# =========================================================

def apply_repliz_runtime_state(
    repliz_user_id=None,
    repliz_primary_account_id=None,
    social_count: Optional[int] = None,
):
    license_caps = load_license_capabilities()

    effective = validate_repliz_binding(
        license_caps=license_caps,
        repliz_user_id=repliz_user_id,
        repliz_primary_account_id=repliz_primary_account_id,
        social_count=int(social_count or 0),
    )

    save_runtime_state({
        "effective_plan": effective.get("effective_plan", "BASIC"),
        "last_repliz_user_id": repliz_user_id,
        "last_repliz_primary_account_id": repliz_primary_account_id,
        "last_social_count": int(social_count or 0),
        "business_charge_units_this_device": effective.get("business_charge_units_this_device", 0),
    })

    return effective


def load_effective_capabilities():
    license_caps = load_license_capabilities()
    state = load_runtime_state()
    repliz = _load_repliz_runtime()

    social_count = int(state.get("last_social_count", 0) or 0)

    effective = validate_repliz_binding(
        license_caps=license_caps,
        repliz_user_id=repliz.get("repliz_user_id"),
        repliz_primary_account_id=repliz.get("repliz_primary_account_id"),
        social_count=social_count,
    )

    save_runtime_state({
        "effective_plan": effective.get("effective_plan", "BASIC"),
        "last_repliz_user_id": repliz.get("repliz_user_id"),
        "last_repliz_primary_account_id": repliz.get("repliz_primary_account_id"),
        "last_social_count": social_count,
        "business_charge_units_this_device": effective.get("business_charge_units_this_device", 0),
    })

    return effective