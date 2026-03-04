from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib import request, parse, error


class ReplizAuthError(RuntimeError):
    pass


class ReplizAPIError(RuntimeError):
    def __init__(self, message: str, status_code: Optional[int] = None, body: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


@dataclass
class ReplizConfig:
    base_url: str = "https://api.repliz.com"
    access_key_env: str = "REPLIZ_ACCESS_KEY"
    secret_key_env: str = "REPLIZ_SECRET_KEY"
    timeout_s: int = 30
    debug_env: str = "REPLIZ_DEBUG"


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
    except Exception:
        _load_env_manual(root / ".env")
        _load_env_manual(root / ".env.local")


def _iso_z(dt: datetime) -> str:
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")


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


class ReplizService:
    """
    Basic Authorization:
      Authorization: Basic base64("ACCESS_KEY:SECRET_KEY")

    Base URL boleh:
      https://api.repliz.com/public
    akan dinormalisasi jadi:
      https://api.repliz.com
    """

    def __init__(self, config: Optional[ReplizConfig] = None):
        self.config = config or ReplizConfig()
        load_dotenv_best_effort(Path.cwd())

        self._access_key: Optional[str] = None
        self._secret_key: Optional[str] = None
        self._base_url: Optional[str] = None

    def set_credentials(self, *, base_url: str, access_key: str, secret_key: str) -> None:
        base = (base_url or "").strip().rstrip("/")
        if base.endswith("/public"):
            base = base[:-7].rstrip("/")
        self._base_url = base
        self._access_key = (access_key or "").strip()
        self._secret_key = (secret_key or "").strip()

    def _resolve_base_url(self) -> str:
        return (self._base_url or self.config.base_url).rstrip("/")

    def _resolve_keys(self) -> tuple[str, str]:
        access = (self._access_key or os.getenv(self.config.access_key_env, "").strip())
        secret = (self._secret_key or os.getenv(self.config.secret_key_env, "").strip())
        if not access or not secret:
            raise ReplizAuthError("Repliz credentials belum diisi. Isi Access Key & Secret Key di menu Repliz.")
        return access, secret

    def _basic_auth_header(self) -> str:
        access, secret = self._resolve_keys()
        token = base64.b64encode(f"{access}:{secret}".encode("utf-8")).decode("utf-8")
        return f"Basic {token}"

    def _headers(self) -> Dict[str, str]:
        # Swagger menggunakan 'Authorization'
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": self._basic_auth_header(),
        }

    def _request(self, method: str, path: str, *, query: Optional[Dict[str, Any]] = None, json_body: Any = None) -> Any:
        base = self._resolve_base_url()
        url = base + path

        if query:
            qs = parse.urlencode({k: v for k, v in query.items() if v is not None}, doseq=True)
            url = url + ("&" if "?" in url else "?") + qs

        data = None
        if json_body is not None:
            data = json.dumps(json_body).encode("utf-8")

        req = request.Request(url=url, data=data, method=method.upper(), headers=self._headers())

        try:
            with request.urlopen(req, timeout=self.config.timeout_s) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                if not raw:
                    return {}
                try:
                    return json.loads(raw)
                except Exception:
                    return {"raw": raw}

        except error.HTTPError as e:
            body = ""
            try:
                body = e.read().decode("utf-8", errors="replace")
            except Exception:
                pass
            code = getattr(e, "code", None)

            if code == 401:
                raise ReplizAuthError("401 Unauthorized: invalid authorization header. Pastikan Basic = base64(access:secret).")
            if code == 402:
                raise ReplizAPIError("402 Invalid plan", status_code=code, body=body)
            if code == 400:
                raise ReplizAPIError(f"HTTP 400: {body[:2000]}", status_code=code, body=body)

            raise ReplizAPIError(f"HTTP {code}: {body[:1200]}", status_code=code, body=body)

        except error.URLError as e:
            raise ReplizAPIError(f"Network error: {e}") from e

    # =========================================================
    # ✅ Validate keys quickly
    # =========================================================
    def validate_keys(self) -> bool:
        # endpoint accounts: page & limit wajib
        _ = self._request("GET", "/public/account", query={"page": 1, "limit": 1})
        return True

    # =========================================================
    # ✅ Accounts (sesuai Swagger)
    # =========================================================
    def get_social_accounts(self, *, page: int = 1, limit: int = 100, search: str = "") -> List[Dict[str, Any]]:
        page = int(page) if page else 1
        limit = int(limit) if limit else 10
        if page <= 0:
            page = 1
        if limit <= 0:
            limit = 10

        raw = self._request(
            "GET",
            "/public/account",
            query={"page": page, "limit": limit, "search": (search or "").strip() or None},
        )

        docs = []
        if isinstance(raw, dict) and isinstance(raw.get("docs"), list):
            docs = raw["docs"]
        elif isinstance(raw, list):
            docs = raw

        out: List[Dict[str, Any]] = []
        for it in docs:
            if not isinstance(it, dict):
                continue
            acc_id = it.get("_id") or it.get("id")
            if not acc_id:
                continue

            platform = (it.get("type") or it.get("platform") or "").strip().lower()
            name = (it.get("name") or "").strip()
            username = (it.get("username") or "").strip()
            picture = (it.get("picture") or "").strip()
            is_connected = bool(it.get("isConnected", True))

            out.append({
                "id": str(acc_id),
                "platform": platform,
                "name": name,
                "username": username,
                "picture": picture,
                "isConnected": is_connected,
                "raw": it,
            })
        return out

    # =========================================================
    # Schedule list
    # =========================================================
    def list_schedule(self, *, account_id: str, page: int = 1, limit: int = 10) -> Any:
        page = int(page) if page else 1
        limit = int(limit) if limit else 10
        return self._request("GET", "/public/schedule", query={"page": page, "limit": limit, "accountIds": account_id})

    # =========================================================
    # Create schedule
    # =========================================================
    def create_schedule(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not payload.get("accountId"):
            raise ValueError("create_schedule(): payload wajib punya accountId")

        medias = payload.get("medias")
        if not isinstance(medias, list) or not medias or not medias[0].get("url"):
            raise ValueError("create_schedule(): payload wajib punya medias=[{type,url}]")

        if not payload.get("scheduleAt"):
            payload["scheduleAt"] = _iso_z(datetime.now(timezone.utc) + timedelta(minutes=10))

        return self._request("POST", "/public/schedule", json_body=payload)

    # =========================================================
    # Single/bulk scheduling helper
    # =========================================================
    def schedule_one_video(
        self,
        *,
        video_url: str,
        account_id: str,
        title: str,
        description: str,
        schedule_at_iso_z: str,
        thumbnail_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        video_url = _normalize_url(video_url)
        thumb = thumbnail_url or _guess_thumbnail(video_url)

        media_obj: Dict[str, Any] = {"type": "video", "url": video_url}
        if thumb:
            media_obj["thumbnail"] = thumb

        payload = {
            "title": title,
            "description": description,
            "type": "video",
            "medias": [media_obj],
            "scheduleAt": schedule_at_iso_z,
            "additionalInfo": {"isAiGenerated": True, "isDraft": False, "collaborators": []},
            "accountId": account_id,
        }
        return self.create_schedule(payload)