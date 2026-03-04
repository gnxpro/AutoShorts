# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules
import os

block_cipher = None

project_root = os.path.abspath(".")
assets_dir = os.path.join(project_root, "assets")
ffmpeg_dir = os.path.join(assets_dir, "ffmpeg")

hiddenimports = []
hiddenimports += collect_submodules("customtkinter")
hiddenimports += collect_submodules("core")
hiddenimports += collect_submodules("gnx")
hiddenimports += collect_submodules("pages")
hiddenimports += collect_submodules("ui")

# Premium: include OpenAI stack
hiddenimports += collect_submodules("openai")
hiddenimports += collect_submodules("httpx")
hiddenimports += collect_submodules("pydantic")

datas = []
binaries = []


def add_dir_as_datas(src_dir: str, dest_prefix: str):
    if not os.path.isdir(src_dir):
        return
    for root, _, files in os.walk(src_dir):
        for f in files:
            src = os.path.join(root, f)
            rel = os.path.relpath(root, src_dir)
            dest = os.path.normpath(os.path.join(dest_prefix, rel))
            datas.append((src, dest))


def find_worker_exe() -> str | None:
    # Try multiple common locations in your project
    candidates = [
        os.path.join(project_root, "gnx_worker.exe"),
        os.path.join(project_root, "installer", "gnx_worker.exe"),
        os.path.join(project_root, "assets", "gnx_worker.exe"),
        os.path.join(project_root, "tools", "gnx_worker.exe"),
        os.path.join(project_root, "bin", "gnx_worker.exe"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p

    # last resort: search recursively (but keep it limited)
    for root, _, files in os.walk(project_root):
        if "dist" in root.lower() or "build" in root.lower() or ".venv" in root.lower() or "venv" in root.lower():
            continue
        for f in files:
            if f.lower() == "gnx_worker.exe":
                return os.path.join(root, f)
    return None


# include assets/*
add_dir_as_datas(assets_dir, "assets")

# optional ffmpeg in assets/ffmpeg/*
add_dir_as_datas(ffmpeg_dir, os.path.join("assets", "ffmpeg"))

# ✅ include worker exe (force-copy via BOTH datas and binaries)
worker_path = find_worker_exe()
if worker_path:
    # Copy to app root folder
    datas.append((worker_path, "."))
    binaries.append((worker_path, "."))
else:
    # Build still works without worker; Worker Control will warn
    pass


a = Analysis(
    ["main.py"],
    pathex=[project_root],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="GNX_Production",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=os.path.join(assets_dir, "icon.ico") if os.path.isfile(os.path.join(assets_dir, "icon.ico")) else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="GNX_Production",
)