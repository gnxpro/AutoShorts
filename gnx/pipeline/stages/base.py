from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional, Protocol, Union

from gnx.models.job_context import JobContext


class StageSkip(Exception):
    """
    Stage boleh raise ini kalau ingin skip (misal: artifact sudah ada).
    """
    pass


class StageError(Exception):
    """
    Stage error yang lebih “terstruktur”.
    """
    pass


class Stage(Protocol):
    """
    Interface stage minimal.
    """
    name: str

    async def run(self, ctx: JobContext) -> JobContext:
        ...

    def should_run(self, ctx: JobContext) -> bool:
        ...


@dataclass
class BaseStage:
    """
    Base class yang enak untuk diturunkan.
    """
    name: str

    def should_run(self, ctx: JobContext) -> bool:
        return True

    async def run(self, ctx: JobContext) -> JobContext:
        raise NotImplementedError("Stage.run() belum diimplementasikan")

    async def _call(self, ctx: JobContext) -> JobContext:
        """
        Wrapper internal untuk memastikan stage punya kesempatan bikin folder.
        """
        ctx.ensure_dirs()
        return await self.run(ctx)


AsyncOrSyncCallable = Union[
    Callable[[JobContext], JobContext],
    Callable[[JobContext], Awaitable[JobContext]],
]


@dataclass
class FunctionStage(BaseStage):
    """
    Stage cepat: bungkus function (sync/async).
    Cocok buat adaptasi service yang sudah ada tanpa bikin class baru.
    """
    fn: AsyncOrSyncCallable = lambda ctx: ctx
    should_run_fn: Optional[Callable[[JobContext], bool]] = None

    def should_run(self, ctx: JobContext) -> bool:
        if self.should_run_fn is None:
            return True
        return bool(self.should_run_fn(ctx))

    async def run(self, ctx: JobContext) -> JobContext:
        res = self.fn(ctx)
        if asyncio.iscoroutine(res):
            return await res  # type: ignore[return-value]
        return res  # type: ignore[return-value]