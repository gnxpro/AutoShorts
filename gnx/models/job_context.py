from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json
import uuid


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobState(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


@dataclass
class JobSource:
    """
    Sumber video:
    - kind: "youtube" atau "file"
    - value: URL YouTube atau path file
    """
    kind: str
    value: str

    def to_dict(self) -> Dict[str, Any]:
        return {"kind": self.kind, "value": self.value}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "JobSource":
        return JobSource(kind=str(d.get("kind", "")), value=str(d.get("value", "")))


@dataclass
class JobSettings:
    """
    Setting job (ini yang nanti dipetakan dari Dashboard).
    """
    format_mode: str = "both"  # "portrait" | "landscape" | "both"

    enable_autosplit: bool = False
    enable_subtitles: bool = False
    enable_hook_overlay: bool = False

    subtitle_languages: List[str] = field(default_factory=lambda: ["id"])
    target_platforms: List[str] = field(default_factory=lambda: ["tiktok", "reels", "shorts"])

    # Kontrol “AI”
    niche: Optional[str] = None
    hook_style: str = "default"
    hashtag_style: str = "default"

    # General
    output_dir: str = "outputs"
    temp_dir: str = "temp"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "format_mode": self.format_mode,
            "enable_autosplit": self.enable_autosplit,
            "enable_subtitles": self.enable_subtitles,
            "enable_hook_overlay": self.enable_hook_overlay,
            "subtitle_languages": list(self.subtitle_languages),
            "target_platforms": list(self.target_platforms),
            "niche": self.niche,
            "hook_style": self.hook_style,
            "hashtag_style": self.hashtag_style,
            "output_dir": self.output_dir,
            "temp_dir": self.temp_dir,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "JobSettings":
        return JobSettings(
            format_mode=str(d.get("format_mode", "both")),
            enable_autosplit=bool(d.get("enable_autosplit", False)),
            enable_subtitles=bool(d.get("enable_subtitles", False)),
            enable_hook_overlay=bool(d.get("enable_hook_overlay", False)),
            subtitle_languages=list(d.get("subtitle_languages", ["id"])),
            target_platforms=list(d.get("target_platforms", ["tiktok", "reels", "shorts"])),
            niche=d.get("niche"),
            hook_style=str(d.get("hook_style", "default")),
            hashtag_style=str(d.get("hashtag_style", "default")),
            output_dir=str(d.get("output_dir", "outputs")),
            temp_dir=str(d.get("temp_dir", "temp")),
        )


@dataclass
class TranscriptSegment:
    """
    Segmen transcript dengan timestamp (detik).
    """
    start_s: float
    end_s: float
    text: str
    confidence: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "start_s": float(self.start_s),
            "end_s": float(self.end_s),
            "text": self.text,
            "confidence": self.confidence,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "TranscriptSegment":
        return TranscriptSegment(
            start_s=float(d.get("start_s", 0.0)),
            end_s=float(d.get("end_s", 0.0)),
            text=str(d.get("text", "")),
            confidence=d.get("confidence"),
        )


@dataclass
class Transcript:
    """
    Transcript full + segments (untuk autosplit, subtitle, dsb).
    """
    language: str = "id"
    text: str = ""
    segments: List[TranscriptSegment] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "language": self.language,
            "text": self.text,
            "segments": [s.to_dict() for s in self.segments],
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Transcript":
        return Transcript(
            language=str(d.get("language", "id")),
            text=str(d.get("text", "")),
            segments=[TranscriptSegment.from_dict(x) for x in (d.get("segments") or [])],
        )


@dataclass
class JobArtifacts:
    """
    Semua output intermediate + final.
    Fokus: penyimpanan path lokal + URL setelah upload.
    """
    raw_video_path: Optional[str] = None  # path string
    processed_variants: Dict[str, str] = field(default_factory=dict)  # {"portrait": "...", "landscape": "..."}
    transcript: Optional[Transcript] = None

    niche_analysis: Dict[str, Any] = field(default_factory=dict)
    hooks: List[str] = field(default_factory=list)
    hashtags: List[str] = field(default_factory=list)

    # subtitle files: {"id": "path/to/id.srt", "en": "path/to/en.srt"}
    subtitle_srt_paths: Dict[str, str] = field(default_factory=dict)

    # overlay assets (optional)
    overlays: Dict[str, Any] = field(default_factory=dict)

    # upload results: {"portrait": {"cloudinary_url": "..."}}
    uploads: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # schedule result: {"account_id": {"post_id": "..."}}
    schedule_result: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "raw_video_path": self.raw_video_path,
            "processed_variants": dict(self.processed_variants),
            "transcript": None if self.transcript is None else self.transcript.to_dict(),
            "niche_analysis": dict(self.niche_analysis),
            "hooks": list(self.hooks),
            "hashtags": list(self.hashtags),
            "subtitle_srt_paths": dict(self.subtitle_srt_paths),
            "overlays": dict(self.overlays),
            "uploads": dict(self.uploads),
            "schedule_result": dict(self.schedule_result),
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "JobArtifacts":
        transcript = d.get("transcript")
        return JobArtifacts(
            raw_video_path=d.get("raw_video_path"),
            processed_variants=dict(d.get("processed_variants") or {}),
            transcript=None if not transcript else Transcript.from_dict(transcript),
            niche_analysis=dict(d.get("niche_analysis") or {}),
            hooks=list(d.get("hooks") or []),
            hashtags=list(d.get("hashtags") or []),
            subtitle_srt_paths=dict(d.get("subtitle_srt_paths") or {}),
            overlays=dict(d.get("overlays") or {}),
            uploads=dict(d.get("uploads") or {}),
            schedule_result=dict(d.get("schedule_result") or {}),
        )


@dataclass
class JobStatus:
    """
    Status berjalan (untuk UI progress bar, log, dll).
    """
    state: JobState = JobState.PENDING
    stage: Optional[str] = None
    progress: float = 0.0  # 0.0 - 1.0
    message: str = ""
    error: Optional[str] = None

    started_at: Optional[str] = None  # ISO
    finished_at: Optional[str] = None  # ISO

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "stage": self.stage,
            "progress": float(self.progress),
            "message": self.message,
            "error": self.error,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "JobStatus":
        state_val = str(d.get("state", JobState.PENDING.value))
        try:
            state = JobState(state_val)
        except Exception:
            state = JobState.PENDING

        return JobStatus(
            state=state,
            stage=d.get("stage"),
            progress=float(d.get("progress", 0.0)),
            message=str(d.get("message", "")),
            error=d.get("error"),
            started_at=d.get("started_at"),
            finished_at=d.get("finished_at"),
        )


@dataclass
class JobContext:
    """
    Objek utama yang dipass ke semua stage.
    """
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: _utcnow().isoformat())

    source: JobSource = field(default_factory=lambda: JobSource(kind="file", value=""))
    settings: JobSettings = field(default_factory=JobSettings)
    artifacts: JobArtifacts = field(default_factory=JobArtifacts)
    status: JobStatus = field(default_factory=JobStatus)

    # Dependency injection (service / clients / helpers).
    # Contoh nanti:
    # ctx.services["download_fn"] = async def(url)->path
    # ctx.services["video_process_fn"] = async def(path, format_mode)->{"portrait": "...", ...}
    services: Dict[str, Any] = field(default_factory=dict)

    # Free-form metadata (misal: UI selections, account list, dll)
    meta: Dict[str, Any] = field(default_factory=dict)

    def ensure_dirs(self) -> None:
        """
        Bikin folder output/temp kalau belum ada.
        """
        Path(self.settings.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.settings.temp_dir).mkdir(parents=True, exist_ok=True)

    def set_running(self, stage: Optional[str] = None, message: str = "") -> None:
        self.status.state = JobState.RUNNING
        self.status.stage = stage
        self.status.message = message
        if not self.status.started_at:
            self.status.started_at = _utcnow().isoformat()

    def set_success(self, message: str = "Done") -> None:
        self.status.state = JobState.SUCCESS
        self.status.progress = 1.0
        self.status.message = message
        self.status.finished_at = _utcnow().isoformat()

    def set_failed(self, error: str) -> None:
        self.status.state = JobState.FAILED
        self.status.error = error
        self.status.message = "FAILED"
        self.status.finished_at = _utcnow().isoformat()

    def cancel(self, message: str = "Canceled") -> None:
        self.status.state = JobState.CANCELED
        self.status.message = message
        self.status.finished_at = _utcnow().isoformat()

    def update_progress(self, stage: Optional[str], progress: float, message: str = "") -> None:
        """
        Dipakai runner/stage untuk update progress.
        """
        self.status.stage = stage
        # clamp 0..1
        if progress < 0:
            progress = 0.0
        if progress > 1:
            progress = 1.0
        self.status.progress = float(progress)
        if message:
            self.status.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "created_at": self.created_at,
            "source": self.source.to_dict(),
            "settings": self.settings.to_dict(),
            "artifacts": self.artifacts.to_dict(),
            "status": self.status.to_dict(),
            "meta": dict(self.meta),
            # NOTE: services tidak diserialisasi (biasanya objects / callables)
        }

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "JobContext":
        ctx = JobContext(
            job_id=str(d.get("job_id", str(uuid.uuid4()))),
            created_at=str(d.get("created_at", _utcnow().isoformat())),
            source=JobSource.from_dict(d.get("source") or {}),
            settings=JobSettings.from_dict(d.get("settings") or {}),
            artifacts=JobArtifacts.from_dict(d.get("artifacts") or {}),
            status=JobStatus.from_dict(d.get("status") or {}),
            meta=dict(d.get("meta") or {}),
        )
        return ctx

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    @staticmethod
    def from_json(s: str) -> "JobContext":
        return JobContext.from_dict(json.loads(s))