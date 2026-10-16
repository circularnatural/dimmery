
"""Smoke test — confirms the package imports and exposes __version__."""

from dimmery import __version__


def test_version_exists() -> None:
    """Package exposes a version string."""
    assert isinstance(__version__, str)
    assert __version__  # not empty



