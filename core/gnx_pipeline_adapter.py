from __future__ import annotations

import asyncio
import inspect
import os
from dataclasses import dataclass
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
# Env loader
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


def load_dotenv_best_effort() -> None:
    roots: List[Path] = [Path.cwd()]
    try:
        import sys
        if getattr(sys, "frozen", False):
            roots.append(Path(sys.executable).parent)
    except Exception:
        pass

    try:
        from dotenv import load_dotenv  # type: ignore
        for r in roots:
            load_dotenv(dotenv_path=r / ".env", override=False)
            load_dotenv(dotenv_path=r / ".env.local", override=False)
    except Exception:
        for r in roots:
            _load_env_manual(r / ".env")
            _load_env_manual(r / ".env.local")


# -----------------------
# Documents root
# -----------------------
def _documents_root() -> Path:
    env = os.getenv("GNX_OUTPUT_ROOT", "").strip()
    if env:
        p = Path(env)
        p.mkdir(parents=True, exist_ok=True)
        return p

    home = Path.home()
    docs = home / "Documents"
    root = docs / "GNX Production"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _default_output_dir() -> str:
    p = _documents_root() / "Outputs"
    p.mkdir(parents=True, exist_ok=True)
    return str(p)


def _default_temp_dir() -> str:
    p = _documents_root() / "Temp"
    p.mkdir(parents=True, exist_ok=True)
    return str(p)


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
    raise TypeError("No matching signature for function call")


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
        return "htt" + u
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
    raise ValueError("Payload has no source. Fill youtube_url OR file_path/offline_path.")


def _uploads_to_variant_urls(uploads: Any) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if isinstance(uploads, dict):
        for variant, v in uploads.items():
            url = None
            if isinstance(v, dict):
                url = v.get("url") or v.get("secure_url") or v.get("cloudinary_url") or v.get("video_url")
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
# AI stage
# -----------------------
def build_ai_stage_fn() -> Callable[[str, JobContext], Any]:
    from core.services.ai_content_service import AIContentService

    def _normalize_tools(ai_options: Dict[str, Any]) -> Dict[str, Any]:
        tools = ai_options.get("tools")
        if isinstance(tools, dict) and tools:
            return tools

        prompts = ai_options.get("prompts") or {}

        return {
            "subtitle": {
                "enabled": bool(ai_options.get("enable_subtitles", False)),
                "mode": str(ai_options.get("subtitle_mode", "auto")).strip().lower(),
                "prompt": str(prompts.get("subtitle", "")).strip(),
            },
            "hook": {
                "enabled": bool(ai_options.get("enable_hooks", False)),
                "mode": str(ai_options.get("hook_mode", "auto")).strip().lower(),
                "prompt": str(prompts.get("hook", "")).strip(),
            },
            "niche": {
                "enabled": bool(ai_options.get("enable_niche", False)),
                "mode": str(ai_options.get("niche_mode", "auto")).strip().lower(),
                "prompt": str(prompts.get("niche", "")).strip(),
            },
            "hashtag": {
                "enabled": bool(ai_options.get("enable_hashtags", False)),
                "mode": str(ai_options.get("hashtag_mode", "auto")).strip().lower(),
                "prompt": str(prompts.get("hashtag", "")).strip(),
            },
        }

    async def _run_ai(output_dir: str, ctx: JobContext) -> Dict[str, Any]:
        ai_options = (ctx.meta.get("ai_options") or {})
        tools = _normalize_tools(ai_options)

        enabled = any(bool(v.get("enabled")) for v in tools.values())
        if not enabled:
            return {
                "enabled": False,
                "reason": "No AI tools enabled",
                "tools": tools,
                "results": {},
            }

        ctx.meta["ai_options"] = dict(ai_options)
        ctx.meta["ai_options"]["tools"] = tools

        svc = AIContentService()
        results = svc.run_enabled_tools(ctx=ctx, output_dir=output_dir)
        ctx.meta["ai_results"] = results
        return {
            "enabled": True,
            "tools": tools,
            "results": results,
        }

    return _run_ai


# -----------------------
# Publish-only variants
# -----------------------
def _find_processed_variants(persist_dir: Union[str, Path]) -> Dict[str, str]:
    base = Path(persist_dir)
    if not base.exists():
        return {}

    files: List[Path] = []
    for ext in VIDEO_EXTS:
        files.extend(base.rglob(f"*{ext}"))

    files = [f for f in files if f.is_file() and f.stat().st_size > 1024]
    if not files:
        return {}

    best_portrait: Optional[Path] = None
    best_landscape: Optional[Path] = None
    best_other: Optional[Path] = None

    for f in files:
        name = f.name.lower()
        if "portrait" in name:
            if best_portrait is None or f.stat().st_size > best_portrait.stat().st_size:
                best_portrait = f
        elif "landscape" in name:
            if best_landscape is None or f.stat().st_size > best_landscape.stat().st_size:
                best_landscape = f
        else:
            if best_other is None or f.stat().st_size > best_other.stat().st_size:
                best_other = f

    out: Dict[str, str] = {}
    if best_portrait:
        out["portrait"] = str(best_portrait)
    if best_landscape:
        out["landscape"] = str(best_landscape)

    if not out:
        out["video"] = str(best_other or max(files, key=lambda x: x.stat().st_size))

    return out


# -----------------------
# Status helper
# -----------------------
@dataclass
class _State:
    value: str


@dataclass
class _Status:
    state: _State
    stage: str
    progress: float
    message: str
    error: Optional[str] = None
    started_at: str = ""
    finished_at: str = ""


def _set_ctx_status(ctx: JobContext, *, state: str, stage: str, progress: float, message: str, error: Optional[str] = None):
    now = datetime.now(timezone.utc).isoformat()
    st = _Status(
        state=_State(state),
        stage=stage,
        progress=float(progress),
        message=message,
        error=error,
        started_at=now,
        finished_at=now,
    )
    try:
        setattr(ctx, "status", st)
    except Exception:
        pass


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

    async def _download(url: str, temp_dir: str, ctx: JobContext) -> str:
        if not method:
            raise RuntimeError("No YouTube download method found in YouTubeService.")

        res = await _call_best_effort(
            method,
            [
                ((url, temp_dir, ctx), {}),
                ((url, temp_dir), {}),
                ((url,), {}),
                ((), {"url": url, "temp_dir": temp_dir, "ctx": ctx}),
                ((), {"url": url, "temp_dir": temp_dir}),
                ((), {"url": url}),
            ],
        )

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
        raise RuntimeError("Download finished but no valid video was found.")

    return _download


def build_process_fn() -> Callable[[str, str, str, str, JobContext], Any]:
    from core.video_processor import VideoProcessor

    vp = VideoProcessor()
    to_portrait = getattr(vp, "to_portrait", None)
    to_landscape = getattr(vp, "to_landscape", None)
    if not callable(to_portrait) or not callable(to_landscape):
        raise RuntimeError("VideoProcessor must implement to_portrait & to_landscape")

    def _invoke(vp_method: Callable[..., Any], *, input_path: str, output_path: str, output_dir: str, temp_dir: str, ctx: JobContext):
        mapping = {
            "input_path": input_path,
            "video_path": input_path,
            "path": input_path,
            "output_path": output_path,
            "out_path": output_path,
            "output_dir": output_dir,
            "out_dir": output_dir,
            "temp_dir": temp_dir,
            "tmp_dir": temp_dir,
            "ctx": ctx,
            "context": ctx,
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
            raise RuntimeError(f"Input video not found: {input_path}")
        if _size(input_path) < 1024:
            raise RuntimeError(f"Input video is invalid/too small: {input_path}")

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        stem = Path(input_path).stem
        out_portrait = str(Path(output_dir) / f"{stem}__portrait.mp4")
        out_landscape = str(Path(output_dir) / f"{stem}__landscape.mp4")

        mode = (format_mode or "both").lower().strip()
        results: Dict[str, str] = {}

        if mode in ("portrait", "both"):
            res = await _call_best_effort(
                to_portrait,
                _invoke(to_portrait, input_path=input_path, output_path=out_portrait, output_dir=output_dir, temp_dir=temp_dir, ctx=ctx),
            )
            portrait_path = res if isinstance(res, str) and _exists_file(res) else out_portrait
            if not _exists_file(portrait_path) or _size(portrait_path) < 1024:
                raise RuntimeError(f"Portrait output not created or invalid: {portrait_path}")
            results["portrait"] = portrait_path

        if mode in ("landscape", "both"):
            res = await _call_best_effort(
                to_landscape,
                _invoke(to_landscape, input_path=input_path, output_path=out_landscape, output_dir=output_dir, temp_dir=temp_dir, ctx=ctx),
            )
            landscape_path = res if isinstance(res, str) and _exists_file(res) else out_landscape
            if not _exists_file(landscape_path) or _size(landscape_path) < 1024:
                raise RuntimeError(f"Landscape output not created or invalid: {landscape_path}")
            results["landscape"] = landscape_path

        if not results:
            raise RuntimeError(f"No output generated for format_mode={mode}")

        ctx.meta["processed_outputs"] = dict(results)
        ctx.meta["persist_dir"] = str(Path(output_dir))
        return results

    return _process


def build_upload_fn(cloudinary_service: Any) -> Callable[[str, str, JobContext, Optional[Dict[str, Any]]], Any]:
    method = None
    for n in ["upload_video", "upload", "upload_file", "upload_asset", "upload_media", "upload_to_cloudinary"]:
        m = getattr(cloudinary_service, n, None)
        if callable(m):
            method = m
            break

    if method is None:
        available = [x for x in dir(cloudinary_service) if not x.startswith("_")]
        raise RuntimeError(f"CloudinaryService tidak punya method upload yang cocok. Available methods: {available}")

    async def _upload(file_path: str, variant: str, ctx: JobContext, metadata: Optional[Dict[str, Any]] = None) -> Any:
        res = await _call_best_effort(
            method,
            [
                ((file_path, variant, ctx), {}),
                ((file_path, variant), {}),
                ((file_path,), {}),
                ((), {"file_path": file_path, "variant": variant, "ctx": ctx, "metadata": metadata or {}}),
                ((), {"file_path": file_path}),
                ((), {"path": file_path}),
            ],
        )

        if isinstance(res, str):
            return {"url": _normalize_url(res)}

        if isinstance(res, dict):
            url = (
                res.get("url")
                or res.get("secure_url")
                or res.get("cloudinary_url")
                or res.get("video_url")
            )
            if url:
                res["url"] = _normalize_url(str(url))
            return res

        return {"result": res}

    return _upload


def build_upload_skip_fn() -> Callable[[str, str, JobContext, Optional[Dict[str, Any]]], Any]:
    async def _skip(file_path: str, variant: str, ctx: JobContext, metadata: Optional[Dict[str, Any]] = None) -> Any:
        return {"skipped": True, "variant": variant, "file_path": str(file_path)}

    return _skip


def build_schedule_fn(repliz_service: Any) -> Callable[[Any, Any, JobContext], Any]:
    create_fn = getattr(repliz_service, "create_schedule", None)
    if not callable(create_fn):
        create_fn = getattr(repliz_service, "schedule", None)
    if not callable(create_fn):
        raise RuntimeError("ReplizService must implement create_schedule(payload) or schedule(payload)")

    async def _schedule(uploads: Any, accounts: Any, ctx: JobContext) -> Dict[str, Any]:
        urls = _uploads_to_variant_urls(uploads)
        if not urls:
            raise RuntimeError("No urls found in uploads for scheduling.")

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
            raise RuntimeError("Account IDs are empty. Select accounts in Repliz page.")
        if len(account_ids) > MAX_REPLIZ_ACCOUNTS:
            raise RuntimeError(f"Max Repliz multi-account is {MAX_REPLIZ_ACCOUNTS}. You provided {len(account_ids)}.")

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

        if not any_success:
            raise RuntimeError(f"Scheduling failed for all targets. Example: {results['failed'][:1]}")

        return results

    return _schedule


# -----------------------
# Main
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
    load_dotenv_best_effort()

    enable_upload = bool(payload.get("enable_upload", False))
    enable_schedule = bool(payload.get("enable_schedule", False)) and enable_upload

    if len(account_ids) > MAX_REPLIZ_ACCOUNTS:
        raise RuntimeError(f"Max Repliz multi-account is {MAX_REPLIZ_ACCOUNTS}. You provided {len(account_ids)}.")

    source_kind, source_value = _payload_source(payload)

    settings = JobSettings(
        format_mode=str(payload.get("format_mode") or payload.get("format") or "both"),
        output_dir=str(payload.get("output_dir") or _default_output_dir()),
        temp_dir=str(payload.get("temp_dir") or _default_temp_dir()),
    )

    ctx = JobContext(source=JobSource(kind=source_kind, value=source_value), settings=settings)
    if job_id:
        ctx.job_id = job_id

    ctx.meta["accounts"] = _account_dicts(account_ids)
    ctx.meta["ai_options"] = payload.get("ai_options") or {}
    ctx.meta["duration_policy"] = payload.get("duration_policy") or {}
    ctx.meta["face_centering"] = payload.get("face_centering") or {}
    ctx.meta["quality_profile"] = payload.get("quality_profile") or payload.get("quality") or "1080p"

    if variant_account_map:
        ctx.meta["variant_account_map"] = variant_account_map

    output_dir = str(payload.get("output_dir") or _default_output_dir())
    temp_dir = str(payload.get("temp_dir") or _default_temp_dir())
    format_mode = str(payload.get("format_mode") or payload.get("format") or "both")

    if source_kind == "youtube":
        download_fn = build_download_fn(youtube_service)
        input_path = await download_fn(source_value, temp_dir, ctx)
        _set_ctx_status(ctx, state="RUNNING", stage="ResolveSource", progress=0.15, message="YouTube downloaded")
    else:
        input_path = source_value
        _set_ctx_status(ctx, state="RUNNING", stage="ResolveSource", progress=0.15, message="Offline source ready")

    process_fn = build_process_fn()
    processed_outputs = await process_fn(input_path, format_mode, output_dir, temp_dir, ctx)
    ctx.meta["processed_outputs"] = processed_outputs
    _set_ctx_status(ctx, state="RUNNING", stage="ProcessVideo", progress=0.45, message="Video processed")

    ai_stage_fn = build_ai_stage_fn()
    try:
        ai_result = await ai_stage_fn(output_dir, ctx)
        ctx.meta["ai_result"] = ai_result
        _set_ctx_status(ctx, state="RUNNING", stage="AIProcessing", progress=0.65, message="AI stage completed")
    except Exception as e:
        ctx.meta["ai_result"] = {"enabled": False, "error": str(e)}
        print(f"[AI_STAGE_ERROR] {e}")
        _set_ctx_status(ctx, state="RUNNING", stage="AIProcessing", progress=0.65, message=f"AI stage skipped/failed: {e}")

    uploads: Dict[str, Any] = {}
    if enable_upload:
        upload_fn = build_upload_fn(cloudinary_service)
        for variant, fp in processed_outputs.items():
            uploads[variant] = await upload_fn(fp, variant, ctx, metadata={"ai_result": ctx.meta.get("ai_result")})
        ctx.meta["uploads"] = uploads
        _set_ctx_status(ctx, state="RUNNING", stage="UploadCloudinary", progress=0.82, message="Cloudinary upload completed")
    else:
        ctx.meta["uploads"] = {"skipped": True}
        _set_ctx_status(ctx, state="RUNNING", stage="UploadCloudinary", progress=0.82, message="Cloudinary upload skipped")

    if enable_schedule:
        schedule_fn = build_schedule_fn(repliz_service)
        schedule_result = await schedule_fn(ctx.meta["uploads"], ctx.meta.get("accounts") or [], ctx)
        ctx.meta["schedule_result"] = schedule_result
        _set_ctx_status(ctx, state="SUCCESS", stage="ScheduleRepliz", progress=1.0, message="Repliz scheduling completed")
    else:
        ctx.meta["schedule_result"] = {}
        _set_ctx_status(ctx, state="SUCCESS", stage="PersistContext", progress=1.0, message="Pipeline done")

    ctx.meta["persist_dir"] = output_dir
    return ctx


__all__ = ["run_gnx_job"]