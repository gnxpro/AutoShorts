import os
import json
from datetime import datetime


class StateManager:
    """
    Maintains engagement_state.json
    """

    def __init__(self, base_dir):
        self.state_file = os.path.join(base_dir, "engagement_state.json")

        if not os.path.exists(self.state_file):
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump({}, f)

    # =====================================================

    def _read(self):
        with open(self.state_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # =====================================================

    def update_status(self, account_id, status):
        data = self._read()

        if account_id not in data:
            data[account_id] = {}

        data[account_id]["status"] = status
        data[account_id]["last_update"] = datetime.utcnow().isoformat()

        self._write(data)