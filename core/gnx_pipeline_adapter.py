from __future__ import annotations

import asyncio
import inspect
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from gnx.models.job_context import JobContext, JobSource, JobSettings
from gnx.pipeline.gnx_pipeline_factory import build_default_gnx_runner, DefaultPipelineOptions
from gnx.pipeline.runner import PipelineRunnerConfig
from gnx.pipeline.events import PipelineEvent

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}
MAX_REPLIZ_ACCOUNTS = 100


# -----------------------
# .env loader (Windows friendly)
# -----------------------
def _load_env_manual(env_path: Path) -> None:
    if not env_path.exists():
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("export "):
            line = line[7:].strip()
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def load_dotenv_best_effort(root_dir: Optional[Path] = None) -> None:
    root = root_dir or Path.cwd()
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(dotenv_path=root / ".env", override=False)
        load_dotenv(dotenv_path=root / ".env.local", override=False)
        return
    except Exception:
        _load_env_manual(root / ".env")
        _load_env_manual(root / ".env.local")


# -----------------------
# Helpers
# -----------------------
async def _maybe_await(x: Any) -> Any:
    if asyncio.iscoroutine(x):
        return await x
    return x


async def _call_best_effort(fn: Callable[..., Any], attempts: List[Tuple[Tuple[Any, ...], Dict[str, Any]]]) -> Any:
    last: Optional[Exception] = None
    for args, kwargs in attempts:
        try:
            return await _maybe_await(fn(*args, **kwargs))
        except TypeError as e:
            last = e
            continue
    if last:
        raise last
    raise TypeError("No matching signature")


def _exists_file(p: Union[str, Path]) -> bool:
    pp = Path(p)
    return pp.exists() and pp.is_file()


def _size(p: Union[str, Path]) -> int:
    return Path(p).stat().st_size


def _normalize_url(u: str) -> str:
    u = (u or "").strip()
    if not u:
        return u
    if u.startswith("ps://"):
        return "htt" + u  # => https://
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("res.cloudinary.com"):
        return "https://" + u
    return u


def _iso_z(dt: datetime) -> str:
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _guess_thumbnail(video_url: str) -> Optional[str]:
    u = _normalize_url(video_url)
    if not u:
        return None

    # Cloudinary trick: mp4 -> jpg frame
    if "res.cloudinary.com" in u and "/video/upload/" in u:
        thumb = u.replace("/video/upload/", "/video/upload/so_0,f_jpg/")
        if thumb.lower().endswith(".mp4"):
            thumb = thumb[:-4] + ".jpg"
        return thumb

    if u.lower().endswith(".mp4"):
        return u[:-4] + ".jpg"

    return None


def _payload_source(payload: Dict[str, Any]) -> Tuple[str, str]:
    for k in ("youtube_url", "url", "youtube"):
        v = payload.get(k)
        if v:
            return "youtube", str(v)

    for k in ("file_path", "path", "offline_path", "local_path"):
        v = payload.get(k)
        if v:
            return "file", str(v)

    raise ValueError("Payload tidak punya source. Isi youtube_url/url atau file_path/offline_path.")


def _uploads_to_variant_urls(uploads: Any) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if isinstance(uploads, dict):
        for variant, v in uploads.items():
            url = None
            if isinstance(v, dict):
                url = v.get("url") or v.get("secure_url") or v.get("cloudinary_url")
            elif isinstance(v, str):
                url = v
            if url:
                out[str(variant)] = _normalize_url(str(url))
    return out


def _account_dicts(account_ids: List[str]) -> List[Dict[str, str]]:
    return [{"id": a} for a in account_ids if a]


def _select_accounts_for_variant(
    variant: str,
    all_accounts: List[str],
    variant_map: Optional[Dict[str, Any]],
) -> List[str]:
    if not variant_map:
        return all_accounts
    v = variant_map.get(variant)
    if v is None:
        return all_accounts
    if isinstance(v, str):
        return [v]
    if isinstance(v, list):
        return [str(x) for x in v if x]
    return all_accounts


# -----------------------
# Service wrappers
# -----------------------
def build_download_fn(youtube_service: Any) -> Callable[[str, str, JobContext], Any]:
    method = None
    for n in ["download", "download_video", "download_to_file", "fetch", "run"]:
        m = getattr(youtube_service, n, None)
        if callable(m):
            method = m
            break

    # fallback ke core.youtube_download
    downloader_fn = None
    if method is None:
        try:
            import core.youtube_download as yd  # type: ignore
            cls = getattr(yd, "YouTubeService", None) or getattr(yd, "YouTubeDownloader", None) or getattr(yd, "YoutubeDownloader", None)
            inst = cls() if cls and callable(cls) else None
            if inst:
                for n in ["download", "download_video", "download_to_file", "fetch", "run"]:
                    m = getattr(inst, n, None)
                    if callable(m):
                        downloader_fn = m
                        break
            if downloader_fn is None:
                for n in ["download", "download_video", "download_youtube", "download_youtube_video", "run_download"]:
                    f = getattr(yd, n, None)
                    if callable(f):
                        downloader_fn = f
                        break
        except Exception:
            downloader_fn = None

    async def _download(url: str, temp_dir: str, ctx: JobContext) -> str:
        fn = method or downloader_fn
        if not fn:
            raise RuntimeError("Tidak ada downloader. Pastikan YouTubeService punya download* atau core/youtube_download.py ada.")

        res = await _call_best_effort(fn, [
            ((url, temp_dir, ctx), {}),
            ((url, temp_dir), {}),
            ((url,), {}),
            ((), {"url": url, "temp_dir": temp_dir, "ctx": ctx}),
            ((), {"url": url, "temp_dir": temp_dir}),
            ((), {"url": url}),
        ])

        # pilih mp4 terbesar di temp_dir
        d = Path(temp_dir)
        best = None
        best_sz = 0
        if d.exists():
            for ext in VIDEO_EXTS:
                for f in d.glob(f"*{ext}"):
                    sz = _size(f)
                    if sz > best_sz:
                        best_sz = sz
                        best = str(f)

        if isinstance(res, str) and _exists_file(res) and _size(res) > 1024:
            return res
        if best:
            return best
        raise RuntimeError("Download selesai tapi video valid tidak ditemukan.")

    return _download


def build_process_fn() -> Callable[[str, str, str, str, JobContext], Any]:
    from core.video_processor import VideoProcessor  # local import

    vp = VideoProcessor()
    to_portrait = getattr(vp, "to_portrait", None)
    to_landscape = getattr(vp, "to_landscape", None)
    if not callable(to_portrait) or not callable(to_landscape):
        raise RuntimeError("VideoProcessor harus punya method to_portrait & to_landscape")

    def _invoke(vp_method: Callable[..., Any], *, input_path: str, output_path: str, output_dir: str, temp_dir: str, ctx: JobContext):
        mapping = {
            "input_path": input_path, "video_path": input_path, "path": input_path,
            "output_path": output_path, "out_path": output_path,
            "output_dir": output_dir, "out_dir": output_dir,
            "temp_dir": temp_dir, "tmp_dir": temp_dir,
            "ctx": ctx, "context": ctx,
        }
        sig = inspect.signature(vp_method)
        kwargs = {k: mapping[k] for k in sig.parameters.keys() if k in mapping}

        attempts: List[Tuple[Tuple[Any, ...], Dict[str, Any]]] = []
        if kwargs:
            attempts.append(((), kwargs))

        attempts += [
            ((input_path, output_path), {}),
            ((input_path, output_dir), {}),
            ((input_path,), {}),
            ((), {"input_path": input_path, "output_path": output_path}),
            ((), {"input_path": input_path, "output_dir": output_dir}),
        ]
        return attempts

    async def _process(input_path: str, format_mode: str, output_dir: str, temp_dir: str, ctx: JobContext) -> Dict[str, str]:
        if not _exists_file(input_path):
            raise RuntimeError(f"Input video tidak ditemukan: {input_path}")
        if _size(input_path) < 1024:
            raise RuntimeError(f"Input video invalid/kecil: {input_path}")

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        stem = Path(input_path).stem
        out_portrait = str(Path(output_dir) / f"{stem}__portrait.mp4")
        out_landscape = str(Path(output_dir) / f"{stem}__landscape.mp4")

        mode = (format_mode or "both").lower().strip()
        results: Dict[str, str] = {}

        if mode in ("portrait", "both"):
            res = await _call_best_effort(to_portrait, _invoke(to_portrait, input_path=input_path, output_path=out_portrait, output_dir=output_dir, temp_dir=temp_dir, ctx=ctx))
            results["portrait"] = res if isinstance(res, str) and _exists_file(res) else out_portrait

        if mode in ("landscape", "both"):
            res = await _call_best_effort(to_landscape, _invoke(to_landscape, input_path=input_path, output_path=out_landscape, output_dir=output_dir, temp_dir=temp_dir, ctx=ctx))
            results["landscape"] = res if isinstance(res, str) and _exists_file(res) else out_landscape

        return results

    return _process


def build_upload_fn(cloudinary_service: Any) -> Callable[[str, str, JobContext, Optional[Dict[str, Any]]], Any]:
    method = None
    for n in ["upload_video", "upload", "upload_file", "upload_asset"]:
        m = getattr(cloudinary_service, n, None)
        if callable(m):
            method = m
            break
    if method is None:
        raise RuntimeError("CloudinaryService tidak punya method upload/upload_video/...")

    async def _upload(file_path: str, variant: str, ctx: JobContext, metadata: Optional[Dict[str, Any]] = None) -> Any:
        res = await _call_best_effort(method, [
            ((file_path, variant, ctx), {}),
            ((file_path, variant), {}),
            ((file_path,), {}),
            ((), {"file_path": file_path, "variant": variant, "ctx": ctx, "metadata": metadata or {}}),
        ])
        if isinstance(res, str):
            return {"url": _normalize_url(res)}
        if isinstance(res, dict):
            if "url" in res:
                res["url"] = _normalize_url(str(res["url"]))
            return res
        return {"result": res}

    return _upload


def build_schedule_fn(repliz_service: Any) -> Callable[[Any, Any, JobContext], Any]:
    """
    ✅ FIX 400: scheduleAt harus ...000Z + medias harus ada thumbnail (best effort)
    """
    create_fn = getattr(repliz_service, "create_schedule", None)
    if not callable(create_fn):
        create_fn = getattr(repliz_service, "schedule", None)
    if not callable(create_fn):
        raise RuntimeError("ReplizService tidak punya create_schedule atau schedule")

    async def _schedule(uploads: Any, accounts: Any, ctx: JobContext) -> Dict[str, Any]:
        urls = _uploads_to_variant_urls(uploads)
        if not urls:
            raise RuntimeError("Tidak ada url pada uploads untuk schedule")

        # normalize accounts -> list ids
        account_ids: List[str] = []
        if isinstance(accounts, list):
            for a in accounts:
                if isinstance(a, dict):
                    _id = a.get("id") or a.get("accountId") or a.get("account_id")
                    if _id:
                        account_ids.append(str(_id))
                elif isinstance(a, str):
                    account_ids.append(a)
        elif isinstance(accounts, str):
            account_ids = [accounts]

        if not account_ids:
            raise RuntimeError("Account IDs kosong. Isi di UI (Account IDs).")

        if len(account_ids) > MAX_REPLIZ_ACCOUNTS:
            raise RuntimeError(f"Max Repliz multi account {MAX_REPLIZ_ACCOUNTS}. Kamu isi: {len(account_ids)}")

        variant_map = ctx.meta.get("variant_account_map") or {}

        base_at = datetime.now(timezone.utc) + timedelta(minutes=10)
        title = (ctx.meta.get("title") or "GNX Auto Schedule")
        desc = (ctx.meta.get("description") or "Auto generated by GNX AI Production Studio")

        results: Dict[str, Any] = {"scheduled": [], "failed": []}
        any_success = False

        for variant, media_url in urls.items():
            targets = _select_accounts_for_variant(variant, account_ids, variant_map)
            for idx, acc_id in enumerate(targets):
                schedule_at = _iso_z(base_at + timedelta(minutes=idx))

                thumb = _guess_thumbnail(media_url)
                media_obj = {"type": "video", "url": media_url}
                if thumb:
                    media_obj["thumbnail"] = thumb

                payload = {
                    "title": title,
                    "description": desc,
                    "type": "video",
                    "medias": [media_obj],
                    "scheduleAt": schedule_at,
                    "additionalInfo": {"isAiGenerated": True, "isDraft": False, "collaborators": []},
                    "accountId": acc_id,
                }

                try:
                    res = await _maybe_await(create_fn(payload))
                    results["scheduled"].append({"variant": variant, "accountId": acc_id, "result": res})
                    any_success = True
                except Exception as e:
                    results["failed"].append({"variant": variant, "accountId": acc_id, "error": str(e)})

        # kalau semuanya gagal -> raise biar user langsung tahu
        if not any_success:
            raise RuntimeError(f"Schedule gagal semua. Contoh error: {results['failed'][:1]}")

        return results

    return _schedule


# -----------------------
# MAIN: Engine imports this
# -----------------------
async def run_gnx_job(
    *,
    payload: Dict[str, Any],
    job_id: Optional[str],
    youtube_service: Any,
    cloudinary_service: Any,
    repliz_service: Any,
    account_ids: List[str],
    variant_account_map: Optional[Dict[str, Any]] = None,
    event_handler: Optional[Callable[[PipelineEvent], Any]] = None,
) -> JobContext:
    load_dotenv_best_effort(Path.cwd())

    source_kind, source_value = _payload_source(payload)

    settings = JobSettings(
        format_mode=str(payload.get("format_mode") or payload.get("format") or "both"),
        output_dir=str(payload.get("output_dir", "outputs")),
        temp_dir=str(payload.get("temp_dir", "temp")),
    )

    ctx = JobContext(source=JobSource(kind=source_kind, value=source_value), settings=settings)
    if job_id:
        ctx.job_id = job_id

    if len(account_ids) > MAX_REPLIZ_ACCOUNTS:
        raise RuntimeError(f"Max Repliz multi account {MAX_REPLIZ_ACCOUNTS}. Kamu isi: {len(account_ids)}")

    ctx.meta["accounts"] = _account_dicts(account_ids)
    if variant_account_map:
        ctx.meta["variant_account_map"] = variant_account_map

    if source_kind == "youtube":
        ctx.services["download_fn"] = build_download_fn(youtube_service)
    ctx.services["process_fn"] = build_process_fn()
    ctx.services["upload_fn"] = build_upload_fn(cloudinary_service)
    ctx.services["schedule_fn"] = build_schedule_fn(repliz_service)

    options = DefaultPipelineOptions(
        include_schedule=bool(payload.get("enable_schedule", True)),
        include_persist=True,
    )

    runner = build_default_gnx_runner(
        event_handler=event_handler,
        config=PipelineRunnerConfig(auto_progress=True, raise_on_error=False),
        options=options,
    )

    return await runner.run(ctx)


__all__ = ["run_gnx_job"]