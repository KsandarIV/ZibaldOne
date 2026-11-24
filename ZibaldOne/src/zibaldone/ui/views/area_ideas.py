"""Area pages (0.3.6): ideas for Studio, Svago and Sociale, from `core/suggestions.py`."""

import random
from typing import Any, List, Optional

import flet as ft

from zibaldone.core import suggestions
from zibaldone.ui import theme as T
from zibaldone.ui import widgets as W
from zibaldone.ui.context import AppContext

PORTAL_TEMPLATE = "portale_studio"
KIND_ICONS = {"link": "LINK", "file": "INSERT_DRIVE_FILE_OUTLINED", "nota": "NOTES"}
KIND_LABELS = {"link": "Link", "file": "File", "nota": "Nota"}


def panel(ctx: AppContext, area: str) -> Optional[ft.Control]:
    """The extra block of an area page, or None when the area has none."""
    if area == "studio":
        return _portals(ctx)
    if area == "svago":
        return _Leisure(ctx).build()
    if area == "sociale":
        return _Social(ctx).build()
    return None


# * — Studio: the portal of references —


def _portals(ctx: AppContext) -> Optional[ft.Control]:
    with ctx.store() as store:
        templates = {template.slug: template for template in store.list_templates()}
        if PORTAL_TEMPLATE not in templates:
            return None
        template = templates[PORTAL_TEMPLATE]
        portals = [entry for entry in store.list_entries(newest_first=True) if entry.template == PORTAL_TEMPLATE]
    rows: List[ft.Control] = [W.body("Portali di studio", size=16, weight=ft.FontWeight.W_600)]
    if not portals:
        rows.append(W.body("Ancora nessun portale: crea una voce «Portale di studio» e metti un riferimento per riga.", dim=True))
    for entry in portals[:6]:
        rows.append(W.body(entry.title(template) or "Senza titolo", size=15, weight=ft.FontWeight.W_600))
        for kind, reference in suggestions.portal_references(str(entry.values.get("riferimenti") or "")):
            rows.append(_reference(ctx, kind, reference))
    return W.panel(ft.Column(rows, spacing=8))


def _reference(ctx: AppContext, kind: str, reference: str) -> ft.Control:
    icon = ft.Icon(getattr(ft.Icons, KIND_ICONS[kind]), color=T.ACCENT_2, size=16)
    text = W.body(reference, size=13, expand=True, selectable=True)
    row = ft.Row([icon, text], spacing=8)
    if kind == "link":
        url = reference if reference.lower().startswith("http") else "https://" + reference
        return ft.Container(row, on_click=lambda _: ctx.open_url(url))
    return row


# * — Svago: what to do with the collections —


class _Leisure:
    def __init__(self, ctx: AppContext) -> None:
        self.ctx = ctx
        self.out = ft.Column(spacing=6)

    def build(self) -> ft.Control:
        return W.panel(
            ft.Column(
                [
                    W.body("Che cosa faccio oggi?", size=16, weight=ft.FontWeight.W_600),
                    W.caption("Pesca dalle tue collezioni: un titolo solo, oppure cinque con una sfida."),
                    ft.Row(
                        [
                            W.secondary_button("Uno a sorte", self.pick, icon="CASINO_OUTLINED"),
                            W.secondary_button("Mescola cinque", self.mix, icon="SHUFFLE"),
                        ],
                        wrap=True,
                        spacing=8,
                    ),
                    self.out,
                ],
                spacing=8,
            )
        )

    def _load(self) -> Any:
        with self.ctx.store() as store:
            return store.list_entries(newest_first=False), {template.slug: template for template in store.list_templates()}

    def _item(self, item: suggestions.MixItem) -> ft.Control:
        return ft.Container(
            W.body(f"{item.title} · {item.template}", size=14),
            on_click=lambda _, entry_id=item.entry_id: self.ctx.go(f"/voci/{entry_id}"),
        )

    def _show(self, controls: List[ft.Control]) -> None:
        self.out.controls = controls
        self.ctx.update(self.out)

    def pick(self, _: Any = None) -> None:
        entries, templates = self._load()
        item = suggestions.pick_one(entries, templates, random.Random())
        self._show([self._item(item)] if item else [W.body("Nelle collezioni di Svago non c'è ancora niente da pescare.", dim=True)])

    def mix(self, _: Any = None) -> None:
        entries, templates = self._load()
        result = suggestions.leisure_mix(entries, templates, random.Random())
        if not result:
            self._show([W.body("Nelle collezioni di Svago non c'è ancora niente da mescolare.", dim=True)])
            return
        self._show([*(self._item(item) for item in result.items), W.body(result.challenge, italic=True, size=14)])


# * — Sociale: not-obvious group activities —


class _Social:
    def __init__(self, ctx: AppContext) -> None:
        self.ctx = ctx
        self.people = W.text_input("3", label="Quante persone", width=150, dense=True, on_submit=self.suggest)
        self.out = ft.Column(spacing=6)
        self.seen: List[str] = []

    def build(self) -> ft.Control:
        return W.panel(
            ft.Column(
                [
                    W.body("Un'idea per stare insieme", size=16, weight=ft.FontWeight.W_600),
                    W.caption("Scrivi in quanti siete: l'app propone qualcosa di non scontato."),
                    ft.Row([self.people, W.secondary_button("Proponimi qualcosa", self.suggest, icon="LIGHTBULB_OUTLINE")], wrap=True, spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                    self.out,
                ],
                spacing=8,
            )
        )

    def suggest(self, _: Any = None) -> None:
        raw = (self.people.value or "").strip()
        if not raw.isdigit() or int(raw) < 1:
            self.out.controls = [W.body("Scrivi un numero di persone, per esempio 4.", dim=True)]
        else:
            idea = suggestions.group_activity(int(raw), random.Random(), exclude=self.seen)
            if idea is None:
                self.out.controls = [W.body("Nessuna idea per questo numero.", dim=True)]
            else:
                self.seen.append(idea.text)
                self.out.controls = [W.body(idea.text, size=14)]
        self.ctx.update(self.out)
