import os


REQUIRED_FOLDERS = [
    "outputs",
    "outputs/jobs",
    "outputs/ready",
    "outputs/temp",
    "outputs/logs",
    "config",
    "assets",
]


def ensure_directories():

    for folder in REQUIRED_FOLDERS:

        try:
            os.makedirs(folder, exist_ok=True)

        except PermissionError:

            # fallback ke user directory
            home = os.path.expanduser("~")
            alt = os.path.join(home, "GNX_PRODUCTION", folder)

            os.makedirs(alt, exist_ok=True)


def ensure_worker_lock():

    try:

        if not os.path.exists("worker.lock"):

            with open("worker.lock", "w") as f:
                f.write("idle")

    except Exception:
        pass