import json
import os

TOKEN_PATH = "tokens/youtube_token.json"


def load_token():
    if not os.path.exists(TOKEN_PATH):
        return None

    with open(TOKEN_PATH, "r") as f:
        return json.load(f)