from y5n.sdk import context, io, ports


async def main():
    text = context.request().arg(0)
    if not text:
        await io.write("Find what?")
        return

    topics = ports.get("abc.topic.service")
    categories = ports.get("abc.category.service")

    matches = await topics.find_topics(text=text)
    if not matches:
        await io.write(f"Nothing found for '{text}'.")
        return

    names = {c.id: c.name for c in await categories.list_categories()}

    lines = [f"Topics matching '{text}':"]
    for t in sorted(matches, key=lambda t: t.name.casefold()):
        label = names.get(t.category_id, t.category_id)
        lines.append(f"  #{t.id} {t.name} — {label}")
    await io.write("\n".join(lines))
