import traceback
import datetime
import os

LOG_FILE = "logs/auto_debug.log"

def log_error(e):
    os.makedirs("logs", exist_ok=True)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write("\n" + "="*50 + "\n")
        f.write(f"TIME: {datetime.datetime.now()}\n")
        f.write("ERROR:\n")
        f.write(str(e) + "\n\n")
        f.write("TRACEBACK:\n")
        f.write(traceback.format_exc())
        f.write("\n")

    print("\n❌ ERROR TERSIMPAN KE logs/auto_debug.log\n")


def format_for_ai():
    if not os.path.exists(LOG_FILE):
        return "Belum ada error log."

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        error_text = f.read()

    prompt = f"""
Gunakan konteks GNX STUDIO

MODE: DEBUG

Error:
{error_text}

Tugas:
- jelaskan penyebab
- beri fix langsung
"""

    return prompt