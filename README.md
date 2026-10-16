# dimmery

Brightness that learns your habits for an external monitor over DDC/CI (Linux). It remembers the brightness
you pick for each weekday and 30-minute slot, and applies it for you next time.

## How it works

Every tick (default: 30 min) dimmery reads the monitor brightness through `ddcutil`:

- if it differs from what dimmery last applied, you changed it: it learns the value for the current
  weekday (mon-sun) and slot, and leaves the screen alone;
- otherwise it applies the value remembered for this slot (or the nearest known slot; a day with no
  history yet borrows the average of the other days).

Learning rule: `new = old + alpha * (your_value - old)`. The first value learned for a day is taken as is.

## Requirements

- Linux, Python 3.11+
- [`ddcutil`](https://www.ddcutil.com/) and a monitor with DDC/CI enabled (`ddcutil detect` must list it)
- Your user in the `i2c` group and the `i2c-dev` kernel module loaded
- PyQt6 (tray and window only; the CLI uses just the standard library)

## Usage

```bash
pip install -e .                   # or: PYTHONPATH=src python3 -m dimmery ...
dimmery tick --dry-run             # decide and log, without writing to the monitor
dimmery tick                       # one real tick (what a systemd timer would run)
dimmery show                       # print the learned table
dimmery gui                        # tray icon + window; runs the ticks itself
```

`contrib/systemd/` has user units to run `dimmery tick` from a timer instead of the tray.

## State and config

- `~/.local/state/dimmery/state.json`: learned table.
- `~/.local/state/dimmery/events.jsonl`: append-only log of every decision (read, learn, apply, error).
- `~/.config/dimmery/config.toml` (optional): `display`, `serial`, `slot_minutes`, `alpha`, `tolerance`,
  `min`, `max`, `interval_minutes`.

## Status

Early. Unit-tested, and a real read plus `--dry-run` tick were validated on an Acer XV325QK V3. Real writes
(`apply`), the tray under KDE and long unattended runs are not validated yet.

## Limits

- It only sees your changes once per tick, so a change you undo between ticks is missed.
- DDC/CI reads and writes take about 1.5 s each.
- Single monitor per run (`display` or `serial` in the config).

## Development

```bash
python3 -m pytest -o addopts="" tests
python3 -m ruff check .
```

License: MIT.
