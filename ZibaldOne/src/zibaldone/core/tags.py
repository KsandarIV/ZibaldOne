"""Tag e super tag, in stile Markdown (0.3.6).

Un tag si scrive come in Obsidian: `#viaggi` oppure annidato `#viaggi/italia/roma`.
Il tag "padre" (`viaggi`, `viaggi/italia`) è un *super tag*: cercare o filtrare per
`viaggi` trova anche le voci con `viaggi/italia/roma`. Nessuna dipendenza da ui, cli o storage.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence

SEPARATOR = "/"
_INLINE = re.compile(r"(?<![\w/#])#([^\s#,;.:!?()\[\]{}\"']+)")


def normalize_tag(tag: str) -> str:
    """'  #Viaggi / Italia ' -> 'viaggi/italia' (minuscolo, senza # e senza spazi attorno alle barre)."""
    parts = [" ".join(part.split()) for part in tag.strip().lstrip("#").lower().split(SEPARATOR)]
    return SEPARATOR.join(part for part in parts if part)


def extract_tags(text: str) -> List[str]:
    """I tag scritti nel testo con `#`, normalizzati, senza doppioni e nell'ordine di apparizione."""
    found: List[str] = []
    for match in _INLINE.finditer(text or ""):
        tag = normalize_tag(match.group(1))
        if tag and not tag.isdigit() and tag not in found:
            found.append(tag)
    return found


def ancestors(tag: str) -> List[str]:
    """'a/b/c' -> ['a', 'a/b'] (i super tag, dal più generale)."""
    parts = normalize_tag(tag).split(SEPARATOR)
    return [SEPARATOR.join(parts[:index]) for index in range(1, len(parts))] if parts != [""] else []


def has_tag(entry_tags: Iterable[str], wanted: str) -> bool:
    """Vero se la voce porta il tag, oppure un suo discendente (il tag cercato è un super tag)."""
    wanted = normalize_tag(wanted)
    if not wanted:
        return False
    return any(tag == wanted or tag.startswith(wanted + SEPARATOR) for tag in map(normalize_tag, entry_tags))


@dataclass
class TagNode:
    name: str  # percorso completo, es. 'viaggi/italia'
    own: int = 0  # voci che portano esattamente questo tag
    total: int = 0  # voci che portano questo tag o un discendente
    children: List["TagNode"] = field(default_factory=list)

    @property
    def label(self) -> str:
        return self.name.rsplit(SEPARATOR, 1)[-1]


def tag_tree(tags_by_entry: Dict[str, Sequence[str]]) -> List[TagNode]:
    """Albero dei tag con i conteggi; ogni voce conta una volta sola per nodo, ordine alfabetico."""
    own: Dict[str, int] = {}
    total: Dict[str, int] = {}
    for tags in tags_by_entry.values():
        clean = {normalize_tag(tag) for tag in tags if normalize_tag(tag)}
        for tag in clean:
            own[tag] = own.get(tag, 0) + 1
        for node in {name for tag in clean for name in [tag, *ancestors(tag)]}:
            total[node] = total.get(node, 0) + 1
    nodes = {name: TagNode(name, own.get(name, 0), count) for name, count in total.items()}
    roots: List[TagNode] = []
    for name in sorted(nodes):
        parents = ancestors(name)
        (nodes[parents[-1]].children if parents else roots).append(nodes[name])
    return roots
