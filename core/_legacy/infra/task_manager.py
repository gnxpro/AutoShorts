import threading
import uuid


class TaskManager:
    def __init__(self):
        self.tasks = {}

    def run(self, target, args=(), on_success=None, on_error=None):
        task_id = str(uuid.uuid4())
        self.tasks[task_id] = {"status": "running"}

        def wrapper():
            try:
                result = target(*args)
                self.tasks[task_id]["status"] = "completed"
                if on_success:
                    on_success(result)
            except Exception as e:
                self.tasks[task_id]["status"] = "failed"
                if on_error:
                    on_error(e)

        threading.Thread(target=wrapper, daemon=True).start()
        return task_id

    def get_status(self, task_id):
        return self.tasks.get(task_id, {})
