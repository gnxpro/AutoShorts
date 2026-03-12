# =========================
# Python
# =========================
__pycache__/
*.py[cod]
*.pyd
*.so
*.egg
*.egg-info/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.cache/

# =========================
# Virtual Environments
# =========================
venv/
.venv/
env/
ENV/

# =========================
# OS / Editor files
# =========================
.DS_Store
Thumbs.db
desktop.ini
.vscode/
.idea/
*.swp

# =========================
# Environment / Secrets
# =========================
.env
.env.*
.env.example

# =========================
# Runtime Outputs (never commit)
# =========================
outputs/
temp/
temp_download/
temp_downloads/
logs/
*.log

# =========================
# Build Artifacts (PyInstaller)
# =========================
build/
dist/
*.spec.bak

# =========================
# Installer Outputs
# =========================
release/
*.exe
*.msi

# =========================
# Large Media Files
# =========================
*.mp4
*.mov
*.mkv
*.avi
*.webm
*.m4v
*.wav
*.mp3

# Images (ignored by default)
*.png
*.jpg
*.jpeg

# Archives
*.zip
*.7z

# =========================
# Allow essential UI assets
# =========================
!assets/
!assets/*.ico
!assets/*.png
!assets/*.jpg
!assets/*.jpeg

# Optional local ffmpeg binary
assets/ffmpeg/

# =========================
# Local Database / User Data
# =========================
*.sqlite
*.db

# =========================
# Local Windows AppData
# =========================
GNX_PRODUCTION/