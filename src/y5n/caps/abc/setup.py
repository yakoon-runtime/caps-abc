from __future__ import annotations

from y5n.runtime.store.event.models import IndexKey, IndexSpec, IndexTerm, ValueType
from y5n.sdk import ports, store

from .services import (
    CategoryService,
    RunService,
    TopicService,
    category_namespace,
    run_namespace,
    topic_namespace,
)


async def main():

    db = store.get("abc")

    INDEX_ALL = IndexSpec(key=IndexKey("all"), value_type=ValueType.TEXT, unique=False)

    for ns in [category_namespace(), topic_namespace(), run_namespace()]:
        await db.ensure_indexes(namespace=ns, specs=[INDEX_ALL])

    async def _scan(namespace):
        keys, _ = await db.scan(
            namespace=namespace, index_key=IndexKey("all"), value="1"
        )
        return await db.get_many(keys=keys)

    async def _replace(*, key, doc, indexes=(), snapshot_hint=None, expected_rev=None):
        idx = list(indexes) + [IndexTerm(key=IndexKey("all"), value="1")]
        return await db.replace(key=key, doc=doc, indexes=idx)

    runs = RunService(
        on_get=db.get,
        on_replace=_replace,
        on_scan=_scan,
        on_next_id=db.next_id,
    )
    topics = TopicService(
        runs=runs,
        on_get=db.get,
        on_replace=_replace,
        on_scan=_scan,
        on_delete=db.delete,
        on_next_id=db.next_id,
    )
    categories = CategoryService(
        topics=topics,
        on_get=db.get,
        on_replace=_replace,
        on_scan=_scan,
        on_delete=db.delete,
        on_next_id=db.next_id,
    )

    ports.publish("abc.run.service", runs)
    ports.publish("abc.topic.service", topics)
    ports.publish("abc.category.service", categories)
