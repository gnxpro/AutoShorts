from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from gnx.models.job_context import JobContext
from gnx.pipeline.stages.base import BaseStage


@dataclass
class PersistContextStage(BaseStage):
    """
    Simpan hasil JobContext ke disk agar:
    - UI bisa tampilkan job history
    - bisa re-open hasil job terakhir
    Output:
      outputs/jobs/<job_id>/
        context.json
        status.json
        artifacts.json
        summary.txt
      outputs/jobs/index.jsonl
      outputs/jobs/latest.json
    """
    name: str = "PersistContext"

    def should_run(self, ctx: JobContext) -> bool:
        return True

    async def run(self, ctx: JobContext) -> JobContext:
        ctx.ensure_dirs()

        out_dir = Path(ctx.settings.output_dir)
        jobs_root = out_dir / "jobs"
        job_dir = jobs_root / ctx.job_id

        jobs_root.mkdir(parents=True, exist_ok=True)
        job_dir.mkdir(parents=True, exist_ok=True)

        # files
        (job_dir / "context.json").write_text(ctx.to_json(indent=2), encoding="utf-8")
        (job_dir / "status.json").write_text(_dump(ctx.status.to_dict()), encoding="utf-8")
        (job_dir / "artifacts.json").write_text(_dump(ctx.artifacts.to_dict()), encoding="utf-8")
        (job_dir / "summary.txt").write_text(_summary(ctx), encoding="utf-8")

        # index.jsonl (append)
        index_line = {
            "job_id": ctx.job_id,
            "created_at": ctx.created_at,
            "state": ctx.status.state.value,
            "stage": ctx.status.stage,
            "progress": ctx.status.progress,
            "source": ctx.source.to_dict(),
            "persist_dir": str(job_dir),
        }
        with (jobs_root / "index.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(index_line, ensure_ascii=False) + "\n")

        # latest.json
        (jobs_root / "latest.json").write_text(_dump(index_line), encoding="utf-8")

        # expose to UI
        ctx.meta["persist_dir"] = str(job_dir)
        ctx.meta["context_json_path"] = str(job_dir / "context.json")
        ctx.meta["status_json_path"] = str(job_dir / "status.json")
        ctx.meta["artifacts_json_path"] = str(job_dir / "artifacts.json")
        ctx.meta["summary_path"] = str(job_dir / "summary.txt")
        return ctx


def _dump(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)


def _summary(ctx: JobContext) -> str:
    lines = [
        f"JOB ID: {ctx.job_id}",
        f"STATE: {ctx.status.state.value}",
        f"STAGE: {ctx.status.stage}",
        f"PROGRESS: {ctx.status.progress}",
        f"MESSAGE: {ctx.status.message}",
        "",
        f"SOURCE: {ctx.source.kind} | {ctx.source.value}",
        "",
        "PROCESSED VARIANTS:",
    ]
    for k, v in (ctx.artifacts.processed_variants or {}).items():
        lines.append(f"  - {k}: {v}")

    lines.append("")
    lines.append("UPLOADS:")
    for k, v in (ctx.artifacts.uploads or {}).items():
        url = v.get("url") if isinstance(v, dict) else str(v)
        lines.append(f"  - {k}: {url}")

    lines.append("")
    lines.append("SCHEDULE RESULT:")
    lines.append(str(ctx.artifacts.schedule_result))

    lines.append("")
    lines.append("META:")
    lines.append(str(ctx.meta))
    return "\n".join(lines)