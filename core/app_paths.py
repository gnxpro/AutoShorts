import os
import sys
import re
from datetime import datetime


APP_NAME = "GNX_PRODUCTION"


# ============================================
# SAFE FILE NAME
# ============================================

def sanitize_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    name = name.replace(" ", "_")
    return name[:80]


# ============================================
# DESKTOP PATH
# ============================================

def get_desktop_path():
    return os.path.join(os.path.expanduser("~"), "Desktop")


# ============================================
# BASE DATA (CONFIG, LOGS, TEMP)
# ============================================

def get_base_data_dir():
    base_dir = os.path.join(
        os.getenv("LOCALAPPDATA"),
        "GNX_PRODUCTION"
    )
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


# ============================================
# LOGS PATH (FIX FOR LOGGER)
# ============================================

def get_logs_path():
    base_dir = get_base_data_dir()
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    return logs_dir


# ============================================
# SESSION AUTO INCREMENT
# ============================================

def get_next_session_folder(base_path):

    session_index = 1

    while True:
        folder_name = f"Run_{session_index:02d}"
        full_path = os.path.join(base_path, folder_name)

        if not os.path.exists(full_path):
            os.makedirs(full_path)
            return full_path

        session_index += 1


# ============================================
# ULTIMATE OUTPUT SYSTEM
# ============================================

def get_output_path(mode, title="Untitled"):

    desktop = get_desktop_path()
    today = datetime.now().strftime("%Y-%m-%d")

    title_safe = sanitize_filename(title)

    base_structure = os.path.join(
        desktop,
        APP_NAME,
        mode.capitalize(),
        today,
        title_safe
    )

    os.makedirs(base_structure, exist_ok=True)

    session_folder = get_next_session_folder(base_structure)

    return session_folder


# ============================================
# ACCOUNT SUBFOLDER
# ============================================

def create_account_subfolder(base_path, account_name):

    account_safe = sanitize_filename(account_name)
    account_folder = os.path.join(base_path, account_safe)

    os.makedirs(account_folder, exist_ok=True)

    return account_folder


# ============================================
# CONFIG PATH
# ============================================

def get_config_path():
    base_dir = get_base_data_dir()
    return os.path.join(base_dir, "config.json")