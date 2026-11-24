from zibaldone.core.collection_filter import CollectionFilter, filter_entries
from zibaldone.core.packs import apply_install, find_builtin_pack, plan_install
from zibaldone.storage.database import Store


def _library(tmp_path):
    store = Store.open(tmp_path)
    apply_install(plan_install(find_builtin_pack("collezioni"), store), store)
    store.add_entry("libro", {"titolo": "Il nome della rosa", "autore": "Umberto Eco", "voto": 5, "generi": ["Giallo", "Storico"],
                              "stato": {"status": "completed"}, "preferito": True})
    store.add_entry("libro", {"titolo": "Perché leggere i classici", "autore": "Italo Calvino", "voto": 3, "stato": {"status": "ongoing"}})
    store.add_entry("libro", {"titolo": "Senza voto"})
    return store, store.get_template("libro"), store.list_entries(template="libro", newest_first=False)


def titles(entries):
    return [entry.values["titolo"] for entry in entries]


def test_empty_filter_keeps_everything_in_order(tmp_path) -> None:
    store, template, entries = _library(tmp_path)
    with store:
        assert not CollectionFilter().active
        assert filter_entries(entries, template, CollectionFilter()) == entries


def test_text_ignores_case_and_accents_and_accepts_half_typed_word(tmp_path) -> None:
    store, template, entries = _library(tmp_path)
    with store:
        assert titles(filter_entries(entries, template, CollectionFilter(text="PERCHE class"))) == ["Perché leggere i classici"]
        assert titles(filter_entries(entries, template, CollectionFilter(text="eco"))) == ["Il nome della rosa"]
        assert filter_entries(entries, template, CollectionFilter(text="inesistente")) == []


def test_filters_combine(tmp_path) -> None:
    store, template, entries = _library(tmp_path)
    with store:
        run = lambda **kw: titles(filter_entries(entries, template, CollectionFilter(**kw)))  # noqa: E731
        assert run(statuses=("ongoing",)) == ["Perché leggere i classici"]
        assert run(statuses=("ongoing", "completed")) == ["Il nome della rosa", "Perché leggere i classici"]
        assert run(min_rating=4) == ["Il nome della rosa"]  # unrated entries fail
        assert run(favorites_only=True) == ["Il nome della rosa"]
        assert run(tags=("giallo",)) == ["Il nome della rosa"]
        assert run(tags=("giallo", "fantasy")) == []
        assert run(min_rating=3, statuses=("ongoing",), text="calvino") == ["Perché leggere i classici"]
