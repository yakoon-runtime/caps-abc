from y5n.sdk import io


async def resolve_topic(topics, ref):
    """Resolve a topic reference (id or name) with explicit errors."""
    if ref.isdigit():
        topic = await topics.get_topic(topic_id=ref)
        if topic is None:
            await io.write(f"Error: Topic '{ref}' not found.")
        return topic
    matches = await topics.get_topics_by_name(name=ref)
    if len(matches) > 1:
        await io.write(f"Topic '{ref}' is ambiguous — use its id.")
        return None
    if not matches:
        await io.write(f"Error: Topic '{ref}' not found.")
        return None
    return matches[0]
