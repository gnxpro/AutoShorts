import asyncio
from typing import Any, Callable, Dict, Optional

from gnx.integration import GNXServiceBundle, inject_services_into_ctx
from gnx.models.job_context import JobContext, JobSource, JobSettings
from gnx.pipeline.gnx_pipeline_factory import build_default_gnx_runner
from gnx.pipeline.events import PipelineEvent


async def run_gnx_default_job(
    *,
    source_kind: str,
    source_value: str,
    youtube_service: Any,
    video_processor: Any,
    cloudinary_service: Any,
    repliz_service: Any,
    settings_overrides: Optional[Dict[str, Any]] = None,
    accounts: Optional[Any] = None,
    event_handler: Optional[Callable[[PipelineEvent], Any]] = None,
) -> JobContext:
    """
    Jalankan default GNX pipeline menggunakan service asli kamu.

    source_kind: "youtube" atau "file"
    source_value: url youtube atau path file
    settings_overrides: dict override JobSettings (contoh: {"format_mode":"both"})
    accounts: list/dict akun repliz, masuk ctx.meta["accounts"]
    event_handler: callback async/sync untuk event progress
    """
    settings = JobSettings()
    if settings_overrides:
        for k, v in settings_overrides.items():
            if hasattr(settings, k):
                setattr(settings, k, v)

    ctx = JobContext(
        source=JobSource(kind=source_kind, value=source_value),
        settings=settings,
    )

    if accounts is not None:
        ctx.meta["accounts"] = accounts

    services = GNXServiceBundle(
        youtube_service=youtube_service,
        video_processor=video_processor,
        cloudinary_service=cloudinary_service,
        repliz_service=repliz_service,
    )

    inject_services_into_ctx(ctx, services)

    runner = build_default_gnx_runner(event_handler=event_handler)
    final_ctx = await runner.run(ctx)
    return final_ctx