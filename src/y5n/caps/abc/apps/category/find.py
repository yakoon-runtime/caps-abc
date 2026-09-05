from y5n.sdk import context, io, ports


async def main():
    text = context.request().arg(0)
    if not text:
        await io.write("Find what?")
        return

    categories = ports.get("abc.category.service")
    matches = await categories.find_categories(text=text)
    if not matches:
        await io.write(f"Nothing found for '{text}'.")
        return

    lines = [f"Categories matching '{text}':"]
    for c in sorted(matches, key=lambda c: c.name.casefold()):
        lines.append(f"  #{c.id} {c.name}")
    await io.write("\n".join(lines))
