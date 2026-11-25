# Mappa del codice

Generata da `scripts/code_map.py` il 2026-11-25. Si rigenera a ogni PR di rilascio.
135 moduli in `src/zibaldone/`. Regola: `core` non importa `ui`, `cli`, `storage` (rispettata).

## Livelli
- **core**: 30 moduli, 9483 righe
- **storage**: 14 moduli, 4491 righe
- **cli**: 25 moduli, 3710 righe
- **cloud**: 8 moduli, 1574 righe
- **notify**: 5 moduli, 643 righe
- **packs**: 1 moduli, 0 righe
- **ui**: 50 moduli, 13684 righe
- **(radice)**: 2 moduli, 6 righe

## Moduli più usati (import in ingresso)
- `zibaldone.ui` (40): ZibaldOne's graphical interface (Flet), from version 0.1.0.
- `zibaldone.ui.context` (32): What every view receives: the data folder, the page and a few app-wide actions.
- `zibaldone.storage.database` (31): SQLite storage for templates and entries, with numbered migrations.
- `zibaldone.core` (28): Domain: blocks, templates, entries, privacy texts. Standard library only.
- `zibaldone.core.templates` (26): Templates (user recipes made of blocks) and entries (filled-in templates).
- `zibaldone.storage` (24): Persistence in the user's data folder: paths, settings, folder usage.
- `zibaldone.core.blocks` (24): Block types: the bricks every template is made of.
- `zibaldone.cli.common` (23): Helpers shared by every CLI command: consent, account, opening the store, answers, errors.
- `zibaldone.ui.navigation` (22): Sections, routes and layout choice. Pure: no Flet import.
- `zibaldone.core.brand` (20): Brand identity: names, mascots and quotes taken from philosophy.
- `zibaldone.core.areas` (16): Eudaimonia (0.2.0): the 8 life areas as a concept of the whole app.
- `zibaldone.storage.settings` (14): User settings saved as `settings.json` inside the data folder.

## Moduli più grandi
- `zibaldone.ui.viewmodels`: 1883 righe
- `zibaldone.storage.database`: 1074 righe
- `zibaldone.storage.backups`: 1045 righe
- `zibaldone.core.stats`: 883 righe
- `zibaldone.ui.views.entry_form`: 840 righe
- `zibaldone.core.reminders`: 829 righe
- `zibaldone.core.blocks`: 793 righe
- `zibaldone.ui.views.settings`: 758 righe

Per lo scopo di un modulo: la prima riga del suo docstring.
