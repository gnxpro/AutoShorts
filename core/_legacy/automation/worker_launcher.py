import os
import subprocess
import psutil


def is_worker_running(process_name="gnx_worker.exe"):
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] == process_name:
            return True
    return False


def launch_worker():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(base_dir, "..", ".."))

    worker_path = os.path.join(root_dir, "gnx_worker.exe")

    if not os.path.exists(worker_path):
        return

    if not is_worker_running():
        subprocess.Popen(
            [worker_path],
            creationflags=subprocess.DETACHED_PROCESS
        )