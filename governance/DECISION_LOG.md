# Decision Log

Non-obvious decisions and their reasoning. Append-only; the next entry takes the next free `D-NNN`.

Status: 🔵 Pending review · ✅ Accepted · 🚫 Rejected · 🟡 Reverted

---

### D-001: Keep the decision logic pure

- **Date:** 16/10/2026
- **Decision:** `step()` in `core.py` takes state in and returns state out; I/O (ddcutil, config, state) lives beside it, and Qt never enters `core.py`.
- **Reason:** the logic is testable without a monitor, and tests never write to hardware.
- **Status:** ✅ Accepted

### D-002: Learning rule is an exponential blend

- **Date:** 18/10/2026
- **Decision:** `new = old + alpha * (your_value - old)` with `alpha` 0.7; the first value of a slot is stored as is; empty slots are interpolated between known neighbours.
- **Reason:** blending an empty slot with a distant neighbour gave wrong values; 0.5 adapted too slowly in daily use.
- **Alternatives considered:** copy the nearest slot (rejected: step changes), `alpha` 0.5 (replaced).
- **Status:** ✅ Accepted

### D-003: Autostart through an XDG `.desktop`, not a systemd timer

- **Date:** 16/10/2026
- **Decision:** `~/.config/autostart/dimmery.desktop` launches `dimmery gui`, which runs the ticks itself. `contrib/systemd/` stays as an optional alternative.
- **Reason:** the tray is the main interface and needs the graphical session anyway.
- **Implication:** enabling the timer together with the GUI would run two tick loops.
- **Status:** ✅ Accepted (validated 21/10/2026, see `BACKLOG.md`)

### D-004: Write brightness through PowerDevil, fall back to ddcutil

- **Date:** 17/10/2026
- **Decision:** writes go through Plasma so its slider, tooltip and OSD stay in sync; `plasma = false` forces ddcutil.
- **Reason:** writing only with ddcutil left Plasma showing a stale value.
- **Status:** ✅ Accepted

### D-005: Wheel gestures are learned once, after they settle

- **Date:** 18/10/2026
- **Decision:** a burst of wheel notches over the tray icon is learned once, 10 s after it stops.
- **Reason:** learning every notch taught intermediate values.
- **Status:** ✅ Accepted
