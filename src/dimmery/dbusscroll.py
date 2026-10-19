"""Parse ``dbus-monitor`` output for StatusNotifierItem ``Scroll`` calls (pure, no Qt)."""

import re

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
