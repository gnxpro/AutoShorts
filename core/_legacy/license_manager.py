import requests
from core.logger import log

LICENSE_URL = "https://yourdomain.com/api/license"

# 🔥 TEMP DISABLE FLAG
LICENSE_ENFORCEMENT = False


def validate_license(license_key=None):

    # Jika enforcement dimatikan → selalu valid
    if not LICENSE_ENFORCEMENT:
        log("License enforcement disabled (dev mode).")
        return True

    try:
        response = requests.post(
            LICENSE_URL,
            json={"license_key": license_key},
            timeout=5
        )

        data = response.json()
        return data.get("valid", False)

    except Exception as e:
        log(f"License check failed: {e}")
        return True  # fallback allow