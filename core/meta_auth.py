import os
import sys
import webbrowser
import requests
import json
import threading
import urllib.parse
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

class MetaAuth:
    def __init__(self):
        # KREDENSIAL UTAMA
        self.app_id = "2399016960550926"
        self.app_secret = "7fb6c387af9f9a7b0cb70954a838468e"
        
        # URL CLOUDFLARE TERBARU (Sesuai Log Terminal Anda)
        self.redirect_uri = "https://main-instrument-know-class.trycloudflare.com/callback"

        self.base_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(os.getcwd())
        self.db_path = self.base_dir / "core" / "account_db.json"

    def get_auth_url(self):
        scopes = "public_profile,pages_manage_posts,pages_read_engagement,pages_show_list,instagram_basic,instagram_content_publish"
        return (
            f"https://www.facebook.com/v19.0/dialog/oauth?"
            f"client_id={self.app_id}&redirect_uri={self.redirect_uri}&scope={scopes}"
            f"&response_type=code&auth_type=rerequest&display=popup"
        )

    def login_and_get_token(self, platform_name):
        self.auth_code = None
        
        def run_server():
            server_address = ('', 5002) # Tetap di 5002 karena Cloudflare nge-forward ke sini
            try:
                self.httpd = HTTPServer(server_address, self._make_handler())
                self.httpd.handle_request()
            except Exception as e:
                print(f"Server Error: {e}")

        threading.Thread(target=run_server, daemon=True).start()
        
        # Buka Jendela Login Meta
        webbrowser.open(self.get_auth_url())
        
        # Tunggu respon (Maks 2 Menit karena jalur internet)
        count = 0
        while self.auth_code is None and count < 120:
            import time
            time.sleep(1)
            count += 1
            
        if not self.auth_code:
            return False, "Gagal: Timeout menunggu respon dari Cloudflare."

        return self._process_token_exchange(platform_name)

    def _process_token_exchange(self, platform_name):
        try:
            # 1. Tukar Code ke Access Token
            token_url = "https://graph.facebook.com/v19.0/oauth/access_token"
            params = {
                "grant_type": "authorization_code",
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "redirect_uri": self.redirect_uri,
                "code": self.auth_code
            }
            res = requests.get(token_url, params=params).json()
            user_token = res.get("access_token")
            
            if not user_token:
                return False, f"Meta Reject: {res.get('error', {}).get('message', 'Auth Failed')}"

            # 2. Ambil Daftar Halaman (Page)
            acc_url = f"https://graph.facebook.com/v19.0/me/accounts?fields=name,access_token,instagram_business_account&access_token={user_token}"
            pages_res = requests.get(acc_url).json()
            pages_data = pages_res.get("data", [])
            
            if not pages_data:
                return False, "Gagal: Anda belum mencentang Halaman saat login."

            # Pilih data sesuai platform
            final_name = pages_data[0]["name"]
            final_token = pages_data[0]["access_token"]

            self._save_to_db(platform_name, final_token, final_name)
            return True, final_name
        except Exception as e:
            return False, f"Sistem Error: {str(e)}"

    def _make_handler(self):
        parent = self
        class CallbackHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args): return
            def do_GET(self):
                query = urllib.parse.urlparse(self.path).query
                params = urllib.parse.parse_qs(query)
                if 'code' in params:
                    parent.auth_code = params['code'][0]
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(b"<html><body style='font-family:sans-serif;text-align:center;padding-top:50px;'>")
                    self.wfile.write(b"<h1 style='color:#2ecc71;'>Koneksi Sah Berhasil!</h1>")
                    self.wfile.write(b"<p>Silakan tutup browser dan kembali ke aplikasi.</p></body></html>")
                else:
                    self.send_response(400)
                    self.end_headers()
        return CallbackHandler

    def _save_to_db(self, platform, token, user_display):
        db = {"FACEBOOK": [], "INSTAGRAM": [], "YOUTUBE": [], "TIKTOK": []}
        if self.db_path.exists():
            try:
                with open(self.db_path, "r") as f: db = json.load(f)
            except: pass
        db[platform.upper()] = [acc for acc in db[platform.upper()] if acc['user'] != user_display]
        db[platform.upper()].append({
            "user": user_display, "status": "ACTIVE", "token": token,
            "last_login": datetime.now().strftime("%Y-%m-%d")
        })
        with open(self.db_path, "w") as f: json.dump(db, f, indent=4)