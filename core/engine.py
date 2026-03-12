import os
import json
import threading
import traceback
from pathlib import Path
from datetime import datetime, timezone

from core.license_manager import load_effective_capabilities
from core.gnx_pipeline_adapter import run_gnx_job
from core.services.repliz_service import ReplizService

try:
    from core.services.youtube_service import YouTubeService
except Exception:
    YouTubeService = None

try:
    from core.services.cloudinary_service import CloudinaryService
except Exception:
    CloudinaryService = None


class Engine:
    def __init__(self):
        self._worker_thread = None
        self._is_running = False

    def get_capabilities(self) -> dict:
        try:
            caps = load_effective_capabilities() or {}
        except Exception as e:
            print(f"[ENGINE] load_effective_capabilities failed: {e}")
            caps = {}

        effective_plan = str(caps.get("effective_plan") or caps.get("plan") or "BASIC").upper()

        caps.setdefault("plan", effective_plan)
        caps.setdefault("effective_plan", effective_plan)
        caps.setdefault("allow_youtube", True)
        caps.setdefault("allow_ai", True)
        caps.setdefault("allow_schedule", True)
        caps.setdefault("max_social_accounts", 2 if effective_plan == "BASIC" else 100)
        caps.setdefault("max_accounts", caps.get("max_social_accounts"))
        caps.setdefault("daily_video_limit", 2 if effective_plan == "BASIC" else 8)
        caps.setdefault("monthly_video_limit", 60 if effective_plan == "BASIC" else 240)
        caps.setdefault("quality_options", ["480p"])
        caps.setdefault("default_quality", "480p")
        caps.setdefault("binding_valid", True)
        caps.setdefault("blocked_for_social_limit", False)
        caps.setdefault("business_charge_units_this_device", 0)
        return caps

    def _documents_root(self) -> Path:
        env = os.getenv("GNX_OUTPUT_ROOT", "").strip()
        if env:
            p = Path(env)
            p.mkdir(parents=True, exist_ok=True)
            return p

        p = Path.home() / "Documents" / "GNX Production"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _appdata_dir(self) -> Path:
        base = os.getenv("LOCALAPPDATA", "").strip()
        if not base:
            base = str(Path.home() / "AppData" / "Local")
        p = Path(base) / "GNX_PRODUCTION"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _outputs_dir(self) -> Path:
        p = self._documents_root() / "Outputs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _jobs_dir(self) -> Path:
        p = self._documents_root() / "Jobs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _temp_dir(self) -> Path:
        p = self._documents_root() / "Temp"
        p.mkdir(parents=True, exist_ok=True)
        return p

    def _usage_file(self) -> Path:
        return self._jobs_dir() / "usage.json"

    def _latest_file(self) -> Path:
        return self._jobs_dir() / "latest.json"

    def _load_json_config(self, path: Path) -> dict:
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _load_repliz_config(self) -> dict:
        appdata_cfg = self._appdata_dir() / "repliz.json"
        if appdata_cfg.exists():
            return self._load_json_config(appdata_cfg)

        project_cfg = Path("config") / "repliz.json"
        return self._load_json_config(project_cfg)

    def _load_cloudinary_config(self) -> dict:
        appdata_cfg = self._appdata_dir() / "cloudinary.json"
        if appdata_cfg.exists():
            return self._load_json_config(appdata_cfg)

        project_cfg = Path("config") / "cloudinary.json"
        return self._load_json_config(project_cfg)

    def _read_usage_data(self) -> dict:
        path = self._usage_file()
        if not path.exists():
            return {"days": {}}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {"days": {}}

    def _write_usage_data(self, data: dict):
        path = self._usage_file()
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _increment_usage_today(self, count: int = 1):
        data = self._read_usage_data()
        days = data.setdefault("days", {})

        now = datetime.now(timezone.utc)
        today_key = now.strftime("%Y-%m-%d")
        days[today_key] = int(days.get(today_key, 0)) + int(count)

        self._write_usage_data(data)

    def _get_usage_stats(self):
        data = self._read_usage_data()
        days = data.get("days", {})

        now = datetime.now(timezone.utc)
        today_key = now.strftime("%Y-%m-%d")

        daily = int(days.get(today_key, 0))
        rolling_30 = 0

        for day_str, count in days.items():
            try:
                dt = datetime.strptime(day_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                age = (now - dt).days
                if 0 <= age < 30:
                    rolling_30 += int(count)
            except Exception:
                continue

        return daily, rolling_30

    def _check_usage_limits(self):
        caps = self.get_capabilities()
        daily_used, rolling_used = self._get_usage_stats()

        daily_limit = caps.get("daily_video_limit")
        monthly_limit = caps.get("monthly_video_limit")

        if daily_limit is not None and int(daily_used) >= int(daily_limit):
            raise RuntimeError(
                f"Daily limit reached for {caps.get('effective_plan', 'BASIC')}: {daily_used}/{daily_limit}"
            )

        if monthly_limit is not None and int(rolling_used) >= int(monthly_limit):
            raise RuntimeError(
                f"30-day limit reached for {caps.get('effective_plan', 'BASIC')}: {rolling_used}/{monthly_limit}"
            )

        if caps.get("blocked_for_social_limit"):
            raise RuntimeError("Connected social account count exceeds the allowed plan limit.")

    def is_running(self) -> bool:
        return bool(self._is_running)

    def start(self, payload: dict, on_status=None, on_done=None):
        if self._is_running:
            if on_status:
                on_status("[warning] Engine :: A job is already running.")
            if on_done:
                on_done(False)
            return

        self._is_running = True

        t = threading.Thread(
            target=self._run_job,
            args=(payload or {}, on_status, on_done),
            daemon=True,
        )
        self._worker_thread = t
        t.start()

    def _emit(self, on_status, message=None, status_type=None, stage=None, progress=None, persist_dir=None):
        if on_status is None:
            return

        if isinstance(message, dict):
            on_status(message)
            return

        if status_type or stage or progress is not None or persist_dir:
            on_status({
                "type": status_type or "info",
                "stage": stage or "Engine",
                "message": message or "",
                "progress": progress,
                "persist_dir": persist_dir,
            })
        else:
            on_status(message)

    def _plan_log_line(self, caps: dict) -> str:
        quality = ", ".join(caps.get("quality_options", [])) if caps.get("quality_options") else "-"
        return (
            f"[PLAN] {caps.get('effective_plan', caps.get('plan', 'BASIC'))} | "
            f"Daily={caps.get('daily_video_limit')} | "
            f"30Days={caps.get('monthly_video_limit')} | "
            f"Accounts={caps.get('max_accounts')} | "
            f"Quality={quality}"
        )

    def _write_latest_job(self, data: dict):
        self._latest_file().write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def _normalize_payload(self, payload: dict) -> dict:
        p = dict(payload or {})

        p.setdefault("output_dir", str(self._outputs_dir()))
        p.setdefault("temp_dir", str(self._temp_dir()))

        caps = self.get_capabilities()

        if not p.get("quality_profile"):
            p["quality_profile"] = caps.get("default_quality", "480p")
        if not p.get("quality"):
            p["quality"] = p["quality_profile"]

        delivery_options = p.get("delivery_options") or {}
        cloudinary_opts = delivery_options.get("cloudinary") or {}
        repliz_opts = delivery_options.get("repliz") or {}

        p["enable_upload"] = bool(cloudinary_opts.get("enabled", False))
        p["enable_schedule"] = bool(repliz_opts.get("enabled", False))

        p["_engine_caps"] = caps
        return p

    def _make_job_id(self) -> str:
        return datetime.now(timezone.utc).strftime("gnx_%Y%m%d_%H%M%S")

    def _parse_account_ids(self, raw_text: str) -> list[str]:
        result = []
        seen = set()

        for part in str(raw_text or "").split(","):
            acc = part.strip()
            if acc and acc not in seen:
                seen.add(acc)
                result.append(acc)

        return result

    def _build_repliz_service(self) -> ReplizService:
        cfg = self._load_repliz_config()

        base_url = os.getenv("REPLIZ_BASE_URL", "").strip() or str(cfg.get("base", "")).strip()
        access_key = os.getenv("REPLIZ_ACCESS_KEY", "").strip() or str(cfg.get("access_key", "")).strip()
        secret_key = os.getenv("REPLIZ_SECRET_KEY", "").strip() or str(cfg.get("secret_key", "")).strip()

        svc = ReplizService(
            base_url=base_url,
            access_key=access_key,
            secret_key=secret_key,
        )
        return svc

    def _get_repliz_account_ids(self) -> list[str]:
        cfg = self._load_repliz_config()

        raw = os.getenv("REPLIZ_ACCOUNT_ID", "").strip()
        if raw:
            return self._parse_account_ids(raw)

        raw = str(cfg.get("account_id", "") or cfg.get("repliz_primary_account_id", "")).strip()
        return self._parse_account_ids(raw)

    def _build_youtube_service(self):
        if YouTubeService is None:
            raise RuntimeError("YouTubeService is not available.")
        try:
            return YouTubeService()
        except TypeError as e:
            raise RuntimeError(f"YouTubeService constructor mismatch: {e}")

    def _build_cloudinary_service(self):
        if CloudinaryService is None:
            raise RuntimeError("CloudinaryService is not available.")

        cfg = self._load_cloudinary_config()

        cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME", "").strip() or str(cfg.get("cloud_name", "")).strip()
        upload_preset = os.getenv("CLOUDINARY_UPLOAD_PRESET", "").strip() or str(cfg.get("upload_preset", "")).strip()

        if not cloud_name or not upload_preset:
            raise RuntimeError(
                "Cloudinary is not fully configured. Please open Cloudinary page and save your Cloud Name and Upload Preset."
            )

        try:
            return CloudinaryService(
                cloud_name=cloud_name,
                upload_preset=upload_preset,
            )
        except TypeError:
            try:
                return CloudinaryService(cloud_name, upload_preset)
            except TypeError as e:
                raise RuntimeError(f"CloudinaryService constructor mismatch: {e}")

    def _pipeline_event_handler(self, on_status):
        def _handler(event):
            try:
                stage = getattr(event, "stage", None) or getattr(event, "name", None) or "Pipeline"
                message = getattr(event, "message", None) or str(event)
                progress = getattr(event, "progress", None)
                self._emit(
                    on_status,
                    message=message,
                    status_type="info",
                    stage=str(stage),
                    progress=progress,
                )
            except Exception:
                pass
        return _handler

    def _run_job(self, payload: dict, on_status=None, on_done=None):
        success = False
        persist_dir = None

        try:
            caps = self.get_capabilities()
            payload = self._normalize_payload(payload)

            self._emit(on_status, self._plan_log_line(caps))
            self._check_usage_limits()

            self._emit(
                on_status,
                message=(
                    f"Pipeline started | "
                    f"Licensed={caps.get('plan', 'BASIC')} | "
                    f"Runtime={caps.get('effective_plan', 'BASIC')} | "
                    f"Quality={payload.get('quality_profile', '-')}"
                ),
                status_type="info",
                stage="Engine",
                progress=0.01,
            )

            if not caps.get("binding_valid", True):
                self._emit(
                    on_status,
                    message="Repliz binding mismatch detected. Runtime plan is Basic.",
                    status_type="warning",
                    stage="Engine",
                    progress=0.02,
                )

            if caps.get("blocked_for_social_limit"):
                raise RuntimeError("Social account limit exceeded for the active plan.")

            youtube_service = self._build_youtube_service()
            cloudinary_service = self._build_cloudinary_service()
            repliz_service = self._build_repliz_service()
            account_ids = self._get_repliz_account_ids()

            if payload.get("enable_schedule") and not account_ids:
                raise RuntimeError("Repliz account IDs are empty. Select accounts in Repliz page first.")

            import asyncio

            result_ctx = asyncio.run(
                run_gnx_job(
                    payload=payload,
                    job_id=self._make_job_id(),
                    youtube_service=youtube_service,
                    cloudinary_service=cloudinary_service,
                    repliz_service=repliz_service,
                    account_ids=account_ids,
                    variant_account_map=None,
                    event_handler=self._pipeline_event_handler(on_status),
                )
            )

            if isinstance(result_ctx, dict):
                meta = result_ctx.get("meta") or {}
                persist_dir = result_ctx.get("persist_dir") or meta.get("persist_dir")
                uploads = result_ctx.get("uploads") or meta.get("uploads") or []
            else:
                meta = getattr(result_ctx, "meta", {}) or {}
                persist_dir = getattr(result_ctx, "persist_dir", None) or meta.get("persist_dir")
                uploads = getattr(result_ctx, "uploads", None) or meta.get("uploads") or []

            self._emit(
                on_status,
                message="Pipeline finished",
                status_type="success",
                stage="Engine",
                progress=1.0,
                persist_dir=persist_dir,
            )

            produced_count = 1
            if isinstance(uploads, dict) and uploads:
                produced_count = max(1, len([k for k, v in uploads.items() if v]))
            elif isinstance(uploads, list) and uploads:
                produced_count = max(1, len(uploads))

            self._increment_usage_today(produced_count)

            latest_payload = {
                "persist_dir": persist_dir,
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "plan": caps.get("plan", "BASIC"),
                "effective_plan": caps.get("effective_plan", caps.get("plan", "BASIC")),
                "quality_profile": payload.get("quality_profile"),
                "uploads_count": produced_count,
            }
            self._write_latest_job(latest_payload)

            success = True

        except Exception as e:
            traceback.print_exc()
            self._emit(
                on_status,
                message=str(e),
                status_type="error",
                stage="Engine",
                progress=1.0,
                persist_dir=persist_dir,
            )
            success = False

        finally:
            self._is_running = False
            if on_done:
                on_done(success)