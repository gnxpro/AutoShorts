import os
import sys

def get_app_root():
    """Mendapatkan root folder aplikasi AutoShorts"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_core_path():
    return os.path.join(get_app_root(), "core")

def get_tokens_path():
    path = os.path.join(get_app_root(), "tokens")
    os.makedirs(path, exist_ok=True)
    return path

def get_logs_path():
    """Fungsi yang tadi hilang: Membuat folder logs"""
    path = os.path.join(get_app_root(), "logs")
    os.makedirs(path, exist_ok=True)
    return path

def get_temp_path():
    path = os.path.join(get_app_root(), "temp")
    os.makedirs(path, exist_ok=True)
    return path

def get_downloads_path():
    path = os.path.join(get_app_root(), "downloads")
    os.makedirs(path, exist_ok=True)
    return path