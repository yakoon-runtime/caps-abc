from y5n.runtime.api.naming import Key, Namespace


def category_key(category_id: str) -> Key:
    return Key.from_parts("abc", "category", "global", category_id)


def topic_key(topic_id: str) -> Key:
    return Key.from_parts("abc", "topic", "global", topic_id)


def category_namespace() -> Namespace:
    return Namespace("abc", "category", "global")


def topic_namespace() -> Namespace:
    return Namespace("abc", "topic", "global")
