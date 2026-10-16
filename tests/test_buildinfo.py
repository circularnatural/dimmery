from datetime import datetime, timedelta, timezone

from dimmery import buildinfo


def test_describe_clean_and_dirty():
    iso = datetime(2026, 10, 16, 11, 45, tzinfo=timezone(timedelta(hours=-3))).isoformat()
    clean = buildinfo.describe({"hash": "abc1234", "iso": iso, "dirty": False})
    dirty = buildinfo.describe({"hash": "abc1234", "iso": iso, "dirty": True})
    assert clean.startswith("abc1234, ")
    assert dirty.startswith("abc1234-dirty, ")


def test_describe_without_info():
    assert buildinfo.describe({}) == "unknown build"


def test_from_git_on_this_repo_or_none(tmp_path):
    assert buildinfo.from_git(tmp_path) is None  # not a repository
    info = buildinfo.from_git(buildinfo.Path(__file__).resolve().parent)
    assert info is None or {"hash", "iso", "dirty"} <= info.keys()
