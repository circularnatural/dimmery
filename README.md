# dimmery

Brightness that learns your habits for an external monitor over DDC/CI (Linux). It remembers the brightness
you pick for each weekday and 30-minute slot, and applies it for you next time.

## How it works

Every tick (default: 30 min) dimmery reads the monitor brightness through `ddcutil`:

- if it differs from what dimmery last applied, you changed it: it learns the value for the current
  weekday (mon-sun) and slot, and leaves the screen alone;
- otherwise it applies the value remembered for this slot. An empty slot gets a linear blend of the previous and
  next known slots of that weekday (around midnight too); a weekday with no history yet borrows the average of
  the other days.

Learning rule: `new = old + alpha * (your_value - old)` (`alpha` 0.7 by default). The first value learned for a
slot is taken as is. Wheel gestures are learned once, 10 s after you stop spinning, so a burst of notches teaches
only the value you settled on.

## Requirements

- Linux, Python 3.11+
- [`ddcutil`](https://www.ddcutil.com/) and a monitor with DDC/CI enabled (`ddcutil detect` must list it)
- Your user in the `i2c` group and the `i2c-dev` kernel module loaded
- PyQt6 (tray and window only; the CLI uses just the standard library)

## Usage

```bash
pip install -e ".[gui]"            # or, without installing: PYTHONPATH=src python3 -m dimmery ...
dimmery tick --dry-run             # decide and log, without writing to the monitor
dimmery tick                       # one real tick (what a systemd timer would run)
dimmery show                       # print the learned table
dimmery gui                        # tray icon + window; runs the ticks itself
```

In the tray, spin the mouse wheel over the icon to nudge the brightness (`scroll_step` % per notch, default 5);
the change is learned right away like any manual adjustment. This relies on `dbus-monitor` (package
`dbus-bin`), because Qt does not expose the wheel event of a tray icon.

If one notch moves more or less than `scroll_step`, run `dimmery scroll-test`, spin one notch over the icon and
set `scroll_notch` (the wheel delta of a single notch, 120 by default) in `config.toml`. KDE's mouse scroll
speed scales the delta (a 1.5x speed sends 180 per notch, which at 120 would move two steps). Every wheel gesture is also
logged as `scroll_input` with its raw delta.

A monitor that does not answer (off, asleep) is logged once as `offline` and marked `recovered` on the first good
tick, instead of one error every 30 minutes.

`contrib/systemd/` has user units to run `dimmery tick` from a timer instead of the tray.

## State and config

- `~/.local/state/dimmery/state.json`: learned table.
- `~/.local/state/dimmery/events.jsonl`: append-only log of every decision (read, learn, apply, error).
- `~/.config/dimmery/config.toml` (optional): `display`, `serial`, `slot_minutes`, `alpha`, `tolerance`,
  `min`, `max`, `interval_minutes`, `scroll_step`, `scroll_notch`, `plasma`.

## Status

Early, in daily use on one machine (Acer XV325QK V3 over DisplayPort, KDE Plasma on Wayland). Validated live:
reading, writing (`apply`), learning a manual change and the tray icon. Not validated yet: long unattended
runs, autostart after a reboot, and learning from changes made on the monitor's own OSD.

## Limits

- It only sees your changes once per tick, so a change you undo between ticks is missed.
- DDC/CI reads and writes take about 1.5 s each.
- Single monitor per run (`display` or `serial` in the config).

## Layout

```
src/dimmery/core.py     decision logic (pure) + ddcutil, config and state I/O
src/dimmery/main.py     CLI: tick | show | gui
src/dimmery/gui.py      tray icon and window (PyQt6, optional)
contrib/systemd/        user units to run `dimmery tick` from a timer
tests/                  no monitor needed; ddcutil is mocked
```

## Development

```bash
pip install -e ".[dev,gui]"
pytest
ruff check .
```

License: MIT.
