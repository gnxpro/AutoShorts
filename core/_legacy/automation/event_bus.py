import os
import json
from datetime import datetime


class EventBus:
    """
    Writes engagement_events.json
    Used for notifying GNX UI
    """

    def __init__(self, base_dir):
        self.event_file = os.path.join(base_dir, "engagement_events.json")

        if not os.path.exists(self.event_file):
            with open(self.event_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    # =====================================================

    def emit(self, event_type, account=None, message=""):
        events = self._read()

        events.append({
            "type": event_type,
            "account": account,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        })

        self._write(events)

    # =====================================================

    def _read(self):
        with open(self.event_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with open(self.event_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)