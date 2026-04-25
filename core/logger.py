import os
import logging
from datetime import datetime
from core.app_paths import get_logs_path

# Setup logging ke file dan console
log_file = os.path.join(get_logs_path(), f"gnx_{datetime.now().strftime('%Y%m%d')}.log")

# Perbaikan format: Menggunakan { style agar tidak bentrok dengan karakter [
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def log_info(msg):
    logging.info(msg)

def log_error(msg):
    logging.error(msg)