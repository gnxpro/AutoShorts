# =========================
# Python
# =========================
__pycache__/
*.py[cod]
*.pyd
*.so
*.egg-info/
*.egg
.pytest_cache/
.mypy_cache/
.ruff_cache/
.cache/

# =========================
# Virtualenv
# =========================
venv/
.venv/
env/
ENV/

# =========================
# OS / Editor
# =========================
.DS_Store
Thumbs.db
desktop.ini
.vscode/
.idea/
*.swp

# =========================
# Secrets / Env
# =========================
.env
.env.*
.env.example

# =========================
# Runtime outputs (DO NOT COMMIT)
# =========================
outputs/
temp/
temp_download/
temp_downloads/
logs/
*.log

# =========================
# Build artifacts (PyInstaller)
# =========================
build/
dist/
*.spec.bak

# =========================
# Installer outputs
# =========================
release/
*.exe
*.msi

# =========================
# Media / Large files
# =========================
*.mp4
*.mov
*.mkv
*.avi
*.webm
*.m4v
*.wav
*.mp3
*.png
*.jpg
*.jpeg
*.zip
*.7z

# Keep essential small UI assets if needed:
!assets/*.ico
!assets/*.png
!assets/*.jpg
!assets/*.jpeg

# If you store ffmpeg binaries locally:
assets/ffmpeg/

# =========================
# Local DB / user data
# =========================
*.sqlite
*.db

# =========================
# Windows appdata (never commit)
# =========================
GNX_PRODUCTION/