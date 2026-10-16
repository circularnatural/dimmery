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
import subprocess
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
        old = lookup(table, slot, n_slots)
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


def read_brightness(cfg: Config) -> int:
    return int(ddc(cfg, "getvcp", "10", "--brief").split()[3])  # "VCP 10 C <current> <max>"


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
        ddc(cfg, "setvcp", "10", str(ev["target"]))
    ev["dry_run"] = dry_run
    (state_dir / "state.json").write_text(json.dumps(state))
    log_event(state_dir, ev)
    return ev
