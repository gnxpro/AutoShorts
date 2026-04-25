import os
import subprocess
import re
from core.logger import log_info, log_error

def download_youtube(url, output_dir):
    log_info(f"🚀 Memulai download YouTube (Mode Bypass): {url}")
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    video_id_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    video_id = video_id_match.group(1) if video_id_match else "video"
    output_template = os.path.join(output_dir, f"{video_id}.%(ext)s")

    # PERINTAH TERKUAT: Menggunakan client 'android' dan 'ios' yang jarang diblokir
    command = [
        "yt-dlp",
        "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--output", output_template,
        "--extractor-args", "youtube:player_client=android,ios;skip=webpage", # Bypass Web Player
        "--no-check-certificates",
        "--merge-output-format", "mp4",
        url
    ]

    try:
        process = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
        
        if process.returncode == 0:
            for file in os.listdir(output_dir):
                if file.startswith(video_id):
                    return os.path.join(output_dir, file)
        
        # JIKA GAGAL, COBA CARA TERAKHIR: Pakai Link Mobile
        mobile_url = url.replace("www.youtube.com", "m.youtube.com")
        command[-1] = mobile_url
        process = subprocess.run(command, capture_output=True, text=True)
        
        if process.returncode == 0:
            for file in os.listdir(output_dir):
                if file.startswith(video_id): return os.path.join(output_dir, file)

    except Exception as e:
        log_error(f"System Error: {str(e)}")

    raise Exception(f"YouTube Blocked: {process.stderr[:200]}")