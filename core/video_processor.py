import os
import subprocess
import json


class VideoProcessorError(Exception):
    pass


class VideoProcessor:

    def __init__(self, ffmpeg_path="ffmpeg", ffprobe_path="ffprobe"):
        self.ffmpeg = ffmpeg_path
        self.ffprobe = ffprobe_path

    # =========================================================
    # GET VIDEO INFO (ROBUST VERSION)
    # =========================================================

    def get_video_info(self, video_path):

        if not os.path.exists(video_path):
            raise VideoProcessorError("Input video file not found")

        cmd = [
            self.ffprobe,
            "-v", "error",
            "-show_streams",
            "-of", "json",
            video_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print("FFPROBE ERROR:")
            print(result.stderr)
            raise VideoProcessorError("Failed to probe video")

        data = json.loads(result.stdout)

        video_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video":
                video_stream = stream
                break

        if not video_stream:
            raise VideoProcessorError("No video stream found")

        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        duration = float(video_stream.get("duration", 0))

        if width == 0 or height == 0:
            raise VideoProcessorError("Invalid video resolution")

        return {
            "width": width,
            "height": height,
            "duration": duration
        }

    # =========================================================
    # CROP TO 9:16 (PORTRAIT)
    # =========================================================

    def to_portrait(self, input_path, output_path):

        info = self.get_video_info(input_path)

        width = info["width"]
        height = info["height"]

        target_ratio = 9 / 16
        current_ratio = width / height

        if current_ratio > target_ratio:
            # terlalu lebar → crop kiri kanan
            new_width = int(height * target_ratio)
            crop_x = int((width - new_width) / 2)
            crop_filter = f"crop={new_width}:{height}:{crop_x}:0"
        else:
            # terlalu tinggi → crop atas bawah
            new_height = int(width / target_ratio)
            crop_y = int((height - new_height) / 2)
            crop_filter = f"crop={width}:{new_height}:0:{crop_y}"

        cmd = [
            self.ffmpeg,
            "-y",
            "-i", input_path,
            "-vf", crop_filter,
            "-c:a", "copy",
            output_path
        ]

        self._run(cmd)

        return output_path

    # =========================================================
    # CROP TO 16:9 (LANDSCAPE)
    # =========================================================

    def to_landscape(self, input_path, output_path):

        info = self.get_video_info(input_path)

        width = info["width"]
        height = info["height"]

        target_ratio = 16 / 9
        current_ratio = width / height

        if current_ratio > target_ratio:
            new_width = int(height * target_ratio)
            crop_x = int((width - new_width) / 2)
            crop_filter = f"crop={new_width}:{height}:{crop_x}:0"
        else:
            new_height = int(width / target_ratio)
            crop_y = int((height - new_height) / 2)
            crop_filter = f"crop={width}:{new_height}:0:{crop_y}"

        cmd = [
            self.ffmpeg,
            "-y",
            "-i", input_path,
            "-vf", crop_filter,
            "-c:a", "copy",
            output_path
        ]

        self._run(cmd)

        return output_path

    # =========================================================
    # INTERNAL RUNNER
    # =========================================================

    def _run(self, cmd):

        process = subprocess.run(cmd)

        if process.returncode != 0:
            raise VideoProcessorError("FFmpeg processing failed")