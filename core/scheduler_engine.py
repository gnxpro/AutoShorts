import json
import os

class GNXScheduler:
    def __init__(self, queue_file="production_queue.json", on_log_callback=None):
        self.queue_file = queue_file
        self.on_log_callback = on_log_callback

    def load_queue(self):
        """Membaca daftar antrean dari file JSON."""
        if not os.path.exists(self.queue_file):
            return []
        try:
            with open(self.queue_file, "r") as f:
                return json.load(f)
        except Exception as e:
            if self.on_log_callback:
                self.on_log_callback({"message": f"❌ ERROR BACA ANTREAN >> {str(e)}"})
            return []

    def save_queue(self, queue_data):
        """Menyimpan pembaruan antrean ke file JSON."""
        try:
            with open(self.queue_file, "w") as f:
                json.dump(queue_data, f, indent=4)
            return True
        except Exception as e:
            if self.on_log_callback:
                self.on_log_callback({"message": f"❌ ERROR SIMPAN ANTREAN >> {str(e)}"})
            return False

    def add_to_queue(self, item_data):
        """Menambahkan video baru ke dalam antrean."""
        queue = self.load_queue()
        queue.append(item_data)
        self.save_queue(queue)
        if self.on_log_callback:
            self.on_log_callback({"message": f"✅ CALENDAR >> '{item_data.get('title', 'Video')}' masuk antrean."})

    def remove_from_queue(self, title_to_remove):
        """Menghapus item dari antrean berdasarkan judul."""
        queue = self.load_queue()
        # Saring daftar: simpan semua KECUALI yang judulnya mau dihapus
        new_queue = [item for item in queue if item.get("title") != title_to_remove]
        
        # Jika panjang antrean berubah, berarti ada yang berhasil dihapus
        if len(queue) != len(new_queue):
            self.save_queue(new_queue)
            if self.on_log_callback:
                self.on_log_callback({"message": f"🗑️ CALENDAR >> Antrean '{title_to_remove}' berhasil dihapus."})
            return True
        return False