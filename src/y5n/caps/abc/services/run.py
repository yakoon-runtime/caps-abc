from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol

from y5n.runtime.store.event.ports import OnDelete, OnGet, OnReplace

from ..data import RunData
from ..models import Run
from .namespaces import run_key, run_namespace, topic_key


class OnScan(Protocol):
    async def __call__(self, *, namespace) -> list: ...


class RunService:
    """Completed runs.

    A run is written once, when the interactive run is finished, and its
    entries are never edited afterwards. A run can be removed as a whole
    (cleanup, discarded test runs); the service deliberately offers no
    update path.
    """

    def __init__(
        self,
        on_get: OnGet,
        on_replace: OnReplace,
        on_scan: OnScan,
        on_delete: OnDelete,
        on_next_id,
    ):
        self._on_get = on_get
        self._on_replace = on_replace
        self._on_scan = on_scan
        self._on_delete = on_delete
        self._on_next_id = on_next_id

    async def add_run(self, *, topic_id: str, entries: dict[str, list[str]]) -> Run:
        topic_row = await self._on_get(key=topic_key(topic_id))
        if topic_row is None or topic_row.data is None:
            raise ValueError(f"Topic '{topic_id}' not found.")
        clean = {k: list(v) for k, v in entries.items() if v}
        next_id = await self._on_next_id(prefix="r")
        created = datetime.now(UTC).isoformat()
        data = RunData(topic_id=topic_id, created=created, entries=clean)
        await self._on_replace(key=run_key(str(next_id)), doc=data.to_dict())
        return Run(id=str(next_id), topic_id=topic_id, created=created, entries=clean)

    async def list_runs(self, *, topic_id: str | None = None) -> list[Run]:
        runs = await self._all_runs()
        if topic_id is not None:
            runs = [r for r in runs if r.topic_id == topic_id]
        return sorted(runs, key=lambda r: (r.created, r.id))

    async def get_run(self, run_id: str) -> Run | None:
        row = await self._on_get(key=run_key(run_id))
        if row is None or row.data is None:
            return None
        data = RunData.from_dict(row.require_object())
        return Run(
            id=run_id,
            topic_id=data.topic_id,
            created=data.created,
            entries=data.entries,
        )

    async def delete_run(self, run_id: str) -> None:
        run = await self.get_run(run_id)
        if run is None:
            raise ValueError(f"Run '{run_id}' not found.")
        await self._on_delete(key=run_key(run_id))

    async def _all_runs(self) -> list[Run]:
        rows = await self._on_scan(namespace=run_namespace())
        result = []
        for r in rows:
            if r is None:
                continue
            data = RunData.from_dict(r.require_object())
            result.append(
                Run(
                    id=r.key.id,
                    topic_id=data.topic_id,
                    created=data.created,
                    entries=data.entries,
                )
            )
        return result
