import threading
import time


class SchedulerEngine:

    def __init__(self, engine):
        self.engine = engine
        self.running = False
        self.thread = None
        self.interval_seconds = 3600  # default 1 hour

    def start(self, payload, interval_minutes=60):

        if self.running:
            print("Scheduler already running")
            return

        self.interval_seconds = interval_minutes * 60
        self.running = True

        def loop():
            while self.running:
                print("Automation cycle started...")
                self.engine.start(payload, print, print)
                time.sleep(self.interval_seconds)

        self.thread = threading.Thread(target=loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        print("Scheduler stopped")