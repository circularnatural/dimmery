"""Minimal tray icon + window for dimmery (PyQt6).

The tray app runs the tick itself every `interval_minutes`; ddcutil calls take
~1.5 s, so they run in a worker thread.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QPointF, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QGuiApplication, QIcon, QPainter, QPalette, QPen, QPixmap, QPolygonF
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


def is_dark_theme() -> bool:
    hints = QGuiApplication.styleHints()
    if hints is not None and hasattr(hints, "colorScheme"):
        scheme = hints.colorScheme()
        if scheme != Qt.ColorScheme.Unknown:
            return scheme == Qt.ColorScheme.Dark
    return QApplication.palette().color(QPalette.ColorRole.Window).lightness() < 128


def draw_lamp(size: int, color: QColor) -> QPixmap:
    """Minimalist bedside lamp on a transparent background (64x64 design grid)."""
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.scale(size / 64, size / 64)
    pen = QPen(color, 3)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(color)
    p.drawPolygon(QPolygonF([QPointF(23, 9), QPointF(41, 9), QPointF(50, 31), QPointF(14, 31)]))
    for width, a, b in ((4, (32, 33), (32, 52)), (5, (22, 55), (42, 55))):
        pen = QPen(color, width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(*a), QPointF(*b))
    p.end()
    return pm


def make_icon(paused: bool = False) -> QIcon:
    """White lamp on dark themes, near-black on light ones; faded while paused."""
    color = QColor(255, 255, 255) if is_dark_theme() else QColor(27, 27, 27)
    icon = QIcon()
    for size in (22, 32, 48, 64, 128, 256):
        pm = draw_lamp(size, color)
        if paused:  # fade the finished drawing, so overlapping strokes do not show through
            faded = QPixmap(size, size)
            faded.fill(Qt.GlobalColor.transparent)
            p = QPainter(faded)
            p.setOpacity(0.45)
            p.drawPixmap(0, 0, pm)
            p.end()
            pm = faded
        icon.addPixmap(pm)
    return icon


class TickWorker(QThread):
    done = pyqtSignal(dict)

    def __init__(self, cfg, state_dir, dry_run):
        super().__init__()
        self.cfg, self.state_dir, self.dry_run = cfg, state_dir, dry_run

    def run(self):
        try:
            self.done.emit(core.tick(self.cfg, self.state_dir, self.dry_run))
        except Exception as e:  # ddcutil missing, monitor off, ...
            now = datetime.now().isoformat(timespec="seconds")
            ev = {"action": "error", "error": str(e)[:200], "ts": now}
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
        self.win.setWindowIcon(make_icon())
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
        hints = QGuiApplication.styleHints()
        if hints is not None and hasattr(hints, "colorSchemeChanged"):
            hints.colorSchemeChanged.connect(lambda *_: self.refresh_icon())
        self.timer = QTimer()
        self.timer.timeout.connect(lambda: self.tick(scheduled=True))
        self.timer.start(int(cfg["interval_minutes"]) * 60_000)

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.win.show()

    def refresh_icon(self):
        icon = make_icon(self.paused)
        self.tray.setIcon(icon)
        self.win.setWindowIcon(icon)

    def toggle_pause(self):
        self.paused = not self.paused
        self.win.pause_btn.setText("Resume" if self.paused else "Pause")
        self.refresh_icon()
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
