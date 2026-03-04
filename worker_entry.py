import os
import time
from core.engine import Engine

lock_file_path = "worker.lock"


def create_lock_file():
    if not os.path.exists(lock_file_path):
        with open(lock_file_path, "w") as f:
            f.write("worker_running")


def delete_lock_file():
    if os.path.exists(lock_file_path):
        os.remove(lock_file_path)


def start_worker():
    print("=== GNX WORKER STARTING ===")

    create_lock_file()

    engine = Engine()

    try:
        while True:
            time.sleep(2)
            print("[Worker] Running background tasks...")
    except KeyboardInterrupt:
        print("[Worker] Stopping...")
    finally:
        delete_lock_file()


if __name__ == "__main__":
    start_worker()