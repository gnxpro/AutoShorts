import os
import sys
import requests
import shutil
from core.app_paths import get_base_data_dir
from core.logger import log

VERSION_URL = "https://yourdomain.com/gnx_version.json"
DOWNLOAD_URL = "https://yourdomain.com/GNX_PRODUCTION.exe"
CURRENT_VERSION = "2.0.0"


def check_for_update():
    try:
        response = requests.get(VERSION_URL, timeout=5)
        data = response.json()

        latest = data.get("version")

        if latest != CURRENT_VERSION:
            download_update()

    except Exception as e:
        log(f"Update check failed: {e}")


def download_update():
    try:
        base_dir = get_base_data_dir()
        temp_path = os.path.join(base_dir, "GNX_update.exe")

        response = requests.get(DOWNLOAD_URL, stream=True)

        with open(temp_path, "wb") as f:
            shutil.copyfileobj(response.raw, f)

        # Replace on next start
        os.startfile(temp_path)

    except Exception as e:
        log(f"Update failed: {e}")