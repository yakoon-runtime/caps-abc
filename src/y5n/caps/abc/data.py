from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CategoryData:
    CURRENT_VERSION = 1
    name: str
    _v: int = field(default=CURRENT_VERSION)

    def to_dict(self) -> dict:
        return {"name": self.name, "_v": self._v}

    @classmethod
    def from_dict(cls, d: dict) -> CategoryData:
        d = dict(d or {})
        return cls(name=d["name"], _v=d.get("_v", 0))


@dataclass
class TopicData:
    CURRENT_VERSION = 1
    category_id: str
    name: str
    _v: int = field(default=CURRENT_VERSION)

    def to_dict(self) -> dict:
        return {"category_id": self.category_id, "name": self.name, "_v": self._v}

    @classmethod
    def from_dict(cls, d: dict) -> TopicData:
        d = dict(d or {})
        return cls(
            category_id=d["category_id"],
            name=d["name"],
            _v=d.get("_v", 0),
        )


@dataclass
class RunData:
    CURRENT_VERSION = 1
    topic_id: str
    created: str
    entries: dict[str, list[str]]
    _v: int = field(default=CURRENT_VERSION)

    def to_dict(self) -> dict:
        return {
            "topic_id": self.topic_id,
            "created": self.created,
            "entries": {k: list(v) for k, v in self.entries.items()},
            "_v": self._v,
        }

    @classmethod
    def from_dict(cls, d: dict) -> RunData:
        d = dict(d or {})
        entries = d.get("entries") or {}
        return cls(
            topic_id=d["topic_id"],
            created=d["created"],
            entries={k: list(v) for k, v in entries.items()},
            _v=d.get("_v", 0),
        )
