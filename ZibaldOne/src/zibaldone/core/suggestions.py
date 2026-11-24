"""Suggerimenti per le aree (0.3.6): Svago e Sociale.

Funzioni pure: il caso arriva da un `random.Random` passato da fuori (nei test con un seme),
così lo stesso seme dà sempre lo stesso suggerimento. Nessuna dipendenza da ui, cli o storage.
Per ora è tutto a sorte e con testi preimpostati; se un giorno ci sarà un modello linguistico
questi testi diventeranno più intelligenti, ma la forma del risultato resta la stessa.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from zibaldone.core.areas import in_area
from zibaldone.core.templates import Entry, Template

MIX_SIZE = 5

# * — Svago: cinque cose delle tue collezioni e una sfida per metterle insieme —

MIX_CHALLENGES: Tuple[str, ...] = (
    "Scrivi una breve storia in cui compaiano tutte e {count}.",
    "Trova una canzone che le riassuma tutte e {count}, e spiega perché.",
    "Immagina un mondo in cui queste {count} cose esistono insieme: come funziona?",
    "Inventa il titolo di un libro che le mescoli, poi scrivine la prima riga.",
    "Disegna, anche male, una scena che le contenga tutte e {count}.",
    "Scrivi una lettera a uno di loro, parlando anche degli altri.",
    "Quale di queste {count} cose salveresti da un trasloco? Racconta la scelta.",
)


@dataclass(frozen=True)
class MixItem:
    entry_id: str
    title: str
    template: str  # nome del modello (per esempio "Libro")


@dataclass(frozen=True)
class LeisureMix:
    """Fino a cinque voci prese a caso dalle collezioni, e cosa farci."""

    items: Tuple[MixItem, ...]
    challenge: str

    def __bool__(self) -> bool:
        return bool(self.items)


def leisure_pool(entries: Sequence[Entry], templates: Mapping[str, Template]) -> List[Entry]:
    """Le voci con un titolo che stanno nell'area Svago."""
    pool = []
    for entry in entries:
        template = templates.get(entry.template)
        if template is None or not in_area(entry, template, "svago"):
            continue
        if entry.title(template).strip():
            pool.append(entry)
    return pool


def pick_one(entries: Sequence[Entry], templates: Mapping[str, Template], rng: random.Random) -> Optional[MixItem]:
    """Un solo suggerimento a sorte dalle collezioni (None se non c'è niente)."""
    pool = leisure_pool(entries, templates)
    if not pool:
        return None
    entry = rng.choice(sorted(pool, key=lambda item: item.id))
    template = templates[entry.template]
    return MixItem(entry.id, entry.title(template), template.name)


def leisure_mix(entries: Sequence[Entry], templates: Mapping[str, Template], rng: random.Random, size: int = MIX_SIZE) -> LeisureMix:
    """`size` voci a caso (meno se ce ne sono meno) e una sfida a caso."""
    pool = sorted(leisure_pool(entries, templates), key=lambda item: item.id)
    chosen = rng.sample(pool, min(max(size, 0), len(pool)))
    items = tuple(MixItem(entry.id, entry.title(templates[entry.template]), templates[entry.template].name) for entry in chosen)
    if not items:
        return LeisureMix((), "")
    return LeisureMix(items, rng.choice(MIX_CHALLENGES).format(count=len(items)))


# * — Sociale: attività di gruppo non scontate —


@dataclass(frozen=True)
class GroupActivity:
    text: str
    min_people: int = 2
    max_people: int = 99


GROUP_ACTIVITIES: Tuple[GroupActivity, ...] = (
    GroupActivity("Passeggiata senza meta: a ogni incrocio decide la moneta.", 2, 6),
    GroupActivity("Ognuno porta un oggetto strano da casa e gli altri inventano a cosa serve.", 3, 12),
    GroupActivity("Cena a tema «solo ingredienti che iniziano con la stessa lettera».", 3, 10),
    GroupActivity("Cercate insieme la scala più alta della città e guardate il tramonto da lì.", 2, 8),
    GroupActivity("Scrivete a turno una storia, una frase a testa, senza rileggere.", 2, 10),
    GroupActivity("Gara di recensioni serissime di cose banali (un cucchiaio, una panchina).", 3, 12),
    GroupActivity("Tornate in un luogo della vostra infanzia e raccontate cosa è cambiato.", 2, 5),
    GroupActivity("Mappa del quartiere disegnata a memoria da ciascuno: poi confrontatele.", 3, 10),
    GroupActivity("Scambiatevi playlist alla cieca e indovinate di chi è ogni brano.", 3, 12),
    GroupActivity("Costruite un gioco da tavolo con quello che c'è in casa e regole inventate sul momento.", 3, 8),
    GroupActivity("Giornata «turista nella tua città»: scegliete un itinerario da guida e seguitelo.", 4, 20),
    GroupActivity("Torneo di una disciplina inventata, con premi e cerimonia di chiusura.", 6, 30),
    GroupActivity("Fate una foto di gruppo ogni ora in un posto diverso e componete l'album.", 4, 20),
    GroupActivity("Cucina a staffetta: ognuno aggiunge un ingrediente al piatto dell'altro.", 4, 12),
)


def group_activity(people: int, rng: random.Random, exclude: Sequence[str] = ()) -> Optional[GroupActivity]:
    """Un'attività adatta a `people` persone, diversa da quelle in `exclude` se possibile.

    Con un numero che nessuna attività prevede si ripiega su quelle di una coppia o di un gruppo grande,
    cioè sulle più vicine, invece di non suggerire niente.
    """
    if people < 1:
        return None
    fit = [item for item in GROUP_ACTIVITIES if item.min_people <= people <= item.max_people]
    if not fit:
        fit = sorted(GROUP_ACTIVITIES, key=lambda item: min(abs(people - item.min_people), abs(people - item.max_people)))[:3]
    fresh = [item for item in fit if item.text not in set(exclude)]
    return rng.choice(fresh or fit)


# * — Studio: il portale dei riferimenti —


def portal_references(text: str) -> List[Tuple[str, str]]:
    """Le righe di un portale come coppie (tipo, riferimento): 'link', 'file' o 'nota'.

    Una riga che inizia con http:// o https:// è un link; una che sembra un percorso
    (C:\\..., /..., ~/..., \\\\server) è un file; il resto è una nota libera.
    """
    result = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        lowered = line.lower()
        if lowered.startswith(("http://", "https://", "www.")):
            kind = "link"
        elif line.startswith(("/", "~", "\\\\")) or (len(line) > 2 and line[1] == ":" and line[2] in "\\/"):
            kind = "file"
        else:
            kind = "nota"
        result.append((kind, line))
    return result
