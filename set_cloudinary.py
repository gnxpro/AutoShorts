from core import settings_store

def setup_cloudinary():
    cfg = settings_store.load_config()
    
    # Masukkan data dari Dashboard Cloudinary Abang
    settings_store.set(cfg, "cloudinary.cloud_name", "datn1gpxd")
    settings_store.set(cfg, "cloudinary.api_key", "122853918123998")
    settings_store.set(cfg, "cloudinary.api_secret", "H_8EluqET3DAYNi3d95gciNqsy8")

    settings_store.save_config(cfg)
    print("✅ Cloudinary berhasil sinkron ke AppData!")

if __name__ == "__main__":
    setup_cloudinary()