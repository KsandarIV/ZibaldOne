from zibaldone.core.collection_filter import CollectionFilter, matches
from zibaldone.core.graph import GraphFilters, build_graph
from zibaldone.core.tags import ancestors, extract_tags, has_tag, normalize_tag, tag_tree
from zibaldone.core.templates import Entry, Template, BlockSpec


def test_normalize_and_extract():
    assert normalize_tag("  #Viaggi / Italia ") == "viaggi/italia"
    assert normalize_tag("#") == ""
    text = "Oggi #Viaggi/Roma e #mare, poi #viaggi/roma di nuovo; #2026 no; mail a@b.it #"
    assert extract_tags(text) == ["viaggi/roma", "mare"]
    assert extract_tags("") == []


def test_ancestors_and_super_tag_match():
    assert ancestors("a/b/c") == ["a", "a/b"]
    assert ancestors("a") == []
    assert has_tag(["viaggi/italia/roma"], "#Viaggi")
    assert has_tag(["viaggi/italia"], "viaggi/italia")
    assert not has_tag(["viaggiatori"], "viaggi")  # prefisso di testo, non super tag
    assert not has_tag([], "viaggi")


def test_tag_tree_counts():
    tree = tag_tree({"1": ["viaggi/italia/roma", "mare"], "2": ["viaggi/italia"], "3": ["viaggi"]})
    assert [node.name for node in tree] == ["mare", "viaggi"]
    viaggi = tree[1]
    assert (viaggi.own, viaggi.total, viaggi.label) == (1, 3, "viaggi")
    italia = viaggi.children[0]
    assert (italia.name, italia.own, italia.total) == ("viaggi/italia", 1, 2)
    assert italia.children[0].name == "viaggi/italia/roma"


def _template():
    return Template(slug="t", name="T", blocks=[BlockSpec(key="titolo", type="text", label="Titolo"), BlockSpec(key="tag", type="tags", label="Tag")])


def test_filters_use_super_tags():
    template = _template()
    entry = Entry(id="e1", template="t", day="2026-11-01", values={"titolo": "Roma", "tag": ["viaggi/italia/roma"]}, created_at="2026-11-01T10:00:00", updated_at="2026-11-01T10:00:00")
    assert matches(entry, template, CollectionFilter(tags=("viaggi",)))
    assert not matches(entry, template, CollectionFilter(tags=("mare",)))
    graph = build_graph([entry], {"t": template}, [], {"e1": ["viaggi/italia/roma"]}, GraphFilters(tag="Viaggi"))
    assert [node.id for node in graph.nodes if node.kind == "entry"] == ["e1"]
