"""Command line: dimmery tick | show | gui | scroll-test."""
import argparse
import json
import sys
from pathlib import Path

from dimmery import __version__, buildinfo, core


def scroll_test(cfg, seconds=15):
    """Print the raw wheel deltas KDE sends over the tray icon (to calibrate scroll_notch)."""
    import selectors
    import subprocess
    import time

    from dimmery.dbusscroll import MATCH, ScrollParser

    print(f"Spin the wheel over the Dimmery tray icon: ONE notch at a time, {seconds} s...")
    cmd = ["stdbuf", "-oL", "dbus-monitor", "--session", MATCH]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, text=True)
    sel, parser, deltas = selectors.DefaultSelector(), ScrollParser(), []
    sel.register(proc.stdout, selectors.EVENT_READ)
    end = time.monotonic() + seconds
    try:
        while time.monotonic() < end:
            if not sel.select(timeout=0.5):
                continue
            hit = parser.feed(proc.stdout.readline().rstrip("\n"))
            if hit and hit[2] == "vertical":
                deltas.append(hit[1])
                print(f"  delta={hit[1]:+d}")
    finally:
        proc.terminate()
    if deltas:
        print(f"{len(deltas)} events, sum {sum(deltas):+d}; scroll_notch is {cfg['scroll_notch']} "
              "(set it to the delta of ONE notch in config.toml if they differ)")
    else:
        print("nothing received (was the pointer over the Dimmery icon?)")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="dimmery", description=__doc__)
    p.add_argument("--version", action="version", version=f"dimmery {__version__} ({buildinfo.describe()})")
    p.add_argument("command", choices=["tick", "show", "gui", "scroll-test"], nargs="?", default="gui")
    p.add_argument("--config", type=Path, default=core.CONFIG_PATH)
    p.add_argument("--state-dir", type=Path, default=core.STATE_DIR)
    p.add_argument("--dry-run", action="store_true", help="decide and log, but do not write to the monitor")
    a = p.parse_args(argv)
    cfg = core.load_config(a.config)
    if a.command == "show":
        print(json.dumps(core.load_state(a.state_dir), indent=1, sort_keys=True))
    elif a.command == "tick":
        print(json.dumps(core.tick(cfg, a.state_dir, a.dry_run)))
    elif a.command == "scroll-test":
        return scroll_test(cfg)
    else:
        from dimmery import gui
        return gui.run(cfg, a.state_dir, a.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
