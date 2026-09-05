from y5n.sdk import context, io, ports


async def main():
    ref = context.request().arg(0)

    categories = ports.get("abc.category.service")

    category = None
    if ref.isdigit():
        category = await categories.get_category(category_id=ref)
    else:
        category = await categories.get_category_by_name(name=ref)
    if category is None:
        await io.write(f"Not found: {ref}")
        return

    try:
        await categories.delete_category(category_id=category.id)
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Category '{category.name}' deleted.")
