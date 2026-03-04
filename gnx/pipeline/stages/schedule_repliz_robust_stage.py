from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from gnx.models.job_context import JobContext
from gnx.pipeline.stages.base import BaseStage, StageError


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
            f"Isi dulu: ctx.services['{key}'] = <callable>."
        )
    if not callable(fn):
        raise StageError(f"Service '{key}' ada tapi bukan callable. Value={type(fn)}")
    return fn


def _normalize_url(u: str) -> str:
    u = (u or "").strip()
    if not u:
        return u
    # kalau user/service ngasih "res.cloudinary.com/..." tanpa skema
    if u.startswith("res.cloudinary.com") or u.startswith("cloudinary.com"):
        return "https://" + u
    # kalau ngasih "//res.cloudinary.com/..."
    if u.startswith("//"):
        return "https:" + u
    # kalau ngasih "ps://..." (pernah kejadian karena string kepotong)
    if u.startswith("ps://"):
        return "htt" + u  # jadi "https://"
    return u


def _extract_http_details(e: Exception) -> Dict[str, Any]:
    """
    Coba ambil detail dari requests/httpx exception jika ada.
    """
    info: Dict[str, Any] = {"exception_type": type(e).__name__, "exception": str(e)}
    resp = getattr(e, "response", None)
    if resp is not None:
        info["status_code"] = getattr(resp, "status_code", None)
        text = getattr(resp, "text", None)
        if isinstance(text, str) and text:
            info["response_text_snippet"] = text[:800]
    return info


def _urls_from_uploads(uploads: Dict[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for variant, v in (uploads or {}).items():
        url = None
        if isinstance(v, dict):
            url = v.get("url") or v.get("cloudinary_url") or v.get("secure_url")
        elif isinstance(v, str):
            url = v
        if url:
            out[str(variant)] = _normalize_url(str(url))
    return out


def _accounts_variants(accounts: Any) -> List[Any]:
    """
    Buat beberapa bentuk accounts agar cocok dengan berbagai implementasi:
    - original
    - list of ids (kalau accounts list of dict)
    """
    variants = [accounts]
    try:
        if isinstance(accounts, list) and accounts and isinstance(accounts[0], dict):
            ids = [a.get("id") or a.get("account_id") for a in accounts if (a.get("id") or a.get("account_id"))]
            if ids:
                variants.append(ids)
    except Exception:
        pass
    return variants


@dataclass
class ScheduleReplizRobustStage(BaseStage):
    """
    Stage schedule yang robust:
    - normalize URL
    - coba payload bentuk berbeda (uploads dict -> urls dict -> list -> single url)
    - simpan detail error ke ctx.meta["schedule_error_details"] kalau gagal
    """
    name: str = "ScheduleRepliz"

    def should_run(self, ctx: JobContext) -> bool:
        return not bool(ctx.artifacts.schedule_result)

    async def run(self, ctx: JobContext) -> JobContext:
        ctx.ensure_dirs()
        schedule_fn = _require_service(ctx, "schedule_fn")

        uploads = ctx.artifacts.uploads or {}
        if not uploads:
            raise StageError("uploads kosong. Pastikan UploadCloudinaryStage sukses dulu.")

        urls_dict = _urls_from_uploads(uploads)
        if not urls_dict:
            raise StageError(f"uploads ada tapi tidak ada url yang bisa dipakai. uploads keys={list(uploads.keys())}")

        urls_list = [{"variant": k, "url": v} for k, v in urls_dict.items()]
        single_url = next(iter(urls_dict.values()), None)

        accounts = ctx.meta.get("accounts") or ctx.meta.get("repliz_accounts")
        acct_variants = _accounts_variants(accounts)

        # kandidat payload upload
        upload_payloads: List[Tuple[str, Any]] = [
            ("uploads_dict", uploads),
            ("urls_dict", urls_dict),
            ("urls_list", urls_list),
        ]
        if single_url:
            upload_payloads.append(("single_url", single_url))

        last_error: Optional[Exception] = None
        attempts_log: List[Dict[str, Any]] = []

        for up_name, up_payload in upload_payloads:
            for acc_payload in acct_variants:
                try:
                    res = await _invoke_best_effort(
                        schedule_fn,
                        ((up_payload, acc_payload, ctx), {}),
                        ((up_payload, acc_payload), {}),
                        ((up_payload, ctx), {}),
                        ((up_payload,), {}),
                        ((), {"uploads": up_payload, "accounts": acc_payload, "ctx": ctx}),
                        ((), {"uploads": up_payload, "accounts": acc_payload}),
                        ((), {"uploads": up_payload, "ctx": ctx}),
                        ((), {"uploads": up_payload}),
                    )

                    ctx.artifacts.schedule_result = res if isinstance(res, dict) else {"result": res}
                    ctx.meta["schedule_payload_used"] = up_name
                    ctx.meta["schedule_accounts_used_type"] = type(acc_payload).__name__
                    return ctx

                except Exception as e:
                    last_error = e
                    attempts_log.append({
                        "upload_payload": up_name,
                        "accounts_type": type(acc_payload).__name__,
                        "error": _extract_http_details(e),
                    })
                    continue

        # kalau gagal semua
        ctx.meta["schedule_error_details"] = {
            "attempts": attempts_log[-10:],  # simpan 10 terakhir biar tidak kebanyakan
            "urls_dict": urls_dict,
            "accounts_present": accounts is not None,
        }

        if last_error:
            details = _extract_http_details(last_error)
            raise StageError(
                "ScheduleRepliz gagal untuk semua variasi payload. "
                f"LastError={details}"
            )

        raise StageError("ScheduleRepliz gagal (unknown).")