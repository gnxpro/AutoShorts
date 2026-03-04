import asyncio

from gnx.models.job_context import JobContext, JobSource, JobSettings
from gnx.pipeline.runner import PipelineRunner
from gnx.pipeline.stages.base import FunctionStage
from gnx.pipeline.events import PipelineEvent


async def print_event(ev: PipelineEvent):
    # Simple logger untuk lihat progress
    stage = ev.stage or "-"
    print(f"[{ev.type}] job={ev.job_id} stage={stage} msg={ev.message} data={ev.data}")


async def stage_a(ctx: JobContext) -> JobContext:
    # simulasi kerja
    await asyncio.sleep(0.2)
    ctx.artifacts.raw_video_path = "temp/input.mp4"
    return ctx


async def stage_b(ctx: JobContext) -> JobContext:
    await asyncio.sleep(0.2)
    ctx.artifacts.processed_variants["portrait"] = "outputs/portrait.mp4"
    ctx.artifacts.processed_variants["landscape"] = "outputs/landscape.mp4"
    return ctx


def should_run_stage_b(ctx: JobContext) -> bool:
    # contoh idempotent: kalau sudah ada output, skip
    return not bool(ctx.artifacts.processed_variants)


async def main():
    ctx = JobContext(
        source=JobSource(kind="file", value="videos/sample.mp4"),
        settings=JobSettings(format_mode="both", enable_subtitles=False),
    )

    runner = PipelineRunner(
        stages=[
            FunctionStage(name="LoadSource", fn=stage_a),
            FunctionStage(name="ProcessVideo", fn=stage_b, should_run_fn=should_run_stage_b),
        ],
        event_handler=print_event,
    )

    ctx = await runner.run(ctx)
    print("\nFINAL STATUS:")
    print(ctx.to_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())