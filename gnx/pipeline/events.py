from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class PipelineEventType(str, Enum):
    PIPELINE_START = "PIPELINE_START"
    PIPELINE_END = "PIPELINE_END"

    STAGE_START = "STAGE_START"
    STAGE_END = "STAGE_END"

    PROGRESS = "PROGRESS"
    ERROR = "ERROR"
    INFO = "INFO"


@dataclass
class PipelineEvent:
    job_id: str
    type: PipelineEventType
    timestamp: str = field(default_factory=_utcnow_iso)

    stage: Optional[str] = None
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)