import os
import requests
from pathlib import Path
from typing import Dict, Any
from core.config_manager import ConfigManager

class CloudinaryServiceError(Exception):
    """Custom error untuk menangani kegagalan upload ke Cloudinary"""
    pass

class CloudinaryService:
    def __init__(self):
        # Mengambil konfigurasi secara otomatis dari gnx_config.json
        self.cfg = ConfigManager()
        self.refresh_credentials()

    def refresh_credentials(self):
        """Memperbarui API Key dari config setiap kali akan melakukan upload"""
        c_data = self.cfg.get_cloudinary()
        
        # Data diambil dari halaman Cloud Storage di aplikasi
        self.cloud_name = str(c_data.get("cloud_name", "datn1gpxd")).strip()
        self.api_key = str(c_data.get("api_key", "763832697194282")).strip()
        self.api_secret = str(c_data.get("api_secret", "PD9nAz_qG5MXYrBQcXx0G2hE3Hw")).strip()
        self.upload_preset = str(c_data.get("upload_preset", "ml_default")).strip()
        self.folder = str(c_data.get("folder", "GNX_Production")).strip()
        self.timeout = 120

    def _upload_url(self) -> str:
        """URL Endpoint resmi Cloudinary untuk upload video"""
        return f"https://api.cloudinary.com/v1_1/{self.cloud_name}/video/upload"

    def upload(self, file_path: str) -> Dict[str, Any]:
        """Proses mengirim file video ke server Cloudinary"""
        self.refresh_credentials() # Pastikan kredensial paling baru
        
        p = Path(file_path)
        if not p.exists():
            raise CloudinaryServiceError(f"File tidak ditemukan: {file_path}")

        # Data form untuk otentikasi Cloudinary
        data = {
            "upload_preset": self.upload_preset,
            "folder": self.folder,
            "api_key": self.api_key
        }

        with p.open("rb") as f:
            files = {"file": (p.name, f, "video/mp4")}
            try:
                # Kirim POST request ke API Cloudinary
                response = requests.post(
                    self._upload_url(),
                    data=data,
                    files=files,
                    timeout=self.timeout
                )
                payload = response.json()
            except Exception as e:
                raise CloudinaryServiceError(f"Koneksi Cloudinary gagal: {str(e)}")

        # Jika server mengembalikan error
        if response.status_code >= 400:
            error_msg = payload.get("error", {}).get("message", "Upload gagal")
            raise CloudinaryServiceError(f"Cloudinary Error: {error_msg}")

        return payload