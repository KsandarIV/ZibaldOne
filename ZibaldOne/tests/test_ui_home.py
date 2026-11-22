"""0.2.8 screens: the home from its layout, the tiles, Lente · Viste and Impostazioni · La tua home."""

from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

ft = pytest.importorskip("flet")

from test_ui_habits import base  # noqa: E402,F401  (fixture)
from test_ui_views import FakePage, button, click, texts, walk  # noqa: E402
from zibaldone.core import home  # noqa: E402
from zibaldone.storage import home_log  # noqa: E402
from zibaldone.core.packs import apply_install, find_builtin_pack, plan_install  # noqa: E402
from zibaldone.core.templates import BlockSpec, Template  # noqa: E402
from zibaldone.storage.database import Store  # noqa: E402
from zibaldone.ui.app import Shell  # noqa: E402
from zibaldone.ui.navigation import SETTINGS_KEYS, parse_route  # noqa: E402
from zibaldone.ui.views import SCREENS  # noqa: E402
from zibaldone.ui.views.tiles import in_days_label  # noqa: E402


def seed(folder: Path, today) -> None:
    with Store.open(folder) as store:
        for name in ("aree", "persone"):
            apply_install(plan_install(find_builtin_pack(name), store), store)
        store.add_entry("persona", {"nome": "Giulia", "compleanno": (today + timedelta(days=3)).replace(year=1990).isoformat()})
        store.add_entry("obiettivo", {"titolo": "Correre 10 km", "stato": {"status": "ongoing", "current": 4, "total": 10}, "scadenza": (today + timedelta(days=20)).isoformat()}, area="salute")
        store.save_template(Template("vista", "Vista", [BlockSpec(key, "text", key) for key in ("nome", "modello", "area", "testo", "campo", "valore", "ordine")], title_block="nome"))
        store.add_entry("persona", {"nome": "Marco"})


def test_routes_and_screens() -> None:
    assert parse_route("/viste").screen == "viste" and parse_route("/viste/abc").arg == "abc" and parse_route("/viste/abc").screen == "vista"
    assert parse_route("/viste/a/b").screen == "oggi"
    assert {"viste", "vista"} <= set(SCREENS) and "home" not in SETTINGS_KEYS


def test_in_days_label() -> None:
    assert [in_days_label(n) for n in (0, 1, 5)] == ["oggi", "domani", "tra 5 giorni"]


def test_oggi_follows_the_layout(base: Path) -> None:  # noqa: F811
    shell = Shell(FakePage(), base)
    shell.start("/oggi")
    today = shell.ctx.now().date()
    seed(base, today)
    shell.start("/oggi")
    shown = texts(shell.body.content)
    assert "RICORRENZE" in shown and "Giulia" in shown and "compleanno · tra 3 giorni · 36 anni" in shown
    assert "OBIETTIVI" in shown and any(text.startswith("Salute · tra 20 giorni") or "tra 20 giorni · 40%" in text for text in shown)
    home_log.save_layout(base, ["stoa", "obiettivi", "ricorrenze"])
    shell.start("/oggi")
    shown = texts(shell.body.content)
    assert shown.index("I TRE MOMENTI") < shown.index("OBIETTIVI") < shown.index("RICORRENZE")
    assert "PENSIERO DEL GIORNO" not in shown and "Pensiero del giorno" not in shown
    assert "LE VOCI DI OGGI" in shown


def test_view_tile_and_screens(base: Path) -> None:  # noqa: F811
    shell = Shell(FakePage(), base)
    shell.start("/viste")
    button(shell.body.content, "Installa «Lente · Viste»")
    seed(base, shell.ctx.now().date())
    shell.start("/viste")
    click(button(shell.body.content, "Nuova vista"))
    dialog = shell.ctx.page.dialogs[-1]
    fields = [item for item in walk(dialog) if isinstance(item, ft.TextField)]
    fields[0].value, fields[1].value = "Persone Marco", "Marco"
    click(button(dialog, "Salva"))
    assert "Vista salvata." in shell.ctx.toasts and "Persone Marco" in texts(shell.body.content)
    with Store.open(base) as store:
        view_id = next(entry.id for entry in store.list_entries(template="vista"))
    home_log.save_layout(base, [f"vista:{view_id}", "citazione"])
    shell.start("/oggi")
    shown = texts(shell.body.content)
    assert "VISTA: PERSONE MARCO" in shown and "Marco" in shown and "Apri la vista" in shown
    shell.start(f"/viste/{view_id}")
    assert "Marco" in texts(shell.body.content)
    shell.start("/viste/nonesiste")
    assert "Questa vista non esiste più." in texts(shell.body.content)
    shell.start("/viste")
    click(next(item for item in walk(shell.body.content) if isinstance(item, ft.IconButton) and item.tooltip == "Togli la vista"))
    click(button(shell.ctx.page.dialogs[-1], "Togli"))
    assert "Vista tolta." in shell.ctx.toasts
    shell.start("/oggi")  # the layout still names the gone view: the tile is just skipped
    assert "VISTA: PERSONE MARCO" not in texts(shell.body.content)


def sorter(root) -> ft.ReorderableListView:
    return next(item for item in walk(root) if isinstance(item, ft.ReorderableListView))


def drop(root, moving: str, target: str) -> None:
    """Move the block `moving` right above `target` (or to the end with "__end__"), as Flet reports it: positions after the drop."""
    keys = [item.key for item in sorter(root).controls]
    old = keys.index(moving)
    new = len(keys) - 1 if target == "__end__" else keys.index(target) - (1 if keys.index(target) > old else 0)
    sorter(root).on_reorder(SimpleNamespace(old_index=old, new_index=new))


def unlock(shell) -> None:
    click(next(item for item in walk(shell.body.content) if isinstance(item, ft.IconButton) and item.tooltip == "Sblocca per spostare i riquadri"))


def test_home_settings_drag_to_reorder_hide_show_reset(base: Path) -> None:  # noqa: F811
    shell = Shell(FakePage(), base)
    shell.start("/organon/personalizza")
    assert home_log.load_layout(base) == list(home.TILES)
    assert "LA HOME" in texts(shell.body.content) and "I TRE MOMENTI" in texts(shell.body.content)  # Oikos lives in Kosmesis, with the real blocks
    unlock(shell)
    drop(shell.body.content, "citazione", "promemoria")  # «citazione» goes above «promemoria»
    assert home_log.load_layout(base)[:2] == ["citazione", "promemoria"]
    switches = [item for item in walk(shell.body.content) if isinstance(item, ft.Switch)]
    switches[1].value = False  # the switches follow the order of the tiles: promemoria, citazione, ...
    switches[1].on_change(SimpleNamespace(control=switches[1]))
    assert "citazione" not in home_log.load_layout(base)
    switches = [item for item in walk(shell.body.content) if isinstance(item, ft.Switch) and not item.value]
    switches[0].value = True
    switches[0].on_change(SimpleNamespace(control=switches[0]))
    assert home_log.load_layout(base)[-1] == "citazione"
    click(button(shell.body.content, "Ripristina"))
    click(button(shell.ctx.page.dialogs[-1], "Ripristina"))
    assert home_log.load_layout(base) == list(home.TILES)


def test_bilancio_tile_is_closed_without_the_pin(base: Path, monkeypatch) -> None:  # noqa: F811
    from zibaldone.core.crypto import ScryptParams
    from zibaldone.storage import keys

    monkeypatch.setattr(keys, "DEFAULT_SCRYPT_PARAMS", ScryptParams(n=2**10))
    shell = Shell(FakePage(), base)
    shell.start("/oggi")
    assert "BILANCIO" not in texts(shell.body.content)  # no finance pack
    with Store.open(base) as store:
        apply_install(plan_install(find_builtin_pack("finanze"), store), store)
    keys.setup_keys(base, "cavallo batteria graffetta")
    with Store.open(base) as store:
        store.add_entry("conto", {"nome": "Carta", "saldo": "1000"})
    shell.start("/oggi")
    shown = texts(shell.body.content)
    assert "BILANCIO" in shown and "Apri con il PIN" in shown and not any("1.000" in text for text in shown)


def test_oggi_can_be_reordered_by_dragging_right_there(base: Path) -> None:  # noqa: F811
    shell = Shell(FakePage(width=412), base)
    shell.start("/oggi")
    seed(base, shell.ctx.now().date())
    shell.start("/oggi")
    assert not any(isinstance(item, ft.ReorderableListView) for item in walk(shell.body.content))  # locked by default
    lock = next(item for item in walk(shell.body.content) if isinstance(item, ft.IconButton) and item.tooltip == "Sblocca per spostare i riquadri")
    click(lock)
    drop(shell.body.content, "aree", "citazione")  # «aree» goes right above «citazione» («promemoria» has a block only at some hours of the day)
    layout = home_log.load_layout(base)
    assert layout.index("aree") + 1 == layout.index("citazione")
    assert "bilancio" in layout  # no finance pack here: the tile is empty, not on screen, and the reorder must keep it
    assert any(isinstance(item, ft.ReorderableListView) for item in walk(shell.body.content))  # still unlocked
    remove = next(item for item in walk(shell.body.content) if isinstance(item, ft.IconButton) and item.tooltip == "Nascondi da Oikos home")
    before = home_log.load_layout(base)
    click(remove)  # the first block that can be taken away
    after = home_log.load_layout(base)
    assert len(after) == len(before) - 1 and all(key in after for key in home.FIXED)
    click(button(shell.body.content, "Aggiungi un riquadro"))
    click(button(shell.ctx.page.dialogs[-1], "Ricorrenze"))  # the block just taken away is offered again
    assert "ricorrenze" in home_log.load_layout(base)
    click(next(item for item in walk(shell.body.content) if isinstance(item, ft.IconButton) and item.tooltip == "Blocca i riquadri"))
    assert not any(isinstance(item, ft.ReorderableListView) for item in walk(shell.body.content))


def test_kosmesis_changes_accent_and_background(base: Path) -> None:  # noqa: F811
    from zibaldone.ui import services
    from zibaldone.ui import theme as T

    try:
        shell = Shell(FakePage(), base)
        shell.start("/organon/personalizza")
        swatches = [item for item in walk(shell.body.content) if isinstance(item, ft.Container) and item.width == 44 and item.tooltip]
        assert len(swatches) == len(T.ACCENT_CHOICES) + len(T.BACKGROUND_CHOICES)
        next(item for item in swatches if item.tooltip == "Rosa").on_click(None)
        next(item for item in swatches if item.tooltip == "Bosco").on_click(None)
        assert services.theme_choice(base) == ("#FF007F", "#0C1511")
        assert T.ACCENT == "#FF007F" and T.BG == "#0C1511" and shell.page.bgcolor == "#0C1511"
        T.apply("#123456", "#FFFFFF")  # not on offer: back to the defaults
        assert (T.ACCENT, T.BG) == (T.DEFAULT_ACCENT, T.DEFAULT_BG) and T.PANEL == "#141521"
        assert all(T.contrast_ratio(accent, bg) >= 4.5 for _, accent in T.ACCENT_CHOICES for _, bg in T.BACKGROUND_CHOICES)
    finally:
        T.apply()
        
        
def test_kosmesis_hides_a_block_with_its_cross_and_moves_it_to_the_end(base: Path) -> None:  # noqa: F811
    shell = Shell(FakePage(), base)
    shell.start("/organon/personalizza")
    unlock(shell)
    hide = next(item for item in walk(shell.body.content) if isinstance(item, ft.IconButton) and item.tooltip == "Nascondi da Oikos home")
    click(hide)  # the ✕ of the first block that can be hidden
    hidden = list(home.TILES)[0]  # in Kosmesis every block has its cross, the fixed ones too
    layout = home_log.load_layout(base)
    assert hidden not in layout and len(layout) == len(home.TILES) - 1
    drop(shell.body.content, layout[0], "__end__")
    assert home_log.load_layout(base) == layout[1:] + layout[:1]


def test_kosmesis_lock_keeps_the_page_still_and_opens_to_drag_whole_blocks(base: Path) -> None:  # noqa: F811
    """KAN-132/133: locked, a normal page; unlocked, every block is its own handle, the same with mouse and finger (no hold)."""
    for page in (FakePage(), FakePage(width=412)):
        shell = Shell(page, base)
        shell.start("/organon/personalizza")
        root = shell.body.content
        assert isinstance(root, ft.Column) and not any(isinstance(item, ft.ReorderableListView) for item in walk(root))
        assert not any(isinstance(item, ft.IconButton) and item.tooltip == "Nascondi da Oikos home" for item in walk(root))  # the cross only when unlocked
        assert "I TRE MOMENTI" in texts(root)  # the real blocks are still shown
        unlock(shell)
        sortable = sorter(shell.body.content)
        assert sortable.show_default_drag_handles is False
        assert all(isinstance(item.content, ft.ReorderableDragHandle) for item in sortable.controls)  # the handle is the whole block
        assert [item.key for item in sortable.controls] == home_log.load_layout(base)
        assert any(isinstance(item, ft.IconButton) and item.tooltip == "Nascondi da Oikos home" for item in walk(sortable))
        click(next(item for item in walk(shell.body.content) if isinstance(item, ft.IconButton) and item.tooltip == "Blocca i riquadri"))
        assert not any(isinstance(item, ft.ReorderableListView) for item in walk(shell.body.content))


def test_kosmesis_changes_the_icon(base: Path) -> None:  # noqa: F811
    from zibaldone.ui import services

    shell = Shell(FakePage(), base)
    shell.start("/organon/personalizza")
    tiles = [item for item in walk(shell.body.content) if isinstance(item, ft.Container) and isinstance(item.content, ft.Image) and item.content.src.startswith("icons/")]
    assert len(tiles) == 4 and services.app_icon(base) == "C"
    tiles[3].on_click(SimpleNamespace(control=tiles[3]))  # D
    assert services.app_icon(base) == "D"


def test_the_builds_use_the_list_that_scrolls_in_the_top_and_bottom_fifth(base: Path, monkeypatch) -> None:  # noqa: F811
    """KAN-133: with zibaldone_riordina (only `flet build` installs it) the open lock gives its list, which scrolls by
    itself when the finger is in the top or bottom fifth; the blocks still move as with Flet's own."""
    import sys

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "extensions" / "zibaldone_riordina" / "src"))
    monkeypatch.setitem(sys.modules, "zibaldone_riordina", None)  # so that the module is gone again after the test
    monkeypatch.delitem(sys.modules, "zibaldone_riordina")
    from zibaldone_riordina import ListaRiordino

    shell = Shell(FakePage(width=412), base)
    shell.start("/organon/personalizza")
    unlock(shell)
    sortable = sorter(shell.body.content)
    assert type(sortable) is ListaRiordino and sortable.edge_fraction == 0.2 and sortable.show_default_drag_handles is False
    # KAN-138: the list makes each block its own handle (mouse at once, finger after a short hold): no Flet handle inside
    assert sortable.touch_delay == 0.3 and not any(isinstance(item.content, ft.ReorderableDragHandle) for item in sortable.controls)
    layout = home_log.load_layout(base)
    drop(shell.body.content, layout[0], "__end__")
    assert home_log.load_layout(base) == layout[1:] + layout[:1]


def test_without_the_extension_the_open_lock_keeps_flets_own_list(base: Path, monkeypatch) -> None:  # noqa: F811
    import sys

    monkeypatch.setitem(sys.modules, "zibaldone_riordina", None)  # as with `flet run` or `python -m zibaldone.ui`
    shell = Shell(FakePage(), base)
    shell.start("/organon/personalizza")
    unlock(shell)
    assert type(sorter(shell.body.content)) is ft.ReorderableListView
