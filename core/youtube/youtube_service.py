import requests


def get_channel_info(access_token):
    url = "https://www.googleapis.com/youtube/v3/channels"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    params = {
        "part": "snippet",
        "mine": "true"
    }

    res = requests.get(url, headers=headers, params=params)

    return res.json()