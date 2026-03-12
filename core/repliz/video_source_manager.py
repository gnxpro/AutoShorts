from pathlib import Path


class VideoSourceManager:

    def __init__(self):

        self.sources = []

    def load_offline(self, folder):

        path = Path(folder)

        if not path.exists():
            return []

        videos = []

        for f in path.glob("*.mp4"):
            videos.append(str(f))

        return videos

    def load_render(self, folder):

        path = Path(folder)

        if not path.exists():
            return []

        videos = []

        for f in path.glob("*.mp4"):
            videos.append(str(f))

        return videos

    def load_cloudinary(self, urls):

        return urls

    def collect_all(self):

        videos = []

        videos += self.load_offline("outputs/jobs")
        videos += self.load_render("outputs/render")

        return videos