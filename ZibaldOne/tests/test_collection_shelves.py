import pytest

from zibaldone.core.collection_shelves import OTHER, RATING, group_entries, sort_entries
from zibaldone.core.packs import apply_install, find_builtin_pack, plan_install
from zibaldone.storage.database import Store


def _books(tmp_path):
    store = Store.open(tmp_path)
    apply_install(plan_install(find_builtin_pack("collezioni"), store), store)
    rows = [
        {"titolo": "Il nome della rosa", "autore": "Umberto Eco", "voto": 5, "generi": ["Giallo", "Storico"]},
        {"titolo": "Il pendolo di Foucault", "autore": "Umberto Eco", "voto": 4, "generi": ["Storico"]},
        {"titolo": "Perché leggere i classici", "autore": "Italo Calvino", "generi": ["Saggio"]},
        {"titolo": "Senza genere", "autore": "Anonimo"},
    ]
    for values in rows:
        store.add_entry("libro", values)
    return store, store.get_template("libro"), store.list_entries(template="libro", newest_first=False)


def names(shelves):
    return [(shelf.name, [entry.values["titolo"] for entry in shelf.entries]) for shelf in shelves]


def test_sort_by_author_then_title_and_by_rating(tmp_path) -> None:
    store, template, entries = _books(tmp_path)
    with store:
        by_author = sort_entries(entries, template, ("autore", "@title"))
        assert [e.values["autore"] for e in by_author] == ["Anonimo", "Italo Calvino", "Umberto Eco", "Umberto Eco"]
        assert [e.values["titolo"] for e in by_author][2:] == ["Il nome della rosa", "Il pendolo di Foucault"]
        best = sort_entries(entries, template, (RATING,), descending=True)
        assert [e.values["titolo"] for e in best][:2] == ["Il nome della rosa", "Il pendolo di Foucault"]
        assert [e.values.get("voto") for e in best][2:] == [None, None]  # unrated stay last
        with pytest.raises(ValueError):
            sort_entries(entries, template, ("inesistente",))


def test_group_by_tags_puts_an_entry_in_each_shelf_and_others_last(tmp_path) -> None:
    store, template, entries = _books(tmp_path)
    with store:
        shelves = group_entries(entries, template, ("generi",))
        assert names(shelves) == [
            ("giallo", ["Il nome della rosa"]),
            ("saggio", ["Perché leggere i classici"]),
            ("storico", ["Il nome della rosa", "Il pendolo di Foucault"]),
            (OTHER, ["Senza genere"]),
        ]
        nested = group_entries(entries, template, ("generi", "autore"))
        storico = next(shelf for shelf in nested if shelf.name == "storico")
        assert [child.name for child in storico.children] == ["Umberto Eco"] and storico.total == 2
        assert group_entries(entries, template)[0].entries == sort_entries(entries, template)
