import os
import subprocess
import re
import sys
from urllib.parse import urlparse, parse_qs


class YouTubeDownloadError(Exception):
    pass


def clean_youtube_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)

    if "v" in query:
        vid = query["v"][0]
        return f"https://youtu.be/{vid}"

    if parsed.netloc in ("youtu.be",):
        return f"https://youtu.be{parsed.path}"

    return url


def download_youtube(
    url: str,
    output_dir: str,
    cookies: str = None,
    progress_callback=None,
    download_subtitle=True
):

    os.makedirs(output_dir, exist_ok=True)

    url = clean_youtube_url(url)

    output_template = os.path.join(output_dir, "%(title)s.%(ext)s")

    yt_dlp_path = os.path.join(
        os.path.dirname(sys.executable),
        "yt-dlp.exe"
    )

    if not os.path.exists(yt_dlp_path):
        raise YouTubeDownloadError("yt-dlp executable not found.")

    cmd = [yt_dlp_path]

    # gunakan cookies browser (lebih stabil)
    cmd += ["--cookies-from-browser", "chrome"]

    cmd += [
        "-f", "best[height<=720]",
        "-o", output_template,
        url
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    percent_pattern = re.compile(r"(\d{1,3}\.\d+)%")
    downloaded_file = None

    for line in process.stdout:
        line = line.strip()

        if "[download]" in line and "%" in line:
            match = percent_pattern.search(line)
            if match and progress_callback:
                progress_callback(float(match.group(1)) / 100)

        if "Destination:" in line:
            downloaded_file = line.split("Destination:")[-1].strip()

    process.wait()

    if process.returncode != 0:
        raise YouTubeDownloadError("yt-dlp CLI download failed.")

    if not downloaded_file:
        files = os.listdir(output_dir)
        if files:
            files.sort(
                key=lambda f: os.path.getmtime(os.path.join(output_dir, f)),
                reverse=True
            )
            downloaded_file = os.path.join(output_dir, files[0])
        else:
            raise YouTubeDownloadError("Downloaded file not found.")

    return downloaded_file