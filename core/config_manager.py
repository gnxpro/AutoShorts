import os
import json

BASE_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", ""),
    "GNX_Production"
)

CONFIG_PATH = os.path.join(BASE_DIR, "gnx_config.json")


class ConfigManager:

    def __init__(self):
        os.makedirs(BASE_DIR, exist_ok=True)
        if not os.path.exists(CONFIG_PATH):
            self._save({})

    # =====================================================
    # INTERNAL
    # =====================================================

    def _load(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # =====================================================
    # REPLIZ
    # =====================================================

    def get_repliz(self):
        data = self._load()

        if "repliz" not in data:
            data["repliz"] = {
                "base_url": "https://api.repliz.com/public",
                "access_key": "9287864374",
                "secret_key": "ueJzAhrO8MuySEKFf22WKQ5u0uK46Txe"
            }
            self._save(data)

        return data["repliz"]

    def save_repliz(self, repliz_config: dict):
        data = self._load()
        data["repliz"] = repliz_config
        self._save(data)

    # =====================================================
    # CLOUDINARY
    # =====================================================

    def get_cloudinary(self):
        data = self._load()

        if "cloudinary" not in data:
            data["cloudinary"] = {
                "cloud_name": "dlcfc8xjy",
                "api_key": "177536419822387",
                "api_secret": "9rUYXx3XMOMfssT37G_fWgy5G3Q"
            }
            self._save(data)

        return data["cloudinary"]

    def save_cloudinary(self, cloud_conf: dict):
        data = self._load()
        data["cloudinary"] = cloud_conf
        self._save(data)

    # =====================================================
    # AI
    # =====================================================

    def get_ai(self):
        data = self._load()

        if "ai" not in data:
            data["ai"] = {
                "provider": "openai",
                "openai_api_key": "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",
                "gemini_api_key": "",
                "model": "gpt-4o",
                "tone": "Viral",
                "hook_style": "Emotional",
                "subtitle_style": "tiktok",
                "language": "id",
                "daily_credit_limit": 1000
            }
            self._save(data)

        return data["ai"]

    def save_ai(self, ai_config: dict):
        data = self._load()
        data["ai"] = ai_config
        self._save(data)