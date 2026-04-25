from core import settings_store

def setup_gemini():
    # 1. Muat config yang sudah ada di AppData
    cfg = settings_store.load_config()

    # 2. Masukkan API Key Gemini
    # Ganti 'KODE_API_KEY_ABANG' dengan key asli dari Google AI Studio
    api_key = "AIzaSyAiILvtv6Xcb01QTigxu9lMDBLoTODwSY0" 
    
    settings_store.set(cfg, "gemini.api_key", api_key)

    # 3. Simpan permanen ke gnx_config.json
    settings_store.save_config(cfg)
    
    print("✅ Berhasil! API Gemini sudah tersimpan di AppData.")

if __name__ == "__main__":
    setup_gemini()