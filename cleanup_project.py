import os
import shutil

# Konfigurasi Path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(PROJECT_ROOT, "_BACKUP_SYSTEM_LAMA")

if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

# 1. File dari Root yang harus dipindah (Sisa tester & duplikat)
ROOT_FILES_TO_BACKUP = [
    "callback_server.py", 
    "fix_tiktok.py",
    "test_ui.py",
    ".env.example.py",
    ".gitignore.py",
    "README_INSTALL.txt",
    "token.json", # Backup token lama agar tidak bentrok dengan account_db.json
    "GNX Production Studio.spec"
]

# 2. File dari Core & Tokens yang sudah tidak dipakai
CORE_FILES_TO_BACKUP = [
    "core/engine_guard.py",
    "core/gnx_job_runner.py",
    "core/tokens/get_tt_token.py",
    "core/tokens/meta_sessions.json",
    "core/tokens/meta_tokens.json",
    "core/tokens/temp_tiktok_verifier.txt"
]

def run_full_cleanup():
    print(f"[*] Memulai pembersihan root & core ke: {BACKUP_DIR}...")

    # Gabungkan semua daftar file
    all_files = []
    for f in ROOT_FILES_TO_BACKUP: all_files.append(f)
    for f in CORE_FILES_TO_BACKUP: all_files.append(f)

    for rel_path in all_files:
        source = os.path.join(PROJECT_ROOT, rel_path)
        if os.path.exists(source):
            filename = os.path.basename(rel_path)
            dest = os.path.join(BACKUP_DIR, filename)
            
            try:
                # Jika file sudah ada di backup, tambahkan nama unik agar tidak tertimpa
                if os.path.exists(dest):
                    dest = os.path.join(BACKUP_DIR, f"old_{filename}")
                
                shutil.move(source, dest)
                print(f"[✔] Pindah: {filename}")
            except Exception as e:
                print(f"[!] Gagal pindah {filename}: {e}")

    # Bersihkan __pycache__
    for root, dirs, files in os.walk(PROJECT_ROOT):
        if "__pycache__" in dirs:
            shutil.rmtree(os.path.join(root, "__pycache__"))

    print("\n[!] CLEANUP SELESAI. Root folder sekarang bersih!")
    print("[*] File utama (main.py, requirements, .env) tetap aman di tempatnya.")

if __name__ == "__main__":
    run_full_cleanup()