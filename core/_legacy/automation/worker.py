import os
import time
import json
import threading
from datetime import datetime

from .queue_manager import QueueManager
from .state_manager import StateManager
from .event_bus import EventBus
from .concurrency_controller import ConcurrencyController


BASE_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "GNX_Production"
)

QUEUE_DIR = os.path.join(BASE_DIR, "engagement_queue")


class EngagementWorker:
    """
    Detached background worker.
    Responsible for:
    - Polling queue
    - Dispatching tasks
    - Managing concurrency
    - Updating state
    - Emitting events
    """

    def __init__(self, max_parallel_accounts=6, poll_interval=5):
        self.queue = QueueManager(QUEUE_DIR)
        self.state = StateManager(BASE_DIR)
        self.events = EventBus(BASE_DIR)
        self.concurrency = ConcurrencyController(max_parallel_accounts)

        self.poll_interval = poll_interval
        self.running = True

    # =====================================================
    # MAIN LOOP
    # =====================================================

    def start(self):
        print("GNX Engagement Worker started.")

        while self.running:
            try:
                tasks = self.queue.fetch_tasks()

                for task in tasks:
                    if not self.concurrency.can_start():
                        break

                    self.concurrency.increment()

                    thread = threading.Thread(
                        target=self._process_task,
                        args=(task,),
                        daemon=True
                    )
                    thread.start()

                time.sleep(self.poll_interval)

            except Exception as e:
                self.events.emit(
                    event_type="worker_error",
                    message=str(e)
                )
                time.sleep(2)

    # =====================================================
    # TASK PROCESSING
    # =====================================================

    def _process_task(self, task):
        try:
            account_id = task.get("account_id")

            self.state.update_status(account_id, "running")

            # Placeholder for actual engagement execution
            # This is where your Repliz adapter will be called
            self._execute_action_stub(task)

            self.state.update_status(account_id, "completed")

        except Exception as e:
            self.state.update_status(account_id, "error")
            self.events.emit(
                event_type="task_error",
                account=task.get("account_id"),
                message=str(e)
            )

        finally:
            self.concurrency.decrement()
            self.queue.mark_done(task)

    # =====================================================
    # STUB (REPLACE WITH ADAPTER CALL)
    # =====================================================

    def _execute_action_stub(self, task):
        """
        Replace this with actual engagement adapter call.
        Keep worker generic.
        """
        time.sleep(2)  # simulate work


if __name__ == "__main__":
    worker = EngagementWorker()
    worker.start()