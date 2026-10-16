"""Command line: dimmery tick | show | gui."""
import argparse
import json
import sys
from pathlib import Path

from dimmery import __version__, buildinfo, core


def main(argv=None):
    p = argparse.ArgumentParser(prog="dimmery", description=__doc__)
    p.add_argument("--version", action="version", version=f"dimmery {__version__} ({buildinfo.describe()})")
    p.add_argument("command", choices=["tick", "show", "gui"], nargs="?", default="gui")
    p.add_argument("--config", type=Path, default=core.CONFIG_PATH)
    p.add_argument("--state-dir", type=Path, default=core.STATE_DIR)
    p.add_argument("--dry-run", action="store_true", help="decide and log, but do not write to the monitor")
    a = p.parse_args(argv)
    cfg = core.load_config(a.config)
    if a.command == "show":
        print(json.dumps(core.load_state(a.state_dir), indent=1, sort_keys=True))
    elif a.command == "tick":
        print(json.dumps(core.tick(cfg, a.state_dir, a.dry_run)))
    else:
        from dimmery import gui
        return gui.run(cfg, a.state_dir, a.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
