import whisper
import os


class SubtitleService:

    def __init__(self, model_size="base"):
        self.model = whisper.load_model(model_size)

    def transcribe(self, video_path, language=None):
        result = self.model.transcribe(
            video_path,
            language=language
        )
        return result["segments"]

    def save_srt(self, segments, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            for i, seg in enumerate(segments, 1):
                start = self._format_time(seg["start"])
                end = self._format_time(seg["end"])
                text = seg["text"].strip()

                f.write(f"{i}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{text}\n\n")

    def _format_time(self, seconds):
        hrs = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return f"{hrs:02}:{mins:02}:{secs:02},{ms:03}"
