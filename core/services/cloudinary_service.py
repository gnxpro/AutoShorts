import os
from pathlib import Path
from typing import Optional, Dict, Any

import requests


class CloudinaryServiceError(Exception):
    pass


class CloudinaryService:
    def __init__(
        self,
        cloud_name: str,
        upload_preset: str,
        folder: Optional[str] = None,
        secure_delivery: bool = True,
        timeout: int = 120,
    ):
        self.cloud_name = str(cloud_name or "").strip()
        self.upload_preset = str(upload_preset or "").strip()
        self.folder = str(folder or os.getenv("CLOUDINARY_FOLDER", "")).strip()
        self.secure_delivery = bool(secure_delivery)
        self.timeout = int(timeout)

        if not self.cloud_name:
            raise CloudinaryServiceError("Cloudinary cloud_name is required.")
        if not self.upload_preset:
            raise CloudinaryServiceError("Cloudinary upload_preset is required.")

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    def _upload_url(self) -> str:
        return f"https://api.cloudinary.com/v1_1/{self.cloud_name}/video/upload"

    def _normalize_result(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        secure_url = str(payload.get("secure_url") or "").strip()
        url = str(payload.get("url") or "").strip()
        public_id = str(payload.get("public_id") or "").strip()
        resource_type = str(payload.get("resource_type") or "").strip()
        original_filename = str(payload.get("original_filename") or "").strip()
        bytes_size = payload.get("bytes")

        final_url = secure_url if self.secure_delivery and secure_url else (secure_url or url)

        return {
            "url": final_url,
            "secure_url": secure_url,
            "public_id": public_id,
            "resource_type": resource_type,
            "original_filename": original_filename,
            "bytes": bytes_size,
            "raw": payload,
        }

    def _validate_file(self, file_path: str) -> Path:
        p = Path(file_path)
        if not p.exists() or not p.is_file():
            raise CloudinaryServiceError(f"File not found: {file_path}")
        if p.stat().st_size < 1024:
            raise CloudinaryServiceError(f"File is too small or invalid: {file_path}")
        return p

    # ---------------------------------------------------------
    # Public upload API
    # ---------------------------------------------------------

    def upload(
        self,
        file_path: str,
        variant: Optional[str] = None,
        ctx: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        file_obj = self._validate_file(file_path)

        data = {
            "upload_preset": self.upload_preset,
        }

        folder_value = self.folder
        if not folder_value and metadata and isinstance(metadata, dict):
            folder_value = str(metadata.get("folder", "")).strip()

        if folder_value:
            data["folder"] = folder_value

        public_id = ""
        try:
            if ctx is not None:
                job_id = str(getattr(ctx, "job_id", "") or "").strip()
                if job_id:
                    stem = file_obj.stem
                    suffix = str(variant or "").strip()
                    public_id = f"{job_id}_{stem}"
                    if suffix:
                        public_id += f"__{suffix}"
        except Exception:
            public_id = ""

        if public_id:
            data["public_id"] = public_id

        if metadata and isinstance(metadata, dict):
            tags = metadata.get("tags")
            if isinstance(tags, list) and tags:
                data["tags"] = ",".join([str(x).strip() for x in tags if str(x).strip()])

            context_parts = []
            for key in ("title", "source", "variant"):
                value = metadata.get(key)
                if value:
                    context_parts.append(f"{key}={value}")
            if context_parts:
                data["context"] = "|".join(context_parts)

        with file_obj.open("rb") as f:
            files = {
                "file": (file_obj.name, f, "video/mp4")
            }

            try:
                r = requests.post(
                    self._upload_url(),
                    data=data,
                    files=files,
                    timeout=self.timeout,
                )
            except requests.RequestException as e:
                raise CloudinaryServiceError(f"Cloudinary request failed: {e}")

        try:
            payload = r.json()
        except Exception:
            payload = None

        if r.status_code >= 400:
            if isinstance(payload, dict):
                err = payload.get("error") or {}
                msg = err.get("message") or r.text
            else:
                msg = r.text
            raise CloudinaryServiceError(msg or f"Cloudinary upload failed with HTTP {r.status_code}")

        if not isinstance(payload, dict):
            raise CloudinaryServiceError("Cloudinary upload returned an invalid response.")

        final = self._normalize_result(payload)

        if not final.get("url"):
            raise CloudinaryServiceError("Cloudinary upload succeeded but no URL was returned.")

        return final

    # Compatibility aliases
    def upload_video(
        self,
        file_path: str,
        variant: Optional[str] = None,
        ctx: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.upload(file_path=file_path, variant=variant, ctx=ctx, metadata=metadata)

    def upload_file(
        self,
        file_path: str,
        variant: Optional[str] = None,
        ctx: Any = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return self.upload(file_path=file_path, variant=variant, ctx=ctx, metadata=metadata)