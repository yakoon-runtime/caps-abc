from y5n.sdk import io


async def resolve_topic(topics, categories, ref):
    """Resolve a topic reference (id or name) with explicit errors.

    This is the caps-abc domain resolution policy, shared by the topic
    and run command groups. An id is looked up directly. A name must be
    unique across ABC; ambiguous names are listed with their category
    so that similarly named topics remain distinguishable. A missing
    reference produces an explicit error message and None — the caller
    adds no further message.
    """
    if ref.isdigit():
        topic = await topics.get_topic(topic_id=ref)
        if topic is None:
            await io.write(f"Error: Topic '{ref}' not found.")
        return topic
    matches = await topics.get_topics_by_name(name=ref)
    if len(matches) > 1:
        lines = [f"Topic '{ref}' is ambiguous — use its id:"]
        for t in matches:
            c = await categories.get_category(category_id=t.category_id)
            label = c.name if c else t.category_id
            lines.append(f"  #{t.id} {t.name} — {label}")
        await io.write("\n".join(lines))
        return None
    if not matches:
        await io.write(f"Error: Topic '{ref}' not found.")
        return None
    return matches[0]
