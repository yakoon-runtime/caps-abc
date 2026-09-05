from y5n.sdk import context, io, ports


async def main():
    ref = context.request().arg(0)
    new_name = context.request().option("new-name")

    topics = ports.get("abc.topic.service")
    categories = ports.get("abc.category.service")

    topic = await _resolve(topics, categories, ref)
    if topic is None:
        await io.write(f"Not found: {ref}")
        return

    try:
        updated = await topics.update_topic(topic_id=topic.id, name=new_name)
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Topic '{updated.name}' updated.")


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
