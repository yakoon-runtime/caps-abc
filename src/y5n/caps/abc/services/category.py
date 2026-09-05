from __future__ import annotations

from typing import Protocol

from y5n.runtime.store.event.ports import OnDelete, OnGet, OnReplace

from ..data import CategoryData
from ..models import Category
from .namespaces import category_key, category_namespace
from .topic import TopicService


class OnScan(Protocol):
    async def __call__(self, *, namespace) -> list: ...


class CategoryService:
    def __init__(
        self,
        topics: TopicService,
        on_get: OnGet,
        on_replace: OnReplace,
        on_scan: OnScan,
        on_delete: OnDelete,
        on_next_id,
    ):
        self._topics = topics
        self._on_get = on_get
        self._on_replace = on_replace
        self._on_scan = on_scan
        self._on_delete = on_delete
        self._on_next_id = on_next_id

    async def list_categories(self) -> list[Category]:
        rows = await self._on_scan(namespace=category_namespace())
        return [self._to_category(r) for r in rows if r is not None]

    async def add_category(self, *, name: str) -> Category:
        if await self.get_category_by_name(name):
            raise ValueError(f"Category '{name}' already exists.")
        next_id = await self._on_next_id(prefix="c")
        data = CategoryData(name=name)
        await self._on_replace(key=category_key(str(next_id)), doc=data.to_dict())
        return Category(id=str(next_id), name=name)

    async def get_category(self, category_id: str) -> Category | None:
        row = await self._on_get(key=category_key(category_id))
        if row is None or row.data is None:
            return None
        data = CategoryData.from_dict(row.require_object())
        return Category(id=category_id, name=data.name)

    async def get_category_by_name(self, name: str) -> Category | None:
        for c in await self.list_categories():
            if c.name.lower() == name.lower():
                return c
        return None

    async def find_categories(self, text: str) -> list[Category]:
        needle = text.lower()
        return [c for c in await self.list_categories() if needle in c.name.lower()]

    async def update_category(self, *, category_id: str, name: str | None) -> Category:
        category = await self.get_category(category_id)
        if category is None:
            raise ValueError(f"Category '{category_id}' not found.")
        new_name = name if name is not None else category.name
        if new_name.lower() != category.name.lower():
            existing = await self.get_category_by_name(new_name)
            if existing and existing.id != category_id:
                raise ValueError(f"Category '{new_name}' already exists.")
        data = CategoryData(name=new_name)
        await self._on_replace(key=category_key(category_id), doc=data.to_dict())
        return Category(id=category_id, name=new_name)

    async def delete_category(self, category_id: str) -> None:
        category = await self.get_category(category_id)
        if category is None:
            raise ValueError(f"Category '{category_id}' not found.")
        if await self._topics.list_topics(category_id=category_id):
            raise ValueError(f"Category '{category.name}' still contains topics.")
        await self._on_delete(key=category_key(category_id))

    def _to_category(self, row) -> Category:
        data = CategoryData.from_dict(row.require_object())
        return Category(id=row.key.id, name=data.name)
