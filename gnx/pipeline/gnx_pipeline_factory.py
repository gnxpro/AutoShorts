from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from gnx.pipeline.runner import PipelineRunner, PipelineRunnerConfig
from gnx.pipeline.stages.gnx_default_stages import (
    ResolveSourceStage,
    ProcessVideoStage,
    UploadCloudinaryStage,
    ScheduleReplizStage,
)
from gnx.pipeline.stages.persist_context_stage import PersistContextStage


@dataclass
class DefaultPipelineOptions:
    include_schedule: bool = True
    include_persist: bool = True


def build_default_gnx_runner(
    *,
    event_handler=None,
    config: Optional[PipelineRunnerConfig] = None,
    options: Optional[DefaultPipelineOptions] = None,
) -> PipelineRunner:
    """
    Default GNX pipeline:
      ResolveSource -> ProcessVideo -> UploadCloudinary -> (optional) ScheduleRepliz -> (optional) PersistContext
    """
    if config is None:
        config = PipelineRunnerConfig()
    if options is None:
        options = DefaultPipelineOptions()

    stages = [
        ResolveSourceStage(),
        ProcessVideoStage(),
        UploadCloudinaryStage(),
    ]

    if options.include_schedule:
        stages.append(ScheduleReplizStage())

    if options.include_persist:
        stages.append(PersistContextStage())

    return PipelineRunner(stages=stages, config=config, event_handler=event_handler)