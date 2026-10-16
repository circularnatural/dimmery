"""Mouse-wheel on the tray icon.

Qt's QSystemTrayIcon ignores the StatusNotifierItem ``Scroll`` call that KDE sends when you spin the wheel
over the icon, so we watch for it with ``dbus-monitor`` and keep only the calls addressed to this process.
"""

import os
import re

from PyQt6.QtCore import QObject, QProcess, pyqtSignal
from PyQt6.QtDBus import QDBusConnection

MATCH = "type='method_call',interface='org.kde.StatusNotifierItem',member='Scroll'"
_HEADER = re.compile(r"^(method call|method return|signal|error)\b")
_DEST = re.compile(r"destination=(\S+)")


class ScrollParser:
    """Turns ``dbus-monitor`` text into ``(destination, delta, orientation)`` tuples, one per Scroll call."""

    def __init__(self) -> None:
        self.dest: str | None = None
        self.delta: int | None = None

    def feed(self, line: str) -> tuple[str, int, str] | None:
        if _HEADER.match(line):
            found = _DEST.search(line)
            is_scroll = "member=Scroll" in line and "interface=org.kde.StatusNotifierItem" in line
            self.dest, self.delta = (found.group(1), None) if is_scroll and found else (None, None)
            return None
        if self.dest is None:
            return None
        text = line.strip()
        if text.startswith("int32 "):
            self.delta = int(text.split()[1])
        elif text.startswith("string ") and self.delta is not None:
            result = (self.dest, self.delta, text.split('"')[1] if '"' in text else "")
            self.dest = self.delta = None
            return result
        return None


class ScrollWatcher(QObject):
    scrolled = pyqtSignal(int)  # raw wheel delta: +-120 per notch, smaller steps on hi-res wheels

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._parser, self._buffer, self._ours = ScrollParser(), "", {}
        self._proc = QProcess(self)
        self._proc.readyReadStandardOutput.connect(self._read)

    def start(self) -> None:
        self._proc.start("dbus-monitor", ["--session", MATCH])

    def stop(self) -> None:
        self._proc.kill()
        self._proc.waitForFinished(500)

    def _is_ours(self, dest: str) -> bool:
        if dest not in self._ours:
            reply = QDBusConnection.sessionBus().interface().servicePid(dest)
            self._ours[dest] = reply.isValid() and reply.value() == os.getpid()
        return self._ours[dest]

    def _read(self) -> None:
        self._buffer += bytes(self._proc.readAllStandardOutput()).decode(errors="replace")
        *lines, self._buffer = self._buffer.split("\n")
        for line in lines:
            hit = self._parser.feed(line)
            if hit and hit[2] == "vertical" and hit[1] and self._is_ours(hit[0]):
                self.scrolled.emit(hit[1])
