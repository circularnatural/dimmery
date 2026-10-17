"""Decision logic and I/O for dimmery.

One tick:
  1. read the monitor brightness;
  2. if it differs from what we last applied, the user changed it: learn it for the current
     (weekday, time slot) and leave the screen alone;
  3. otherwise apply the value remembered for this slot (nearest known slot if it is still empty;
     a weekday with nothing learned yet borrows the average of the other days).

Every decision is appended to ``events.jsonl``.
"""

from __future__ import annotations

import json
import re
import subprocess
import time
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any

Config = dict[str, Any]
State = dict[str, Any]
Event = dict[str, Any]

DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
DEFAULTS: Config = {
    "display": 1,
    "serial": "",
    "slot_minutes": 30,
    "interval_minutes": 30,
    "alpha": 0.5,
    "tolerance": 2,
    "scroll_step": 5,
    "plasma": True,
    "min": 0,
    "max": 100,
}
CONFIG_PATH = Path.home() / ".config/dimmery/config.toml"
STATE_DIR = Path.home() / ".local/state/dimmery"


# --- pure logic -------------------------------------------------------------------------------

def daytype(now: datetime) -> str:
    return DAYS[now.weekday()]


def slot_of(now: datetime, slot_minutes: int) -> int:
    return (now.hour * 60 + now.minute) // slot_minutes


def pooled(tables: dict[str, dict[str, int]]) -> dict[str, int]:
    """Mean value per slot across all days."""
    acc: dict[str, list[int]] = {}
    for table in tables.values():
        for slot, value in table.items():
            acc.setdefault(slot, []).append(value)
    return {slot: round(sum(vs) / len(vs)) for slot, vs in acc.items()}


def lookup(table: dict[str, int], slot: int, n_slots: int) -> int | None:
    """Value for ``slot``, else the nearest known slot on the 24h circle, else None."""
    if str(slot) in table:
        return table[str(slot)]
    if not table:
        return None
    nearest = min((int(k) for k in table), key=lambda k: min((k - slot) % n_slots, (slot - k) % n_slots))
    return table[str(nearest)]


def step(state: State, now: datetime, current: int, cfg: Config) -> tuple[State, Event]:
    """Pure decision: ``event["action"]`` is ``learn``, ``apply`` or ``none``."""
    n_slots = 1440 // cfg["slot_minutes"]
    day, slot = daytype(now), slot_of(now, cfg["slot_minutes"])
    tables = state.setdefault("table", {})
    table = tables.setdefault(day, {})
    last = state.get("last")
    ev: Event = {"ts": now.isoformat(timespec="seconds"), "daytype": day, "slot": slot, "read": current}

    if last is not None and abs(current - last) > cfg["tolerance"]:
        old = table.get(str(slot))  # blend only with this slot's own history, never a distant neighbour
        new = current if old is None else round(old + cfg["alpha"] * (current - old))
        table[str(slot)] = max(cfg["min"], min(cfg["max"], new))
        state["last"] = current
        ev.update(action="learn", old=old, new=table[str(slot)])
        return state, ev

    target = lookup(table, slot, n_slots)
    if target is None:
        target = lookup(pooled(tables), slot, n_slots)
    if target is None:  # very first run: seed with what the user already has
        table[str(slot)] = target = current
    target = max(cfg["min"], min(cfg["max"], target))
    if abs(target - current) > cfg["tolerance"]:
        state["last"] = target
        ev.update(action="apply", target=target)
    else:
        state["last"] = current
        ev.update(action="none", target=target)
    return state, ev


# --- ddcutil ----------------------------------------------------------------------------------

def ddc(cfg: Config, *args: str) -> str:
    target = ["--sn", cfg["serial"]] if cfg["serial"] else ["--display", str(cfg["display"])]
    return subprocess.run(["ddcutil", *target, *args], capture_output=True, text=True, check=True).stdout


# --- Plasma (PowerDevil) ----------------------------------------------------------------------
# Writing through PowerDevil keeps Plasma's slider, tooltip and OSD in sync with the real value; writing
# straight through ddcutil would leave Plasma showing a stale percentage.

PD_SERVICE = "org.kde.ScreenBrightness"
PD_ROOT = "/org/kde/ScreenBrightness"
PD_DISPLAY = "org.kde.ScreenBrightness.Display"
SUPPRESS_INDICATOR = 1  # SetBrightness flag: do not pop up Plasma's OSD


def _busctl(*args: str) -> str:
    run = subprocess.run(["busctl", "--user", *args], capture_output=True, text=True, check=True, timeout=5)
    return run.stdout


def plasma_display() -> str | None:
    """Object path of the first external display PowerDevil controls, or None."""
    try:
        listing = _busctl("get-property", PD_SERVICE, PD_ROOT, PD_SERVICE, "DisplaysDBusNames")
        names = re.findall(r'"([^"]+)"', listing)
        for name in names:
            path = f"{PD_ROOT}/{name}"
            if _busctl("get-property", PD_SERVICE, path, PD_DISPLAY, "IsInternal").split()[-1] == "false":
                return path
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def plasma_set(cfg: Config, percent: int, show_osd: bool = True) -> bool:
    """Set the brightness through PowerDevil. False means "not possible, use ddcutil"."""
    if not cfg["plasma"]:
        return False
    path = plasma_display()
    if path is None:
        return False
    try:
        top = int(_busctl("get-property", PD_SERVICE, path, PD_DISPLAY, "MaxBrightness").split()[-1])
        _busctl("call", PD_SERVICE, path, PD_DISPLAY, "SetBrightness", "iu",
                str(round(percent * top / 100)), "0" if show_osd else str(SUPPRESS_INDICATOR))
    except (OSError, subprocess.SubprocessError, ValueError):
        return False
    return True


def plasma_percent(path: str) -> int | None:
    """The percentage Plasma itself shows for this display (cheap: no DDC/CI traffic)."""
    try:
        value, top = (int(_busctl("get-property", PD_SERVICE, path, PD_DISPLAY, p).split()[-1])
                      for p in ("Brightness", "MaxBrightness"))
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    return round(100 * value / top) if top else None


def set_brightness(cfg: Config, percent: int, show_osd: bool = False) -> None:
    """Write ``percent``: via Plasma when possible (then wait until the monitor reports it), else ddcutil."""
    if plasma_set(cfg, percent, show_osd):
        for _ in range(3):  # best effort: the write itself already went through PowerDevil
            time.sleep(0.8)
            try:
                if abs(read_brightness(cfg) - percent) <= cfg["tolerance"]:
                    return
            except (RuntimeError, subprocess.SubprocessError):
                continue
        return
    ddc(cfg, "setvcp", "10", str(percent))


_VCP_10 = re.compile(r"VCP\s+10\s+C\s+(\d+)\s+(\d+)")  # "VCP 10 C <current> <max>"


def read_brightness(cfg: Config) -> int:
    out = ddc(cfg, "getvcp", "10", "--brief")
    match = _VCP_10.search(out)
    if match is None:  # e.g. the monitor is still waking up: report what ddcutil printed
        raise RuntimeError(f"unexpected ddcutil output: {out.strip()[:120]!r}")
    return int(match.group(1))


# --- config, state and log --------------------------------------------------------------------

def load_config(path: Path = CONFIG_PATH) -> Config:
    cfg = dict(DEFAULTS)
    if path.exists():
        cfg.update(tomllib.loads(path.read_text()))
    return cfg


def load_state(state_dir: Path = STATE_DIR) -> State:
    path = state_dir / "state.json"
    return json.loads(path.read_text()) if path.exists() else {}


def log_event(state_dir: Path, ev: Event) -> None:
    state_dir.mkdir(parents=True, exist_ok=True)
    with (state_dir / "events.jsonl").open("a") as f:
        f.write(json.dumps(ev) + "\n")


def read_events(state_dir: Path = STATE_DIR, n: int = 20) -> list[Event]:
    path = state_dir / "events.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines()[-n:]]


def tick(cfg: Config, state_dir: Path = STATE_DIR, dry_run: bool = False) -> Event:
    """Read the monitor, decide, apply, persist and log. Returns the event."""
    state_dir.mkdir(parents=True, exist_ok=True)
    state, ev = step(load_state(state_dir), datetime.now().astimezone(), read_brightness(cfg), cfg)
    if ev["action"] == "apply" and not dry_run:
        set_brightness(cfg, ev["target"])
    ev["dry_run"] = dry_run
    (state_dir / "state.json").write_text(json.dumps(state))
    log_event(state_dir, ev)
    return ev


def nudge(cfg: Config, state_dir: Path = STATE_DIR, steps: int = 0, dry_run: bool = False) -> Event:
    """Move the brightness by ``steps`` * scroll_step, then tick so the change is learned right away."""
    current = read_brightness(cfg)
    target = max(cfg["min"], min(cfg["max"], current + steps * cfg["scroll_step"]))
    log_event(state_dir, {"ts": datetime.now().astimezone().isoformat(timespec="seconds"), "action": "scroll",
                          "read": current, "target": target, "dry_run": dry_run})
    if target != current and not dry_run:
        set_brightness(cfg, target, show_osd=True)
    return tick(cfg, state_dir, dry_run)
