from y5n.sdk import context, io, ports


async def main():
    ref = context.request().arg(0)

    topics = ports.get("abc.topic.service")
    categories = ports.get("abc.category.service")

    topic = await _resolve(topics, categories, ref)
    if topic is None:
        return

    try:
        await topics.delete_topic(topic_id=topic.id)
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Topic '{topic.name}' deleted.")


async def _resolve(topics, categories, ref):
    if ref.isdigit():
        return await topics.get_topic(topic_id=ref)
    matches = await topics.get_topics_by_name(name=ref)
    if len(matches) > 1:
        lines = [f"Topic '{ref}' is ambiguous — use its id:"]
        for t in matches:
            c = await categories.get_category(category_id=t.category_id)
            label = c.name if c else t.category_id
            lines.append(f"  #{t.id} {t.name} — {label}")
        await io.write("\n".join(lines))
        return None
    return matches[0] if matches else None
