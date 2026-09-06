from y5n.sdk import context, io, ports

from ..topics import resolve_topic


async def main():
    topic_ref = context.request().arg(0)
    run_ref = context.request().arg(1)

    categories = ports.get("abc.category.service")
    topics = ports.get("abc.topic.service")
    runs = ports.get("abc.run.service")

    topic = await resolve_topic(topics, categories, topic_ref)
    if topic is None:
        return

    run = await runs.get_run(run_id=run_ref) if run_ref and run_ref.isdigit() else None
    if run is None or run.topic_id != topic.id:
        await io.write(f"Run not found for '{topic.name}': {run_ref}")
        return

    try:
        await runs.delete_run(run_id=run.id)
    except ValueError as e:
        await io.write(f"Error: {e}")
        return

    await io.write(f"Run #{run.id} deleted.")
