import shutil


def check_ffmpeg():
    return shutil.which("ffmpeg") is not None


def check_ytdlp():
    return shutil.which("yt-dlp") is not None
