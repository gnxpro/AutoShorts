from core.video_pipeline import split_into_clips
from core.services.subtitle_service import SubtitleService


class ClipService:

    @staticmethod
    def generate(input_path, output_dir, duration, count, progress_callback=None):
        return split_into_clips(
            input_path,
            output_dir,
            duration,
            count,
            progress_callback=progress_callback
        )

    @staticmethod
    def generate_subtitles(video_path, output_dir):
        service = SubtitleService()
        segments = service.transcribe(video_path)

        srt_path = output_dir + "/subtitles.srt"
        service.save_srt(segments, srt_path)
        return srt_path
