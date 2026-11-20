"""ZibaldOne · the reorderable list that scrolls by itself in its top and bottom band (KAN-133).

Only in the builds (`flet build apk`/`windows`, pyproject [tool.flet.*].dependencies): with the
plain Flet client (`flet run`, `python -m zibaldone.ui`, the tests) the app keeps ft.ReorderableListView.
"""

import flet as ft
from flet.controls.base_control import control

__all__ = ["ListaRiordino"]


@control("ZibaldoneListaRiordino")
class ListaRiordino(ft.ReorderableListView):
    """ft.ReorderableListView that, while a block is dragged, scrolls when the finger or the mouse
    is in the top or bottom `edge_fraction` of the list: faster the closer to the edge, up to
    `edge_speed` logical pixels per second."""

    edge_fraction: float = 0.2
    edge_speed: float = 1000.0
