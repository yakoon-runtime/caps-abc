from y5n.sdk import io, ports


async def main():
    categories = ports.get("abc.category.service")

    all_categories = await categories.list_categories()
    if not all_categories:
        await io.write("No categories yet.")
        return

    lines = ["Categories:"]
    for c in sorted(all_categories, key=lambda c: c.name.casefold()):
        lines.append(f"  #{c.id} {c.name}")
    await io.write("\n".join(lines))
