import asyncio
import threading
from typing import Any, Dict, List, Optional

from core.services.async_job_controller import AsyncJobController
from core.services.youtube_service import YouTubeService
from core.services.cloudinary_service import CloudinaryService
from core.services.repliz_service import ReplizService

from core.gnx_pipeline_adapter import run_gnx_job
from core.licensing.license_manager import LicenseManager


class Engine:
    def __init__(self):
        self.controller = AsyncJobController()
        self.license = LicenseManager()

        self.default_account_id: Optional[str] = None
        self.selected_account_ids: List[str] = []
        self.variant_account_map: Dict[str, Any] = {}
        self.repliz_schedule_enabled: bool = True

        self.youtube_service = YouTubeService()
        self.cloudinary_service = CloudinaryService()
        self.repliz_service = ReplizService()

        self.status_listeners = []

    # ===== capability for UI =====
    def get_capabilities(self) -> Dict[str, Any]:
        return self.license.get_capabilities()

    # ===== licensing API (if some pages still call it) =====
    def get_license_status(self) -> Dict[str, Any]:
        st = self.license.get_status()
        caps = self.license.get_capabilities()
        return {
            "ok": st.ok,
            "mode": st.mode,
            "plan": st.plan,
            "days_left": st.days_left,
            "expires_at": st.expires_at,
            "max_accounts": caps["max_accounts"],
            "message": st.message,
            "caps": caps,
        }

    def activate_license(self, key: str) -> Dict[str, Any]:
        st = self.license.activate_license(key)
        return {"ok": st.ok, "mode": st.mode, "plan": st.plan, "days_left": st.days_left, "message": st.message}

    def start_trial(self, days: int) -> Dict[str, Any]:
        st = self.license.start_trial(days)
        return {"ok": st.ok, "mode": st.mode, "plan": st.plan, "days_left": st.days_left, "message": st.message}

    # ===== accounts =====
    def set_default_account(self, account_id: Optional[str]):
        self.default_account_id = account_id

    def set_selected_accounts(self, account_ids: List[str]):
        self.selected_account_ids = [a for a in account_ids if a]

    def set_variant_account_map(self, mapping: Dict[str, Any]):
        self.variant_account_map = dict(mapping or {})

    def set_schedule_enabled(self, enabled: bool):
        self.repliz_schedule_enabled = bool(enabled)

    # ===== start job =====
    def start(self, payload, on_status, on_done):
        caps = self.get_capabilities()

        youtube_url = (payload.get("youtube_url") or payload.get("url") or "").strip()
        offline_path = (payload.get("file_path") or payload.get("offline_path") or payload.get("path") or "").strip()

        # ✅ FREE/BASIC: offline only
        if youtube_url and not caps["allow_youtube"]:
            if on_status:
                on_status({"type": "ERROR", "stage": "ResolveSource", "message": "YouTube mode is disabled on this plan. Use Offline Video only."})
            on_done(False)
            return

        # resolve enable schedule (plan-aware)
        enable_schedule = payload.get("enable_schedule")
        if enable_schedule is None:
            enable_schedule = getattr(self, "repliz_schedule_enabled", True)
        enable_schedule = bool(enable_schedule)

        # ✅ plan may disable schedule
        if enable_schedule and not caps["allow_schedule"]:
            enable_schedule = False
            if on_status:
                on_status({"type": "WARN", "stage": "ScheduleRepliz", "message": "Scheduling is disabled on this plan. Skipping schedule."})

        # resolve accounts
        account_ids = payload.get("account_ids") or self.selected_account_ids or []
        if not account_ids and self.default_account_id:
            account_ids = [self.default_account_id]

        # schedule requested but no accounts -> skip (do not fail)
        if enable_schedule and not account_ids:
            enable_schedule = False
            if on_status:
                on_status({"type": "WARN", "stage": "ScheduleRepliz", "message": "Schedule skipped: no Repliz accounts selected."})

        # enforce account limit by plan (FREE/BASIC 5, PRO/TRIAL 100)
        required_accounts = len(account_ids) if enable_schedule else 0
        ok, msg, st = self.license.check_allowed(required_accounts=required_accounts)
        if not ok:
            if on_status:
                on_status({"type": "ERROR", "stage": "ScheduleRepliz", "message": msg})
            on_done(False)
            return

        # AI gating (UI should disable; backend just warns)
        if not caps["allow_ai"] and on_status:
            on_status({"type": "INFO", "stage": "AI", "message": "AI features are disabled on this plan."})

        variant_map = payload.get("variant_account_map") or self.variant_account_map

        payload = dict(payload)
        payload["enable_schedule"] = enable_schedule
        payload["account_ids"] = account_ids
        if variant_map:
            payload["variant_account_map"] = variant_map

        job = self.controller.create_job(payload)

        def run():
            async def async_runner():
                try:
                    async def event_handler(ev):
                        status = {
                            "job_id": getattr(job, "id", None) or getattr(job, "job_id", None),
                            "type": ev.type.value if hasattr(ev.type, "value") else str(ev.type),
                            "stage": ev.stage,
                            "message": ev.message,
                            "progress": (ev.data or {}).get("progress"),
                            "data": ev.data,
                        }
                        if on_status:
                            try:
                                on_status(status)
                            except Exception:
                                pass

                    final_ctx = await run_gnx_job(
                        payload=payload,
                        job_id=getattr(job, "id", None) or None,
                        youtube_service=self.youtube_service,
                        cloudinary_service=self.cloudinary_service,
                        repliz_service=self.repliz_service,
                        account_ids=account_ids,
                        variant_account_map=variant_map,
                        event_handler=event_handler,
                    )

                    if on_status:
                        on_status({
                            "job_id": final_ctx.job_id,
                            "type": "FINAL",
                            "stage": final_ctx.status.stage,
                            "message": final_ctx.status.message,
                            "progress": final_ctx.status.progress,
                            "state": final_ctx.status.state.value,
                            "persist_dir": final_ctx.meta.get("persist_dir"),
                        })

                    on_done(True)
                except Exception as e:
                    if on_status:
                        on_status({"type": "ERROR", "message": str(e)})
                    on_done(False)

            asyncio.run(async_runner())

        threading.Thread(target=run, daemon=True).start()

    def add_status_listener(self, callback):
        self.status_listeners.append(callback)

    def get_jobs(self):
        return list(self.controller.jobs.values())