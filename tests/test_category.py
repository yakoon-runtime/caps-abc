import pytest


@pytest.mark.asyncio
async def test_category_lifecycle(categories):
    c = await categories.add_category(name="Geschichte")
    assert c.id
    assert c.name == "Geschichte"

    found = await categories.get_category(category_id=c.id)
    assert found is not None and found.name == "Geschichte"

    by_name = await categories.get_category_by_name(name="geschichte")
    assert by_name is not None and by_name.id == c.id

    renamed = await categories.update_category(category_id=c.id, name="Alte Geschichte")
    assert renamed.name == "Alte Geschichte"
    assert (await categories.get_category(category_id=c.id)).name == ("Alte Geschichte")

    await categories.delete_category(category_id=c.id)
    assert await categories.get_category(category_id=c.id) is None


@pytest.mark.asyncio
async def test_duplicate_category_rejected_case_insensitively(categories):
    await categories.add_category(name="Geschichte")
    with pytest.raises(ValueError):
        await categories.add_category(name="geschichte")
    with pytest.raises(ValueError):
        await categories.add_category(name="GESCHICHTE")


@pytest.mark.asyncio
async def test_rename_collision_rejected(categories):
    c1 = await categories.add_category(name="Geschichte")
    await categories.add_category(name="Führung")

    with pytest.raises(ValueError):
        await categories.update_category(category_id=c1.id, name="führung")

    # rename to the same name (case difference only) is a no-op, not a clash
    updated = await categories.update_category(category_id=c1.id, name="geschichte")
    assert updated.id == c1.id


@pytest.mark.asyncio
async def test_list_categories(categories):
    await categories.add_category(name="Führung")
    await categories.add_category(name="Geschichte")

    names = [c.name for c in await categories.list_categories()]
    assert names == ["Führung", "Geschichte"]


@pytest.mark.asyncio
async def test_find_categories_substring(categories):
    await categories.add_category(name="Geschichte")
    await categories.add_category(name="Führung")

    assert [c.name for c in await categories.find_categories(text="GESCH")] == [
        "Geschichte"
    ]
    assert [c.name for c in await categories.find_categories(text="ü")] == ["Führung"]
    assert await categories.find_categories(text="sport") == []


@pytest.mark.asyncio
async def test_delete_category_with_topics_rejected(categories, topics):
    c = await categories.add_category(name="Geschichte")
    await topics.add_topic(category_id=c.id, name="Römisches Reich")

    with pytest.raises(ValueError):
        await categories.delete_category(category_id=c.id)

    assert await categories.get_category(category_id=c.id) is not None

    # after removing the topic the category is deletable
    t = (await topics.list_topics(category_id=c.id))[0]
    await topics.delete_topic(topic_id=t.id)
    await categories.delete_category(category_id=c.id)
    assert await categories.get_category(category_id=c.id) is None


@pytest.mark.asyncio
async def test_delete_missing_category_rejected(categories):
    with pytest.raises(ValueError):
        await categories.delete_category(category_id="999")
