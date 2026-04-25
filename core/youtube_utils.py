import os
import sys
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from core.youtube_download import download_youtube 
from core.logger import log_info, log_error

class YouTubeUtils:
    def __init__(self):
        # --- LOGIKA JALUR UNIVERSAL ---
        if getattr(sys, 'frozen', False):
            # Jika aplikasi sudah di-build menjadi .exe
            # Base dir adalah folder tempat file .exe tersebut berada
            self.base_dir = Path(sys.executable).parent
        else:
            # Jika masih dijalankan lewat terminal (python main.py)
            # Base dir adalah folder utama project tempat terminal dibuka
            self.base_dir = Path(os.getcwd())
            
        self.token_dir = self.base_dir / "tokens"
        self.token_path = self.token_dir / "youtube_token.json"
        
        # client_secret.json akan selalu dicari tepat di sebelah file main.py atau file .exe
        self.client_secrets_file = self.base_dir / "client_secret.json"
        
        self.scopes = ["https://www.googleapis.com/auth/youtube.upload", 
                       "https://www.googleapis.com/auth/youtube.readonly"]
        
        self.token_dir.mkdir(parents=True, exist_ok=True)
        log_info(f"INIT >> Menjalankan YouTubeUtils dari: {self.base_dir}")

    def login(self):
        """Membuka browser otomatis secara aman di komputer siapapun"""
        creds = None
        
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(str(self.token_path), self.scopes)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Cek ketersediaan file dengan path universal
                if not self.client_secrets_file.exists():
                    log_error(f"File {self.client_secrets_file.name} tidak ditemukan di: {self.base_dir}")
                    raise Exception(f"Pastikan file client_secret.json ada di folder: {self.base_dir}")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(self.client_secrets_file), self.scopes
                )
                
                # Membuka browser otomatis
                creds = flow.run_local_server(
                    port=9222, 
                    prompt='consent',
                    authorization_prompt_message='Browser terbuka! Silakan login akun YouTube Anda...',
                    success_message='Login Berhasil! Anda dapat menutup halaman browser ini.'
                )

            with open(self.token_path, "w") as token:
                token.write(creds.to_json())
            log_info("SUCCESS: Token YouTube diperbarui dan diamankan.")
        
        return creds

    def _get_service(self):
        try:
            creds = self.login()
            return build("youtube", "v3", credentials=creds)
        except Exception as e:
            log_error(f"Gagal membangun service API: {str(e)}")
            raise

    def upload_video(self, file_path, title, description, category="22", privacy_status="public"):
        try:
            youtube = self._get_service()
            body = {
                'snippet': {'title': title, 'description': description, 'categoryId': category},
                'status': {'privacyStatus': privacy_status, 'selfDeclaredMadeForKids': False}
            }
            media = MediaFileUpload(file_path, mimetype='video/mp4', resumable=True)
            request = youtube.videos().insert(part='snippet,status', body=body, media_body=media)
            
            log_info(f"UPLOAD >> Memulai pengunggahan: {title}")
            response = request.execute()
            log_info(f"UPLOAD >> Selesai! ID Video: {response.get('id')}")
            return response
        except Exception as e:
            log_error(f"Google API Error: {str(e)}")
            raise

    def download(self, url, output_dir):
        if not os.path.exists(output_dir): 
            os.makedirs(output_dir, exist_ok=True)
        return download_youtube(url, output_dir)