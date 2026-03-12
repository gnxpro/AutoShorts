import os
import requests

icons = {
    "youtube": "https://cdn.simpleicons.org/youtube",
    "instagram": "https://cdn.simpleicons.org/instagram",
    "tiktok": "https://cdn.simpleicons.org/tiktok",
    "facebook": "https://cdn.simpleicons.org/facebook",
    "linkedin": "https://cdn.simpleicons.org/linkedin",
    "twitter": "https://cdn.simpleicons.org/twitter",
    "pinterest": "https://cdn.simpleicons.org/pinterest"
}

path = "assets/icons/social"
os.makedirs(path, exist_ok=True)

for name, url in icons.items():

    r = requests.get(url)

    file = os.path.join(path, f"{name}.png")

    with open(file, "wb") as f:
        f.write(r.content)

print("✔ Social icons downloaded")