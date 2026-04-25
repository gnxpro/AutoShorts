from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List
import json

try:
    from config.app_paths import ACCOUNTS_FILE
except Exception:
    ACCOUNTS_FILE = Path(__file__).resolve().parents[2] / "data" / "accounts" / "social_accounts.json"
