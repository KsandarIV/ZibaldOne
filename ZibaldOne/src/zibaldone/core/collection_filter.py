"""Collezioni: search bar and filters over the entries of one collection (KAN-78).

Pure functions on entries already loaded: a collection holds a few hundred items
at most, so no SQL and no index are needed.
"""

from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Tuple

from zibaldone.core.search import fold, words
from zibaldone.core.tags import has_tag
from zibaldone.core.templates import Entry, Template


@dataclass(frozen=True)
class CollectionFilter:
    """What the user typed or ticked. Empty fields filter nothing."""

    text: str = ""  # every word must appear in some text of the entry (accents and case ignored)
    statuses: Tuple[str, ...] = ()  # progress statuses, e.g. "ongoing"; an entry matches any of them
    min_rating: Optional[float] = None  # inclusive; unrated entries fail when set
    favorites_only: bool = False
    tags: Tuple[str, ...] = ()  # the entry must carry all of them

    @property
    def active(self) -> bool:
        return bool(words(self.text) or self.statuses or self.min_rating is not None or self.favorites_only or self.tags)


def _texts(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _texts(item)


def _first_value(entry: Entry, template: Template, kind: str) -> Any:
    spec = next((block for block in template.blocks if block.type == kind), None)
    return entry.values.get(spec.key) if spec else None


def _tags(entry: Entry, template: Template) -> set:
    return {fold(tag) for spec in template.blocks if spec.type == "tags" for tag in _texts(entry.values.get(spec.key))}


def matches(entry: Entry, template: Template, query: CollectionFilter) -> bool:
    if query.statuses:
        progress = _first_value(entry, template, "progress")
        if not isinstance(progress, dict) or progress.get("status", "") not in query.statuses:
            return False
    if query.min_rating is not None:
        rating = _first_value(entry, template, "rating")
        if not isinstance(rating, (int, float)) or isinstance(rating, bool) or rating < query.min_rating:
            return False
    if query.favorites_only and not any(spec.type == "favorite" and entry.values.get(spec.key) for spec in template.blocks):
        return False
    if query.tags and not all(has_tag(_tags(entry, template), fold(tag)) for tag in query.tags):
        return False
    wanted = words(query.text)
    if wanted:
        haystack = set(words(" ".join(text for value in entry.values.values() for text in _texts(value))))
        if not all(any(have.startswith(word) for have in haystack) for word in wanted):  # the last word may be half typed
            return False
    return True


def filter_entries(entries: Iterable[Entry], template: Template, query: CollectionFilter) -> List[Entry]:
    """Keep the entries that satisfy every filter, in their original order."""
    return [entry for entry in entries if matches(entry, template, query)]
