from y5n.sdk import context, io, ports
from y5n.sdk.models import (
    Document,
    Header,
    Heading,
    InlineText,
    Rule,
    Text,
)

from ..topics import resolve_topic
from .parsing import KEYS


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

    blocks = [
        Heading(level=1, text=[InlineText(text=topic.name.upper())]),
        Text(text=[InlineText(text=f"Run #{run.id} — {run.created}")]),
        Rule(),
    ]
    for key in KEYS:
        entries = run.entries.get(key)
        if entries:
            blocks.append(
                Text(
                    text=[
                        InlineText(text=f"{key}: "),
                        InlineText(text="; ".join(entries)),
                    ]
                )
            )
    await io.write(
        Document(header=Header(role="info", title=topic.name), blocks=blocks)
    )
