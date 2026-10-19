# Changelog

Format inspired by [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

- 16/10/2026 -> Initial version: per-weekday learned brightness over DDC/CI, CLI (`tick`, `show`, `gui`) and tray window.
- 16/10/2026 -> Trim inherited template scaffolding; add `--version`, type hints and CLI tests.
- 16/10/2026 -> Minimalist bedside-lamp tray icon, white on dark themes and near-black on light ones, drawn with QPainter (no SVG dependency).
- 16/10/2026 -> About dialog (tray menu and window button).
- 16/10/2026 -> Learning an empty slot stores your value as is; it is no longer blended with a distant neighbour slot.
- 16/10/2026 -> About and `--version` show the build (commit hash, date and time, `-dirty`); tray menu gets "Restart".
- 16/10/2026 -> Mouse wheel over the tray icon adjusts the brightness (`scroll_step`, learned immediately).
- 16/10/2026 -> Writes go through Plasma (PowerDevil) so its slider, tooltip and OSD stay in sync; the tray tooltip shows the brightness Plasma reports; hi-res wheels count 120 per notch. Falls back to ddcutil (`plasma = false` forces it).
- 17/10/2026 -> Reading the brightness validates ddcutil output (clear error instead of a bare ValueError) and the post-write confirmation is best effort.
- 18/10/2026 -> Unreachable monitor is logged once as `offline` (and `recovered`), not as an error every tick; all events carry a UTC offset; the dbus-monitor child dies with the app (SIGTERM handler + pdeathsig); `dimmery scroll-test` and `scroll_notch` calibrate the wheel, gestures are logged as `scroll_input`.
- 18/10/2026 -> Learning quality: wheel bursts are learned once, 10 s after they stop; an empty slot is interpolated between its known neighbours instead of copying the nearest one; default `alpha` 0.5 -> 0.7.
