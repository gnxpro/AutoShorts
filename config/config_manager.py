import os
import json
import uuid
import socket

# Menggunakan direktori lokal proyek agar portable
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(BASE_DIR, "core", "gnx_config.json")
TOKEN_BASE_DIR = os.path.join(BASE_DIR, "tokens")

class ConfigManager:
    def __init__(self):
        os.makedirs(os.path.join(BASE_DIR, "core"), exist_ok=True)
        os.makedirs(TOKEN_BASE_DIR, exist_ok=True)
        
        if not os.path.exists(CONFIG_PATH):
            self._save({
                "hwid": self._generate_hwid(),
                "license_type": "PREMIUM",
                "max_accounts": 100
            })
        
        self.apply_cloudinary_env()

    def _generate_hwid(self):
        host_name = socket.gethostname()
        unique_id = uuid.uuid4().hex[:12]
        return f"GNX-{host_name}-{unique_id}".upper()

    def _load(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save(self, data):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_youtube_user(self):
        """Membaca file token untuk mengambil nama channel asli"""
        token_path = os.path.join(TOKEN_BASE_DIR, "youtube_token.json")
        if not os.path.exists(token_path):
            return None
        try:
            with open(token_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Prioritas mengambil user_name yang ditarik dari API Google
                return data.get("user_name") or data.get("email") or "YouTube Channel"
        except Exception:
            return None

    def get_tiktok_config(self):
        data = self._load()
        if "tiktok" not in data:
            data["tiktok"] = {
                "client_key": "awxwx7hykacynvsf",
                "client_secret": "TQ45o3qu8S1sXBkgoA0OWfuk2jbYoQ3p",
                "redirect_uri": "https://api.gnxpro.my.id/auth/tiktok/callback"
            }
            self._save(data)
        return data["tiktok"]

    def get_cloudinary(self):
        data = self._load()
        if "cloudinary" not in data:
            data["cloudinary"] = {
                "cloud_name": "datn1gpxd",
                "api_key": "763832697194282",
                "api_secret": "PD9nAz_qG5MXYrBQcXx0G2hE3Hw",
                "upload_preset": "ml_default",
                "folder": "GNX_Assets",
                "secure_delivery": True
            }
            self._save(data)
        return data["cloudinary"]

    def apply_cloudinary_env(self):
        conf = self.get_cloudinary()
        os.environ["CLOUDINARY_CLOUD_NAME"] = str(conf.get("cloud_name", "")).strip()
        os.environ["CLOUDINARY_UPLOAD_PRESET"] = str(conf.get("upload_preset", "")).strip()