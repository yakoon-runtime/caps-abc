from y5n.sdk import context, io, ports


async def main():
    name = context.request().arg(0)

    categories = ports.get("abc.category.service")
    try:
        category = await categories.add_category(name=name)
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Category #{category.id} '{category.name}' created.")
