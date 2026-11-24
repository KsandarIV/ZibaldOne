import random

from zibaldone.core.suggestions import (
    GROUP_ACTIVITIES,
    group_activity,
    leisure_mix,
    leisure_pool,
    pick_one,
    portal_references,
)
from zibaldone.core.templates import BlockSpec, Entry, Template


def _template(slug: str, name: str, area: str) -> Template:
    return Template(slug=slug, name=name, area=area, blocks=[BlockSpec(key="titolo", type="text", label="Titolo")])


def _entry(entry_id: str, slug: str, title: str) -> Entry:
    return Entry(id=entry_id, template=slug, day="2026-11-01", values={"titolo": title}, created_at="2026-11-01T10:00:00", updated_at="2026-11-01T10:00:00")


TEMPLATES = {"libro": _template("libro", "Libro", "svago"), "film": _template("film", "Film", "svago"), "spesa": _template("spesa", "Spesa", "finanze")}
ENTRIES = [_entry(f"e{index}", "libro" if index % 2 else "film", f"Titolo {index}") for index in range(8)] + [_entry("x", "spesa", "Pane"), _entry("v", "libro", "  ")]


def test_pool_has_only_titled_leisure_entries() -> None:
    assert {entry.id for entry in leisure_pool(ENTRIES, TEMPLATES)} == {f"e{index}" for index in range(8)}


def test_mix_is_five_distinct_items_and_repeatable() -> None:
    mix = leisure_mix(ENTRIES, TEMPLATES, random.Random(7))
    assert len(mix.items) == 5 and len({item.entry_id for item in mix.items}) == 5
    assert mix.challenge and "{count}" not in mix.challenge
    assert leisure_mix(ENTRIES, TEMPLATES, random.Random(7)) == mix
    assert {item.template for item in mix.items} <= {"Libro", "Film"}


def test_mix_with_little_or_nothing() -> None:
    assert not leisure_mix([], TEMPLATES, random.Random(1))
    two = leisure_mix(ENTRIES[:2], TEMPLATES, random.Random(1))
    assert len(two.items) == 2 and "{count}" not in two.challenge
    assert pick_one([], TEMPLATES, random.Random(1)) is None
    assert pick_one(ENTRIES, TEMPLATES, random.Random(1)).entry_id.startswith("e")


def test_group_activity_fits_the_group_and_avoids_repeats() -> None:
    for people in (2, 5, 12):
        activity = group_activity(people, random.Random(people))
        assert activity.min_people <= people <= activity.max_people
    first = group_activity(3, random.Random(0))
    assert group_activity(3, random.Random(0), exclude=[first.text]).text != first.text
    assert group_activity(0, random.Random(0)) is None
    assert group_activity(500, random.Random(0)) in GROUP_ACTIVITIES  # nessuna lo prevede: ripiega sulle più vicine


def test_portal_references_tell_links_files_and_notes() -> None:
    text = "https://example.org/corso\n\nC:\\Studio\\dispense.pdf\n~/Documenti/tesi.docx\nripassare il cap. 3\nwww.wikipedia.org"
    assert [kind for kind, _ in portal_references(text)] == ["link", "file", "file", "nota", "link"]
    assert portal_references("") == []
