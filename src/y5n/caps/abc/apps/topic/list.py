from y5n.sdk import io, ports


async def main():
    topics = ports.get("abc.topic.service")
    categories = ports.get("abc.category.service")

    all_topics = await topics.list_topics()
    if not all_topics:
        await io.write("No topics yet.")
        return

    names = {c.id: c.name for c in await categories.list_categories()}

    lines = ["Topics:"]
    for t in sorted(all_topics, key=lambda t: t.name.casefold()):
        label = names.get(t.category_id, t.category_id)
        lines.append(f"  #{t.id} {t.name} — {label}")
    await io.write("\n".join(lines))
