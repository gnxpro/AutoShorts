import threading
import time
from core.logger import log


class SchedulerEngine:

    def __init__(self):
        self.running = False

    def start(self, interval_seconds, task_function):
        self.running = True

        def loop():
            while self.running:
                try:
                    task_function()
                except Exception as e:
                    log(f"Scheduler error: {e}")
                time.sleep(interval_seconds)

        thread = threading.Thread(target=loop, daemon=True)
        thread.start()

    def stop(self):
        self.running = False