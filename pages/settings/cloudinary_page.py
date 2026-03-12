import base64
import json
from typing import Any, Dict, Optional

import requests


class ReplizAuthError(Exception):
    pass


class ReplizAPIError(Exception):
    pass


class ReplizService:
    def __init__(
        self,
        base_url: str = "",
        username: str = "",
        password: str = "",
        timeout: int = 30,
    ):
        self.base_url = (base_url or "").strip().rstrip("/")
        self.username = (username or "").strip()
        self.password = (password or "").strip()
        self.timeout = timeout

    # ---------------------------------------------------------
    # Credentials
    # ---------------------------------------------------------
    def set_credentials(self, base_url: str, username: str, password: str):
        self.base_url = (base_url or "").strip().rstrip("/")
        self.username = (username or "").strip()
        self.password = (password or "").strip()

    def is_configured(self) -> bool:
        return bool(self.base_url and self.username and self.password)

    def _ensure_configured(self):
        if not self.is_configured():
            raise ReplizAuthError("Repliz belum dikonfigurasi lengkap. Isi Base URL, Username, dan Password.")

    # ---------------------------------------------------------
    # HTTP helpers
    # ---------------------------------------------------------
    def _auth_header(self) -> Dict[str, str]:
        self._ensure_configured()
        token = base64.b64encode(f"{self.username}:{self.password}".encode("utf-8")).decode("utf-8")
        return {
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        path = (path or "").strip()
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def _handle_response(self, response: requests.Response) -> Any:
        text = response.text or ""

        try:
            data = response.json()
        except Exception:
            data = None

        if response.status_code in (401, 403):
            msg = "Unauthorized"
            if isinstance(data, dict):
                msg = data.get("message") or data.get("error") or msg
            raise ReplizAuthError(msg)

        if response.status_code >= 400:
            msg = f"HTTP {response.status_code}"
            if isinstance(data, dict):
                msg = data.get("message") or data.get("error") or msg
            elif text:
                msg = text[:300]
            raise ReplizAPIError(msg)

        return data if data is not None else text

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        self._ensure_configured()
        try:
            r = requests.get(
                self._url(path),
                headers=self._auth_header(),
                params=params or {},
                timeout=self.timeout,
            )
            return self._handle_response(r)
        except requests.RequestException as e:
            raise ReplizAPIError(str(e))

    def _post(self, path: str, payload: Dict[str, Any]) -> Any:
        self._ensure_configured()
        try:
            r = requests.post(
                self._url(path),
                headers=self._auth_header(),
                data=json.dumps(payload),
                timeout=self.timeout,
            )
            return self._handle_response(r)
        except requests.RequestException as e:
            raise ReplizAPIError(str(e))

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def validate_keys(self) -> bool:
        """
        Test basic auth against a lightweight endpoint.
        """
        # Umumnya daftar social accounts cukup aman untuk validasi
        self.get_social_accounts(limit=1)
        return True

    def get_social_accounts(self, page: int = 1, limit: int = 50) -> Any:
        """
        Fetch connected social accounts.
        Sesuaikan endpoint jika instance Repliz kamu beda.
        """
        candidates = [
            "/social-accounts",
            "/socialAccounts",
            "/accounts/social",
            "/accounts",
        ]

        last_error = None
        for path in candidates:
            try:
                return self._get(path, params={"page": page, "limit": limit})
            except Exception as e:
                last_error = e

        if last_error:
            raise last_error
        raise ReplizAPIError("Gagal mengambil social accounts.")

    def create_schedule(self, payload: Dict[str, Any]) -> Any:
        """
        Create schedule / publish job.
        """
        candidates = [
            "/queue",
            "/queues",
            "/schedule",
            "/schedules",
            "/posts/schedule",
        ]

        last_error = None
        for path in candidates:
            try:
                return self._post(path, payload)
            except Exception as e:
                last_error = e

        if last_error:
            raise last_error
        raise ReplizAPIError("Gagal membuat schedule.")

    def schedule(self, payload: Dict[str, Any]) -> Any:
        return self.create_schedule(payload)