import hashlib
import base64
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
from core.config_manager import ConfigManager

class TikTokAuth:
    """Handle TikTok OAuth2 authentication with PKCE flow"""
    
    def __init__(self):
        """Initialize TikTok auth with config from config_manager"""
        self.config = ConfigManager().get_tiktok_config()
        self.client_key = self.config.get("client_key")
        self.client_secret = self.config.get("client_secret")
        self.redirect_uri = self.config.get("redirect_uri", "http://localhost:5000/callback")
        
        # Setup base directory (handles both frozen and dev environments)
        if getattr(sys, 'frozen', False):
            self.base_dir = Path(sys.executable).parent
        else:
            self.base_dir = Path(os.getcwd())
        
        self.token_dir = self.base_dir / "data" / "tokens"
        self.verifier_path = self.token_dir / "temp_tiktok_verifier.txt"
        self.code_path = self.token_dir / "tiktok_code.txt"

    def generate_pkce(self):
        """Generate PKCE verifier and challenge for OAuth2 flow"""
        verifier = base64.urlsafe_b64encode(os.urandom(32)).decode('utf-8').replace('=', '')
        self.token_dir.mkdir(parents=True, exist_ok=True)
        
        # Save verifier for later use in token exchange
        with open(self.verifier_path, "w") as f:
            f.write(verifier)
        
        # Generate challenge from verifier
        sha256_hash = hashlib.sha256(verifier.encode('utf-8')).digest()
        challenge = base64.urlsafe_b64encode(sha256_hash).decode('utf-8').replace('=', '')
        return challenge

    def get_authorize_url(self):
        """Generate TikTok authorization URL with PKCE challenge"""
        challenge = self.generate_pkce()
        scopes = "user.info.basic,video.upload"
        return (
            f"https://www.tiktok.com/v2/auth/authorize/"
            f"?client_key={self.client_key}"
            f"&scope={scopes}"
            f"&response_type=code"
            f"&redirect_uri={self.redirect_uri}"
            f"&code_challenge={challenge}"
            f"&code_challenge_method=S256"
        )

    def open_browser(self):
        """Open browser for TikTok OAuth and start local callback server"""
        code_file = self.code_path

        class TikTokCallbackHandler(BaseHTTPRequestHandler):
            """Handle OAuth callback from TikTok"""
            
            def do_GET(self):
                """Handle GET request with authorization code"""
                parsed_path = urllib.parse.urlparse(self.path)
                if parsed_path.path == '/callback':
                    query = urllib.parse.parse_qs(parsed_path.query)
                    if 'code' in query:
                        # Save authorization code to file
                        with open(code_file, "w") as f:
                            f.write(query['code'][0])
                        
                        # Send success response
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html; charset=utf-8')
                        self.end_headers()
                        success_html = (
                            b"<html><body style='text-align:center; padding:50px; "
                            b"font-family:sans-serif; background:#111; color:#fff;'>"
                            b"<h2>TikTok Login Success! \xe2\x9c\x85</h2>"
                            b"<p>Code captured. Close this window and return to AutoShorts.</p>"
                            b"</body></html>"
                        )
                        self.wfile.write(success_html)
                    else:
                        # Send error response
                        self.send_response(400)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        error_html = (
                            b"<html><body style='text-align:center; padding:50px; "
                            b"font-family:sans-serif;'><h2>Login Failed \xe2\x9d\x8c</h2></body></html>"
                        )
                        self.wfile.write(error_html)
                
                # Shutdown server after request
                threading.Thread(target=self.server.shutdown).start()

            def log_message(self, format, *args):
                """Suppress HTTP server logging"""
                pass

        # Start local callback server
        server = HTTPServer(('localhost', 5000), TikTokCallbackHandler)
        
        # Open browser to authorization URL
        webbrowser.open(self.get_authorize_url())
        
        # Wait for callback
        server.serve_forever()

    def finalize_login(self):
        """Exchange authorization code for access token"""
        if not self.code_path.exists() or not self.verifier_path.exists():
            return False, "Authorization data missing or not captured."

        try:
            # Read code and verifier from files
            with open(self.code_path, "r") as f:
                code = f.read().strip()
            with open(self.verifier_path, "r") as f:
                verifier = f.read().strip()

            # Exchange code for token
            url = "https://www.tiktok.com/v2/auth/token"
            data = {
                'client_key': self.client_key,
                'client_secret': self.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.redirect_uri,
                'code_verifier': verifier
            }
            
            res = requests.post(url, data=data, 
                              headers={'Content-Type': 'application/x-www-form-urlencoded'})
            res_data = res.json()
            access_token = res_data.get('access_token', '')
            
            # Save session with token
            self._save_session("gnx.prd (Connected)", access_token)
            
            # Clean up temp files
            if self.code_path.exists():
                os.remove(self.code_path)
            
            return True, "gnx.prd (Connected)"
        except Exception as e:
            return False, str(e)

    def _save_session(self, name, access_token):
        """Save TikTok session to the shared account database"""
        db_path = self.base_dir / "data" / "tokens" / "social_accounts.json"
        
        db = {"FACEBOOK": [], "INSTAGRAM": [], "YOUTUBE": [], "TIKTOK": []}
        if db_path.exists():
            with open(db_path, "r") as f:
                try:
                    db = json.load(f)
                except:
                    pass

        db["TIKTOK"] = [acc for acc in db.get("TIKTOK", []) if acc.get('user') != name]
        db["TIKTOK"].append({
            "user": name,
            "status": "ACTIVE",
            "token": access_token,
            "last_login": datetime.now().strftime("%Y-%m-%d")
        })

        with open(db_path, "w") as f:
            json.dump(db, f, indent=4)        