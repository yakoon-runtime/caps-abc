from dataclasses import dataclass, field


@dataclass
class Run:
    id: str
    topic_id: str
    created: str
    entries: dict[str, list[str]] = field(default_factory=dict)
