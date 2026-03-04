import threading


class ConcurrencyController:
    """
    Controls how many accounts run in parallel.
    """

    def __init__(self, max_parallel):
        self.max_parallel = max_parallel
        self.current = 0
        self.lock = threading.Lock()

    # =====================================================

    def can_start(self):
        with self.lock:
            return self.current < self.max_parallel

    def increment(self):
        with self.lock:
            self.current += 1

    def decrement(self):
        with self.lock:
            if self.current > 0:
                self.current -= 1