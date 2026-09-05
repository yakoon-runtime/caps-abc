from dataclasses import dataclass


@dataclass
class Topic:
    id: str
    category_id: str
    name: str
