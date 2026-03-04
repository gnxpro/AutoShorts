import asyncio

from gnx.integration import GNXServiceBundle, run_default_gnx_job, make_print_event_handler
from gnx.models.job_context import JobSettings

# TODO: import service asli kamu
# from core.youtube_service import YouTubeService
# from core.video_processor import VideoProcessor
# from core.cloudinary_service import CloudinaryService
# from core.repliz_service import ReplizService


async def main():
    # TODO: instantiate service asli kamu di sini
    youtube_service = None
    video_processor = None
    cloudinary_service = None
    repliz_service = None

    services = GNXServiceBundle(
        youtube_service=youtube_service,
        video_processor=video_processor,
        cloudinary_service=cloudinary_service,
        repliz_service=repliz_service,
    )

    settings = JobSettings(
        format_mode="both",
        output_dir="outputs",
        temp_dir="temp",
    )

    final_ctx = await run_default_gnx_job(
        source_kind="youtube",  # atau "file"
        source_value="https://youtube.com/watch?v=dQw4w9WgXcQ",
        services=services,
        settings=settings,
        accounts=[{"id": "acc_1", "name": "Main"}],
        event_handler=make_print_event_handler(),
    )

    print("\nFINAL STATUS:")
    print(final_ctx.to_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())