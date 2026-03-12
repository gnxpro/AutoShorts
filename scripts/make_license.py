import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.license_manager import export_signed_license_file


def basic_features():
    return {
        "max_social_accounts": 2,
        "daily_video_limit": 2,
        "monthly_video_limit": 60,
        "quality_options": ["480p"],
        "default_quality": "480p",
        "allow_youtube": True,
        "allow_ai": True,
        "allow_schedule": True,
        "installation_policy": "unlimited",
        "billing_mode": "none",
        "admin_managed": False,
        "per_device_social_block": None,
    }


def premium_features():
    return {
        "max_social_accounts": 100,
        "daily_video_limit": 8,
        "monthly_video_limit": 240,
        "quality_options": ["480p", "720p", "1080p"],
        "default_quality": "1080p",
        "allow_youtube": True,
        "allow_ai": True,
        "allow_schedule": True,
        "installation_policy": "unlimited",
        "billing_mode": "fixed_plan",
        "admin_managed": False,
        "per_device_social_block": None,
    }


def business_features():
    return {
        "max_social_accounts": None,
        "daily_video_limit": None,
        "monthly_video_limit": None,
        "quality_options": ["480p", "720p", "1080p", "4K"],
        "default_quality": "1080p",
        "allow_youtube": True,
        "allow_ai": True,
        "allow_schedule": True,
        "installation_policy": "unlimited",
        "billing_mode": "per_100_accounts_per_device",
        "admin_managed": True,
        "per_device_social_block": 100,
    }


def main():
    parser = argparse.ArgumentParser(description="GNX License Generator")
    parser.add_argument("--plan", required=True, choices=["BASIC", "PREMIUM", "BUSINESS"])
    parser.add_argument("--issued-to", required=True)
    parser.add_argument("--license-id", required=True)
    parser.add_argument("--repliz-user-id", default=None)
    parser.add_argument("--repliz-primary-account-id", default=None)
    parser.add_argument("--expires-at", default=None)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    plan = args.plan.upper().strip()

    if plan == "BASIC":
        features = basic_features()
    elif plan == "PREMIUM":
        features = premium_features()
    else:
        features = business_features()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    export_signed_license_file(
        output_path=str(output_path),
        license_id=args.license_id,
        plan=plan,
        issued_to=args.issued_to,
        repliz_user_id=args.repliz_user_id,
        repliz_primary_account_id=args.repliz_primary_account_id,
        expires_at=args.expires_at,
        features=features,
    )

    print(f"[OK] License created: {output_path}")


if __name__ == "__main__":
    main()