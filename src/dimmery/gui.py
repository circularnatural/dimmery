"""Minimal tray icon + window for dimmery (PyQt6).

The tray app runs the tick itself every `interval_minutes`; ddcutil calls take
~1.5 s, so they run in a worker thread.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)

from dimmery import core


def make_icon(paused=False):
    pm = QPixmap(64, 64)
    pm.fill(QColor(0, 0, 0, 0))
    p = QPainter(pm)
    p.setBrush(QColor(150, 150, 150) if paused else QColor(255, 190, 40))
    p.setPen(QColor(0, 0, 0, 0))
    p.drawEllipse(8, 8, 48, 48)
    p.end()
    return QIcon(pm)


class TickWorker(QThread):
    done = pyqtSignal(dict)

    def __init__(self, cfg, state_dir, dry_run):
        super().__init__()
        self.cfg, self.state_dir, self.dry_run = cfg, state_dir, dry_run

    def run(self):
        try:
            self.done.emit(core.tick(self.cfg, self.state_dir, self.dry_run))
        except Exception as e:  # ddcutil missing, monitor off, ...
            ev = {"action": "error", "error": str(e)[:200], "ts": datetime.now().isoformat(timespec="seconds")}
            core.log_event(self.state_dir, ev)
            self.done.emit(ev)


class Window(QWidget):
    def __init__(self, cfg, state_dir):
        super().__init__()
        self.cfg, self.state_dir = cfg, state_dir
        self.setWindowTitle("Dimmery")
        self.resize(420, 560)
        self.status = QLabel("starting...")
        self.day = QComboBox()
        self.day.addItems(core.DAYS)
        self.day.setCurrentText(core.daytype(datetime.now()))
        self.day.currentTextChanged.connect(self.refresh)
        self.slots = QListWidget()
        self.log = QPlainTextEdit(readOnly=True)
        self.log.setMaximumHeight(130)
        self.tick_btn = QPushButton("Tick now")
        self.pause_btn = QPushButton("Pause")
        row = QHBoxLayout()
        row.addWidget(QLabel("Learned table:"))
        row.addWidget(self.day)
        row.addStretch()
        row.addWidget(self.tick_btn)
        row.addWidget(self.pause_btn)
        lay = QVBoxLayout(self)
        lay.addWidget(self.status)
        lay.addLayout(row)
        lay.addWidget(self.slots)
        lay.addWidget(QLabel("Recent events:"))
        lay.addWidget(self.log)
        self.refresh()

    def refresh(self, *_):
        table = core.load_state(self.state_dir).get("table", {}).get(self.day.currentText(), {})
        minutes = self.cfg["slot_minutes"]
        self.slots.clear()
        for s in range(1440 // minutes):
            m = s * minutes
            val = table.get(str(s))
            self.slots.addItem(f"{m // 60:02d}:{m % 60:02d}   {'-' if val is None else str(val) + '%'}")
        self.log.setPlainText("\n".join(json.dumps(e) for e in reversed(core.read_events(self.state_dir, 8))))

    def closeEvent(self, e):  # hide to tray instead of quitting
        e.ignore()
        self.hide()


class App:
    def __init__(self, cfg, state_dir, dry_run):
        self.cfg, self.state_dir, self.dry_run = cfg, state_dir, dry_run
        self.paused, self.worker = False, None
        self.win = Window(cfg, state_dir)
        self.win.tick_btn.clicked.connect(lambda: self.tick())
        self.win.pause_btn.clicked.connect(self.toggle_pause)
        self.tray = QSystemTrayIcon(make_icon())
        self.tray.setToolTip("Dimmery")
        menu = QMenu()
        for label, fn in (("Open", self.win.show), ("Tick now", lambda: self.tick()),
                          ("Pause / Resume", self.toggle_pause), ("Quit", QApplication.quit)):
            act = QAction(label, menu)
            act.triggered.connect(fn)
            menu.addAction(act)
        self.menu = menu
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.on_tray_click)
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.tick(scheduled=True))
        self.timer.start(int(cfg["interval_minutes"]) * 60_000)

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.win.show()

    def toggle_pause(self):
        self.paused = not self.paused
        self.win.pause_btn.setText("Resume" if self.paused else "Pause")
        self.tray.setIcon(make_icon(self.paused))
        self.set_status("paused" if self.paused else "resumed")

    def set_status(self, text):
        self.win.status.setText(text)
        self.tray.setToolTip(f"Dimmery: {text}")

    def tick(self, scheduled=False):
        if (self.paused and scheduled) or (self.worker and self.worker.isRunning()):
            return
        self.set_status("working...")
        self.worker = TickWorker(self.cfg, self.state_dir, self.dry_run)
        self.worker.done.connect(self.on_done)
        self.worker.start()

    def on_done(self, ev):
        if ev["action"] == "error":
            self.set_status(f"error: {ev['error']}")
        else:
            self.set_status(f"{ev['read']}% | {ev['daytype']} slot {ev['slot']} | {ev['action']}")
        self.win.refresh()


def run(cfg, state_dir: Path, dry_run=False):
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    ui = App(cfg, state_dir, dry_run)
    if QSystemTrayIcon.isSystemTrayAvailable():
        ui.tray.show()
    else:
        ui.win.show()  # no tray (e.g. headless): fall back to the window
    QTimer.singleShot(1000, lambda: ui.tick())
    return app.exec()
