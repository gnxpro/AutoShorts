class QueueManager:

    def __init__(self):

        self.queue = []

    def load_videos(self, videos):

        self.queue = videos

    def get_queue(self):

        return self.queue

    def pop_next(self):

        if not self.queue:
            return None

        return self.queue.pop(0)