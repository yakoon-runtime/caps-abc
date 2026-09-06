from y5n.sdk import context, io, ports

from ..topics import resolve_topic


async def main():
    ref = context.request().arg(0)

    topics = ports.get("abc.topic.service")
    categories = ports.get("abc.category.service")

    topic = await resolve_topic(topics, categories, ref)
    if topic is None:
        return

    try:
        await topics.delete_topic(topic_id=topic.id)
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Topic '{topic.name}' deleted.")
