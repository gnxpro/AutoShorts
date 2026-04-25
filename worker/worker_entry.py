import os
import time


LOCK_FILE = "worker.lock"
STOP_FILE = "stop.flag"


def create_lock_file():

    try:

        with open(LOCK_FILE, "w") as f:
            f.write("running")

    except Exception:
        pass


def remove_lock():

    try:

        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)

    except Exception:
        pass


def start_worker():

    create_lock_file()

    print("GNX Worker started")

    while True:

        if os.path.exists(STOP_FILE):

            print("Worker stop signal received")

            os.remove(STOP_FILE)

            break

        time.sleep(5)

    remove_lock()


if __name__ == "__main__":

    start_worker()