from dimmery import core
from dimmery.dbusscroll import ScrollParser

CALL = (
    "method call time=1.5 sender=:1.921 -> destination=:1.910 serial=2 path=/StatusNotifierItem; "
    "interface=org.kde.StatusNotifierItem; member=Scroll"
)


def feed_all(parser, lines):
    return [hit for line in lines if (hit := parser.feed(line))]


def test_parser_extracts_destination_delta_and_orientation():
    hits = feed_all(ScrollParser(), [CALL, "   int32 120", '   string "vertical"'])
    assert hits == [(":1.910", 120, "vertical")]


def test_parser_ignores_other_messages_and_resets_between_calls():
    other = "method call time=1 sender=:1.1 -> destination=:1.2 serial=3 path=/x; interface=a.b; member=Other"
    lines = [other, "   int32 5", '   string "vertical"', CALL, "   int32 -120", '   string "vertical"']
    hits = feed_all(ScrollParser(), lines)
    assert hits == [(":1.910", -120, "vertical")]


def fake_ddc(monkeypatch, brightness):
    calls = []

    def ddc(cfg, *args):
        calls.append(args)
        if args[0] == "setvcp":
            brightness[0] = int(args[2])
        return f"VCP 10 C {brightness[0]} 100\n"

    monkeypatch.setattr(core, "ddc", ddc)
    return calls


def test_nudge_moves_by_step_and_a_later_tick_learns_the_settled_value(monkeypatch, tmp_path):
    level = [40]
    calls = fake_ddc(monkeypatch, level)
    core.tick(core.DEFAULTS, tmp_path)                  # seed: remembers 40
    core.nudge(core.DEFAULTS, tmp_path, steps=1)        # +5 -> 45
    ev = core.nudge(core.DEFAULTS, tmp_path, steps=1)   # +5 -> 50 (a burst of notches)
    assert ev["action"] == "scroll" and ev["target"] == 50
    assert [tuple(a) for a in calls].count(("setvcp", "10", "45")) == 1 and level[0] == 50
    learned = core.tick(core.DEFAULTS, tmp_path)        # the quiet-period tick: one lesson, the final value
    assert learned["action"] == "learn" and learned["read"] == 50
    assert learned["new"] == 47                         # 40 + 0.7 * (50 - 40)


def test_nudge_clamps_to_range_and_dry_run_writes_nothing(monkeypatch, tmp_path):
    level = [98]
    calls = fake_ddc(monkeypatch, level)
    core.nudge(core.DEFAULTS, tmp_path, steps=3, dry_run=True)
    assert not any(a[0] == "setvcp" for a in calls)
    assert core.read_events(tmp_path)[0]["target"] == 100


def test_plasma_percent_and_set_use_the_scaled_range(monkeypatch):
    seen = []

    def busctl(*args):
        seen.append(args)
        if args[0] == "get-property" and args[-1] == "DisplaysDBusNames":
            return 'as 1 "display0"\n'
        if args[-1] == "IsInternal":
            return "b false\n"
        return "i 10000\n" if args[-1] == "MaxBrightness" else "i 6000\n"

    monkeypatch.setattr(core, "_busctl", busctl)
    path = core.plasma_display()
    assert path == "/org/kde/ScreenBrightness/display0"
    assert core.plasma_percent(path) == 60
