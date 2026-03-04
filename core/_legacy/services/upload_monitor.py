import os
from core.logger import log


FAILED_LOG = "failed_uploads.txt"


def log_failed(video_path):
    with open(FAILED_LOG, "a", encoding="utf-8") as f:
        f.write(video_path + "\n")


def retry_failed(upload_function):
    if not os.path.exists(FAILED_LOG):
        return

    with open(FAILED_LOG, "r", encoding="utf-8") as f:
        videos = f.readlines()

    remaining = []

    for video in videos:
        video = video.strip()
        try:
            upload_function(video)
            log(f"Retry success: {video}")
        except:
            remaining.append(video)

    with open(FAILED_LOG, "w", encoding="utf-8") as f:
        for v in remaining:
            f.write(v + "\n")