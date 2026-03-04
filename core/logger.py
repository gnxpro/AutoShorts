import os
from datetime import datetime
from core.app_paths import get_logs_path


LOG_DIR = get_logs_path()


def log(message):
    try:
        log_file = os.path.join(LOG_DIR, "app.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now()}] {message}\n")
    except Exception:
        pass