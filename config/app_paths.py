from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"

GNX_CONFIG_FILE = CONFIG_DIR / "gnx_config.json"
GNX_MEMBER_FILE = CONFIG_DIR / "gnx_member.json"

ACCOUNTS_FILE = DATA_DIR / "accounts" / "social_accounts.json"
QUEUE_FILE = DATA_DIR / "queue" / "production_queue.json"
