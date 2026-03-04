import asyncio
import sys
from pathlib import Path

# ------------------------------------------------------------
# FIX untuk run sebagai file langsung (python gnx\scripts\....py)
# Menambahkan root project (AutoShorts) ke sys.path.
# ------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[2]  # .../AutoShorts
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from gnx.models.job_context import JobContext, JobSource, JobSettings
from gnx.pipeline.events import PipelineEvent
from gnx.pipeline.gnx_pipeline_factory import build_default_gnx_runner


async def print_event(ev: PipelineEvent):
    stage = ev.stage or "-"
    print(f"[{ev.type}] stage={stage} msg={ev.message} data={ev.data}")


# -------------------------
# DUMMY SERVICES (GANTI INI)
# -------------------------
async def dummy_download_fn(url: str, temp_dir: str, ctx: JobContext) -> str:
    Path(temp_dir).mkdir(parents=True, exist_ok=True)
    out = Path(temp_dir) / "downloaded.mp4"
    out.write_bytes(b"fake")  # demo only
    return str(out)


async def dummy_process_fn(input_path: str, format_mode: str, output_dir: str, temp_dir: str, ctx: JobContext):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    out_portrait = Path(output_dir) / "portrait.mp4"
    out_landscape = Path(output_dir) / "landscape.mp4"
    out_portrait.write_bytes(b"fake")
    out_landscape.write_bytes(b"fake")
    if format_mode == "portrait":
        return {"portrait": str(out_portrait)}
    if format_mode == "landscape":
        return {"landscape": str(out_landscape)}
    return {"portrait": str(out_portrait), "landscape": str(out_landscape)}


async def dummy_upload_fn(file_path: str, variant: str, ctx: JobContext):
    return {"url": f"https://cloudinary.example/{ctx.job_id}/{variant}.mp4", "file_path": file_path}


async def dummy_schedule_fn(uploads, accounts, ctx: JobContext):
    return {"scheduled": True, "uploads": uploads, "accounts": accounts}


async def main():
    ctx = JobContext(
        source=JobSource(kind="youtube", value="https://youtube.com/watch?v=dQw4w9WgXcQ"),
        settings=JobSettings(format_mode="both", output_dir="outputs", temp_dir="temp"),
    )

    # Inject services (INI KUNCI INTEGRASI)
    ctx.services["download_fn"] = dummy_download_fn
    ctx.services["process_fn"] = dummy_process_fn
    ctx.services["upload_fn"] = dummy_upload_fn
    ctx.services["schedule_fn"] = dummy_schedule_fn

    # optional accounts
    ctx.meta["accounts"] = [{"id": "acc_1", "name": "Main"}]

    runner = build_default_gnx_runner(event_handler=print_event)

    final_ctx = await runner.run(ctx)
    print("\nFINAL:")
    print(final_ctx.to_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())