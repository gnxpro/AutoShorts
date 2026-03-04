import asyncio
import os
import sys
import importlib
import inspect
from pathlib import Path
from typing import Any, Callable, Dict, Optional, List, Tuple, Union

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Load .env (best effort)
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

def load_dotenv_best_effort():
    try:
        from dotenv import load_dotenv  # type: ignore
        load_dotenv(dotenv_path=ROOT_DIR / ".env", override=False)
        load_dotenv(dotenv_path=ROOT_DIR / ".env.local", override=False)
    except Exception:
        _load_env_manual(ROOT_DIR / ".env")
        _load_env_manual(ROOT_DIR / ".env.local")

load_dotenv_best_effort()

from gnx.models.job_context import JobContext, JobSource, JobSettings
from gnx.pipeline.events import PipelineEvent
from gnx.pipeline.runner import PipelineRunner, PipelineRunnerConfig
from gnx.pipeline.stages.gnx_default_stages import (
    ResolveSourceStage,
    ProcessVideoStage,
    UploadCloudinaryStage,
    ScheduleReplizStage,
)

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}

async def maybe_await(x):
    if asyncio.iscoroutine(x):
        return await x
    return x

async def call_best_effort(fn, attempts: List[Tuple[Tuple[Any, ...], Dict[str, Any]]]):
    last = None
    for args, kwargs in attempts:
        try:
            return await maybe_await(fn(*args, **kwargs))
        except TypeError as e:
            last = e
            continue
    if last:
        raise last
    raise TypeError("Tidak ada signature yang cocok.")

def import_first_module(module_names: List[str]):
    last = None
    for name in module_names:
        try:
            return importlib.import_module(name)
        except Exception as e:
            last = e
    raise last if last else ImportError("Import module gagal")

def _exists_file(p: Union[str, Path]) -> bool:
    pp = Path(p)
    return pp.exists() and pp.is_file()

def _size(p: Union[str, Path]) -> int:
    return Path(p).stat().st_size

def _is_video_path(p: Union[str, Path]) -> bool:
    return Path(p).suffix.lower() in VIDEO_EXTS

def pick_best_video_file(candidates: List[Union[str, Path]], fallback_dir: Optional[Union[str, Path]] = None) -> Optional[str]:
    vids: List[Tuple[int, str]] = []
    for c in candidates:
        if not c:
            continue
        p = str(c)
        if _exists_file(p) and _is_video_path(p):
            vids.append((_size(p), p))
    if vids:
        vids.sort(key=lambda x: x[0], reverse=True)
        return vids[0][1]

    if fallback_dir:
        d = Path(fallback_dir)
        if d.exists():
            best: Tuple[int, Optional[str]] = (0, None)
            for ext in VIDEO_EXTS:
                for f in d.glob(f"*{ext}"):
                    sz = _size(f)
                    if sz > best[0]:
                        best = (sz, str(f))
            return best[1]
    return None

def coerce_download_result_to_video_path(result: Any, temp_dir: str) -> str:
    candidates: List[Union[str, Path]] = []
    if isinstance(result, str):
        candidates.append(result)
    elif isinstance(result, dict):
        for v in result.values():
            if isinstance(v, str):
                candidates.append(v)
    elif isinstance(result, (list, tuple, set)):
        for v in result:
            if isinstance(v, str):
                candidates.append(v)
    else:
        candidates.append(str(result))

    best = pick_best_video_file(candidates, fallback_dir=temp_dir)
    if best:
        return best

    # fallback: cari mp4 terbesar di temp_dir
    best2 = pick_best_video_file([], fallback_dir=temp_dir)
    if best2:
        return best2

    raise RuntimeError("Download selesai tapi tidak bisa menentukan file video output.")

def build_download_fn() -> Callable[[str, str, JobContext], Any]:
    mod = import_first_module(["core.youtube_download"])

    cls = getattr(mod, "YouTubeService", None) or getattr(mod, "YouTubeDownloader", None) or getattr(mod, "YoutubeDownloader", None)
    inst = cls() if cls and callable(cls) else None

    method = None
    if inst is not None:
        for name in ["download", "download_video", "download_to_file", "fetch", "run"]:
            m = getattr(inst, name, None)
            if m and callable(m):
                method = m
                break

    func = None
    for name in ["download", "download_video", "download_youtube", "download_youtube_video", "run_download"]:
        f = getattr(mod, name, None)
        if f and callable(f):
            func = f
            break

    async def _download(url: str, temp_dir: str, ctx: JobContext) -> str:
        if method:
            res = await call_best_effort(method, [
                ((url, temp_dir, ctx), {}),
                ((url, temp_dir), {}),
                ((url,), {}),
                ((), {"url": url, "temp_dir": temp_dir, "ctx": ctx}),
                ((), {"url": url, "temp_dir": temp_dir}),
                ((), {"url": url}),
            ])
        elif func:
            res = await call_best_effort(func, [
                ((url, temp_dir, ctx), {}),
                ((url, temp_dir), {}),
                ((url,), {}),
                ((), {"url": url, "temp_dir": temp_dir, "ctx": ctx}),
                ((), {"url": url, "temp_dir": temp_dir}),
                ((), {"url": url}),
            ])
        else:
            raise RuntimeError("Tidak menemukan downloader di core.youtube_download")

        return coerce_download_result_to_video_path(res, temp_dir=temp_dir)

    return _download

def _invoke_vp(vp_method: Callable[..., Any], *, input_path: str, output_path: str, output_dir: str, temp_dir: str, ctx: JobContext):
    mapping = {
        "input_path": input_path, "video_path": input_path, "path": input_path,
        "output_path": output_path, "out_path": output_path,
        "output_dir": output_dir, "out_dir": output_dir,
        "temp_dir": temp_dir, "tmp_dir": temp_dir,
        "ctx": ctx,
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

def build_process_fn() -> Callable[[str, str, str, str, JobContext], Any]:
    mod = import_first_module(["core.video_processor"])
    VP = getattr(mod, "VideoProcessor", None)
    if not VP or not callable(VP):
        raise RuntimeError("Tidak menemukan class VideoProcessor di core.video_processor")

    vp = VP()
    to_portrait = getattr(vp, "to_portrait", None)
    to_landscape = getattr(vp, "to_landscape", None)
    if not callable(to_portrait) or not callable(to_landscape):
        raise RuntimeError("VideoProcessor harus punya method to_portrait dan to_landscape")

    async def _process(input_path: str, format_mode: str, output_dir: str, temp_dir: str, ctx: JobContext):
        if not _exists_file(input_path):
            raise RuntimeError(f"Input video tidak ditemukan: {input_path}")
        if _size(input_path) < 1024:
            raise RuntimeError(f"Input video terlalu kecil/invalid: {input_path}")

        Path(output_dir).mkdir(parents=True, exist_ok=True)
        stem = Path(input_path).stem
        out_portrait = str(Path(output_dir) / f"{stem}__portrait.mp4")
        out_landscape = str(Path(output_dir) / f"{stem}__landscape.mp4")

        mode = (format_mode or "both").lower().strip()
        results: Dict[str, str] = {}

        if mode in ("portrait", "both"):
            res = await call_best_effort(
                to_portrait,
                _invoke_vp(to_portrait, input_path=input_path, output_path=out_portrait, output_dir=output_dir, temp_dir=temp_dir, ctx=ctx),
            )
            best = pick_best_video_file([res] if isinstance(res, str) else [out_portrait], fallback_dir=output_dir) or out_portrait
            results["portrait"] = best

        if mode in ("landscape", "both"):
            res = await call_best_effort(
                to_landscape,
                _invoke_vp(to_landscape, input_path=input_path, output_path=out_landscape, output_dir=output_dir, temp_dir=temp_dir, ctx=ctx),
            )
            best = pick_best_video_file([res] if isinstance(res, str) else [out_landscape], fallback_dir=output_dir) or out_landscape
            results["landscape"] = best

        return results

    return _process

def build_upload_fn():
    mod = import_first_module([
        "core.services.cloudinary_service",
        "core.services.cloudinary",
        "core.services.cloudinary_uploader",
    ])
    service_cls = getattr(mod, "CloudinaryService", None) or getattr(mod, "CloudinaryUploader", None) or getattr(mod, "CloudinaryClient", None)
    inst = service_cls() if service_cls and callable(service_cls) else None

    fn = None
    if inst is not None:
        for name in ["upload", "upload_video", "upload_file", "upload_asset"]:
            m = getattr(inst, name, None)
            if m and callable(m):
                fn = m
                break
    if fn is None:
        for name in ["upload", "upload_video", "upload_file"]:
            f = getattr(mod, name, None)
            if f and callable(f):
                fn = f
                break

    async def _upload(file_path: str, variant: str, ctx: JobContext, metadata: Optional[Dict[str, Any]] = None):
        if not fn:
            raise RuntimeError("Cloudinary upload callable tidak ditemukan (core/services).")
        return await call_best_effort(fn, [
            ((file_path, variant, ctx), {}),
            ((file_path, variant), {}),
            ((file_path,), {}),
            ((), {"file_path": file_path, "variant": variant, "ctx": ctx, "metadata": metadata or {}}),
        ])
    return _upload

def build_schedule_fn():
    mod = import_first_module([
        "core.services.repliz_service",
        "core.services.repliz",
        "core.services.repliz_client",
    ])
    service_cls = getattr(mod, "ReplizService", None) or getattr(mod, "ReplizClient", None)
    inst = service_cls() if service_cls and callable(service_cls) else None

    fn = None
    if inst is not None:
        for name in ["schedule", "schedule_post", "schedule_posts", "enqueue", "publish"]:
            m = getattr(inst, name, None)
            if m and callable(m):
                fn = m
                break
    if fn is None:
        for name in ["schedule", "schedule_post", "schedule_posts"]:
            f = getattr(mod, name, None)
            if f and callable(f):
                fn = f
                break

    async def _schedule(uploads: Dict[str, Any], accounts: Any, ctx: JobContext):
        if not fn:
            raise RuntimeError("Repliz schedule callable tidak ditemukan (core/services).")
        return await call_best_effort(fn, [
            ((uploads, accounts, ctx), {}),
            ((uploads, accounts), {}),
            ((uploads,), {}),
            ((), {"uploads": uploads, "accounts": accounts, "ctx": ctx}),
        ])
    return _schedule

async def print_event(ev: PipelineEvent):
    stage = ev.stage or "-"
    print(f"[{ev.type}] stage={stage} msg={ev.message} data={ev.data}")

def parse_account_ids_env() -> List[str]:
    # kamu bisa set salah satu:
    # GNX_ACCOUNT_IDS="id1,id2"
    # REPLIZ_ACCOUNT_IDS="id1,id2"
    raw = (os.environ.get("GNX_ACCOUNT_IDS") or os.environ.get("REPLIZ_ACCOUNT_IDS") or "").strip()
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]

async def main():
    demo_mode = os.environ.get("GNX_DEMO_MODE", "full").strip().lower()
    source_kind = os.environ.get("GNX_SOURCE_KIND", "file").strip().lower()
    source_value = os.environ.get("GNX_SOURCE_VALUE", r"assets\video.mp4").strip()
    fmt = os.environ.get("GNX_FORMAT_MODE", "both").strip().lower()

    # ✅ ACCOUNT IDs dari ENV
    ids = parse_account_ids_env()
    if not ids:
        print("[WARN] Account ID kosong. Set env GNX_ACCOUNT_IDS atau REPLIZ_ACCOUNT_IDS (comma-separated).")
    accounts_payload = [{"id": i} for i in ids] if ids else []

    settings = JobSettings(format_mode=fmt, output_dir="outputs", temp_dir="temp")
    ctx = JobContext(source=JobSource(kind=source_kind, value=source_value), settings=settings)
    ctx.meta["accounts"] = accounts_payload

    if source_kind == "youtube":
        ctx.services["download_fn"] = build_download_fn()
    ctx.services["process_fn"] = build_process_fn()

    stages = [ResolveSourceStage(), ProcessVideoStage()]

    if demo_mode in ("upload", "full"):
        ctx.services["upload_fn"] = build_upload_fn()
        stages.append(UploadCloudinaryStage())

    if demo_mode == "full":
        ctx.services["schedule_fn"] = build_schedule_fn()
        stages.append(ScheduleReplizStage())

    runner = PipelineRunner(
        stages=stages,
        config=PipelineRunnerConfig(auto_progress=True, raise_on_error=False),
        event_handler=print_event,
    )

    final_ctx = await runner.run(ctx)
    print("\nFINAL STATUS:")
    print(final_ctx.to_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())