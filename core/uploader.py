import sys
import json
import os
import requests
import time
from pathlib import Path
from core.logger import log_info, log_error
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

class GNXUploader:
    def __init__(self):
        # Jalur dasar aplikasi untuk mencari database akun
        if getattr(sys, 'frozen', False):
            self.base_dir = Path(sys.executable).parent
        else:
            self.base_dir = Path(os.getcwd())
            
        self.db_path = self.base_dir / "core" / "account_db.json"

    def post_video(self, platform, video_path, title, description):
        """Fungsi utama pengiriman video menggunakan API Resmi"""
        if not os.path.exists(self.db_path):
            log_error("❌ UPLOADER >> Database akun (account_db.json) tidak ditemukan.")
            return False
        
        with open(self.db_path, "r") as f: 
            db = json.load(f)
            
        accounts = db.get(platform.upper(), [])
        if not accounts: 
            return False

        all_success = True
        for acc in accounts:
            user_name = acc.get("user", "Unknown")
            token = acc.get("token")
            log_info(f"UPLOADER >> Mengirim ke {platform}: {user_name}...")

            success = False
            if platform.upper() == "YOUTUBE":
                # Jalur Sah: Google Python API Client
                success = self._upload_youtube_real(video_path, title, description, token)
            elif platform.upper() == "FACEBOOK":
                # Jalur Sah: Meta Graph API v19.0
                success = self._upload_facebook_real(video_path, description, token)
            elif platform.upper() == "TIKTOK":
                # Jalur Sah sementara masih simulasi/menunggu izin resmi TikTok
                log_info(f"⏳ TIKTOK >> Simulasi sukses untuk {user_name}.")
                success = True

            if not success: 
                all_success = False
            
        return all_success

    def _upload_facebook_real(self, video_path, desc, token):
        """Upload ke Facebook Page menggunakan Meta Graph API Resmi"""
        try:
            url = "https://graph.facebook.com/v19.0/me/videos"
            with open(video_path, 'rb') as f:
                payload = {
                    'description': desc, 
                    'access_token': token
                }
                files = {'source': f}
                # Request langsung ke server Meta
                res = requests.post(url, data=payload, files=files, timeout=300).json()
            
            if "id" in res:
                log_info(f"✅ FACEBOOK SUCCESS >> Video ID: {res['id']}")
                return True
            
            log_error(f"❌ FB ERROR >> {res.get('error', {}).get('message')}")
            return False
        except Exception as e:
            log_error(f"❌ FB FATAL ERROR >> {str(e)}")
            return False

    def _upload_youtube_real(self, video_path, title, desc, token_data):
        """Upload ke YouTube menggunakan Google API Client Resmi"""
        try:
            # Mengubah string token menjadi format Credentials Google yang sah
            creds_info = json.loads(token_data) if isinstance(token_data, str) else token_data
            creds = Credentials.from_authorized_user_info(creds_info)
            youtube = build("youtube", "v3", credentials=creds)
            
            body = {
                'snippet': {
                    'title': title, 
                    'description': desc, 
                    'categoryId': '22' # People & Blogs
                },
                'status': {
                    'privacyStatus': 'public', 
                    'selfDeclaredMadeForKids': False
                }
            }
            
            media = MediaFileUpload(video_path, mimetype='video/mp4', resumable=True)
            request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
            
            response = request.execute()
            
            if response.get("id"):
                log_info(f"✅ YOUTUBE SUCCESS >> Video ID: {response['id']}")
                return True
            return False
        except Exception as e:
            log_error(f"❌ YOUTUBE ERROR >> {str(e)}")
            return False