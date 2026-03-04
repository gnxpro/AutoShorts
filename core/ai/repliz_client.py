import requests
import json
import os


CONFIG_PATH = "config/repliz_config.json"


class ReplizClient:

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self):
        if not os.path.exists(CONFIG_PATH):
            raise Exception("Repliz config not found")

        with open(CONFIG_PATH, "r") as f:
            return json.load(f)

    def transcribe(self, audio_path):

        url = self.config["api_url"] + "/transcribe"

        headers = {
            "X-Access-Key": self.config["access_key"],
            "X-Secret-Key": self.config["secret_key"]
        }

        files = {
            "file": open(audio_path, "rb")
        }

        response = requests.post(url, headers=headers, files=files)

        if response.status_code != 200:
            raise Exception("Repliz API error")

        return response.json()
