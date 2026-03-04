import os
import json
from datetime import datetime


BASE_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "GNX_Production"
)

CREDIT_FILE = os.path.join(BASE_DIR, "ai_credit_state.json")


class CreditManager:

    def __init__(self):
        os.makedirs(BASE_DIR, exist_ok=True)
        self.state = self._load()

    def _today(self):
        return datetime.utcnow().strftime("%Y-%m-%d")

    def _load(self):
        if not os.path.exists(CREDIT_FILE):
            return {
                "date": self._today(),
                "used": 0
            }

        with open(CREDIT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self):
        with open(CREDIT_FILE, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    def add_usage(self, amount: int):
        if self.state["date"] != self._today():
            self.state = {
                "date": self._today(),
                "used": 0
            }

        self.state["used"] += amount
        self._save()

    def get_usage(self):
        if self.state["date"] != self._today():
            return 0
        return self.state["used"]