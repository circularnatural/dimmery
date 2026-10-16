import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


import pytest  # noqa: E402


@pytest.fixture(autouse=True)
def never_touch_plasma(monkeypatch):
    """Tests must not drive the real PowerDevil: force the ddcutil fallback (which tests mock)."""
    from dimmery import core

    monkeypatch.setattr(core, "plasma_set", lambda *a, **k: False)
