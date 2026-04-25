import json
from pathlib import Path

import requests
from fastapi import FastAPI, Request

app = FastAPI()

CLIENT_ID = "352361357334-bv1dkb46nkn1c72q6d5k1aiofms2nvhj.apps.googleusercontent.com"
CLIENT_SECRET = "HAPUS_SEMENTARA"
REDIRECT_URI = "HAPUS_SEMENTARA"
TOKEN_PATH = Path("tokens/youtube_token.json")


def _ensure_token_dir() -> None:
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)


@app.get("/auth/youtube/callback")
async def youtube_callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"error": "No code received"}

    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    response = requests.post(token_url, data=payload)
    response.raise_for_status()
    token_data = response.json()

    _ensure_token_dir()
    with TOKEN_PATH.open("w", encoding="utf-8") as f:
        json.dump(token_data, f, indent=2)

    return {"status": "SUCCESS"}
