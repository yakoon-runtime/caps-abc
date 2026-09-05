from y5n.sdk import context, io, ports

from .topics import resolve_topic


async def main():
    topic_ref = context.request().arg(0)

    topics = ports.get("abc.topic.service")
    runs = ports.get("abc.run.service")

    topic = await resolve_topic(topics, topic_ref)
    if topic is None:
        return

    topic_runs = await runs.list_runs(topic_id=topic.id)
    if not topic_runs:
        await io.write(f"No runs yet for '{topic.name}'.")
        return

    lines = [f"Runs for '{topic.name}':"]
    for r in topic_runs:
        count = sum(len(v) for v in r.entries.values())
        lines.append(f"  #{r.id} {r.created} — {count} entries")
    await io.write("\n".join(lines))
