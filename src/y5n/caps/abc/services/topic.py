from __future__ import annotations

from typing import Protocol

from y5n.runtime.store.event.ports import OnDelete, OnGet, OnReplace

from ..data import TopicData
from ..models import Topic
from .namespaces import category_key, topic_key, topic_namespace
from .run import RunService


class OnScan(Protocol):
    async def __call__(self, *, namespace) -> list: ...


class TopicService:
    def __init__(
        self,
        runs: RunService,
        on_get: OnGet,
        on_replace: OnReplace,
        on_scan: OnScan,
        on_delete: OnDelete,
        on_next_id,
    ):
        self._runs = runs
        self._on_get = on_get
        self._on_replace = on_replace
        self._on_scan = on_scan
        self._on_delete = on_delete
        self._on_next_id = on_next_id

    async def list_topics(self, *, category_id: str | None = None) -> list[Topic]:
        topics = await self._all_topics()
        if category_id is None:
            return topics
        return [t for t in topics if t.category_id == category_id]

    async def add_topic(self, *, category_id: str, name: str) -> Topic:
        category_row = await self._on_get(key=category_key(category_id))
        if category_row is None or category_row.data is None:
            raise ValueError(f"Category '{category_id}' not found.")
        for topic in await self.list_topics(category_id=category_id):
            if topic.name.lower() == name.lower():
                raise ValueError(f"Topic '{name}' already exists.")
        next_id = await self._on_next_id(prefix="t")
        data = TopicData(category_id=category_id, name=name)
        await self._on_replace(key=topic_key(str(next_id)), doc=data.to_dict())
        return Topic(id=str(next_id), category_id=category_id, name=name)

    async def get_topic(self, topic_id: str) -> Topic | None:
        row = await self._on_get(key=topic_key(topic_id))
        if row is None or row.data is None:
            return None
        data = TopicData.from_dict(row.require_object())
        return Topic(
            id=topic_id,
            category_id=data.category_id,
            name=data.name,
        )

    async def get_topics_by_name(self, name: str) -> list[Topic]:
        return [t for t in await self._all_topics() if t.name.lower() == name.lower()]

    async def find_topics(self, text: str) -> list[Topic]:
        needle = text.lower()
        return [t for t in await self._all_topics() if needle in t.name.lower()]

    async def update_topic(self, *, topic_id: str, name: str | None) -> Topic:
        topic = await self.get_topic(topic_id)
        if topic is None:
            raise ValueError(f"Topic '{topic_id}' not found.")
        new_name = name if name is not None else topic.name
        if new_name.lower() != topic.name.lower():
            for other in await self.list_topics(category_id=topic.category_id):
                if other.id != topic_id and other.name.lower() == new_name.lower():
                    raise ValueError(f"Topic '{new_name}' already exists.")
        data = TopicData(category_id=topic.category_id, name=new_name)
        await self._on_replace(key=topic_key(topic_id), doc=data.to_dict())
        return Topic(id=topic_id, category_id=topic.category_id, name=new_name)

    async def delete_topic(self, topic_id: str) -> None:
        topic = await self.get_topic(topic_id)
        if topic is None:
            raise ValueError(f"Topic '{topic_id}' not found.")
        if await self._runs.list_runs(topic_id=topic_id):
            raise ValueError(f"Topic '{topic.name}' still contains runs.")
        await self._on_delete(key=topic_key(topic_id))

    async def _all_topics(self) -> list[Topic]:
        rows = await self._on_scan(namespace=topic_namespace())
        result = []
        for r in rows:
            if r is None:
                continue
            data = TopicData.from_dict(r.require_object())
            result.append(
                Topic(
                    id=r.key.id,
                    category_id=data.category_id,
                    name=data.name,
                )
            )
        return result
