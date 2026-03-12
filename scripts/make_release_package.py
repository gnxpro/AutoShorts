from pathlib import Path
import argparse
import shutil

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


INSTALL_PS1 = r'''New-Item -ItemType Directory -Force "$env:LOCALAPPDATA\GNX_PRODUCTION" | Out-Null
Copy-Item "$PSScriptRoot\license.gnxlic" "$env:LOCALAPPDATA\GNX_PRODUCTION\license.gnxlic" -Force

Write-Host ""
Write-Host "License installed successfully."
Write-Host "Please restart GNX Production Studio."
Write-Host "The plan will remain active only when the registered Repliz account is connected."
Write-Host ""
Pause
'''


def main():
    parser = argparse.ArgumentParser(description="Create GNX member release package")
    parser.add_argument("--plan", required=True, choices=["BASIC", "PREMIUM", "BUSINESS"])
    parser.add_argument("--member", required=True, help="member slug, example: member01")
    parser.add_argument("--issued-to", required=True, help="display name / member id")
    parser.add_argument("--license-id", required=True, help="unique license id")
    parser.add_argument("--repliz-user-id", default=None)
    parser.add_argument("--repliz-primary-account-id", default=None)
    parser.add_argument("--expires-at", default=None)
    parser.add_argument("--output-root", default="release", help="root output folder")
    parser.add_argument("--copy-installer", default="", help="optional path to installer exe")
    args = parser.parse_args()

    plan = args.plan.upper().strip()
    member = args.member.strip()

    if plan == "BASIC":
        features = basic_features()
    elif plan == "PREMIUM":
        features = premium_features()
    else:
        features = business_features()

    out_dir = Path(args.output_root) / f"{member}_{plan.lower()}"
    out_dir.mkdir(parents=True, exist_ok=True)

    license_path = out_dir / "license.gnxlic"
    export_signed_license_file(
        output_path=str(license_path),
        license_id=args.license_id,
        plan=plan,
        issued_to=args.issued_to,
        repliz_user_id=args.repliz_user_id,
        repliz_primary_account_id=args.repliz_primary_account_id,
        expires_at=args.expires_at,
        features=features,
    )

    ps1_path = out_dir / "install_license.ps1"
    ps1_path.write_text(INSTALL_PS1, encoding="utf-8")

    if args.copy_installer:
        installer_src = Path(args.copy_installer)
        if installer_src.exists() and installer_src.is_file():
            shutil.copy2(installer_src, out_dir / installer_src.name)

    readme = out_dir / "README_INSTALL.txt"
    readme.write_text(
        "\n".join([
            "GNX Production Studio License Package",
            "",
            "1. Close GNX Production Studio if it is running.",
            "2. Right-click install_license.ps1",
            "3. Choose 'Run with PowerShell'",
            "4. Restart GNX Production Studio",
            "5. Connect the registered Repliz account",
            "",
            "If a different Repliz account is connected, the app will run in Basic mode.",
        ]),
        encoding="utf-8",
    )

    print(f"[OK] Package created: {out_dir}")


if _name_ == "_main_":
    main()