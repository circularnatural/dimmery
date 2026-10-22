# Architecture

dimmery decides a brightness every tick and applies it through Plasma (PowerDevil) or ddcutil.

## Flow of a tick

1. Read the current brightness (`ddcutil`).
2. Differs from what dimmery last applied: the user changed it, so learn it for the current weekday and 30-minute slot.
3. Otherwise apply the value remembered for the slot (see `README.md` for the empty-slot rules).
4. Append the decision to `events.jsonl`.

## Modules

- `core.py`: pure `step()` plus ddcutil, config and state I/O. Stdlib only.
- `main.py`: CLI (`tick`, `show`, `gui`, `scroll-test`). Stdlib only.
- `gui.py`: tray icon, window and wheel handling (PyQt6, optional extra).
- `dbusscroll.py`, `scroll.py`: wheel events via `dbus-monitor` and burst handling.
- `buildinfo.py`: build provenance shown in About and `--version`.

## State

`state.json` (learned table) and `events.jsonl` (every decision, errors included) under `~/.local/state/dimmery`.

Decisions behind these choices: `governance/DECISION_LOG.md`.
