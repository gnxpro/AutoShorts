import os
import json
import subprocess
import hashlib
import uuid
from pathlib import Path

# --- STANDALONE FUNCTIONS FOR UI COMPATIBILITY ---

def get_license_path():
    """Returns the absolute path to the license file."""
    return os.path.abspath(os.path.join("core", "gnx_license.json"))

def load_effective_capabilities():
    """Function used by AppShell and Engine to check current limits."""
    manager = LicenseManager()
    return manager.get_current_caps()

def load_license_capabilities():
    """Function specifically requested by LicensePage."""
    manager = LicenseManager()
    return manager.get_current_caps()

# --- CORE LICENSE CLASS ---

class LicenseManager:
    def __init__(self):
        self.config_path = get_license_path()
        self.hwid = self._generate_hwid()

    def _generate_hwid(self):
        """Generates a unique Hardware ID."""
        try:
            cmd = "powershell (Get-CimInstance Win32_ComputerSystemProduct).UUID"
            raw_id = subprocess.check_output(cmd, shell=True).decode().strip()
            if not raw_id or "Error" in raw_id:
                raise Exception("PowerShell ID failed")
            return hashlib.sha256(raw_id.encode()).hexdigest()[:16].upper()
        except:
            try:
                fallback_id = str(uuid.getnode())
                return hashlib.sha256(fallback_id.encode()).hexdigest()[:16].upper()
            except:
                return "GNX-STATIC-ID-99"

    def get_current_caps(self):
        """Validates license and hardware lock status based on tier."""
        
        # FIX ADMIN BYPASS: Jika file lisensi belum ada (sedang testing), 
        # JANGAN kasih Basic. Langsung tembak ke BUSINESS (24 video, 100 akun).
        if not os.path.exists(self.config_path):
            return self.get_business_caps()
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # Default baca dari file, kalau error fallback ke BUSINESS
                caps = data.get("capabilities", self.get_business_caps())
                
                if caps.get("pc_lock", True):
                    is_valid, msg = self.verify_pc_access(data)
                    if not is_valid:
                        return {"effective_plan": "LOCKED", "error": msg}
                
                return caps
        except:
            # FIX ADMIN BYPASS 2: Jika file lisensi corrupt, tetapkan sebagai BUSINESS
            return self.get_business_caps()

    def verify_pc_access(self, license_data):
        """Strictly locks Premium licenses to a single PC."""
        registered_hwid = license_data.get("registered_hwid")
        
        if not registered_hwid:
            license_data["registered_hwid"] = self.hwid
            self._save_license(license_data)
            return True, "Device successfully registered."

        if registered_hwid != self.hwid:
            return False, "Access Denied: This License is locked to 1 PC only."
            
        return True, "Access Granted."

    def get_basic_caps(self):
        """Basic tier: Marketing funnel, 2 accounts, free forever."""
        return {
            "effective_plan": "BASIC",
            "max_social_accounts": 2,
            "daily_video_limit": 2,
            "max_resolution": "1080p",
            "pc_lock": True
        }

    def get_premium_caps(self):
        """Premium tier: 100 accounts, 24 videos, up to 2K, locked to 1 PC."""
        return {
            "effective_plan": "PREMIUM",
            "max_social_accounts": 100,
            "daily_video_limit": 24,
            "max_resolution": "1440p", # 2K
            "pc_lock": True
        }

    def get_business_caps(self):
        """Business tier: 100 accounts per PC, 24 vids/day, up to 4K, unlimited PCs."""
        return {
            "effective_plan": "BUSINESS",
            "max_social_accounts": 100, 
            "daily_video_limit": 24,
            "max_resolution": "4k",
            "pc_lock": False 
        }

    def _save_license(self, data):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)