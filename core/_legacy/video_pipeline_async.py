print("PIPELINE STARTED", job.payload)
import asyncio
import os
import uuid
import subprocess
from datetime import datetime, timezone
from yt_dlp import YoutubeDL


class AsyncVideoPipeline:

    def __init__(self, youtube_utils, cloudinary_service, repliz_service):
        self.youtube_utils = youtube_utils
        self.cloudinary_service = cloudinary_service
        self.repliz_service = repliz_service

    async def process_job(self, job, account):

        url = job.payload.get("url")
        offline_path = job.payload.get("offline_path")
        schedule_time = job.payload.get("schedule_time")
        account_id = account.repliz_account_id

        if not account_id:
            raise Exception("No account_id provided")

        # STEP 1
        job.progress = 10

        if url:
            video_path = await self._download_youtube(url)
        elif offline_path:
            video_path = offline_path
        else:
            raise Exception("No source provided")

        job.progress = 40

        # STEP 2 Upload
        uploaded_url = await self.cloudinary_service.upload_video(video_path)

        job.progress = 70

        # STEP 3 Schedule
        schedule_iso = self._to_iso(schedule_time)

        await self.repliz_service.schedule_video(
            account_id=account_id,
            video_url=uploaded_url,
            title="Auto Generated Title",
            description="Auto Generated Description",
            schedule_time_iso=schedule_iso,
        )

        job.progress = 100

    async def _download_youtube(self, url):

        loop = asyncio.get_event_loop()

        return await loop.run_in_executor(
            None,
            self._sync_download,
            url
        )

    def _sync_download(self, url):

        output_dir = os.path.join(os.getcwd(), "temp_downloads")
        os.makedirs(output_dir, exist_ok=True)

        filename = f"{uuid.uuid4()}.mp4"
        output_path = os.path.join(output_dir, filename)

        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": output_path,
            "merge_output_format": "mp4",
            "quiet": True,
        }

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return output_path

    def _to_iso(self, schedule_time_str):
        dt = datetime.strptime(schedule_time_str, "%Y-%m-%d %H:%M:%S")
        dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat().replace("+00:00", "Z")