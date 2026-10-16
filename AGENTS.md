# AGENTS.md

Dimmery learns your brightness habits for an external DDC/CI monitor (Linux). Python 3.11+, `ddcutil` as backend.

## Layout

- `src/dimmery/core.py`: pure decision logic (`step`) plus ddcutil, config and state I/O. No Qt here.
- `src/dimmery/main.py`: CLI (`tick`, `show`, `gui`). `src/dimmery/gui.py`: tray and window (PyQt6).
- `tests/`: `test_core.py` covers the decision logic without hardware; the GUI test runs offscreen.
- `contrib/systemd/`: user units to run `dimmery tick` from a timer.

## Commands

```bash
python3 -m pytest              # tests (no monitor needed)
python3 -m ruff check .        # lint
PYTHONPATH=src python3 -m dimmery tick --dry-run --state-dir /tmp/dimmery-test   # live read, writes nothing
```

## Conventions

- Keep decision logic in `step()` pure (state in, state out) so it stays testable without hardware.
- Never write to the monitor in tests or experiments: use `--dry-run` and a throwaway `--state-dir`.
- Every decision must land in `events.jsonl` (auditability is a feature, errors included).
- Code, comments and commits in English; [Conventional Commits](https://www.conventionalcommits.org/).
- Stdlib only in `core.py` and `main.py`; PyQt6 is an optional extra used only by `gui.py`.
- Update `CHANGELOG.md` with user-visible changes.
