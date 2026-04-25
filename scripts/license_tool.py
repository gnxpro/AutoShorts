import argparse
from datetime import datetime, timedelta, timezone

from core.licensing.license_manager import LicenseManager


def main():
    ap = argparse.ArgumentParser(description="GNX Offline License Generator (HMAC)")
    ap.add_argument("--days", type=int, default=365, help="Masa aktif license (hari), contoh 30/365")
    ap.add_argument("--plan", type=str, default="PRO", help="Nama plan, contoh PRO")
    ap.add_argument("--max-accounts", type=int, default=100, help="Max multi-account")
    ap.add_argument("--name", type=str, default="", help="Nama customer (optional)")
    args = ap.parse_args()

    lm = LicenseManager()  # ambil secret dari env GNX_LICENSE_SECRET atau default

    now = datetime.now(timezone.utc)
    exp_dt = now + timedelta(days=args.days)

    payload = {
        "plan": args.plan,
        "exp": exp_dt.strftime("%Y-%m-%d"),     # YYYY-MM-DD
        "max_accounts": int(args.max_accounts),
        "iat": now.isoformat().replace("+00:00", "Z"),
        "name": args.name,
    }

    key = LicenseManager.create_license_key(payload, lm.secret)

    print("\n=== LICENSE PAYLOAD ===")
    print(payload)
    print("\n=== LICENSE KEY ===")
    print(key)
    print("\nNOTE: Simpan key ini. Berikan ke user untuk di-activate di About -> Licensing.\n")


if __name__ == "__main__":
    main()