import json

import pytest
from y5n.runtime.api.flow.primitives import AwaitEvent
from y5n.runtime.api.runtime import Event
from y5n.runtime.api.runtime.context import set_context

# ----------------------------------------
# topic domain (service level)
# ----------------------------------------


@pytest.mark.asyncio
async def test_topic_lifecycle(categories, topics):
    c = await categories.add_category(name="Geschichte")
    t = await topics.add_topic(category_id=c.id, name="Römisches Reich")
    assert t.id
    assert t.category_id == c.id
    assert t.name == "Römisches Reich"

    found = await topics.get_topic(topic_id=t.id)
    assert found is not None and found.name == "Römisches Reich"

    renamed = await topics.update_topic(topic_id=t.id, name="Römische Kaiserzeit")
    assert renamed.name == "Römische Kaiserzeit"

    await topics.delete_topic(topic_id=t.id)
    assert await topics.get_topic(topic_id=t.id) is None


@pytest.mark.asyncio
async def test_topic_missing_category_rejected(categories, topics):
    with pytest.raises(ValueError):
        await topics.add_topic(category_id="999", name="Römisches Reich")


@pytest.mark.asyncio
async def test_duplicate_topic_within_category_rejected_case_insensitively(
    categories, topics
):
    c = await categories.add_category(name="Geschichte")
    await topics.add_topic(category_id=c.id, name="Römisches Reich")

    with pytest.raises(ValueError):
        await topics.add_topic(category_id=c.id, name="römisches reich")


@pytest.mark.asyncio
async def test_same_topic_name_in_different_categories_allowed(categories, topics):
    c1 = await categories.add_category(name="Geschichte")
    c2 = await categories.add_category(name="Führung")

    t1 = await topics.add_topic(category_id=c1.id, name="Change")
    t2 = await topics.add_topic(category_id=c2.id, name="change")

    assert t1.id != t2.id
    names = sorted(t.name for t in await topics.get_topics_by_name(name="CHANGE"))
    assert names == ["Change", "change"]


@pytest.mark.asyncio
async def test_topic_rename_collision_within_category_rejected(categories, topics):
    c = await categories.add_category(name="Geschichte")
    await topics.add_topic(category_id=c.id, name="Römisches Reich")
    t2 = await topics.add_topic(category_id=c.id, name="Caesar")

    with pytest.raises(ValueError):
        await topics.update_topic(topic_id=t2.id, name="römisches reich")

    # a name used in another category is not a collision within this one
    c2 = await categories.add_category(name="Führung")
    await topics.add_topic(category_id=c2.id, name="Change")
    renamed = await topics.update_topic(topic_id=t2.id, name="Change")
    assert renamed.name == "Change"
    assert renamed.category_id == c.id


@pytest.mark.asyncio
async def test_list_topics_filtered_by_category(categories, topics):
    c1 = await categories.add_category(name="Geschichte")
    c2 = await categories.add_category(name="Führung")
    await topics.add_topic(category_id=c1.id, name="Römisches Reich")
    await topics.add_topic(category_id=c2.id, name="Change")

    names = [t.name for t in await topics.list_topics(category_id=c1.id)]
    assert names == ["Römisches Reich"]
    assert len(await topics.list_topics()) == 2


@pytest.mark.asyncio
async def test_find_topics_substring(categories, topics):
    c1 = await categories.add_category(name="Geschichte")
    c2 = await categories.add_category(name="Führung")
    await topics.add_topic(category_id=c1.id, name="Römisches Reich")
    await topics.add_topic(category_id=c2.id, name="Veränderung")

    assert [t.name for t in await topics.find_topics(text="REICH")] == [
        "Römisches Reich"
    ]
    assert [t.name for t in await topics.find_topics(text="ö")] == ["Römisches Reich"]
    assert [t.name for t in await topics.find_topics(text="er")] == ["Veränderung"]
    assert await topics.find_topics(text="sport") == []


@pytest.mark.asyncio
async def test_delete_missing_topic_rejected(topics):
    with pytest.raises(ValueError):
        await topics.delete_topic(topic_id="999")


# ----------------------------------------
# shared topic resolution (app level, driven like the shell)
# ----------------------------------------


def _drive(coro, inputs: list) -> list:
    """Drive a command coroutine like the shell: respond to prompt pulses
    with raw input events (str or FormAction), collect all pulses."""
    pulses = []
    try:
        pulse = coro.send(None)
        while True:
            pulses.append(pulse)
            control = getattr(pulse, "control", None)
            if isinstance(control, AwaitEvent) and control.channel == "__user__":
                pulse = coro.send(Event(payload=inputs.pop(0)))
            else:
                pulse = coro.send(None)
    except StopIteration:
        return pulses


def _all_views(pulses: list) -> list:
    return [
        effect.view
        for pulse in pulses
        for effect in pulse.effects
        if hasattr(effect, "view")
    ]


def _view_text(view: dict) -> str:
    return json.dumps(view, ensure_ascii=False)


def _set_topic_context(command: str, *args: str) -> None:
    set_context(
        {
            "node": {"path": f"/opt/abc/topic/{command}", "name": command},
            "user": {},
            "session": {},
            "flow": {},
            "args": list(args),
        }
    )


def _topic_delete():
    from y5n.caps.abc.apps.topic import delete as topic_delete

    return topic_delete.main()


def _topic_edit():
    from y5n.caps.abc.apps.topic import edit as topic_edit

    return topic_edit.main()


@pytest.mark.asyncio
async def test_topic_edit_resolves_unique_name_and_renames(categories, topics):
    c = await categories.add_category(name="Geschichte")
    await topics.add_topic(category_id=c.id, name="Römisches Reich")
    _set_topic_context("edit", "Römisches Reich", "--new-name", "Kaiserzeit")

    _drive(_topic_edit(), [])

    renamed = await topics.get_topics_by_name(name="Kaiserzeit")
    assert len(renamed) == 1


@pytest.mark.asyncio
async def test_topic_edit_missing_reference_reports_error(categories, topics):
    c = await categories.add_category(name="Geschichte")
    await topics.add_topic(category_id=c.id, name="Römisches Reich")
    _set_topic_context("edit", "Ghost")

    pulses = _drive(_topic_edit(), [])

    text = _view_text(_all_views(pulses)[-1])
    assert "Error: Topic 'Ghost' not found." in text
    assert len(await topics.get_topics_by_name(name="Römisches Reich")) == 1


@pytest.mark.asyncio
async def test_topic_edit_ambiguous_name_lists_candidates_without_not_found(
    categories, topics
):
    c1 = await categories.add_category(name="Geschichte")
    c2 = await categories.add_category(name="Führung")
    t1 = await topics.add_topic(category_id=c1.id, name="Change")
    t2 = await topics.add_topic(category_id=c2.id, name="Change")
    _set_topic_context("edit", "Change")

    pulses = _drive(_topic_edit(), [])

    text = _view_text(_all_views(pulses)[-1])
    assert "ambiguous" in text
    assert f"#{t1.id} Change — Geschichte" in text
    assert f"#{t2.id} Change — Führung" in text
    assert "Not found" not in text
    assert len(await topics.get_topics_by_name(name="Change")) == 2


@pytest.mark.asyncio
async def test_topic_delete_resolves_unique_name(categories, topics):
    c = await categories.add_category(name="Geschichte")
    t = await topics.add_topic(category_id=c.id, name="Römisches Reich")
    _set_topic_context("delete", "Römisches Reich")

    pulses = _drive(_topic_delete(), [])

    text = _view_text(_all_views(pulses)[-1])
    assert "Topic 'Römisches Reich' deleted." in text
    assert await topics.get_topic(topic_id=t.id) is None


@pytest.mark.asyncio
async def test_topic_delete_missing_reference_reports_error(categories, topics):
    c = await categories.add_category(name="Geschichte")
    await topics.add_topic(category_id=c.id, name="Römisches Reich")
    _set_topic_context("delete", "999")

    pulses = _drive(_topic_delete(), [])

    text = _view_text(_all_views(pulses)[-1])
    assert "Error: Topic '999' not found." in text
    assert len(await topics.get_topics_by_name(name="Römisches Reich")) == 1


@pytest.mark.asyncio
async def test_topic_delete_ambiguous_name_lists_candidates(categories, topics):
    c1 = await categories.add_category(name="Geschichte")
    c2 = await categories.add_category(name="Führung")
    t1 = await topics.add_topic(category_id=c1.id, name="Change")
    t2 = await topics.add_topic(category_id=c2.id, name="Change")
    _set_topic_context("delete", "Change")

    pulses = _drive(_topic_delete(), [])

    text = _view_text(_all_views(pulses)[-1])
    assert "ambiguous" in text
    assert f"#{t1.id} Change — Geschichte" in text
    assert f"#{t2.id} Change — Führung" in text
    assert len(await topics.get_topics_by_name(name="Change")) == 2
