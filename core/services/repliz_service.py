import json
import base64
from typing import Any, Dict, Optional, List

import requests


class ReplizAuthError(Exception):
    pass


class ReplizAPIError(Exception):
    pass


class ReplizService:
    def __init__(
        self,
        base_url: str = "",
        access_key: str = "",
        secret_key: str = "",
        timeout: int = 30,
    ):
        self.base_url = (base_url or "").strip().rstrip("/")
        self.access_key = (access_key or "").strip()
        self.secret_key = (secret_key or "").strip()
        self.timeout = timeout

    # =========================================================
    # CONFIG
    # =========================================================

    def set_credentials(self, base_url: str, access_key: str, secret_key: str):
        self.base_url = (base_url or "").strip().rstrip("/")
        self.access_key = (access_key or "").strip()
        self.secret_key = (secret_key or "").strip()

    def is_configured(self) -> bool:
        return bool(self.base_url and self.access_key and self.secret_key)

    def _ensure_configured(self):
        if not self.is_configured():
            raise ReplizAuthError(
                "Repliz is not fully configured. Please fill Base URL, Access Key, and Secret Key."
            )

    def _url(self, path: str) -> str:
        path = (path or "").strip()
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def _headers(self) -> Dict[str, str]:
        token = base64.b64encode(
            f"{self.access_key}:{self.secret_key}".encode("utf-8")
        ).decode("utf-8")

        return {
            "Authorization": f"Basic {token}",
            "accept": "application/json",
            "Content-Type": "application/json",
        }

    # =========================================================
    # RESPONSE HANDLING
    # =========================================================

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
            print(f"[REPLIZ] GET {self._url(path)}")
            r = requests.get(
                self._url(path),
                headers=self._headers(),
                params=params or {},
                timeout=self.timeout,
            )
            return self._handle_response(r)
        except requests.RequestException as e:
            raise ReplizAPIError(str(e))

    def _post(self, path: str, payload: Dict[str, Any]) -> Any:
        self._ensure_configured()
        try:
            print(f"[REPLIZ] POST {self._url(path)}")
            r = requests.post(
                self._url(path),
                headers=self._headers(),
                data=json.dumps(payload or {}),
                timeout=self.timeout,
            )
            return self._handle_response(r)
        except requests.RequestException as e:
            raise ReplizAPIError(str(e))

    # =========================================================
    # BASIC API METHODS
    # =========================================================

    def validate_keys(self) -> bool:
        self.get_social_accounts(limit=1)
        return True

    def get_social_accounts(
        self,
        page: int = 1,
        limit: int = 50,
        search: str = "",
    ) -> Any:
        params: Dict[str, Any] = {"page": page, "limit": limit}
        if search:
            params["search"] = search
        return self._get("/account", params=params)

    def get_account(self, account_id: str) -> Any:
        return self._get(f"/account/{account_id}")

    def get_schedules(
        self,
        page: int = 1,
        limit: int = 10,
        account_ids: Optional[List[str]] = None,
    ) -> Any:
        params: Dict[str, Any] = {"page": page, "limit": limit}
        if account_ids:
            params["accountIds"] = account_ids
        return self._get("/schedule", params=params)

    def create_schedule(self, payload: Dict[str, Any]) -> Any:
        return self._post("/schedule", payload)

    def schedule(self, payload: Dict[str, Any]) -> Any:
        return self.create_schedule(payload)

    # =========================================================
    # LICENSE / PLAN VALIDATION HELPERS
    # =========================================================

    def _extract_accounts_list(self, data: Any) -> List[Dict[str, Any]]:
        if isinstance(data, dict):
            docs = data.get("docs")
            if isinstance(docs, list):
                return docs
        if isinstance(data, list):
            return data
        return []

    def _first_non_empty(self, *values):
        for value in values:
            if value is None:
                continue
            text = str(value).strip()
            if text:
                return text
        return None

    def get_social_accounts_summary(
        self,
        limit: int = 200,
        search: str = "",
    ) -> Dict[str, Any]:
        """
        Returns a normalized summary used by:
        - license validation
        - plan binding
        - UI account summary

        Output:
        {
            "repliz_user_id": "...",
            "repliz_primary_account_id": "...",
            "social_count": 17,
            "accounts": [...]
        }
        """
        data = self.get_social_accounts(page=1, limit=limit, search=search)
        accounts = self._extract_accounts_list(data)

        repliz_user_id = None
        primary_account_id = None

        if accounts:
            first = accounts[0] or {}

            repliz_user_id = self._first_non_empty(
                first.get("userId"),
                first.get("user_id"),
                first.get("ownerId"),
            )

            primary_account_id = self._first_non_empty(
                first.get("accountId"),
                first.get("_id"),
                first.get("id"),
            )

        # fallback scan if first row incomplete
        if repliz_user_id is None:
            for acc in accounts:
                repliz_user_id = self._first_non_empty(
                    acc.get("userId"),
                    acc.get("user_id"),
                    acc.get("ownerId"),
                )
                if repliz_user_id:
                    break

        if primary_account_id is None:
            for acc in accounts:
                primary_account_id = self._first_non_empty(
                    acc.get("accountId"),
                    acc.get("_id"),
                    acc.get("id"),
                )
                if primary_account_id:
                    break

        summary = {
            "repliz_user_id": repliz_user_id,
            "repliz_primary_account_id": primary_account_id,
            "social_count": len(accounts),
            "accounts": accounts,
        }

        print(
            "[REPLIZ] summary | "
            f"user_id={summary['repliz_user_id']} | "
            f"primary_account_id={summary['repliz_primary_account_id']} | "
            f"social_count={summary['social_count']}"
        )

        return summary

    def get_repliz_identity(self) -> Dict[str, Any]:
        """
        Short helper for binding checks.
        """
        summary = self.get_social_accounts_summary(limit=200)
        return {
            "repliz_user_id": summary.get("repliz_user_id"),
            "repliz_primary_account_id": summary.get("repliz_primary_account_id"),
            "social_count": summary.get("social_count", 0),
        }

    # =========================================================
    # SCHEDULING HELPERS
    # =========================================================

    def build_video_schedule_payload(
        self,
        account_id: str,
        media_url: str,
        schedule_at_iso: str,
        title: str = "",
        description: str = "",
        thumbnail_url: str = "",
    ) -> Dict[str, Any]:
        medias = [
            {
                "type": "video",
                "url": media_url,
                "thumbnail": thumbnail_url or "",
            }
        ]

        return {
            "title": title or "",
            "description": description or "",
            "type": "video",
            "medias": medias,
            "scheduleAt": schedule_at_iso,
            "accountId": account_id,
        }

    def schedule_video(
        self,
        account_id: str,
        media_url: str,
        schedule_at_iso: str,
        title: str = "",
        description: str = "",
        thumbnail_url: str = "",
    ) -> Any:
        payload = self.build_video_schedule_payload(
            account_id=account_id,
            media_url=media_url,
            schedule_at_iso=schedule_at_iso,
            title=title,
            description=description,
            thumbnail_url=thumbnail_url,
        )
        return self.create_schedule(payload)