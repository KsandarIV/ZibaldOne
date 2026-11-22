"""Novità: what the latest version brought (KAN-137: only the last patch note; the older ones stay in the files and on GitHub)."""

from typing import List

import flet as ft

from zibaldone.ui import novita
from zibaldone.ui import theme as T
from zibaldone.ui import widgets as W
from zibaldone.ui.context import AppContext
from zibaldone.ui.navigation import Route

KIND_COLORS = {"nuovo": T.ACCENT, "migliorato": T.ACCENT_2, "corretto": T.TEXT_DIM}


def build(ctx: AppContext, route: Route) -> ft.Control:
    releases = novita.load_releases()[:1]
    novita.mark_seen(ctx.folder, releases)
    controls: List[ft.Control] = [W.screen_header("Novità", "Neon", "cosa è arrivato con l'ultima versione", on_back=ctx.back)]
    if not releases:
        controls.append(W.empty_state("Nessuna novità da mostrare, per ora.", "AUTO_AWESOME"))
    for release in releases:
        lines: List[ft.Control] = [ft.Row([W.h2(f"{release.version} · {release.title}" if release.title else release.version)]), W.caption(release.date)]
        for kind, text in release.items:
            lines.append(ft.Row([W.pill(novita.KINDS.get(kind, kind), KIND_COLORS.get(kind, T.TEXT_DIM)), W.body(text, size=14, expand=True)], vertical_alignment=ft.CrossAxisAlignment.START, spacing=8))
        controls.append(W.panel(ft.Column(lines, spacing=8)))
    return W.screen(controls, ctx.wide)
