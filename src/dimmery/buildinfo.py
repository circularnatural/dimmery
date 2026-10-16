"""Build provenance: which commit this code was built from, and whether it was dirty.

Installed copies carry a stamp written at build time (``_buildinfo.py``, see setup.py); running from a
source checkout asks git directly.
"""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any


def _git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


def from_git(cwd: Path) -> dict[str, Any] | None:
    """Hash, commit time (ISO 8601) and dirty flag of the repo containing ``cwd``; None if not a repo."""
    try:
        commit_hash, iso = _git(cwd, "log", "-1", "--format=%h %cI").split()
        dirty = bool(_git(cwd, "status", "--porcelain", "--untracked-files=no"))
    except (OSError, ValueError, subprocess.CalledProcessError):
        return None
    return {"hash": commit_hash, "iso": iso, "dirty": dirty}


def get() -> dict[str, Any]:
    try:
        from dimmery import _buildinfo  # written at build time
    except ImportError:
        return from_git(Path(__file__).resolve().parent) or {}
    return dict(_buildinfo.INFO)


def describe(info: dict[str, Any] | None = None) -> str:
    """``4444d2c-dirty, 16/10/2026 11:45`` (local time), or ``unknown build``."""
    info = get() if info is None else info
    if not info:
        return "unknown build"
    when = datetime.fromisoformat(info["iso"]).astimezone().strftime("%d/%m/%Y %H:%M")
    return f"{info['hash']}{'-dirty' if info['dirty'] else ''}, {when}"
