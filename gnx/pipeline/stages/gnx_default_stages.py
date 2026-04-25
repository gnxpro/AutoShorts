from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

from gnx.models.job_context import JobContext
from gnx.pipeline.stages.base import BaseStage, StageError, StageSkip


async def _maybe_await(value: Any) -> Any:
    if asyncio.iscoroutine(value):
        return await value
    return value


async def _invoke_best_effort(fn: Any, *arg_sets: Any) -> Any:
    """
    Panggil callable dengan beberapa kemungkinan signature (best-effort).
    arg_sets adalah tuple berisi (args, kwargs) yang dicoba berurutan.
    """
    last_exc: Optional[Exception] = None
    for args, kwargs in arg_sets:
        try:
            return await _maybe_await(fn(*args, **kwargs))
        except TypeError as e:
            last_exc = e
            continue
    if last_exc:
        raise last_exc
    raise TypeError("No callable invocation attempted")


def _require_service(ctx: JobContext, key: str) -> Any:
    fn = ctx.services.get(key)
    if fn is None:
        raise StageError(
            f"Service '{key}' tidak ditemukan di ctx.services. "
            f"Harus diisi sebelum pipeline jalan. Contoh: ctx.services['{key}'] = <callable>."
        )
    if not callable(fn):
        raise StageError(f"Service '{key}' ada tapi bukan callable. Value={type(fn)}")
    return fn


def _norm_path(p: str) -> str:
    return os.path.normpath(p)


def _file_exists(p: str) -> bool:
    try:
        return Path(p).exists() and Path(p).is_file()
    except Exception:
        return False


def _coerce_upload_result(result: Any) -> Dict[str, Any]:
    """
    Upload fn bisa return:
    - string URL
    - dict {url:..., ...}
    """
    if isinstance(result, str):
        return {"url": result}
    if isinstance(result, dict):
        return dict(result)
    return {"result": result}


@dataclass
class ResolveSourceStage(BaseStage):
    """
    Stage 1: Resolve input menjadi file lokal.

    Rules:
    - Jika ctx.artifacts.raw_video_path sudah ada & file exists -> skip.
    - Jika ctx.source.kind == "file" -> raw_video_path = ctx.source.value (cek exists).
    - Jika ctx.source.kind == "youtube"/"yt" -> pakai ctx.services['download_fn'] untuk download.

    Expected service keys:
    - download_fn (opsional; wajib jika source youtube)

    download_fn signature yang didukung (best effort):
    - download_fn(url) -> path
    - download_fn(url, temp_dir)
    - download_fn(url, temp_dir, ctx)
    - download_fn(url=url, temp_dir=..., ctx=...)
    """

    name: str = "ResolveSource"

    def should_run(self, ctx: JobContext) -> bool:
        if ctx.artifacts.raw_video_path and _file_exists(ctx.artifacts.raw_video_path):
            return False
        return True

    async def run(self, ctx: JobContext) -> JobContext:
        ctx.ensure_dirs()

        # Idempotent: sudah ada raw path valid
        if ctx.artifacts.raw_video_path and _file_exists(ctx.artifacts.raw_video_path):
            raise StageSkip("raw_video_path sudah ada dan valid")

        kind = (ctx.source.kind or "").lower().strip()
        value = (ctx.source.value or "").strip()

        if not kind:
            raise StageError("ctx.source.kind kosong. Set ke 'file' atau 'youtube'.")

        if kind in ("file", "local", "offline"):
            if not value:
                raise StageError("ctx.source.value kosong untuk source file.")
            if not _file_exists(value):
                raise StageError(f"File source tidak ditemukan: {value}")
            ctx.artifacts.raw_video_path = _norm_path(value)
            return ctx

        if kind in ("youtube", "yt"):
            if not value:
                raise StageError("ctx.source.value kosong untuk source youtube (butuh URL).")

            download_fn = _require_service(ctx, "download_fn")

            # best-effort calling
            temp_dir = ctx.settings.temp_dir
            result = await _invoke_best_effort(
                download_fn,
                ((value,), {}),
                ((value, temp_dir), {}),
                ((value, temp_dir, ctx), {}),
                ((), {"url": value}),
                ((), {"url": value, "temp_dir": temp_dir}),
                ((), {"url": value, "temp_dir": temp_dir, "ctx": ctx}),
            )

            if not isinstance(result, str):
                raise StageError(f"download_fn harus return path string. Dapat: {type(result)}")

            if not _file_exists(result):
                raise StageError(f"Hasil download_fn tidak ditemukan di disk: {result}")

            ctx.artifacts.raw_video_path = _norm_path(result)
            return ctx

        raise StageError(f"source.kind tidak didukung: {kind}")


@dataclass
class ProcessVideoStage(BaseStage):
    """
    Stage 2: Process video (crop portrait/landscape/both) via VideoProcessor.

    Expected service keys:
    - process_fn (wajib)

    process_fn signature yang didukung (best effort):
    - process_fn(input_path) -> dict|str
    - process_fn(input_path, format_mode) -> dict|str
    - process_fn(input_path, format_mode, output_dir) -> dict|str
    - process_fn(input_path, format_mode, output_dir, temp_dir) -> dict|str
    - process_fn(input_path, format_mode, output_dir, temp_dir, ctx) -> dict|str
    - process_fn(input_path=..., format_mode=..., output_dir=..., temp_dir=..., ctx=...)
    """

    name: str = "ProcessVideo"

    def should_run(self, ctx: JobContext) -> bool:
        mode = (ctx.settings.format_mode or "both").lower().strip()
        pv = ctx.artifacts.processed_variants or {}

        # Jika sudah punya output yang diperlukan -> skip
        if mode == "portrait" and pv.get("portrait") and _file_exists(pv["portrait"]):
            return False
        if mode == "landscape" and pv.get("landscape") and _file_exists(pv["landscape"]):
            return False
        if mode == "both":
            if (
                pv.get("portrait") and _file_exists(pv["portrait"])
                and pv.get("landscape") and _file_exists(pv["landscape"])
            ):
                return False
        return True

    async def run(self, ctx: JobContext) -> JobContext:
        ctx.ensure_dirs()

        raw = ctx.artifacts.raw_video_path
        if not raw or not _file_exists(raw):
            raise StageError("raw_video_path belum ada / tidak valid. Pastikan ResolveSourceStage jalan dulu.")

        process_fn = _require_service(ctx, "process_fn")

        mode = (ctx.settings.format_mode or "both").lower().strip()
        out_dir = ctx.settings.output_dir
        temp_dir = ctx.settings.temp_dir

        result = await _invoke_best_effort(
            process_fn,
            ((raw, mode, out_dir, temp_dir, ctx), {}),
            ((raw, mode, out_dir, temp_dir), {}),
            ((raw, mode, out_dir), {}),
            ((raw, mode), {}),
            ((raw,), {}),
            ((), {"input_path": raw, "format_mode": mode, "output_dir": out_dir, "temp_dir": temp_dir, "ctx": ctx}),
            ((), {"input_path": raw, "format_mode": mode, "output_dir": out_dir, "temp_dir": temp_dir}),
            ((), {"input_path": raw, "format_mode": mode, "output_dir": out_dir}),
            ((), {"input_path": raw, "format_mode": mode}),
            ((), {"input_path": raw}),
        )

        # Normalize output
        # - dict: {"portrait": path, "landscape": path}
        # - str: single path; infer variant from mode
        new_variants: Dict[str, str] = {}

        if isinstance(result, dict):
            for k, v in result.items():
                if isinstance(v, str) and v:
                    new_variants[str(k)] = _norm_path(v)
        elif isinstance(result, str):
            # infer
            if mode == "portrait":
                new_variants["portrait"] = _norm_path(result)
            elif mode == "landscape":
                new_variants["landscape"] = _norm_path(result)
            else:
                # mode both tapi cuma dapat 1 string -> tidak cukup
                raise StageError(
                    "process_fn return string tapi format_mode='both'. "
                    "Untuk 'both', process_fn harus return dict dengan portrait & landscape."
                )
        else:
            raise StageError(f"process_fn return type tidak didukung: {type(result)}")

        # Validate files exist
        for variant, p in new_variants.items():
            if not _file_exists(p):
                raise StageError(f"Output process_fn untuk '{variant}' tidak ditemukan: {p}")

        # Merge ke artifacts (jangan hilangkan yang sudah ada)
        ctx.artifacts.processed_variants.update(new_variants)
        return ctx


@dataclass
class UploadCloudinaryStage(BaseStage):
    """
    Stage 3: Upload ke Cloudinary.

    Expected service keys:
    - upload_fn (wajib)

    upload_fn signature yang didukung (best effort):
    - upload_fn(file_path) -> dict|str
    - upload_fn(file_path, variant) -> dict|str
    - upload_fn(file_path, variant, ctx) -> dict|str
    - upload_fn(file_path=file_path, variant=..., ctx=..., metadata=...)
    """

    name: str = "UploadCloudinary"

    def should_run(self, ctx: JobContext) -> bool:
        # Jika semua variant yang akan diupload sudah punya uploads -> skip.
        mode = (ctx.settings.format_mode or "both").lower().strip()
        pv = ctx.artifacts.processed_variants or {}

        targets = []
        if mode == "portrait":
            if pv.get("portrait"):
                targets = ["portrait"]
        elif mode == "landscape":
            if pv.get("landscape"):
                targets = ["landscape"]
        else:
            if pv.get("portrait"):
                targets.append("portrait")
            if pv.get("landscape"):
                targets.append("landscape")

        if not targets:
            return True

        uploads = ctx.artifacts.uploads or {}
        all_done = True
        for v in targets:
            if v not in uploads:
                all_done = False
                break
        return not all_done

    async def run(self, ctx: JobContext) -> JobContext:
        ctx.ensure_dirs()

        upload_fn = _require_service(ctx, "upload_fn")

        mode = (ctx.settings.format_mode or "both").lower().strip()
        pv = ctx.artifacts.processed_variants or {}

        targets = []
        if mode == "portrait":
            targets = ["portrait"] if pv.get("portrait") else []
        elif mode == "landscape":
            targets = ["landscape"] if pv.get("landscape") else []
        else:
            if pv.get("portrait"):
                targets.append("portrait")
            if pv.get("landscape"):
                targets.append("landscape")

        if not targets:
            raise StageError("processed_variants kosong. Pastikan ProcessVideoStage jalan dulu.")

        for variant in targets:
            # Idempotent per-variant
            if variant in ctx.artifacts.uploads:
                continue

            file_path = pv.get(variant)
            if not file_path or not _file_exists(file_path):
                raise StageError(f"File variant '{variant}' tidak ditemukan: {file_path}")

            metadata = {
                "job_id": ctx.job_id,
                "variant": variant,
                "source_kind": ctx.source.kind,
            }

            result = await _invoke_best_effort(
                upload_fn,
                ((file_path, variant, ctx), {}),
                ((file_path, variant), {}),
                ((file_path,), {}),
                ((), {"file_path": file_path, "variant": variant, "ctx": ctx, "metadata": metadata}),
                ((), {"file_path": file_path, "variant": variant, "metadata": metadata}),
                ((), {"file_path": file_path, "variant": variant}),
                ((), {"file_path": file_path}),
            )

            ctx.artifacts.uploads[variant] = _coerce_upload_result(result)

        return ctx


@dataclass
class ScheduleReplizStage(BaseStage):
    """
    Stage 4: Schedule upload via Repliz.

    Expected service keys:
    - schedule_fn (wajib)

    schedule_fn signature yang didukung (best effort):
    - schedule_fn(uploads) -> dict
    - schedule_fn(uploads, ctx) -> dict
    - schedule_fn(uploads, accounts) -> dict
    - schedule_fn(uploads, accounts, ctx) -> dict
    - schedule_fn(uploads=..., accounts=..., ctx=...)
    """

    name: str = "ScheduleRepliz"

    def should_run(self, ctx: JobContext) -> bool:
        # Kalau sudah ada schedule_result -> skip
        return not bool(ctx.artifacts.schedule_result)

    async def run(self, ctx: JobContext) -> JobContext:
        ctx.ensure_dirs()

        schedule_fn = _require_service(ctx, "schedule_fn")

        uploads = ctx.artifacts.uploads or {}
        if not uploads:
            raise StageError("uploads kosong. Pastikan UploadCloudinaryStage jalan dulu.")

        # accounts bisa kamu isi dari UI ke ctx.meta
        # contoh: ctx.meta["accounts"] = [{"id": "...", "name": "..."}] atau list id
        accounts = ctx.meta.get("accounts") or ctx.meta.get("repliz_accounts")

        result = await _invoke_best_effort(
            schedule_fn,
            ((uploads, accounts, ctx), {}),
            ((uploads, accounts), {}),
            ((uploads, ctx), {}),
            ((uploads,), {}),
            ((), {"uploads": uploads, "accounts": accounts, "ctx": ctx}),
            ((), {"uploads": uploads, "accounts": accounts}),
            ((), {"uploads": uploads, "ctx": ctx}),
            ((), {"uploads": uploads}),
        )

        if isinstance(result, dict):
            ctx.artifacts.schedule_result = dict(result)
        else:
            # tetap simpan supaya UI ada output
            ctx.artifacts.schedule_result = {"result": result}

        return ctx