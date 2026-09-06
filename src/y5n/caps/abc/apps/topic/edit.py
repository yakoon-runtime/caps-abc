from y5n.sdk import context, io, ports

from ..topics import resolve_topic


async def main():
    ref = context.request().arg(0)
    new_name = context.request().option("new-name")

    topics = ports.get("abc.topic.service")
    categories = ports.get("abc.category.service")

    topic = await resolve_topic(topics, categories, ref)
    if topic is None:
        return

    try:
        updated = await topics.update_topic(topic_id=topic.id, name=new_name)
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Topic '{updated.name}' updated.")
