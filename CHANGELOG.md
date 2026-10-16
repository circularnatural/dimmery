# Changelog

Format inspired by [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

- 16/10/2026 -> Initial version: per-weekday learned brightness over DDC/CI, CLI (`tick`, `show`, `gui`) and tray window.
- 16/10/2026 -> Trim inherited template scaffolding; add `--version`, type hints and CLI tests.
- 16/10/2026 -> Minimalist bedside-lamp tray icon, white on dark themes and near-black on light ones, drawn with QPainter (no SVG dependency).
- 16/10/2026 -> About dialog (tray menu and window button).
- 16/10/2026 -> Learning an empty slot stores your value as is; it is no longer blended with a distant neighbour slot.
