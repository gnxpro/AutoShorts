from __future__ import annotations

import asyncio
import traceback
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, List, Optional, Sequence, Union

from gnx.models.job_context import JobContext, JobState
from gnx.pipeline.events import PipelineEvent, PipelineEventType
from gnx.pipeline.stages.base import BaseStage, StageSkip, Stage


EventHandler = Union[
    Callable[[PipelineEvent], None],
    Callable[[PipelineEvent], Awaitable[None]],
]


@dataclass
class PipelineRunnerConfig:
    """
    Konfigurasi runner.
    """
    # Kalau True, runner akan stop dan raise exception saat ada stage error.
    raise_on_error: bool = False

    # Update progress otomatis berdasarkan urutan stage (0..1).
    auto_progress: bool = True

    # Jika True, skip stage yang outputnya sudah ada (bergantung stage logic).
    # (ini lebih ke guideline; stage-lah yang menentukan lewat should_run)
    enable_idempotency: bool = True


@dataclass
class PipelineRunner:
    """
    Menjalankan list stage secara berurutan.
    Emit events untuk UI.
    """
    stages: Sequence[Stage]
    config: PipelineRunnerConfig = field(default_factory=PipelineRunnerConfig)
    event_handler: Optional[EventHandler] = None

    async def _emit(self, event: PipelineEvent) -> None:
        if not self.event_handler:
            return
        try:
            res = self.event_handler(event)
            if asyncio.iscoroutine(res):
                await res  # type: ignore[misc]
        except Exception:
            # Jangan biarkan event handler merusak runner.
            # Kalau butuh debug, print traceback minimal.
            print("Event handler error:")
            traceback.print_exc()

    async def run(self, ctx: JobContext, cancel_event: Optional[asyncio.Event] = None) -> JobContext:
        """
        Jalankan pipeline sampai selesai / gagal / cancel.
        """
        total = max(1, len(self.stages))

        ctx.set_running(stage=None, message="Pipeline start")
        ctx.update_progress(stage=None, progress=0.0, message="Pipeline start")

        await self._emit(PipelineEvent(
            job_id=ctx.job_id,
            type=PipelineEventType.PIPELINE_START,
            stage=None,
            message="Pipeline started",
            data={"total_stages": total},
        ))

        for idx, stage in enumerate(self.stages):
            stage_name = getattr(stage, "name", stage.__class__.__name__)

            # Cancel check
            if cancel_event is not None and cancel_event.is_set():
                ctx.cancel("Canceled by cancel_event")
                await self._emit(PipelineEvent(
                    job_id=ctx.job_id,
                    type=PipelineEventType.PIPELINE_END,
                    stage=stage_name,
                    message="Pipeline canceled",
                    data={"state": ctx.status.state.value},
                ))
                return ctx

            if ctx.status.state == JobState.CANCELED:
                await self._emit(PipelineEvent(
                    job_id=ctx.job_id,
                    type=PipelineEventType.PIPELINE_END,
                    stage=stage_name,
                    message="Pipeline canceled",
                    data={"state": ctx.status.state.value},
                ))
                return ctx

            # Auto progress (sebelum stage run)
            if self.config.auto_progress:
                # progress baseline = idx/total
                baseline = float(idx) / float(total)
                ctx.update_progress(stage=stage_name, progress=baseline, message=f"Starting {stage_name}")
                await self._emit(PipelineEvent(
                    job_id=ctx.job_id,
                    type=PipelineEventType.PROGRESS,
                    stage=stage_name,
                    message=ctx.status.message,
                    data={"progress": ctx.status.progress},
                ))

            # Should run?
            should_run = True
            try:
                should_run = bool(stage.should_run(ctx))
            except Exception as e:
                # Kalau should_run crash, treat as error stage
                err = f"Stage should_run() error at {stage_name}: {e}"
                ctx.set_failed(err)
                await self._emit(PipelineEvent(
                    job_id=ctx.job_id,
                    type=PipelineEventType.ERROR,
                    stage=stage_name,
                    message=err,
                    data={"traceback": traceback.format_exc()},
                ))
                if self.config.raise_on_error:
                    raise
                return ctx

            if not should_run:
                await self._emit(PipelineEvent(
                    job_id=ctx.job_id,
                    type=PipelineEventType.STAGE_END,
                    stage=stage_name,
                    message="Skipped (should_run = False)",
                    data={"skipped": True},
                ))
                continue

            await self._emit(PipelineEvent(
                job_id=ctx.job_id,
                type=PipelineEventType.STAGE_START,
                stage=stage_name,
                message=f"Stage start: {stage_name}",
                data={},
            ))

            try:
                # Jalankan stage
                if isinstance(stage, BaseStage):
                    ctx = await stage._call(ctx)  # type: ignore[attr-defined]
                else:
                    ctx = await stage.run(ctx)

                # Update progress setelah stage selesai
                if self.config.auto_progress:
                    done = float(idx + 1) / float(total)
                    ctx.update_progress(stage=stage_name, progress=done, message=f"Done {stage_name}")
                    await self._emit(PipelineEvent(
                        job_id=ctx.job_id,
                        type=PipelineEventType.PROGRESS,
                        stage=stage_name,
                        message=ctx.status.message,
                        data={"progress": ctx.status.progress},
                    ))

                await self._emit(PipelineEvent(
                    job_id=ctx.job_id,
                    type=PipelineEventType.STAGE_END,
                    stage=stage_name,
                    message=f"Stage end: {stage_name}",
                    data={"skipped": False},
                ))

            except StageSkip as e:
                await self._emit(PipelineEvent(
                    job_id=ctx.job_id,
                    type=PipelineEventType.STAGE_END,
                    stage=stage_name,
                    message=f"Skipped: {e}",
                    data={"skipped": True},
                ))
                continue

            except asyncio.CancelledError:
                # Task dibatalkan oleh asyncio
                ctx.cancel("Canceled by asyncio.CancelledError")
                await self._emit(PipelineEvent(
                    job_id=ctx.job_id,
                    type=PipelineEventType.ERROR,
                    stage=stage_name,
                    message="Pipeline cancelled by asyncio.CancelledError",
                    data={},
                ))
                await self._emit(PipelineEvent(
                    job_id=ctx.job_id,
                    type=PipelineEventType.PIPELINE_END,
                    stage=stage_name,
                    message="Pipeline canceled",
                    data={"state": ctx.status.state.value},
                ))
                return ctx

            except Exception as e:
                # Stage crash
                err = f"Stage error at {stage_name}: {e}"
                ctx.set_failed(err)

                await self._emit(PipelineEvent(
                    job_id=ctx.job_id,
                    type=PipelineEventType.ERROR,
                    stage=stage_name,
                    message=err,
                    data={"traceback": traceback.format_exc()},
                ))

                if self.config.raise_on_error:
                    raise
                return ctx

        # Selesai semua stage
        if ctx.status.state not in (JobState.FAILED, JobState.CANCELED):
            ctx.set_success("Pipeline done")

        await self._emit(PipelineEvent(
            job_id=ctx.job_id,
            type=PipelineEventType.PIPELINE_END,
            stage=None,
            message="Pipeline ended",
            data={"state": ctx.status.state.value},
        ))
        return ctx