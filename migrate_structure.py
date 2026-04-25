import os
import shutil

# mapping lama → baru
MOVE_MAP = {
    "pages": "ui/pages",
    "logs": "data/logs",
    "tokens": "data/tokens",
}

CREATE_DIRS = [
    "app",
    "core",
    "ui/pages",
    "ui/components",
    "ui/layout",
    "services",
    "workers",
    "config",
    "data/logs",
    "data/tokens",
    "scripts",
]

def create_dirs():
    for d in CREATE_DIRS:
        os.makedirs(d, exist_ok=True)
        print(f"📁 Created: {d}")

def move_folders():
    for src, dst in MOVE_MAP.items():
        if os.path.exists(src):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            print(f"🚚 Moved: {src} → {dst}")
        else:
            print(f"⚠️ Not found: {src}")

def main():
    print("🚀 START MIGRATION\n")

    create_dirs()
    move_folders()

    print("\n✅ DONE (cek manual import & main.py)")

if __name__ == "__main__":
    main()