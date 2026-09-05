import pytest


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
