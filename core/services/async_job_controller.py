import uuid
import asyncio
from datetime import datetime
from core.services.job_storage import JobStorage


class Job:

    def __init__(self, payload):
        self.id = str(uuid.uuid4())
        self.payload = payload
        self.status = "PENDING"
        self.progress = 0
        self.created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


class AsyncAccount:

    def __init__(self, name, repliz_account_id, max_concurrent_jobs=1):
        self.name = name
        self.repliz_account_id = repliz_account_id
        self.max_concurrent_jobs = max_concurrent_jobs


class AsyncJobController:

    def __init__(self):
        self.jobs = {}
        self.accounts = []
        self.storage = JobStorage()
        self._load_existing_jobs()

    def _load_existing_jobs(self):

        saved_jobs = self.storage.load_jobs()

        for data in saved_jobs:
            job = Job(data["payload"])
            job.id = data["id"]
            job.status = data["status"]
            job.progress = data["progress"]
            job.created_at = data["created_at"]

            self.jobs[job.id] = job

        print(f"Loaded {len(self.jobs)} existing jobs from DB")

    # ==================================================
    # JOB API
    # ==================================================

    def create_job(self, payload):
        job = Job(payload)
        self.jobs[job.id] = job
        self.storage.save_job(job)
        return job

    def get_job(self, job_id):
        return self.jobs.get(job_id)

    def clear_accounts(self):
        self.accounts = []

    def register_account(self, account):
        self.accounts.append(account)

    # ==================================================
    # RUN
    # ==================================================

    async def run_batch(self, worker_func):

        for job in list(self.jobs.values()):
            if job.status == "PENDING":
                await self._run_single_job(job, worker_func)

    async def _run_single_job(self, job, worker_func):

        if not self.accounts:
            job.status = "FAILED"
            self.storage.update_job(job)
            return

        account = self.accounts[0]

        job.status = "RUNNING"
        self.storage.update_job(job)

        try:
            await worker_func(job, account)
            job.status = "DONE"
        except Exception as e:
            print("JOB ERROR:", e)
            job.status = "FAILED"

        self.storage.update_job(job)