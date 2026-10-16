#!/usr/bin/env python3
"""dimmery core: learn-as-you-go brightness for a DDC/CI monitor.

One tick does:
  1. read the monitor brightness;
  2. if it differs from what we last applied, the user changed it: learn it
     for the current (weekday, time slot) and leave the screen alone;
  3. otherwise apply the value remembered for this slot (nearest known slot
     if this one is still empty).
Every decision is appended to events.jsonl.
"""
import json
import subprocess
import tomllib
from datetime import datetime
from pathlib import Path

DEFAULTS = {"display": 1, "serial": "", "slot_minutes": 30, "alpha": 0.5,
            "tolerance": 2, "min": 0, "max": 100,
            "interval_minutes": 30}


DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def daytype(now):
    return DAYS[now.weekday()]


def pooled(tables):
    """Mean value per slot across all days; used while a day has nothing learned yet."""
    acc = {}
    for table in tables.values():
        for slot, v in table.items():
            acc.setdefault(slot, []).append(v)
    return {slot: round(sum(vs) / len(vs)) for slot, vs in acc.items()}


def slot_of(now, slot_minutes):
    return (now.hour * 60 + now.minute) // slot_minutes


def lookup(table, slot, n_slots):
    """Value for slot, else nearest known slot on the 24h circle, else None."""
    if str(slot) in table:
        return table[str(slot)]
    known = [int(k) for k in table]
    if not known:
        return None
    best = min(known, key=lambda k: min((k - slot) % n_slots, (slot - k) % n_slots))
    return table[str(best)]


def step(state, now, current, cfg):
    """Pure decision. Returns (new_state, event) where event['action'] is
    'learn', 'apply' or 'none'."""
    n_slots = 1440 // cfg["slot_minutes"]
    dt, slot = daytype(now), slot_of(now, cfg["slot_minutes"])
    tables = state.setdefault("table", {})
    table = tables.setdefault(dt, {})
    last = state.get("last")
    ev = {"ts": now.isoformat(timespec="seconds"), "daytype": dt, "slot": slot, "read": current}
    if last is not None and abs(current - last) > cfg["tolerance"]:
        old = lookup(table, slot, n_slots)
        new = current if old is None else round(old + cfg["alpha"] * (current - old))
        table[str(slot)] = max(cfg["min"], min(cfg["max"], new))
        state["last"] = current
        ev.update(action="learn", old=old, new=table[str(slot)])
        return state, ev
    target = lookup(table, slot, n_slots)
    if target is None:                       # this day has nothing yet: borrow from the other days
        target = lookup(pooled(tables), slot, n_slots)
    if target is None:                       # first ever run: seed with what the user has
        table[str(slot)] = target = current
    target = max(cfg["min"], min(cfg["max"], target))
    if abs(target - current) > cfg["tolerance"]:
        state["last"] = target
        ev.update(action="apply", target=target)
    else:
        state["last"] = current
        ev.update(action="none", target=target)
    return state, ev


def ddc(cfg, *args):
    sel = ["--sn", cfg["serial"]] if cfg["serial"] else ["--display", str(cfg["display"])]
    return subprocess.run(["ddcutil", *sel, *args], capture_output=True, text=True, check=True).stdout


def read_brightness(cfg):
    return int(ddc(cfg, "getvcp", "10", "--brief").split()[3])   # "VCP 10 C <cur> <max>"


CONFIG_PATH = Path.home() / ".config/dimmery/config.toml"
STATE_DIR = Path.home() / ".local/state/dimmery"


def load_config(path=CONFIG_PATH):
    cfg = dict(DEFAULTS)
    if path.exists():
        cfg.update(tomllib.loads(path.read_text()))
    return cfg


def load_state(state_dir=STATE_DIR):
    sf = state_dir / "state.json"
    return json.loads(sf.read_text()) if sf.exists() else {}


def read_events(state_dir=STATE_DIR, n=20):
    log = state_dir / "events.jsonl"
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text().splitlines()[-n:]]


def tick(cfg, state_dir=STATE_DIR, dry_run=False):
    """Read the monitor, decide, apply, persist and log. Returns the event."""
    state_dir.mkdir(parents=True, exist_ok=True)
    state = load_state(state_dir)
    now = datetime.now().astimezone()
    state, ev = step(state, now, read_brightness(cfg), cfg)
    if ev["action"] == "apply" and not dry_run:
        ddc(cfg, "setvcp", "10", str(ev["target"]))
    ev["dry_run"] = dry_run
    (state_dir / "state.json").write_text(json.dumps(state))
    log_event(state_dir, ev)
    return ev


def log_event(state_dir, ev):
    state_dir.mkdir(parents=True, exist_ok=True)
    with (state_dir / "events.jsonl").open("a") as f:
        f.write(json.dumps(ev) + "\n")
