import os
import sys
from pathlib import Path


APPDATA_FOLDER = "GNX_PRODUCTION"


def app_root_dir() -> Path:
    """
    Where the app binaries/assets live.
    - PyInstaller installed: folder of GNX_Production.exe
    - Dev: project root (AutoShorts/)
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    # core/app_paths.py -> core -> project root
    return Path(__file__).resolve().parents[1]


def appdata_dir() -> Path:
    """
    Writable folder for installed apps.
    """
    base = os.getenv("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
    d = Path(base) / APPDATA_FOLDER
    d.mkdir(parents=True, exist_ok=True)
    return d


def outputs_dir() -> Path:
    d = appdata_dir() / "outputs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def jobs_dir() -> Path:
    d = outputs_dir() / "jobs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def ensure_writable_workdir() -> Path:
    """
    Ensure the process is running in a writable directory.
    This prevents WinError 5 when app is installed in Program Files.

    Strategy:
    - Always ensure AppData dirs exist
    - If current working directory is not writable, chdir to AppData
    - Also set env vars for debugging/reference
    """
    ad = appdata_dir()
    outputs_dir()
    jobs_dir()

    os.environ["GNX_APPDATA_DIR"] = str(ad)
    os.environ["GNX_APP_ROOT"] = str(app_root_dir())

    # Test if current folder is writable
    cwd = Path.cwd()
    try:
        test_file = cwd / ".gnx_write_test.tmp"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        return cwd
    except Exception:
        # Not writable → move to AppData
        os.chdir(str(ad))
        return ad