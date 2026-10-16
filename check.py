
#!/usr/bin/env python3
"""
check.py — Single quality gate: runs ruff, basedpyright, pytest and fitness_functions.py
in sequence and aggregates one exit code.

Usage:
    python check.py            # ruff + basedpyright + pytest + fitness_functions
    python check.py --fast     # skips ruff and basedpyright
    python check.py --no-types # skips basedpyright only (ruff still runs)
    python check.py --no-fitness  # skips fitness_functions
"""

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def run(name, cmd):
    print(f"\n▶ {name} — {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT)
    ok = result.returncode == 0
    print(f"{'✅' if ok else '❌'} {name} {'OK' if ok else f'failed (exit {result.returncode})'}")
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--fast", action="store_true", help="Skip ruff and basedpyright")
    parser.add_argument("--no-types", action="store_true", help="Skip basedpyright only (ruff still runs)")
    parser.add_argument("--no-fitness", action="store_true", help="Skip fitness_functions")
    args = parser.parse_args()

    results = {}
    if not args.fast:
        results["ruff check"] = run("ruff check", [sys.executable, "-m", "ruff", "check", "."])
    if not args.fast and not args.no_types:
        results["basedpyright"] = run("basedpyright", [sys.executable, "-m", "basedpyright"])
    results["pytest"] = run("pytest", [sys.executable, "-m", "pytest"])

    print("\n" + "—" * 60)
    for name, ok in results.items():
        print(f"{'✅' if ok else '❌'} {name}")

    if not all(results.values()):
        print("\nSomething failed — don't proceed until this is all green.")
        sys.exit(1)
    print("\nAll green.")


if __name__ == "__main__":
    main()

