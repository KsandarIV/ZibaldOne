"""Collezioni: shelves, the user's own sections and order for a collection (KAN-80).

A library, a wardrobe or a console view is the same thing seen differently: the entries
of one collection split into sections (by genre, platform, category …), then sorted.
Pure functions on entries already loaded; the screens decide how a shelf looks.
"""

from dataclasses import dataclass, field
from typing import Any, Iterable, List, Sequence, Tuple

from zibaldone.core.search import fold
from zibaldone.core.templates import Entry, Template

OTHER = "Altro"  # the section of entries with nothing in the chosen block
TITLE, RATING, RECENT = "@title", "@rating", "@recent"  # special sort keys; any other key is a block key


@dataclass
class Shelf:
    name: str
    entries: List[Entry] = field(default_factory=list)  # the entries that sit here directly
    children: List["Shelf"] = field(default_factory=list)  # sub-sections, when more than one block was chosen

    @property
    def total(self) -> int:
        return len(self.entries) + sum(child.total for child in self.children)


def _labels(entry: Entry, template: Template, key: str) -> List[str]:
    """The section names an entry belongs to for one block: a tag list gives several, a progress gives its status."""
    spec = template.block(key)
    value = entry.values.get(key)
    if value in (None, "", []):
        return [OTHER]
    if spec.type == "progress":
        from zibaldone.core.blocks import PROGRESS_STATUSES

        return [PROGRESS_STATUSES.get(value.get("status", ""), OTHER)]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()] or [OTHER]
    if isinstance(value, bool):
        return [spec.label] if value else [OTHER]
    return [str(value)]


def _sort_value(entry: Entry, template: Template, key: str) -> Tuple[int, Any]:
    """A sortable pair: entries with nothing to sort by go last (flag 1), the rest by value."""
    if key == RECENT:
        return (0, entry.updated_at)
    if key == TITLE:
        key = template.title_key or ""
    value = entry.values.get(key) if key != RATING else _first_rating(entry, template)
    if value in (None, "", []):
        return (1, "")
    if isinstance(value, bool):
        return (0, int(value))
    if isinstance(value, (int, float)):
        return (0, value)
    if isinstance(value, list):
        return (0, fold(", ".join(str(item) for item in value)))
    if isinstance(value, dict):
        return (0, fold(str(value.get("status", ""))))
    return (0, fold(str(value)))


def _first_rating(entry: Entry, template: Template) -> Any:
    spec = next((block for block in template.blocks if block.type == "rating"), None)
    return entry.values.get(spec.key) if spec else None


def sort_entries(entries: Iterable[Entry], template: Template, keys: Sequence[str] = (TITLE,), descending: bool = False) -> List[Entry]:
    """Order by several keys in turn (for a library: author, then title). `descending` flips every key; empty values stay last."""
    result = list(entries)
    for key in reversed(list(keys) or [TITLE]):
        if key not in (TITLE, RATING, RECENT):
            template.block(key)  # an unknown block is a ValueError in Italian, not a silent no-op
        result.sort(key=lambda entry: _sort_value(entry, template, key), reverse=False)
        if descending:
            present = [entry for entry in result if _sort_value(entry, template, key)[0] == 0]
            missing = [entry for entry in result if _sort_value(entry, template, key)[0] == 1]
            result = present[::-1] + missing
    return result


def group_entries(
    entries: Iterable[Entry],
    template: Template,
    group_by: Sequence[str] = (),
    sort_by: Sequence[str] = (TITLE,),
    descending: bool = False,
) -> List[Shelf]:
    """Split entries into shelves by the blocks in `group_by` (first = sections, second = sub-sections …).

    An entry with several tags sits in each of its shelves. Shelves come in alphabetical order with «Altro» last.
    With no `group_by` there is one shelf holding everything.
    """
    ordered = sort_entries(entries, template, sort_by, descending)
    if not group_by:
        return [Shelf("", ordered)]
    key, rest = group_by[0], tuple(group_by[1:])
    template.block(key)
    buckets: dict = {}
    for entry in ordered:
        for label in _labels(entry, template, key):
            buckets.setdefault(label, []).append(entry)
    shelves = []
    for name in sorted(buckets, key=lambda label: (label == OTHER, fold(label))):
        shelf = Shelf(name)
        if rest:
            shelf.children = group_entries(buckets[name], template, rest, sort_by, descending)
        else:
            shelf.entries = buckets[name]
        shelves.append(shelf)
    return shelves
