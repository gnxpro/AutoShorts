from google import genai
import cloudinary.uploader
from core import settings_store

class AIConnector:
    def __init__(self):
        self.cfg = settings_store.load_config()
        
        # Inisialisasi Gemini
        gemini_key = settings_store.get(self.cfg, "gemini.api_key")
        self.gemini_client = genai.Client(api_key=gemini_key)
        
        # Inisialisasi Cloudinary
        cloudinary.config(
            cloud_name = settings_store.get(self.cfg, "cloudinary.cloud_name"),
            api_key = settings_store.get(self.cfg, "cloudinary.api_key"),
            api_secret = settings_store.get(self.cfg, "cloudinary.api_secret"),
            secure = True
        )

    def process_for_upload(self, video_path, title):
        # 1. Upload ke Cloudinary untuk dapat URL
        print("⏳ Uploading ke Cloudinary...")
        upload_res = cloudinary.uploader.upload_large(video_path, resource_type="video")
        video_url = upload_res.get("secure_url")
        
        # 2. Minta Gemini buat caption
        print("⏳ Generating Caption...")
        prompt = f"Buat caption viral untuk video: {title}"
        ai_res = self.gemini_client.models.generate_content(
            model="models/gemini-1.5-flash", 
            contents=prompt
        )
        
        return {
            "url": video_url,
            "caption": ai_res.text
        }