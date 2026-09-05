from y5n.sdk import context, io, ports


async def main():
    name = context.request().arg(0)
    category_ref = context.request().option("category")

    categories = ports.get("abc.category.service")
    category_id = category_ref
    if not category_id.isdigit():
        c = await categories.get_category_by_name(name=category_id)
        if c is None:
            await io.write(f"Not found: {category_ref}")
            return
        category_id = c.id

    topics = ports.get("abc.topic.service")
    try:
        topic = await topics.add_topic(category_id=category_id, name=name)
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Topic #{topic.id} '{topic.name}' created.")
