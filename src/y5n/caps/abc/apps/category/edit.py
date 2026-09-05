from y5n.sdk import context, io, ports


async def main():
    ref = context.request().arg(0)
    new_name = context.request().option("new-name")

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
        updated = await categories.update_category(
            category_id=category.id,
            name=new_name,
        )
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Category '{updated.name}' updated.")
