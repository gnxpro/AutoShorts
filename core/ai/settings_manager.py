from core.ai.settings_manager import SettingsManager
import requests


class GeminiConnectionTester:
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    def __init__(self):
        self.api_key = SettingsManager().get("gemini_api_key")

    def test(self) -> dict:
        if not self.api_key:
            return {"status": False, "message": "API Key belum diset"}

        try:
            url = f"{self.BASE_URL}?key={self.api_key}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                return {"status": True, "message": "Koneksi berhasil"}
            else:
                return {"status": False, "message": f"HTTP {response.status_code}"}

        except Exception as e:
            return {"status": False, "message": str(e)}