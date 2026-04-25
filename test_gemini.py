from google import genai
from core import settings_store

def sync_check():
    # 1. Ambil config dari AppData
    cfg = settings_store.load_config()
    api_key = settings_store.get(cfg, "gemini.api_key")
    
    if not api_key:
        print("❌ Error: API Key kosong.")
        return

    # 2. Inisialisasi Client
    client = genai.Client(api_key=api_key)
    
    print("🔍 Mencari daftar model yang aktif untuk Key ini...")
    try:
        # Ambil semua nama model yang tersedia
        model_names = [m.name for m in client.models.list()]
        
        if not model_names:
            print("❌ Tidak ada model yang ditemukan.")
            return

        print(f"✅ Model ditemukan: {model_names}")

        # Cari model yang ada kata 'flash' (biasanya paling stabil untuk testing)
        target = next((m for m in model_names if "flash" in m), model_names[0])
        
        print(f"⏳ Mencoba generate dengan: {target}...")
        response = client.models.generate_content(
            model=target, 
            contents="Buat caption singkat untuk video viral 'AutoShorts Production'."
        )
        
        if response.text:
            print("\n🤖 Respon Gemini:")
            print("-" * 30)
            print(response.text)
            print("-" * 30)
            print("\n🚀 AKHIRNYA SINKRON TOTAL! Gaskan Mas Bro!")
            
    except Exception as e:
        print(f"❌ Masalah: {str(e)}")
        print("\n💡 Tips: Pastikan Anda sudah membuat API Key BARU di 'New Project' Google AI Studio.")

if __name__ == "__main__":
    sync_check()