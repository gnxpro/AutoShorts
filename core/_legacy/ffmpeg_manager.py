import os
import requests
import zipfile
import io
import shutil
from core.app_paths import get_base_data_dir


FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"


def get_ffmpeg_path():
    base_dir = get_base_data_dir()
    bin_dir = os.path.join(base_dir, "bin")
    ffmpeg_path = os.path.join(bin_dir, "ffmpeg.exe")

    if not os.path.exists(ffmpeg_path):
        download_and_extract_ffmpeg(bin_dir)

    return ffmpeg_path


def download_and_extract_ffmpeg(target_dir):
    os.makedirs(target_dir, exist_ok=True)

    response = requests.get(FFMPEG_URL, stream=True)
    if response.status_code != 200:
        raise Exception("Failed to download FFmpeg.")

    zip_data = zipfile.ZipFile(io.BytesIO(response.content))

    extracted_ffmpeg = None

    for file in zip_data.namelist():
        if file.endswith("bin/ffmpeg.exe"):
            zip_data.extract(file, target_dir)
            extracted_ffmpeg = os.path.join(target_dir, file)
            break

    if not extracted_ffmpeg or not os.path.exists(extracted_ffmpeg):
        raise Exception("FFmpeg binary not found in archive.")

    final_path = os.path.join(target_dir, "ffmpeg.exe")

    shutil.move(extracted_ffmpeg, final_path)

    # Cleanup nested folders
    for root, dirs, files in os.walk(target_dir, topdown=False):
        for d in dirs:
            try:
                shutil.rmtree(os.path.join(root, d))
            except:
                pass