# GNX PRO – AI STUDIO (Desktop → Future SaaS)

GNX PRO – AI STUDIO is a desktop automation studio for video processing:
- Offline / YouTube source
- FFmpeg processing (portrait 9:16, landscape 16:9, or both)
- Cloudinary upload
- Repliz scheduling (multi-account, max 100 accounts)
- Optional AI tools (Hooks, Subtitles, Niche, Hashtags) on PRO/TRIAL plans

---

## 1) Requirements
- Windows 10/11
- Python 3.10+ recommended
- FFmpeg installed (or bundled in `assets/ffmpeg/`)

---

## 2) Setup (Developer)

### Create/activate venv

**If you use `venv`:**

```powershell
cd C:\Users\GenEx\Desktop\AutoShorts
python -m venv venv
.\venv\Scripts\Activate.ps1