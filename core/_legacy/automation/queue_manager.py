import os
import json
import shutil
from datetime import datetime


class QueueManager:
    """
    File-based queue system.
    Safe for desktop environment.
    """

    def __init__(self, queue_dir):
        self.queue_dir = queue_dir
        self.processing_dir = os.path.join(queue_dir, "processing")
        self.done_dir = os.path.join(queue_dir, "done")

        os.makedirs(self.queue_dir, exist_ok=True)
        os.makedirs(self.processing_dir, exist_ok=True)
        os.makedirs(self.done_dir, exist_ok=True)

    # =====================================================

    def fetch_tasks(self):
        tasks = []

        for filename in os.listdir(self.queue_dir):
            if not filename.endswith(".json"):
                continue

            file_path = os.path.join(self.queue_dir, filename)

            try:
                processing_path = os.path.join(self.processing_dir, filename)
                shutil.move(file_path, processing_path)

                with open(processing_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                data["_file_path"] = processing_path
                tasks.append(data)

            except Exception:
                continue

        return tasks

    # =====================================================

    def mark_done(self, task):
        file_path = task.get("_file_path")
        if not file_path or not os.path.exists(file_path):
            return

        filename = os.path.basename(file_path)
        done_path = os.path.join(self.done_dir, filename)

        shutil.move(file_path, done_path)