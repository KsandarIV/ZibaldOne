"""Modelli · importare un pacchetto ricevuto (KAN-77) e dare un'esportazione a chi la vuole (KAN-76)."""

from pathlib import Path
from typing import Any, Callable, List, Tuple

import flet as ft

from zibaldone.core.packs import InstallPlan, Pack, apply_install, load_pack_bytes, plan_install
from zibaldone.storage.database import StoreError
from zibaldone.ui import cloud_model as cm
from zibaldone.ui import theme as T
from zibaldone.ui import viewmodels as vm
from zibaldone.ui import widgets as W
from zibaldone.ui.context import AppContext
from zibaldone.ui.views.import_dialog import read_picked


def open_import_pack(ctx: AppContext, after: Callable[[], Any]) -> None:
    """Pick a `.zbpack.json`, show what it would add, and install it on a tap. `after` runs once something was installed."""
    ctx.pick_files(lambda files: _read(ctx, files, after), multiple=False)


def _read(ctx: AppContext, files: List[Any], after: Callable[[], Any]) -> None:
    if not files:
        return
    picked = files[0]

    def work() -> Tuple[Pack, InstallPlan]:
        pack = load_pack_bytes(read_picked(picked))  # a file that is not a pack: ValueError in Italian
        with ctx.store() as store:
            return pack, plan_install(pack, store)

    ctx.run_blocking(work, lambda found: _confirm(ctx, found[0], found[1], after), lambda problem: ctx.toast(cm.error_text(problem), error=True))


def _confirm(ctx: AppContext, pack: Pack, plan: InstallPlan, after: Callable[[], Any]) -> None:
    rows: List[ft.Control] = [W.body(f"«{pack.name}»" + (f" di {pack.author}" if pack.author else ""), weight=ft.FontWeight.W_600)]
    if pack.description:
        rows.append(W.caption(pack.description))
    for row in vm.plan_rows(plan):
        rows.append(ft.Row([W.body(row.template_name, expand=True), W.pill(row.action_label, row.color)], vertical_alignment=ft.CrossAxisAlignment.CENTER))
    rows.append(W.caption(vm.plan_summary(plan) + ". Le tue voci non si toccano."))
    changes = vm.plan_has_changes(plan)

    def install(_: Any) -> None:
        try:
            with ctx.store() as store:
                done = apply_install(plan_install(pack, store), store)
        except (StoreError, ValueError) as problem:
            ctx.toast(str(problem), error=True)
            return
        ctx.close_dialog()
        ctx.data_changed()
        ctx.toast(f"{pack.name}: {'1 modello installato' if len(done) == 1 else f'{len(done)} modelli installati'}.")
        after()

    ctx.show_dialog(
        ft.AlertDialog(
            title="Importa modelli",
            content=ft.Container(ft.Column(rows, spacing=8, scroll=ft.ScrollMode.AUTO, tight=True), width=420),
            actions=[W.text_button("Annulla", ctx.close_dialog, color=T.TEXT_DIM), W.primary_button("Installa" if changes else "Già tutto installato", install, icon="DOWNLOAD_DONE", disabled=not changes)],
        )
    )


def show_export_result(ctx: AppContext, path: Path) -> None:
    """The exported pack: save it where the person chooses, or share it at once (phone)."""
    ctx.toast(f"Esportato in {path}")
    mobile = bool(getattr(getattr(ctx.page, "platform", None), "is_mobile", lambda: False)())

    def save_as(_: Any) -> None:
        ctx.save_file(path.name, path.read_bytes(), lambda where: ctx.toast(f"Salvato in {where}"))

    actions: List[ft.Control] = [W.text_button("Chiudi", ctx.close_dialog, color=T.TEXT), W.secondary_button("Salva con nome…", save_as, icon="SAVE_ALT")]
    if mobile:
        actions.append(W.primary_button("Condividi", lambda _: ctx.open_file(path), icon="SHARE"))
    ctx.show_dialog(
        ft.AlertDialog(
            title="Pacchetto pronto",
            content=ft.Column(
                [
                    W.body("Scegli dove salvarlo" + (" oppure condividilo subito." if mobile else ".")),
                    W.caption("Una copia è anche nella cartella dati, sotto exports:"),
                    W.panel(W.body(str(path), selectable=True, size=13), padding=10, bgcolor=T.BG),
                ],
                spacing=10,
                tight=True,
            ),
            actions=actions,
        )
    )
