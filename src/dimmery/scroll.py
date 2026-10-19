"""Mouse-wheel on the tray icon.

Qt's QSystemTrayIcon ignores the StatusNotifierItem ``Scroll`` call that KDE sends when you spin the wheel
over the icon, so we watch for it with ``dbus-monitor`` and keep only the calls addressed to this process.
"""

import os
import shutil

from PyQt6.QtCore import QObject, QProcess, pyqtSignal
from PyQt6.QtDBus import QDBusConnection

from dimmery.dbusscroll import MATCH, ScrollParser


class ScrollWatcher(QObject):
    scrolled = pyqtSignal(int)  # raw wheel delta: +-120 per notch, smaller steps on hi-res wheels

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._parser, self._buffer, self._ours = ScrollParser(), "", {}
        self._proc = QProcess(self)
        self._proc.readyReadStandardOutput.connect(self._read)

    def start(self) -> None:
        cmd = ["dbus-monitor", "--session", MATCH]
        if shutil.which("setpriv"):  # the monitor must die with us, however we die (SIGKILL, crash, ...)
            cmd = ["setpriv", "--pdeathsig", "SIGTERM", *cmd]
        self._proc.start(cmd[0], cmd[1:])

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
