import os
import requests

icons = {
    "youtube": "https://cdn-icons-png.flaticon.com/512/1384/1384060.png",
    "instagram": "https://cdn-icons-png.flaticon.com/512/1384/1384063.png",
    "facebook": "https://cdn-icons-png.flaticon.com/512/1384/1384053.png",
    "tiktok": "https://cdn-icons-png.flaticon.com/512/3046/3046121.png",
    "linkedin": "https://cdn-icons-png.flaticon.com/512/1384/1384014.png",
    "twitter": "https://cdn-icons-png.flaticon.com/512/733/733579.png",
    "default": "https://cdn-icons-png.flaticon.com/512/565/565547.png"
}

folder = "assets/icons"

os.makedirs(folder, exist_ok=True)

for name, url in icons.items():

    path = f"{folder}/{name}.png"

    print("Downloading:", name)

    r = requests.get(url)

    with open(path, "wb") as f:
        f.write(r.content)

print("DONE")