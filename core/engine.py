import os, time, subprocess, cv2, shutil, re
from pathlib import Path
from datetime import datetime
from core.config_manager import ConfigManager
from core.youtube_utils import YouTubeUtils
from core.logger import log_info, log_error
from core.scheduler_engine import GNXScheduler 

# --- IMPORT MESIN FACE TRACKER ABANG ---
from core.video_processor import VideoProcessor

class Engine:
    def __init__(self):
        self.config = ConfigManager()
        self.output_dir = Path.home() / "Desktop" / "GNX Production" / "Outputs"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.youtube_service = YouTubeUtils() 
        
        # Bangunkan AI Face Tracker
        try:
            self.video_processor = VideoProcessor()
        except Exception as e:
            log_error(f"Gagal memuat VideoProcessor: {e}")
            self.video_processor = None

        try:
            from core.cloudinary_service import CloudinaryService
            self.cloudinary_service = CloudinaryService()
        except: self.cloudinary_service = None
        self.config.apply_cloudinary_env()

    def clean_filename(self, filename):
        return re.sub(r'[\\/*?:"<>|]', "", filename).replace(" ", "_")

    def get_video_duration(self, file_path):
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{file_path}"'
        try:
            return float(subprocess.check_output(cmd, shell=True).decode().strip())
        except: return 0

    def process_image_to_video(self, source, log_callback, update_ui_callback):
        try:
            video_title = self.clean_filename(Path(source).stem)
            log_callback(f"STYLE >> Image reference set: {Path(source).name}")
            dest_img = self.output_dir / Path(source).name
            if str(source) != str(dest_img): shutil.copy(source, dest_img)
            res = self.cloudinary_service.upload(str(dest_img)) if self.cloudinary_service else {}
            
            scheduler = GNXScheduler(on_log_callback=lambda msg: log_callback(msg['message']))
            scheduler.add_to_queue({
                "title": f"AI Gen: {video_title}",
                "type": "IMAGE_GEN",
                "file_name": f"Outputs/{Path(source).name}", 
                "targets": ["Instagram", "Facebook"],
                "url": res.get("secure_url", "")
            })
            
            if update_ui_callback:
                update_ui_callback({"title": f"AI Gen: {video_title}", "url": res.get("secure_url", ""), "local_path": str(dest_img), "status": "Ready to Process", "type": "IMAGE_GEN"})
            return True
        except Exception as e:
            log_error(f"PINTU_FOTO_ERROR >> {str(e)}")
            return False

    def process_video_editing(self, source, source_type, command, log_callback, update_ui_callback):
        try:
            temp_raw = self.output_dir / "raw_source.mp4"
            
            if source_type == "YOUTUBE":
                log_callback("FETCH >> Mengambil informasi judul video...")
                try:
                    cmd_title = f'yt-dlp --print title "{source}"'
                    raw_title = subprocess.check_output(cmd_title, shell=True, text=True, encoding='utf-8', errors='ignore').strip()
                except:
                    raw_title = source.split("/")[-1]
                
                log_callback("FETCH >> Downloading from YouTube...")
                os.system(f'yt-dlp --no-warnings -f mp4 -o "{temp_raw}" {source}')
            else:
                raw_title = Path(source).stem
                shutil.copy(source, temp_raw)

            clean_title = self.clean_filename(raw_title)
            total_dur = self.get_video_duration(temp_raw)
            
            if total_dur <= 0:
                log_callback("❌ ERROR >> Gagal mendapatkan video source atau durasi 0.")
                return False

            for start in range(0, int(total_dur), 60):
                part_idx = (start // 60) + 1
                temp_part = self.output_dir / f"TEMP_PART_{part_idx}.mp4"
                final_name = f"PART_{part_idx}_{clean_title}.mp4"
                final_output = self.output_dir / final_name
                
                log_callback(f"RENDER >> Memotong Part {part_idx}...")
                # Potong video 60 detik (TANPA CROP DULU)
                os.system(f'ffmpeg -hide_banner -loglevel error -ss {start} -t 60 -i "{temp_raw}" -c copy -y "{temp_part}"')
                
                if temp_part.exists():
                    log_callback(f"🎯 FACE TRACKER >> Menganalisa wajah untuk Part {part_idx}...")
                    
                    # Coba pakai AI Face Tracker
                    tracker_success = False
                    if self.video_processor:
                        try:
                            # Memanggil OpenCV dari video_processor.py
                            self.video_processor.to_portrait(str(temp_part), str(final_output))
                            tracker_success = True
                        except Exception as e:
                            log_error(f"Face Tracker Error: {e}")
                    
                    # Jika AI Face Tracker gagal (atau tidak ada wajah), kembali ke potong tengah biasa
                    if not tracker_success or not final_output.exists():
                        log_callback(f"⚠️ Wajah tidak jelas, pakai potong tengah biasa untuk Part {part_idx}...")
                        os.system(f'ffmpeg -hide_banner -loglevel error -i "{temp_part}" -vf "crop=ih*(9/16):ih" -y "{final_output}"')
                
                # Bersihkan file part sementara
                if temp_part.exists(): os.remove(temp_part)
                
                # Masukkan ke kalender jika sukses
                if final_output.exists() and os.path.getsize(final_output) > 1000:
                    log_callback(f"✅ DONE >> Part {part_idx} berhasil di-render!")
                    res = self.cloudinary_service.upload(str(final_output)) if self.cloudinary_service else {}
                    
                    scheduler = GNXScheduler(on_log_callback=lambda msg: log_callback(msg['message']))
                    scheduler.add_to_queue({
                        "title": f"{clean_title} P{part_idx}",
                        "type": "EDIT",
                        "file_name": f"Outputs/{final_name}",
                        "targets": ["YouTube", "TikTok", "Facebook", "Instagram"],
                        "url": res.get("secure_url", "") 
                    })
                    
                    if update_ui_callback:
                        update_ui_callback({"title": f"{clean_title} P{part_idx}", "url": res.get("secure_url", ""), "local_path": str(final_output), "status": "Success", "type": "EDIT"})
            
            if temp_raw.exists(): os.remove(temp_raw)
            return True
        except Exception as e:
            log_error(f"PINTU_VIDEO_ERROR >> {str(e)}")
            return False

    def process_full_pipeline(self, source, source_type, command, log_callback, update_ui_callback=None):
        is_image = any(source.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp'])
        if is_image: return self.process_image_to_video(source, log_callback, update_ui_callback)
        return self.process_video_editing(source, source_type, command, log_callback, update_ui_callback)