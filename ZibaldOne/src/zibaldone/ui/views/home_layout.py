"""Kosmesis · Oikos (0.2.8, moved here in 0.3.3): which tiles Oggi shows, and in what order (moved by hand since 0.3.3.2, KAN-132/133)."""

from typing import Any, Callable, Dict, List, Optional, Tuple

import flet as ft

from zibaldone.core import home
from zibaldone.storage import home_log
from zibaldone.ui import services
from zibaldone.core import views as V
from zibaldone.ui import theme as T
from zibaldone.ui import widgets as W
from zibaldone.ui.context import AppContext

ARRANGE_KEY = "kosmesis_riordina"  # ctx.memory: the lock of the Oikos blocks is open

LABELS: Dict[str, str] = {
    "promemoria": "Promemoria",
    "citazione": "Pensiero del giorno",
    "stoa": "I tre momenti",
    "aree": "Le otto aree",
    "abitudini": "Abitudini di oggi",
    "ricorrenze": "Ricorrenze",
    "obiettivi": "Obiettivi",
    "bilancio": "Bilancio",
    "viste": "Viste Lente",
}

def label_of(key: str, view_names: Dict[str, str]) -> str:
    if key.startswith("vista:"):
        return f"Vista: {view_names.get(key.split(':', 1)[1], 'non più disponibile')}"
    return LABELS.get(key, key)


def labelled(key: str, block: ft.Control, view_names: Dict[str, str], hide: Any = None) -> ft.Control:
    """A block under a strip with its name; with the lock open the strip shows the grip and the cross that hides it."""
    open_ = hide is not None
    head = ([ft.Icon(W.icon_of("DRAG_INDICATOR"), size=20, color=T.TEXT_DIM)] if open_ else []) + [W.body(label_of(key, view_names), size=13, expand=True)] + ([hide] if open_ else [])
    strip = ft.Container(ft.Row(head, vertical_alignment=ft.CrossAxisAlignment.CENTER), padding=ft.Padding.symmetric(horizontal=10, vertical=2 if open_ else 10), bgcolor=T.PANEL, border_radius=T.RADIUS_SMALL)
    return ft.Column([strip, block], spacing=6)


def sortable(
    entries: List[Tuple[str, ft.Control]],
    view_names: Dict[str, str],
    save: Callable[[List[str]], None],
    remove: Callable[[str], None],
    kept: Tuple[str, ...] = home.FIXED,
) -> Tuple[List[Tuple[str, ft.Control]], Callable[[int, int], None]]:
    """The blocks as they look, for `W.sortable_screen`, and what to do when one is moved.

    Used only with the lock open: then the whole block is what moves (KAN-133), at once, with the mouse or the finger; with the lock closed the page
    scrolls and selects as usual (KAN-132).
    The cross on a block hides it (it comes back from «Accendi e spegni» in Kosmesis); `kept` blocks have none (on Oggi the fixed ones: only Kosmesis
    switches them off), and neither has the last block, so Oggi never stays empty.
    """
    keys = [key for key, _ in entries]

    def card(key: str, block: ft.Control) -> ft.Control:
        hide = W.icon_button("CLOSE", lambda _, key=key: remove(key), "Nascondi da Oikos home", color=T.TEXT_DIM) if key not in kept and len(keys) > 1 else None
        return labelled(key, block, view_names, hide)

    def moved(old: int, new: int) -> None:
        if old == new or not 0 <= old < len(keys):
            return
        order = list(keys)
        order.insert(min(max(new, 0), len(order) - 1), order.pop(old))
        save(order)

    return [(key, card(key, block)) for key, block in entries], moved


def build(ctx: AppContext) -> Tuple[List[ft.Control], List[Tuple[str, ft.Control]], Optional[Callable[[int, int], None]], List[ft.Control]]:
    """The Oikos section of Kosmesis: what goes above the blocks, the blocks to put in order, what to do when one moves, what goes below.

    With the lock closed (the default) there is nothing to put in order: the blocks are in the part above, and the page is a normal one.
    """
    with ctx.store() as store:
        view_names = {item.id: item.name for item in V.load_views(store)} if store.find_template(V.TEMPLATE) is not None else {}
    shown = [key for key in home_log.load_layout(ctx.folder) if not key.startswith("vista:") or key.split(":", 1)[1] in view_names]
    offered = list(home.TILES) + [f"vista:{view_id}" for view_id in view_names]

    def save(tiles: List[str]) -> None:
        home_log.save_layout(ctx.folder, tiles)
        ctx.refresh_keep_scroll()

    def switch(key: str, visible: bool) -> ft.Switch:
        def changed(event: Any) -> None:
            save(shown + [key] if event.control.value else [item for item in shown if item != key])

        return ft.Switch(value=visible, on_change=changed, active_color=T.ACCENT, disabled=visible and len(shown) == 1, tooltip="Mostra in Oikos home" if not visible else "Nascondi da Oikos home")

    def reset() -> None:
        home_log.reset_layout(ctx.folder)
        ctx.toast("La home è tornata com'era all'inizio.")
        ctx.refresh_keep_scroll()

    from zibaldone.ui.views import today  # here, not on top: Oggi imports this module

    entries, _ = today.preview_entries(ctx)
    unlocked = bool(ctx.memory.get(ARRANGE_KEY))

    def toggle_lock(_: Any) -> None:
        ctx.memory[ARRANGE_KEY] = not unlocked
        ctx.refresh_keep_scroll()

    lock = W.icon_button("LOCK_OPEN" if unlocked else "LOCK", toggle_lock, "Blocca i riquadri" if unlocked else "Sblocca per spostare i riquadri")
    say = (
        "Sbloccata: trascina un riquadro per spostarlo, la crocetta lo nasconde. Richiudi il lucchetto per scorrere la pagina come sempre."
        if unlocked
        else "Così è la tua home, con i riquadri veri. Apri il lucchetto per spostarli o nasconderli; «Le voci di oggi» restano sempre in fondo."
    )
    head: List[ft.Control] = [ft.Row([ft.Container(W.caption(say), expand=True), lock], vertical_alignment=ft.CrossAxisAlignment.CENTER)]
    if unlocked:
        blocks, moved = sortable(entries, view_names, save, lambda key: save([item for item in shown if item != key]), kept=())
    else:
        blocks, moved = [], None
        head += [labelled(key, block, view_names) for key, block in entries]
    tail: List[ft.Control] = [
        W.section_label("Accendi e spegni"),
        W.panel(ft.Column([ft.Row([W.body(label_of(key, view_names), dim=key not in shown, expand=True), switch(key, key in shown)]) for key in offered], spacing=2)),
    ]
    pinned = services.shortcuts(ctx.folder)
    with ctx.store() as store:
        names = {slug: store.find_template(slug) for slug in pinned}
    tail.append(W.section_label("Scorciatoie ai modelli"))
    pinned_rows = [
        ft.Row(
            [W.body(names[slug].name, expand=True), W.text_button("Togli", lambda _, slug=slug: (services.toggle_shortcut(ctx.folder, slug), ctx.refresh_keep_scroll()), icon="PUSH_PIN")]
        )
        for slug in pinned
        if names[slug] is not None
    ]
    tail.append(W.panel(ft.Column(pinned_rows or [W.caption("Nessuna. Da Modelli, la puntina mette un modello in Oikos home: un tocco e scrivi.")], spacing=2)))
    tail.append(
        ft.Row(
            [W.secondary_button("Ripristina", lambda _: ctx.confirm("Ripristinare la home?", "I riquadri tornano tutti visibili, nell'ordine di partenza.", "Ripristina", reset, danger=False), icon="RESTART_ALT")],
            alignment=ft.MainAxisAlignment.END,
        )
    )
    return head, blocks, moved, tail
