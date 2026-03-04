from core.youtube_utils import fetch_info
from core.youtube_download import download_youtube


class YouTubeService:

    @staticmethod
    def get_info(url, cookies=None):
        return fetch_info(url, cookies)

    @staticmethod
    def download(url, output_dir, cookies=None):
        return download_youtube(url, output_dir, cookies)
