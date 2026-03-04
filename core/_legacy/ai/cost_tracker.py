import os
import json
from datetime import datetime

BASE_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "GNX_Production"
)

COST_FILE = os.path.join(BASE_DIR, "ai_cost_state.json")


class CostTracker:

    def __init__(self):
        os.makedirs(BASE_DIR, exist_ok=True)
        self.state = self._load()

    def _today(self):
        return datetime.utcnow().strftime("%Y-%m-%d")

    def _load(self):
        if not os.path.exists(COST_FILE):
            return {
                "date": self._today(),
                "total_calls": 0,
                "models": {},
                "tasks": {}
            }

        with open(COST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self):
        with open(COST_FILE, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    def track(self, model, task_type, duration):
        if self.state["date"] != self._today():
            self.state = {
                "date": self._today(),
                "total_calls": 0,
                "models": {},
                "tasks": {}
            }

        self.state["total_calls"] += 1

        # Model stats
        if model not in self.state["models"]:
            self.state["models"][model] = {
                "calls": 0,
                "total_time": 0
            }

        self.state["models"][model]["calls"] += 1
        self.state["models"][model]["total_time"] += duration

        # Task stats
        if task_type not in self.state["tasks"]:
            self.state["tasks"][task_type] = 0

        self.state["tasks"][task_type] += 1

        self._save()

    def get_stats(self):
        return self.state