# Backlog

Prioritized pending work.

## Priority

- [ ] Review the long-run behaviour: events recorded since 16/10/2026 have not been audited for gaps or drift.

## Important

- [ ] Define what "1.0" means (candidate: long-run review done, no known failures within the current limits).

## Nice to have

- [ ] Catch changes that are undone between two ticks (today a tick only compares against what dimmery last applied).
- [ ] Support more than one monitor per run (`display` or `serial` in the config is single-valued today).

## Icebox

- Learn changes made on the monitor's own OSD: not validated, not needed for now (decided 21/10/2026). To test: change the brightness with the monitor buttons, wait one tick and check `events.jsonl`.

## Done

- Autostart after reboot (21/10/2026): `~/.config/autostart/dimmery.desktop` runs `dimmery gui`; first tick logged 2 minutes after the boot of 20/10/2026. The `contrib/systemd` units are an unused alternative.
