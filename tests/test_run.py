import json

import pytest
from y5n.runtime.api.flow.patterns.public import FormAction
from y5n.runtime.api.flow.primitives import AwaitEvent
from y5n.runtime.api.runtime import Event
from y5n.runtime.api.runtime.context import set_context

from y5n.caps.abc.apps.run.parsing import parse_entries


def test_parse_single_entry():
    assert parse_entries("Augustus") == ([("A", "Augustus")], [])


def test_parse_semicolon_separates():
    pairs, rejected = parse_entries("Armee; Kaiser; Republik")
    assert [k for k, _ in pairs] == ["A", "K", "R"]
    assert rejected == []


def test_parse_trims_whitespace():
    assert parse_entries("  Army  ;  Emperor  ") == (
        [("A", "Army"), ("E", "Emperor")],
        [],
    )


def test_parse_empty_segments_discarded():
    pairs, rejected = parse_entries("; ; Army")
    assert pairs == [("A", "Army")]
    assert rejected == []


def test_parse_comma_is_content():
    pairs, _ = parse_entries("a: Rome, Carthage")
    assert pairs == [("A", "Rome, Carthage")]


def test_parse_comma_preserved_in_plain_entry():
    pairs, _ = parse_entries("Rome, Carthage")
    assert pairs == [("R", "Rome, Carthage")]


def test_parse_first_character_determines_key():
    assert parse_entries("Emperor")[0] == [("E", "Emperor")]
    assert parse_entries("emperor")[0] == [("E", "emperor")]


def test_parse_rejects_non_letter_first_character():
    assert parse_entries("Übermut") == ([], ["Übermut"])
    assert parse_entries("äpfel") == ([], ["äpfel"])
    assert parse_entries(": test") == ([], [": test"])
    assert parse_entries("!!!") == ([], ["!!!"])
    assert parse_entries("- dash") == ([], ["- dash"])


def test_parse_digits_are_keys():
    assert parse_entries("1945") == ([("1", "1945")], [])
    assert parse_entries("1933") == ([("1", "1933")], [])
    assert parse_entries("9. November") == ([("9", "9. November")], [])
    assert parse_entries("4: 1945") == ([("4", "1945")], [])
    assert parse_entries("42") == ([("4", "42")], [])


def test_parse_override_assigns_rejected_entries():
    assert parse_entries("u: Übermut")[0] == [("U", "Übermut")]
    assert parse_entries("a: äpfel")[0] == [("A", "äpfel")]
    assert parse_entries("w: 3 wishes")[0] == [("W", "3 wishes")]


def test_parse_lowercase_key_normalized():
    pairs, _ = parse_entries("emperor")
    assert pairs == [("E", "emperor")]


def test_parse_override_prefix():
    pairs, _ = parse_entries("a: plenty of distance")
    assert pairs == [("A", "plenty of distance")]


def test_parse_override_case_insensitive():
    pairs, _ = parse_entries("B: civil rights")
    assert pairs == [("B", "civil rights")]


def test_parse_override_empty_text_rejected():
    pairs, rejected = parse_entries("a:")
    assert pairs == []
    assert rejected == ["a:"]


def test_parse_order_preserved_per_letter():
    pairs, _ = parse_entries("Army; Augustus")
    assert pairs == [("A", "Army"), ("A", "Augustus")]


def test_parse_rejected_parts_keep_their_text():
    pairs, rejected = parse_entries(".x; !!!; Army")
    assert pairs == [("A", "Army")]
    assert rejected == [".x", "!!!"]


# ----------------------------------------
# run domain (service level)
# ----------------------------------------


@pytest.mark.asyncio
async def test_run_lifecycle(categories, topics, runs):
    c = await categories.add_category(name="Geschichte")
    t = await topics.add_topic(category_id=c.id, name="Römisches Reich")

    run = await runs.add_run(
        topic_id=t.id,
        entries={"A": ["Augustus", "Armee"], "K": ["Kaiser"]},
    )
    assert run.id
    assert run.topic_id == t.id

    stored = await runs.get_run(run_id=run.id)
    assert stored is not None
    assert stored.entries == {"A": ["Augustus", "Armee"], "K": ["Kaiser"]}
    assert "T" in stored.created
    assert stored.created.endswith("+00:00")


@pytest.mark.asyncio
async def test_run_missing_topic_rejected(runs):
    with pytest.raises(ValueError):
        await runs.add_run(topic_id="999", entries={"A": ["Augustus"]})


@pytest.mark.asyncio
async def test_multiple_runs_per_topic(categories, topics, runs):
    c = await categories.add_category(name="Geschichte")
    t = await topics.add_topic(category_id=c.id, name="Römisches Reich")

    first = await runs.add_run(topic_id=t.id, entries={"A": ["Augustus"]})
    second = await runs.add_run(topic_id=t.id, entries={"B": ["Brot"]})

    assert first.id != second.id
    listed = await runs.list_runs(topic_id=t.id)
    assert [r.id for r in listed] == [first.id, second.id]


@pytest.mark.asyncio
async def test_list_runs_only_requested_topic(categories, topics, runs):
    c1 = await categories.add_category(name="Geschichte")
    c2 = await categories.add_category(name="Führung")
    t1 = await topics.add_topic(category_id=c1.id, name="Römisches Reich")
    t2 = await topics.add_topic(category_id=c2.id, name="Change")

    await runs.add_run(topic_id=t1.id, entries={"A": ["Augustus"]})
    await runs.add_run(topic_id=t2.id, entries={"B": ["Buy-in"]})

    assert [r.topic_id for r in await runs.list_runs(topic_id=t1.id)] == [t1.id]
    assert [r.topic_id for r in await runs.list_runs(topic_id=t2.id)] == [t2.id]


@pytest.mark.asyncio
async def test_completed_run_has_no_update_path(runs):
    assert not hasattr(runs, "update_run")


@pytest.mark.asyncio
async def test_run_delete_removes_whole_run(categories, topics, runs):
    c = await categories.add_category(name="Geschichte")
    t = await topics.add_topic(category_id=c.id, name="Römisches Reich")
    run = await runs.add_run(topic_id=t.id, entries={"A": ["Augustus"]})

    await runs.delete_run(run_id=run.id)

    assert await runs.get_run(run_id=run.id) is None
    assert await runs.list_runs(topic_id=t.id) == []


@pytest.mark.asyncio
async def test_run_delete_missing_rejected(runs):
    with pytest.raises(ValueError):
        await runs.delete_run(run_id="999")


@pytest.mark.asyncio
async def test_topic_deletable_after_runs_deleted(categories, topics, runs):
    c = await categories.add_category(name="Geschichte")
    t = await topics.add_topic(category_id=c.id, name="Römisches Reich")
    run = await runs.add_run(topic_id=t.id, entries={"A": ["Augustus"]})

    await runs.delete_run(run_id=run.id)
    await topics.delete_topic(topic_id=t.id)

    assert await topics.get_topic(topic_id=t.id) is None


@pytest.mark.asyncio
async def test_topic_with_run_cannot_be_deleted(categories, topics, runs):
    c = await categories.add_category(name="Geschichte")
    t = await topics.add_topic(category_id=c.id, name="Römisches Reich")
    await runs.add_run(topic_id=t.id, entries={"A": ["Augustus"]})

    with pytest.raises(ValueError):
        await topics.delete_topic(topic_id=t.id)

    assert await topics.get_topic(topic_id=t.id) is not None


# ----------------------------------------
# interaction (app level, driven like the shell)
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


def _persist_views(pulses: list) -> list[dict]:
    return [
        effect.view
        for pulse in pulses
        for effect in pulse.effects
        if getattr(effect, "persist", False)
    ]


def _all_views(pulses: list) -> list:
    return [
        effect.view
        for pulse in pulses
        for effect in pulse.effects
        if hasattr(effect, "view")
    ]


def _view_text(view: dict) -> str:
    return json.dumps(view, ensure_ascii=False)


def _set_run_context(topic_name: str, *extra_args: str) -> None:
    set_context(
        {
            "node": {"path": "/opt/abc/run/new", "name": "new"},
            "user": {},
            "session": {},
            "flow": {},
            "args": [topic_name, *extra_args],
        }
    )


def _set_run_delete_context(topic_name: str, run_id: str) -> None:
    set_context(
        {
            "node": {"path": "/opt/abc/run/delete", "name": "delete"},
            "user": {},
            "session": {},
            "flow": {},
            "args": [topic_name, run_id],
        }
    )


def _new_run():
    from y5n.caps.abc.apps.run import new as run_new

    return run_new.main()


def _delete_run():
    from y5n.caps.abc.apps.run import delete as run_delete

    return run_delete.main()


async def _make_topic(categories, topics, name="Roman Empire"):
    c = await categories.add_category(name="History")
    return await topics.add_topic(category_id=c.id, name=name)


@pytest.mark.asyncio
async def test_run_interaction_accumulates_and_persists_once(categories, topics, runs):
    t = await _make_topic(categories, topics)
    _set_run_context("Roman Empire")

    pulses = _drive(
        _new_run(),
        [
            "Augustus",
            "Army; Kaiser",
            "a: plenty of distance",
            FormAction("submit"),
        ],
    )

    stored = await runs.list_runs(topic_id=t.id)
    assert len(stored) == 1
    run = stored[0]
    assert run.entries == {
        "A": ["Augustus", "Army", "plenty of distance"],
        "K": ["Kaiser"],
    }

    views = _persist_views(pulses)
    assert views, "the active run view is projected"
    first = _view_text(views[0])
    assert "ROMAN EMPIRE" in first
    assert "Enter associations · Ctrl+N finish" in first

    blocks = [b for b in views[0]["blocks"] if b["type"] == "text"]
    assert len(blocks) == 5
    assert blocks[0].get("text")
    assert not blocks[1].get("text")
    assert blocks[2].get("text")
    assert not blocks[3].get("text")
    assert "Ctrl+N finish" in _view_text(blocks[4])

    last = _view_text(views[-1])
    assert "Army" in last and "plenty of distance" in last
    assert "; " in last
    assert '"type": "underline"' in last
    assert '"type": "strong"' not in last

    summary = _all_views(pulses)[-1]
    assert "Run #1 saved" in _view_text(summary)
    assert "skipped" not in _view_text(summary)


@pytest.mark.asyncio
async def test_run_interaction_rejected_entries_feedback(categories, topics, runs):
    t = await _make_topic(categories, topics)
    _set_run_context("Roman Empire")

    pulses = _drive(
        _new_run(),
        ["Übermut", "u: Übermut", "!!!", FormAction("submit")],
    )

    views = _persist_views(pulses)
    texts = [_view_text(v) for v in views]
    assert "Not stored:" in texts[1]
    assert "Übermut" in texts[1]
    assert "use a key prefix" in texts[1]
    assert "Not stored" not in texts[2]
    assert "Not stored:" in texts[3]
    assert "!!!" in texts[3]

    stored = await runs.list_runs(topic_id=t.id)
    assert len(stored) == 1
    assert stored[0].entries == {"U": ["Übermut"]}


@pytest.mark.asyncio
async def test_run_new_missing_topic_error(categories, topics, runs):
    _set_run_context("Does Not Exist")

    pulses = _drive(_new_run(), [])

    views = _all_views(pulses)
    assert any(
        "Error: Topic 'Does Not Exist' not found." in _view_text(v) for v in views
    )
    assert _persist_views(pulses) == []
    assert await runs.list_runs() == []


@pytest.mark.asyncio
async def test_run_interaction_empty_input_is_ignored(categories, topics, runs):
    t = await _make_topic(categories, topics)
    _set_run_context("Roman Empire")

    _drive(_new_run(), ["Augustus", "", FormAction("submit")])

    stored = await runs.list_runs(topic_id=t.id)
    assert len(stored) == 1
    assert stored[0].entries == {"A": ["Augustus"]}


@pytest.mark.asyncio
async def test_run_interaction_empty_run_discarded(categories, topics, runs):
    await _make_topic(categories, topics)
    _set_run_context("Roman Empire")

    _drive(_new_run(), [FormAction("submit")])

    assert await runs.list_runs() == []


@pytest.mark.asyncio
async def test_run_interaction_abandoned_run_not_persisted(categories, topics, runs):
    t = await _make_topic(categories, topics)
    _set_run_context("Roman Empire")

    coro = _new_run()
    try:
        coro.send(None)
        for payload in ["Augustus", "Army"]:
            coro.send(Event(payload=payload))
    finally:
        coro.close()

    assert await runs.list_runs(topic_id=t.id) == []


@pytest.mark.asyncio
async def test_run_interaction_numeric_keys_underlined(categories, topics, runs):
    t = await _make_topic(categories, topics)
    _set_run_context("Roman Empire")

    pulses = _drive(_new_run(), ["1945", FormAction("submit")])

    views = _persist_views(pulses)
    marked = []
    for view in views:
        for b in view["blocks"]:
            if b["type"] == "text" and b.get("text"):
                for run in b["text"]:
                    if run.get("type") == "underline":
                        for child in run.get("children", []):
                            marked.append(child["text"])
    assert "1" in marked

    stored = await runs.list_runs(topic_id=t.id)
    assert len(stored) == 1
    assert stored[0].entries == {"1": ["1945"]}


@pytest.mark.asyncio
async def test_run_interaction_deduplicates_exact_entries(categories, topics, runs):
    t = await _make_topic(categories, topics)
    _set_run_context("Roman Empire")

    pulses = _drive(
        _new_run(),
        ["Afrika", "Afrika", "Afrika; Afrika", FormAction("submit")],
    )

    stored = await runs.list_runs(topic_id=t.id)
    assert len(stored) == 1
    assert stored[0].entries == {"A": ["Afrika"]}

    last = _view_text(_persist_views(pulses)[-1])
    assert last.count("Afrika") == 1


@pytest.mark.asyncio
async def test_run_interaction_deduplicates_case_insensitively(
    categories, topics, runs
):
    t = await _make_topic(categories, topics)
    _set_run_context("Roman Empire")

    _drive(_new_run(), ["Afrika", "afrika", "AFRIKA", FormAction("submit")])

    stored = await runs.list_runs(topic_id=t.id)
    assert stored[0].entries == {"A": ["Afrika"]}


@pytest.mark.asyncio
async def test_run_interaction_shows_no_previous_runs(categories, topics, runs):
    t = await _make_topic(categories, topics)
    await runs.add_run(topic_id=t.id, entries={"A": ["SECRETMARKER"]})
    _set_run_context("Roman Empire")

    pulses = _drive(_new_run(), ["Fresh", FormAction("submit")])

    views = _persist_views(pulses)
    assert views
    for view in views:
        assert "SECRETMARKER" not in _view_text(view)

    stored = await runs.list_runs(topic_id=t.id)
    assert len(stored) == 2


# ----------------------------------------
# run delete (app level, driven like the shell)
# ----------------------------------------


@pytest.mark.asyncio
async def test_run_delete_interaction_removes_run(categories, topics, runs):
    t = await _make_topic(categories, topics)
    run = await runs.add_run(topic_id=t.id, entries={"A": ["Augustus"]})
    _set_run_delete_context("Roman Empire", run.id)

    pulses = _drive(_delete_run(), [])

    assert f"Run #{run.id} deleted" in _view_text(_all_views(pulses)[-1])
    assert await runs.get_run(run_id=run.id) is None
    assert await runs.list_runs(topic_id=t.id) == []


@pytest.mark.asyncio
async def test_run_delete_interaction_run_of_other_topic_rejected(
    categories, topics, runs
):
    c1 = await categories.add_category(name="Geschichte")
    c2 = await categories.add_category(name="Führung")
    t1 = await topics.add_topic(category_id=c1.id, name="Römisches Reich")
    t2 = await topics.add_topic(category_id=c2.id, name="Change")
    run = await runs.add_run(topic_id=t2.id, entries={"B": ["Buy-in"]})
    _set_run_delete_context("Römisches Reich", run.id)

    pulses = _drive(_delete_run(), [])

    assert f"Run not found for 'Römisches Reich': {run.id}" in _view_text(
        _all_views(pulses)[-1]
    )
    assert await runs.get_run(run_id=run.id) is not None


@pytest.mark.asyncio
async def test_run_delete_interaction_missing_run_rejected(categories, topics, runs):
    await _make_topic(categories, topics)
    _set_run_delete_context("Roman Empire", "99")

    pulses = _drive(_delete_run(), [])

    assert "Run not found for 'Roman Empire': 99" in _view_text(_all_views(pulses)[-1])


# ----------------------------------------
# run new --test (app level, driven like the shell)
# ----------------------------------------


@pytest.mark.asyncio
async def test_run_interaction_test_mode_marks_view_and_stores_nothing(
    categories, topics, runs
):
    t = await _make_topic(categories, topics)
    _set_run_context("Roman Empire", "--test")

    pulses = _drive(
        _new_run(),
        ["Afrika", "Army; Kaiser", FormAction("submit")],
    )

    views = _persist_views(pulses)
    first = _view_text(views[0])
    assert "Test run — nothing will be stored." in first
    last = _view_text(views[-1])
    assert "Afrika" in last and "Kaiser" in last

    summary = _view_text(_all_views(pulses)[-1])
    assert "Test run finished — 3 entries in 2 keys — nothing stored." in summary

    assert await runs.list_runs(topic_id=t.id) == []


@pytest.mark.asyncio
async def test_run_interaction_test_mode_empty_run_discarded(categories, topics, runs):
    t = await _make_topic(categories, topics)
    _set_run_context("Roman Empire", "--test")

    pulses = _drive(_new_run(), [FormAction("submit")])

    assert "Run discarded — no entries." in _view_text(_all_views(pulses)[-1])
    assert await runs.list_runs(topic_id=t.id) == []


@pytest.mark.asyncio
async def test_run_interaction_without_test_flag_still_saves(categories, topics, runs):
    t = await _make_topic(categories, topics)
    _set_run_context("Roman Empire")

    _drive(_new_run(), ["Afrika", FormAction("submit")])

    stored = await runs.list_runs(topic_id=t.id)
    assert len(stored) == 1
    assert stored[0].entries == {"A": ["Afrika"]}
