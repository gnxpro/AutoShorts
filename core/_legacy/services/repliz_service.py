import base64
import requests
from core.config_manager import ConfigManager


class ReplizService:

    def __init__(self):

        config = ConfigManager().get_repliz()

        self.base_url = config.get("base_url")
        self.access_key = config.get("access_key")
        self.secret_key = config.get("secret_key")

        if not self.access_key or not self.secret_key:
            raise Exception("Repliz credentials missing")

    def _auth_header(self):
        credentials = f"{self.access_key}:{self.secret_key}"
        encoded = base64.b64encode(credentials.encode()).decode()

        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json"
        }

    def create_schedule(self, title, description, video_url, account_id):

        url = f"{self.base_url}/schedule"

        payload = {
            "title": title,
            "description": description,
            "type": "video",
            "accountId": account_id,
            "medias": [
                {
                    "type": "video",
                    "url": video_url
                }
            ]
        }

        response = requests.post(
            url,
            headers=self._auth_header(),
            json=payload,
            timeout=60
        )

        if response.status_code not in (200, 201):
            raise Exception(response.text)

        return response.json()