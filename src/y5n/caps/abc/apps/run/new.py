from y5n.runtime.api.flow.patterns.public import FormAction
from y5n.sdk import context, io, ports
from y5n.sdk.models import (
    Document,
    Header,
    Heading,
    InlineEm,
    InlineText,
    InlineUnderline,
    Rule,
    Text,
)

from .parsing import KEYS, parse_entries
from .topics import resolve_topic


async def main():
    request = context.request()
    topic_ref = request.arg(0)
    test_mode = request.has_option("test")

    topics = ports.get("abc.topic.service")
    runs = ports.get("abc.run.service")

    topic = await resolve_topic(topics, topic_ref)
    if topic is None:
        return

    entries: dict[str, list[str]] = {}
    rejected: list[str] = []
    while True:
        event = await io.prompt(_run_view(topic, entries, rejected, test_mode))
        payload = event.payload
        if isinstance(payload, FormAction):
            if payload.action == "submit":
                break
            continue
        text = str(payload or "").strip()
        if not text:
            continue
        pairs, rejected = parse_entries(text)
        for key, entry in pairs:
            bucket = entries.setdefault(key, [])
            folded = [e.casefold() for e in bucket]
            if entry.casefold() not in folded:
                bucket.append(entry)

    count = sum(len(v) for v in entries.values())
    if count == 0:
        await io.write("Run discarded — no entries.")
        return
    if test_mode:
        await io.write(
            f"Test run finished — {count} entries in {len(entries)} keys"
            " — nothing stored."
        )
        return
    run = await runs.add_run(topic_id=topic.id, entries=entries)
    await io.write(f"Run #{run.id} saved — {count} entries in {len(entries)} keys.")


def _run_view(
    topic, entries: dict[str, list[str]], rejected: list[str], test_mode: bool = False
) -> dict:
    cue: list = []
    for i, key in enumerate(KEYS):
        if i % 5 == 0 and i > 0:
            cue.append(InlineText(text=" - "))
        elif cue:
            cue.append(InlineText(text=" "))
        if entries.get(key):
            cue.append(InlineUnderline(children=[InlineText(text=key)]))
        else:
            cue.append(InlineText(text=key))

    collected: list[str] = []
    for key in KEYS:
        collected.extend(entries.get(key, []))

    blocks = [
        Heading(level=1, text=[InlineText(text=topic.name.upper())]),
        Rule(),
        Text(text=cue),
        Text(),
        Text(text=[InlineText(text="; ".join(collected))]),
    ]
    if rejected:
        listed = ", ".join(f'"{part}"' for part in rejected)
        blocks.append(
            Text(
                text=[
                    InlineEm(
                        children=[
                            InlineText(
                                text=(
                                    f"Not stored: {listed}"
                                    ' — use a key prefix, e.g. "u: text"'
                                )
                            )
                        ]
                    )
                ]
            )
        )
    blocks.append(Text())
    blocks.append(
        Text(
            text=[
                InlineEm(
                    children=[InlineText(text="Enter associations · Ctrl+N finish")]
                )
            ]
        )
    )
    if test_mode:
        blocks.append(Text())
        blocks.append(
            Text(
                text=[
                    InlineEm(
                        children=[
                            InlineText(text="Test run — nothing will be stored.")
                        ]
                    )
                ]
            )
        )
    return Document(
        header=Header(role="info", title=topic.name), blocks=blocks
    ).to_dict()
