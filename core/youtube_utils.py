from yt_dlp import YoutubeDL


def fetch_info(url: str):

    if not url:
        raise Exception("URL kosong")

    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "nocheckcertificate": True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        return {
            "title": info.get("title", "No Title"),
            "duration": info.get("duration", 0),
            "thumbnail": info.get("thumbnail", None),
        }

    except Exception as e:
        raise Exception(f"YouTube fetch error: {str(e)}")