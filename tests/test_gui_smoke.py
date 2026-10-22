"""Headless smoke test: the window builds and renders a learned table."""
import json
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_window_shows_learned_table(tmp_path):
    from PyQt6.QtWidgets import QApplication

    from dimmery import core
    from dimmery.gui import Window

    app = QApplication.instance() or QApplication([])  # keep a reference alive
    (tmp_path / "state.json").write_text(json.dumps({"table": {"mon": {"20": 55}}}))
    w = Window(core.load_config(tmp_path / "none.toml"), tmp_path)
    w.day.setCurrentText("mon")
    assert app is not None
    assert w.slots.count() == 48
    assert "55%" in w.slots.item(20).text()


def test_about_dialog_shows_version_and_repo(tmp_path):
    from PyQt6.QtWidgets import QApplication, QLabel

    from dimmery import __version__
    from dimmery.gui import REPO_URL, AboutDialog

    app = QApplication.instance() or QApplication([])
    assert app is not None
    dialog = AboutDialog(tmp_path)
    text = " ".join(label.text() for label in dialog.findChildren(QLabel))
    assert __version__ in text
    assert REPO_URL in text


def test_tooltip_survives_powerdevil_renumbering_displays(monkeypatch, tmp_path):
    from PyQt6.QtWidgets import QApplication

    from dimmery import core
    from dimmery.gui import App

    app = QApplication.instance() or QApplication([])
    assert app is not None
    paths = iter(["/org/kde/ScreenBrightness/display0", "/org/kde/ScreenBrightness/display11"])
    monkeypatch.setattr(core, "plasma_display", lambda: next(paths))
    monkeypatch.setattr(core, "plasma_percent", lambda path: 57 if path.endswith("display11") else None)
    ui = App(core.load_config(tmp_path / "none.toml"), tmp_path, True)
    ui.scroll_timer.stop()
    ui.update_tooltip()  # display0 no longer answers -> must resolve display11 and show 57
    assert "57%" in ui.tray.toolTip()


def test_plasma_seeing_the_monitor_again_triggers_a_tick(monkeypatch, tmp_path):
    from PyQt6.QtWidgets import QApplication

    from dimmery import core
    from dimmery.gui import App

    app = QApplication.instance() or QApplication([])
    assert app is not None
    monkeypatch.setattr(core, "plasma_display", lambda: "/p/display0")
    monkeypatch.setattr(core, "plasma_percent", lambda path: 57)
    ui = App(core.load_config(tmp_path / "none.toml"), tmp_path, True)
    ticks = []
    monkeypatch.setattr(ui, "tick", lambda *a, **k: ticks.append(1))
    ui.offline = True
    ui.update_tooltip()
    assert ticks == [1] and ui.offline is False
