import os
import json
import math
import shutil
import tempfile
import subprocess
from pathlib import Path

import cv2
import numpy as np


class VideoProcessorError(Exception):
    pass


class VideoProcessor:
    def __init__(self, ffmpeg_path="ffmpeg", ffprobe_path="ffprobe"):
        self.ffmpeg = ffmpeg_path
        self.ffprobe = ffprobe_path
        self.face_cascade = self._load_face_cascade()

    # =========================================================
    # CASCADE LOADER
    # =========================================================

    def _load_face_cascade(self):
        candidates = []

        try:
            candidates.append(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml")
        except Exception:
            pass

        candidates.append(Path("assets") / "opencv" / "haarcascade_frontalface_default.xml")
        candidates.append(Path(__file__).resolve().parent.parent / "assets" / "opencv" / "haarcascade_frontalface_default.xml")

        for path in candidates:
            try:
                if path and path.exists():
                    cascade = cv2.CascadeClassifier(str(path))
                    if not cascade.empty():
                        print(f"[FACE] cascade loaded from: {path}")
                        return cascade
            except Exception as e:
                print(f"[FACE] cascade load candidate failed: {path} | {e}")

        print("[FACE] WARNING: Failed to load OpenCV face cascade. Fallback mode will be used.")
        return None

    # =========================================================
    # VIDEO INFO
    # =========================================================

    def get_video_info(self, video_path):
        if not os.path.exists(video_path):
            raise VideoProcessorError("Input video file not found")

        cmd = [
            self.ffprobe,
            "-v", "error",
            "-show_streams",
            "-show_format",
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
        audio_stream = None
        for stream in data.get("streams", []):
            if stream.get("codec_type") == "video" and video_stream is None:
                video_stream = stream
            elif stream.get("codec_type") == "audio" and audio_stream is None:
                audio_stream = stream

        if not video_stream:
            raise VideoProcessorError("No video stream found")

        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))

        duration = 0.0
        if video_stream.get("duration"):
            duration = float(video_stream.get("duration", 0))
        else:
            fmt = data.get("format", {})
            duration = float(fmt.get("duration", 0) or 0)

        fps = 0.0
        fps_raw = video_stream.get("r_frame_rate") or video_stream.get("avg_frame_rate") or "0/1"
        try:
            num, den = fps_raw.split("/")
            num = float(num)
            den = float(den)
            if den != 0:
                fps = num / den
        except Exception:
            fps = 0.0

        if fps <= 1.0:
            fps = 30.0

        if width == 0 or height == 0:
            raise VideoProcessorError("Invalid video resolution")

        return {
            "width": width,
            "height": height,
            "duration": duration,
            "fps": fps,
            "has_audio": audio_stream is not None
        }

    # =========================================================
    # QUALITY PROFILE
    # =========================================================

    def _quality_profile(self, ctx):
        try:
            meta = getattr(ctx, "meta", {}) or {}
            return str(
                meta.get("quality_profile")
                or meta.get("quality")
                or "1080p"
            ).strip().lower()
        except Exception:
            return "1080p"

    def _profile_to_resolution(self, quality, orientation):
        quality = (quality or "1080p").lower().strip()

        portrait_map = {
            "480p": (480, 854),
            "720p": (720, 1280),
            "1080p": (1080, 1920),
            "1440p": (1440, 2560),
            "2160p": (2160, 3840),
            "4k": (2160, 3840),
        }

        landscape_map = {
            "480p": (854, 480),
            "720p": (1280, 720),
            "1080p": (1920, 1080),
            "1440p": (2560, 1440),
            "2160p": (3840, 2160),
            "4k": (3840, 2160),
        }

        if orientation == "portrait":
            return portrait_map.get(quality, portrait_map["1080p"])
        return landscape_map.get(quality, landscape_map["1080p"])

    # =========================================================
    # FACE CENTER / META
    # =========================================================

    def _face_center_settings(self, ctx):
        try:
            meta = getattr(ctx, "meta", {}) or {}
            fc = meta.get("face_centering") or {}
            strategy = str(fc.get("strategy", "center_face")).strip().lower()

            return {
                "enabled": bool(fc.get("enabled", False)),
                "mode": str(fc.get("mode", "off")).strip().lower(),
                "strategy": strategy,
                "fallback": str(fc.get("fallback", "center_face")).strip().lower(),
                "debug_overlay": bool(fc.get("debug_overlay", False)),
                "switch_cooldown_sec": float(fc.get("switch_cooldown_sec", 1.2)),
                "lock_strength": float(fc.get("lock_strength", 0.72)),
                "min_face_size_ratio": float(fc.get("min_face_size_ratio", 0.015)),
            }
        except Exception:
            return {
                "enabled": False,
                "mode": "off",
                "strategy": "center_face",
                "fallback": "center_face",
                "debug_overlay": False,
                "switch_cooldown_sec": 1.2,
                "lock_strength": 0.72,
                "min_face_size_ratio": 0.015,
            }

    # =========================================================
    # DURATION POLICY
    # =========================================================

    def _max_duration_for_orientation(self, orientation):
        if orientation == "portrait":
            return 120
        return 180

    def _min_duration_for_orientation(self, orientation):
        if orientation == "portrait":
            return 30
        return None

    # =========================================================
    # FACE DETECTION / TRACKING
    # =========================================================

    def _detect_faces(self, frame_bgr):
        if self.face_cascade is None:
            gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
            return gray, []

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.08,
            minNeighbors=5,
            minSize=(48, 48),
            flags=cv2.CASCADE_SCALE_IMAGE
        )

        return gray, faces

    def _face_box_to_dict(self, face):
        x, y, w, h = [int(v) for v in face]
        return {"x": x, "y": y, "w": w, "h": h}

    def _face_center(self, face):
        return (
            face["x"] + face["w"] / 2.0,
            face["y"] + face["h"] / 2.0
        )

    def _center_distance_score(self, face, frame_w, frame_h):
        cx, cy = self._face_center(face)
        fx = frame_w / 2.0
        fy = frame_h / 2.0

        dist = math.sqrt((cx - fx) ** 2 + (cy - fy) ** 2)
        max_dist = math.sqrt(fx ** 2 + fy ** 2)
        score = 1.0 - (dist / max_dist if max_dist > 0 else 0.0)
        return max(0.0, min(1.0, score))

    def _proximity_to_prev_score(self, face, prev_center, frame_w, frame_h):
        if prev_center is None:
            return 0.5

        cx, cy = self._face_center(face)
        dist = math.sqrt((cx - prev_center[0]) ** 2 + (cy - prev_center[1]) ** 2)
        max_dist = math.sqrt(frame_w ** 2 + frame_h ** 2)
        score = 1.0 - (dist / max_dist if max_dist > 0 else 0.0)
        return max(0.0, min(1.0, score))

    def _area_score(self, face, frame_w, frame_h):
        area = float(face["w"] * face["h"])
        full = float(frame_w * frame_h)
        if full <= 0:
            return 0.0
        ratio = area / full
        score = min(ratio * 12.0, 1.0)
        return max(0.0, min(1.0, score))

    def _mouth_motion_score(self, gray_now, gray_prev, face):
        if gray_prev is None:
            return 0.0

        x = face["x"]
        y = face["y"]
        w = face["w"]
        h = face["h"]

        x0 = max(0, x)
        y0 = max(0, y + int(h * 0.45))
        x1 = min(gray_now.shape[1], x + w)
        y1 = min(gray_now.shape[0], y + h)

        if x1 <= x0 or y1 <= y0:
            return 0.0

        roi_now = gray_now[y0:y1, x0:x1]
        roi_prev = gray_prev[y0:y1, x0:x1]

        if roi_now.size == 0 or roi_prev.size == 0:
            return 0.0

        if roi_now.shape != roi_prev.shape:
            try:
                roi_prev = cv2.resize(roi_prev, (roi_now.shape[1], roi_now.shape[0]))
            except Exception:
                return 0.0

        diff = cv2.absdiff(roi_now, roi_prev)
        score = float(np.mean(diff)) / 32.0
        return max(0.0, min(1.0, score))

    def _side_bias(self, face, frame_w):
        cx, _ = self._face_center(face)
        if cx < frame_w * 0.42:
            return "left"
        if cx > frame_w * 0.58:
            return "right"
        return "center"

    def _same_identity_score(self, face, locked_face, frame_w, frame_h):
        if locked_face is None:
            return 0.0

        cx1, cy1 = self._face_center(face)
        cx2, cy2 = self._face_center(locked_face)

        d = math.sqrt((cx1 - cx2) ** 2 + (cy1 - cy2) ** 2)
        max_d = math.sqrt(frame_w ** 2 + frame_h ** 2)
        pos_score = 1.0 - (d / max_d if max_d > 0 else 0.0)

        area1 = face["w"] * face["h"]
        area2 = locked_face["w"] * locked_face["h"]
        if area1 <= 0 or area2 <= 0:
            area_score = 0.0
        else:
            ratio = min(area1, area2) / max(area1, area2)
            area_score = max(0.0, min(1.0, ratio))

        return (pos_score * 0.7) + (area_score * 0.3)

    def _filter_small_faces(self, faces, frame_w, frame_h, min_face_size_ratio):
        min_area = frame_w * frame_h * max(0.001, min_face_size_ratio)
        out = []
        for f in faces:
            fd = self._face_box_to_dict(f)
            if (fd["w"] * fd["h"]) >= min_area:
                out.append(fd)
        return out

    def _choose_best_face(self, faces, frame_w, frame_h, prev_center, strategy, gray_now, gray_prev, locked_face=None):
        if faces is None or len(faces) == 0:
            return None, []

        scored = []

        for face in faces:
            area_score = self._area_score(face, frame_w, frame_h)
            center_score = self._center_distance_score(face, frame_w, frame_h)
            prev_score = self._proximity_to_prev_score(face, prev_center, frame_w, frame_h)
            mouth_score = self._mouth_motion_score(gray_now, gray_prev, face)
            identity_score = self._same_identity_score(face, locked_face, frame_w, frame_h)

            if strategy == "speaker_priority":
                score = (
                    area_score * 0.28 +
                    mouth_score * 0.34 +
                    prev_score * 0.18 +
                    identity_score * 0.12 +
                    center_score * 0.08
                )
            elif strategy == "eyes_priority":
                upper_face_bonus = max(0.0, 1.0 - ((face["y"] + face["h"] * 0.35) / max(frame_h, 1)))
                score = (
                    area_score * 0.34 +
                    prev_score * 0.20 +
                    identity_score * 0.18 +
                    center_score * 0.14 +
                    upper_face_bonus * 0.14
                )
            elif strategy == "podcast_dual_speaker":
                side = self._side_bias(face, frame_w)
                side_bonus = 0.15 if side in ("left", "right") else 0.0
                score = (
                    area_score * 0.25 +
                    mouth_score * 0.28 +
                    prev_score * 0.16 +
                    identity_score * 0.16 +
                    center_score * 0.05 +
                    side_bonus
                )
            else:
                score = (
                    area_score * 0.42 +
                    prev_score * 0.22 +
                    identity_score * 0.14 +
                    center_score * 0.22
                )

            scored.append({
                "face": face,
                "score": float(score),
                "mouth_score": float(mouth_score),
                "area_score": float(area_score),
                "center_score": float(center_score),
                "identity_score": float(identity_score),
                "side": self._side_bias(face, frame_w),
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        best = scored[0]["face"] if scored else None
        return best, scored

    def _should_switch_target(self, best_scored, locked_scored, face_settings, fps, frames_since_switch):
        cooldown_frames = max(1, int(face_settings["switch_cooldown_sec"] * fps))
        if frames_since_switch < cooldown_frames:
            return False

        if best_scored is None:
            return False
        if locked_scored is None:
            return True

        margin = float(face_settings["lock_strength"])
        return best_scored["score"] > (locked_scored["score"] + (0.18 * margin))

    def _target_center_from_face(self, face, strategy):
        x = face["x"]
        y = face["y"]
        w = face["w"]
        h = face["h"]

        cx = x + (w / 2.0)
        cy = y + (h / 2.0)

        if strategy == "eyes_priority":
            cy = y + (h * 0.38)
        elif strategy in ("speaker_priority", "podcast_dual_speaker"):
            cy = y + (h * 0.46)

        return float(cx), float(cy)

    def _crop_size_for_ratio(self, frame_w, frame_h, target_ratio):
        current_ratio = frame_w / frame_h

        if current_ratio > target_ratio:
            crop_h = frame_h
            crop_w = int(frame_h * target_ratio)
        else:
            crop_w = frame_w
            crop_h = int(frame_w / target_ratio)

        crop_w = max(2, min(crop_w, frame_w))
        crop_h = max(2, min(crop_h, frame_h))
        return crop_w, crop_h

    def _crop_frame_centered(self, frame, center_x, center_y, crop_w, crop_h):
        frame_h, frame_w = frame.shape[:2]

        x1 = int(round(center_x - crop_w / 2.0))
        y1 = int(round(center_y - crop_h / 2.0))

        x1 = max(0, min(x1, frame_w - crop_w))
        y1 = max(0, min(y1, frame_h - crop_h))

        x2 = x1 + crop_w
        y2 = y1 + crop_h

        return frame[y1:y2, x1:x2], (x1, y1, x2, y2)

    def _draw_debug_overlay(self, frame, faces, locked_face, crop_box, strategy):
        out = frame.copy()

        for face in faces:
            x = face["x"]
            y = face["y"]
            w = face["w"]
            h = face["h"]
            cv2.rectangle(out, (x, y), (x + w, y + h), (100, 180, 255), 2)

        if locked_face is not None:
            x = locked_face["x"]
            y = locked_face["y"]
            w = locked_face["w"]
            h = locked_face["h"]
            cv2.rectangle(out, (x, y), (x + w, y + h), (0, 255, 0), 3)
            cv2.putText(
                out,
                f"TARGET {strategy}",
                (x, max(20, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
                cv2.LINE_AA
            )

        if crop_box is not None:
            x1, y1, x2, y2 = crop_box
            cv2.rectangle(out, (x1, y1), (x2, y2), (255, 0, 255), 2)

        return out

    # =========================================================
    # AUDIO MUX
    # =========================================================

    def _mux_audio(self, silent_video, source_video, output_path, duration_limit=None):
        info = self.get_video_info(source_video)
        if not info.get("has_audio"):
            shutil.copy2(silent_video, output_path)
            return

        cmd = [
            self.ffmpeg,
            "-y",
            "-i", silent_video,
            "-i", source_video,
        ]

        if duration_limit:
            cmd.extend(["-t", str(int(duration_limit))])

        cmd.extend([
            "-map", "0:v:0",
            "-map", "1:a:0?",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            output_path
        ])

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print("FFMPEG MUX ERROR:")
            print(result.stderr)
            raise VideoProcessorError("Failed to mux processed video with audio")

    # =========================================================
    # DYNAMIC FACE-CENTER RENDER
    # =========================================================

    def _render_dynamic_crop(self, input_path, output_path, orientation, ctx=None):
        info = self.get_video_info(input_path)
        src_w = int(info["width"])
        src_h = int(info["height"])
        fps = float(info["fps"])
        duration = float(info["duration"])

        face_settings = self._face_center_settings(ctx)
        quality = self._quality_profile(ctx)

        if self.face_cascade is None:
            print("[FACE] cascade unavailable, forcing fallback crop mode.")

        target_w, target_h = self._profile_to_resolution(quality, orientation)
        target_ratio = target_w / target_h

        min_duration = self._min_duration_for_orientation(orientation)
        max_duration = self._max_duration_for_orientation(orientation)

        if min_duration and duration and duration < min_duration:
            pass

        effective_duration = duration
        if max_duration and duration and duration > max_duration:
            effective_duration = float(max_duration)

        max_frames = None
        if effective_duration and fps > 0:
            max_frames = int(effective_duration * fps)

        crop_w, crop_h = self._crop_size_for_ratio(src_w, src_h, target_ratio)

        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise VideoProcessorError("Failed to open input video with OpenCV")

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        temp_dir = tempfile.mkdtemp(prefix="gnx_face_render_")
        silent_output = os.path.join(temp_dir, f"silent_{orientation}.mp4")

        writer = cv2.VideoWriter(silent_output, fourcc, fps, (target_w, target_h))
        if not writer.isOpened():
            cap.release()
            raise VideoProcessorError("Failed to create output writer")

        mode = face_settings["mode"]
        strategy = face_settings["strategy"]

        detect_interval_frames = 1 if mode == "best_face_center" else max(1, int(round(fps / 5.0)))

        if mode == "best_face_center":
            smooth_alpha = 0.10
        elif mode == "auto_fast":
            smooth_alpha = 0.24
        else:
            smooth_alpha = 0.20

        frame_index = 0
        detected_once = False

        target_center = (src_w / 2.0, src_h / 2.0)
        smooth_center = (src_w / 2.0, src_h / 2.0)

        prev_detect_gray = None
        prev_face_center = None
        locked_face = None
        frames_since_switch = 999999

        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                if max_frames is not None and frame_index >= max_frames:
                    break

                faces_debug = []

                if frame_index % detect_interval_frames == 0:
                    gray_now, faces_raw = self._detect_faces(frame)
                    faces = self._filter_small_faces(
                        faces_raw,
                        src_w,
                        src_h,
                        face_settings["min_face_size_ratio"]
                    )
                    faces_debug = list(faces)

                    if self.face_cascade is not None and face_settings["enabled"] and face_settings["mode"] != "off" and len(faces) > 0:
                        best_face, scored_faces = self._choose_best_face(
                            faces=faces,
                            frame_w=src_w,
                            frame_h=src_h,
                            prev_center=prev_face_center,
                            strategy=strategy,
                            gray_now=gray_now,
                            gray_prev=prev_detect_gray,
                            locked_face=locked_face
                        )

                        locked_scored = None
                        best_scored = None

                        if scored_faces:
                            best_scored = scored_faces[0]
                            if locked_face is not None:
                                for item in scored_faces:
                                    if item["face"] == locked_face:
                                        locked_scored = item
                                        break

                        if locked_face is None and best_face is not None:
                            locked_face = best_face
                            frames_since_switch = 0
                        elif best_face is not None:
                            if self._should_switch_target(
                                best_scored=best_scored,
                                locked_scored=locked_scored,
                                face_settings=face_settings,
                                fps=fps,
                                frames_since_switch=frames_since_switch
                            ):
                                locked_face = best_face
                                frames_since_switch = 0
                            else:
                                refreshed = None
                                refreshed_score = -1.0
                                for item in scored_faces:
                                    identity_score = self._same_identity_score(
                                        item["face"], locked_face, src_w, src_h
                                    )
                                    if identity_score > refreshed_score:
                                        refreshed_score = identity_score
                                        refreshed = item["face"]
                                if refreshed is not None and refreshed_score > 0.25:
                                    locked_face = refreshed

                        if locked_face is not None:
                            target_center = self._target_center_from_face(locked_face, strategy)
                            prev_face_center = target_center
                            detected_once = True

                    prev_detect_gray = gray_now

                if not detected_once:
                    target_center = (src_w / 2.0, src_h / 2.0)

                smooth_center = (
                    (1.0 - smooth_alpha) * smooth_center[0] + smooth_alpha * target_center[0],
                    (1.0 - smooth_alpha) * smooth_center[1] + smooth_alpha * target_center[1],
                )

                cropped, crop_box = self._crop_frame_centered(
                    frame=frame,
                    center_x=smooth_center[0],
                    center_y=smooth_center[1],
                    crop_w=crop_w,
                    crop_h=crop_h
                )

                if face_settings["debug_overlay"]:
                    frame_for_debug = self._draw_debug_overlay(
                        frame=frame,
                        faces=faces_debug,
                        locked_face=locked_face,
                        crop_box=crop_box,
                        strategy=strategy
                    )
                    cropped, _ = self._crop_frame_centered(
                        frame=frame_for_debug,
                        center_x=smooth_center[0],
                        center_y=smooth_center[1],
                        crop_w=crop_w,
                        crop_h=crop_h
                    )

                rendered = cv2.resize(cropped, (target_w, target_h), interpolation=cv2.INTER_AREA)
                writer.write(rendered)

                frame_index += 1
                frames_since_switch += 1

        finally:
            cap.release()
            writer.release()

        if not os.path.exists(silent_output) or os.path.getsize(silent_output) < 1024:
            raise VideoProcessorError("Dynamic face-center render failed: invalid silent output")

        try:
            self._mux_audio(
                silent_video=silent_output,
                source_video=input_path,
                output_path=output_path,
                duration_limit=effective_duration
            )
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self._ensure_output_ok(output_path)
        return output_path

    # =========================================================
    # PUBLIC METHODS
    # =========================================================

    def to_portrait(self, input_path, output_path, ctx=None):
        return self._render_dynamic_crop(
            input_path=input_path,
            output_path=output_path,
            orientation="portrait",
            ctx=ctx
        )

    def to_landscape(self, input_path, output_path, ctx=None):
        return self._render_dynamic_crop(
            input_path=input_path,
            output_path=output_path,
            orientation="landscape",
            ctx=ctx
        )

    # =========================================================
    # VALIDATION
    # =========================================================

    def _ensure_output_ok(self, output_path):
        if not os.path.exists(output_path):
            raise VideoProcessorError(f"Output file not created: {output_path}")

        size = os.path.getsize(output_path)
        if size < 1024:
            raise VideoProcessorError(f"Output file invalid/too small: {output_path}")