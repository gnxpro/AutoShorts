from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence, Union

from gnx.models.job_context import JobContext, JobSource, JobSettings
from gnx.pipeline.events import PipelineEvent
from gnx.pipeline.gnx_pipeline_factory import build_default_gnx_runner


AsyncOrSync = Union[Any, Awaitable[Any]]


async def _maybe_await(x: AsyncOrSync) -> Any:
    if asyncio.iscoroutine(x):
        return await x
    return x


def _pick_method(obj: Any, candidates: Sequence[str]) -> Callable[..., Any]:
    """
    Cari method yang ada di object berdasarkan list nama yang umum.
    """
    for name in candidates:
        fn = getattr(obj, name, None)
        if fn and callable(fn):
            return fn
    raise AttributeError(f"Tidak menemukan method di {type(obj).__name__}. Coba salah satu: {list(candidates)}")


async def _call_best_effort(fn: Callable[..., Any], *attempts: Any) -> Any:
    """
    Coba panggil callable dengan beberapa kemungkinan signature.
    attempts berisi tuple (args, kwargs).
    """
    last: Optional[Exception] = None
    for args, kwargs in attempts:
        try:
            return await _maybe_await(fn(*args, **kwargs))
        except TypeError as e:
            last = e
            continue
    if last:
        raise last
    raise TypeError("Tidak ada attempt pemanggilan yang dicoba.")


@dataclass
class GNXServiceBundle:
    """
    Bundle object service asli kamu.
    Kamu cukup isi objectnya, adaptor akan cari method yang cocok.

    Kalau kamu mau override, isi juga callable customnya:
    - download_fn / process_fn / upload_fn / schedule_fn
    """
    youtube_service: Optional[Any] = None
    video_processor: Optional[Any] = None
    cloudinary_service: Optional[Any] = None
    repliz_service: Optional[Any] = None

    download_fn: Optional[Callable[..., Any]] = None
    process_fn: Optional[Callable[..., Any]] = None
    upload_fn: Optional[Callable[..., Any]] = None
    schedule_fn: Optional[Callable[..., Any]] = None


def inject_services_into_ctx(ctx: JobContext, services: GNXServiceBundle) -> JobContext:
    """
    Mengisi ctx.services['download_fn'/'process_fn'/'upload_fn'/'schedule_fn']
    dengan wrapper yang memanggil service asli (async/sync).
    """
    # -------------------------
    # DOWNLOAD
    # -------------------------
    async def download_wrapper(url: str, temp_dir: str, ctx_: JobContext) -> str:
        if services.download_fn:
            res = await _call_best_effort(
                services.download_fn,
                ((url,), {}),
                ((url, temp_dir), {}),
                ((url, temp_dir, ctx_), {}),
                ((), {"url": url, "temp_dir": temp_dir, "ctx": ctx_}),
            )
            return str(res)

        if not services.youtube_service:
            raise RuntimeError("youtube_service belum di-set dan download_fn override juga tidak ada.")

        fn = _pick_method(
            services.youtube_service,
            candidates=[
                "download",
                "download_video",
                "download_to_file",
                "fetch",
                "get_video",
            ],
        )

        res = await _call_best_effort(
            fn,
            ((url,), {}),
            ((url, temp_dir), {}),
            ((url, temp_dir, ctx_), {}),
            ((), {"url": url}),
            ((), {"url": url, "temp_dir": temp_dir}),
            ((), {"url": url, "temp_dir": temp_dir, "ctx": ctx_}),
        )
        return str(res)

    # -------------------------
    # PROCESS VIDEO
    # -------------------------
    async def process_wrapper(
        input_path: str,
        format_mode: str,
        output_dir: str,
        temp_dir: str,
        ctx_: JobContext,
    ) -> Any:
        if services.process_fn:
            return await _call_best_effort(
                services.process_fn,
                ((input_path,), {}),
                ((input_path, format_mode), {}),
                ((input_path, format_mode, output_dir), {}),
                ((input_path, format_mode, output_dir, temp_dir), {}),
                ((input_path, format_mode, output_dir, temp_dir, ctx_), {}),
                ((), {"input_path": input_path, "format_mode": format_mode, "output_dir": output_dir, "temp_dir": temp_dir, "ctx": ctx_}),
            )

        if not services.video_processor:
            raise RuntimeError("video_processor belum di-set dan process_fn override juga tidak ada.")

        fn = _pick_method(
            services.video_processor,
            candidates=[
                "process",
                "process_video",
                "run",
                "crop",
                "crop_video",
                "render",
            ],
        )

        return await _call_best_effort(
            fn,
            ((input_path,), {}),
            ((input_path, format_mode), {}),
            ((input_path, format_mode, output_dir), {}),
            ((input_path, format_mode, output_dir, temp_dir), {}),
            ((input_path, format_mode, output_dir, temp_dir, ctx_), {}),
            ((), {"input_path": input_path}),
            ((), {"input_path": input_path, "format_mode": format_mode}),
            ((), {"input_path": input_path, "format_mode": format_mode, "output_dir": output_dir}),
            ((), {"input_path": input_path, "format_mode": format_mode, "output_dir": output_dir, "temp_dir": temp_dir}),
            ((), {"input_path": input_path, "format_mode": format_mode, "output_dir": output_dir, "temp_dir": temp_dir, "ctx": ctx_}),
        )

    # -------------------------
    # UPLOAD CLOUDINARY
    # -------------------------
    async def upload_wrapper(file_path: str, variant: str, ctx_: JobContext, metadata: Optional[Dict[str, Any]] = None) -> Any:
        if services.upload_fn:
            return await _call_best_effort(
                services.upload_fn,
                ((file_path,), {}),
                ((file_path, variant), {}),
                ((file_path, variant, ctx_), {}),
                ((), {"file_path": file_path, "variant": variant, "ctx": ctx_, "metadata": metadata or {}}),
            )

        if not services.cloudinary_service:
            raise RuntimeError("cloudinary_service belum di-set dan upload_fn override juga tidak ada.")

        fn = _pick_method(
            services.cloudinary_service,
            candidates=[
                "upload",
                "upload_video",
                "upload_file",
                "upload_asset",
            ],
        )

        return await _call_best_effort(
            fn,
            ((file_path,), {}),
            ((file_path, variant), {}),
            ((file_path, variant, ctx_), {}),
            ((), {"file_path": file_path}),
            ((), {"file_path": file_path, "variant": variant}),
            ((), {"file_path": file_path, "variant": variant, "ctx": ctx_}),
            ((), {"file_path": file_path, "variant": variant, "metadata": metadata or {}}),
            ((), {"file_path": file_path, "variant": variant, "ctx": ctx_, "metadata": metadata or {}}),
        )

    # -------------------------
    # SCHEDULE REPLIZ
    # -------------------------
    async def schedule_wrapper(uploads: Dict[str, Any], accounts: Any, ctx_: JobContext) -> Any:
        if services.schedule_fn:
            return await _call_best_effort(
                services.schedule_fn,
                ((uploads,), {}),
                ((uploads, accounts), {}),
                ((uploads, accounts, ctx_), {}),
                ((uploads, ctx_), {}),
                ((), {"uploads": uploads, "accounts": accounts, "ctx": ctx_}),
            )

        if not services.repliz_service:
            raise RuntimeError("repliz_service belum di-set dan schedule_fn override juga tidak ada.")

        fn = _pick_method(
            services.repliz_service,
            candidates=[
                "schedule",
                "schedule_post",
                "schedule_posts",
                "create_schedule",
                "enqueue",
                "publish",
            ],
        )

        return await _call_best_effort(
            fn,
            ((uploads,), {}),
            ((uploads, accounts), {}),
            ((uploads, accounts, ctx_), {}),
            ((uploads, ctx_), {}),
            ((), {"uploads": uploads}),
            ((), {"uploads": uploads, "accounts": accounts}),
            ((), {"uploads": uploads, "accounts": accounts, "ctx": ctx_}),
            ((), {"uploads": uploads, "ctx": ctx_}),
        )

    # inject ke ctx.services sesuai kontrak stage
    ctx.services["download_fn"] = download_wrapper
    ctx.services["process_fn"] = process_wrapper
    ctx.services["upload_fn"] = upload_wrapper
    ctx.services["schedule_fn"] = schedule_wrapper
    return ctx


def make_print_event_handler() -> Callable[[PipelineEvent], Awaitable[None]]:
    """
    Event handler sederhana untuk debugging (console).
    """
    async def _handler(ev: PipelineEvent):
        stage = ev.stage or "-"
        print(f"[{ev.type}] stage={stage} msg={ev.message} data={ev.data}")
    return _handler


async def run_default_gnx_job(
    *,
    source_kind: str,
    source_value: str,
    services: GNXServiceBundle,
    settings: Optional[JobSettings] = None,
    settings_overrides: Optional[Dict[str, Any]] = None,
    accounts: Optional[Any] = None,
    event_handler: Optional[Callable[[PipelineEvent], Any]] = None,
) -> JobContext:
    """
    Helper 1-liner untuk menjalankan default pipeline GNX dengan service asli.

    - source_kind: "youtube" | "file"
    - source_value: url/path
    - services: GNXServiceBundle(youtube_service=..., video_processor=..., cloudinary_service=..., repliz_service=...)
    - accounts: bisa list/dict apa pun, akan masuk ctx.meta["accounts"]
    """
    if settings is None:
        settings = JobSettings()

    if settings_overrides:
        # apply override ke JobSettings dengan aman
        for k, v in settings_overrides.items():
            if hasattr(settings, k):
                setattr(settings, k, v)

    ctx = JobContext(
        source=JobSource(kind=source_kind, value=source_value),
        settings=settings,
    )

    if accounts is not None:
        ctx.meta["accounts"] = accounts

    inject_services_into_ctx(ctx, services)

    runner = build_default_gnx_runner(event_handler=event_handler)
    final_ctx = await runner.run(ctx)
    return final_ctx