from pathlib import Path
import re

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

CONFIG_PATH = Path("config/client_secret.json")
TOKENS_DIR = Path("data/tokens/youtube")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]


def _safe_name(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-zA-Z0-9]+", "_", value)
    return value or "member"


def start_auth(member_id: str):
    TOKENS_DIR.mkdir(parents=True, exist_ok=True)
    flow = InstalledAppFlow.from_client_secrets_file(
        str(CONFIG_PATH),
        SCOPES,
    )
    creds = flow.run_local_server(
        host="127.0.0.1",
        port=54321,
        open_browser=True,
        authorization_prompt_message="",
        success_message="✅ LOGIN SUKSES! Silakan kembali ke aplikasi.",
        access_type="offline",
        prompt="select_account consent",
        include_granted_scopes="false",
    )
    youtube = build("youtube", "v3", credentials=creds)
    response = youtube.channels().list(part="snippet", mine=True).execute()
    items = response.get("items", [])
    if not items:
        raise RuntimeError("Channel YouTube tidak ditemukan dari akun yang login.")
    channel = items[0]
    snippet = channel.get("snippet", {})
    channel_id = channel.get("id")
    channel_name = snippet.get("title", "YouTube Channel")
    safe_member = _safe_name(member_id)
    token_path = TOKENS_DIR / f"{safe_member}_{channel_id}.json"
    with token_path.open("w", encoding="utf-8") as f:
        f.write(creds.to_json())
    return {
        "user": channel_name,
        "channel_id": channel_id,
        "token_path": str(token_path),
    }
