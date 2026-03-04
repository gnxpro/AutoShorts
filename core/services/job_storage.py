import sqlite3
import os
import json
from pathlib import Path


def get_db_path():
    base_dir = os.getenv("LOCALAPPDATA")
    app_dir = os.path.join(base_dir, "GNX_Production")

    os.makedirs(app_dir, exist_ok=True)

    return os.path.join(app_dir, "gnx_jobs.db")


class JobStorage:

    def __init__(self):
        self.db_path = get_db_path()
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            payload TEXT,
            status TEXT,
            progress INTEGER,
            created_at TEXT
        )
        """)

        conn.commit()
        conn.close()

    # ==================================================
    # CRUD
    # ==================================================

    def save_job(self, job):

        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR REPLACE INTO jobs
        (id, payload, status, progress, created_at)
        VALUES (?, ?, ?, ?, ?)
        """, (
            job.id,
            json.dumps(job.payload),
            job.status,
            job.progress,
            job.created_at
        ))

        conn.commit()
        conn.close()

    def update_job(self, job):
        self.save_job(job)

    def load_jobs(self):

        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("SELECT id, payload, status, progress, created_at FROM jobs")
        rows = cursor.fetchall()

        conn.close()

        jobs = []

        for row in rows:
            jobs.append({
                "id": row[0],
                "payload": json.loads(row[1]),
                "status": row[2],
                "progress": row[3],
                "created_at": row[4],
            })

        return jobs