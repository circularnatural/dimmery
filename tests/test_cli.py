"""CLI and tick I/O with ddcutil mocked: no monitor, nothing written outside tmp_path."""
import json

from dimmery import core, main


def fake_ddc(monkeypatch, brightness):
    calls = []

    def ddc(cfg, *args):
        calls.append(args)
        return f"VCP 10 C {brightness} 100\n"

    monkeypatch.setattr(core, "ddc", ddc)
    return calls


def test_first_tick_seeds_and_logs(monkeypatch, tmp_path):
    fake_ddc(monkeypatch, 40)
    ev = core.tick(core.DEFAULTS, tmp_path)
    assert ev["action"] == "none"
    assert core.read_events(tmp_path)[-1]["read"] == 40
    assert 40 in next(iter(core.load_state(tmp_path)["table"].values())).values()


def test_dry_run_never_writes_to_monitor(monkeypatch, tmp_path):
    calls = fake_ddc(monkeypatch, 40)
    core.tick(core.DEFAULTS, tmp_path)
    state = core.load_state(tmp_path)
    day = next(iter(state["table"]))
    slot = next(iter(state["table"][day]))
    state["table"][day][slot] = 80                       # remembered 80, screen shows 40
    (tmp_path / "state.json").write_text(json.dumps(state))
    ev = core.tick(core.DEFAULTS, tmp_path, dry_run=True)
    assert ev["action"] == "apply"
    assert not any(a[0] == "setvcp" for a in calls)


def test_show_prints_state(monkeypatch, tmp_path, capsys):
    fake_ddc(monkeypatch, 40)
    core.tick(core.DEFAULTS, tmp_path)
    assert main.main(["show", "--state-dir", str(tmp_path)]) == 0
    assert "table" in capsys.readouterr().out


def test_read_brightness_reports_unexpected_output(monkeypatch):
    import pytest

    monkeypatch.setattr(core, "ddc", lambda cfg, *a: "Display is busy, wait and retry\n")
    with pytest.raises(RuntimeError, match="unexpected ddcutil output"):
        core.read_brightness(core.DEFAULTS)


def test_set_brightness_survives_a_garbled_confirmation_read(monkeypatch):
    monkeypatch.setattr(core, "plasma_set", lambda *a, **k: True)  # write "succeeds" through Plasma
    monkeypatch.setattr(core.time, "sleep", lambda s: None)
    monkeypatch.setattr(core, "ddc", lambda cfg, *a: "wait\n")
    core.set_brightness(core.DEFAULTS, 40)  # must not raise
