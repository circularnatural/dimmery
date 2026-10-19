import unittest
from datetime import datetime

from dimmery.core import DEFAULTS, daytype, lookup, step

CFG = dict(DEFAULTS)
MON = datetime(2026, 10, 12, 10, 0)   # Monday 10:00 -> slot 20
SAT = datetime(2026, 10, 17, 10, 0)


class T(unittest.TestCase):
    def test_daytype(self):
        self.assertEqual(daytype(MON), "mon")
        self.assertEqual(daytype(SAT), "sat")

    def test_first_run_seeds_and_does_nothing(self):
        s, ev = step({}, MON, 60, CFG)
        self.assertEqual(s["table"]["mon"]["20"], 60)
        self.assertEqual(ev["action"], "none")

    def test_applies_remembered_value(self):
        s = {"table": {"mon": {"20": 40}}, "last": 70}
        s, ev = step(s, MON, 70, CFG)
        self.assertEqual((ev["action"], ev["target"]), ("apply", 40))
        self.assertEqual(s["last"], 40)

    def test_manual_change_is_learned_not_overwritten(self):
        s = {"table": {"mon": {"20": 40}}, "last": 40}
        s, ev = step(s, MON, 80, CFG)                      # user moved 40 -> 80
        self.assertEqual(ev["action"], "learn")
        self.assertEqual(s["table"]["mon"]["20"], 68)
        self.assertEqual(s["last"], 80)                    # screen untouched this tick

    def test_learning_one_day_leaves_others_alone(self):
        s = {"table": {"mon": {"20": 40}}, "last": 40}
        s, ev = step(s, SAT, 90, CFG)                      # user sets 90 on a saturday
        self.assertEqual(ev["action"], "learn")
        self.assertEqual(s["table"]["sat"]["20"], 90)      # first lesson for that day: take it as is
        self.assertEqual(s["table"]["mon"]["20"], 40)

    def test_empty_slot_interpolates_between_neighbours_across_midnight(self):
        # slot 1 sits 2 slots after 47 (30) and 19 before 20 (90): 30 + 60 * 2/21
        self.assertEqual(lookup({"47": 30, "20": 90}, 1, 48), 36)

    def test_empty_slot_midway_gets_the_midpoint(self):
        self.assertEqual(lookup({"10": 20, "30": 60}, 20, 48), 40)

    def test_single_known_slot_is_used_everywhere(self):
        self.assertEqual(lookup({"10": 20}, 33, 48), 20)

    def test_empty_slot_learns_value_as_is_not_blended_with_neighbour(self):
        s = {"table": {"mon": {"1": 8}}, "last": 8}        # only a far-away slot is known
        s, ev = step(s, MON, 70, CFG)
        self.assertEqual((ev["action"], ev["old"], ev["new"]), ("learn", None, 70))
        self.assertEqual(s["table"]["mon"]["20"], 70)

    def test_empty_day_borrows_from_other_days(self):
        s = {"table": {"mon": {"20": 40}, "tue": {"20": 60}}, "last": 70}
        s, ev = step(s, SAT, 70, CFG)                      # saturday has nothing yet
        self.assertEqual((ev["action"], ev["target"]), ("apply", 50))

    def test_small_noise_ignored(self):
        s = {"table": {"mon": {"20": 40}}, "last": 40}
        s, ev = step(s, MON, 41, CFG)
        self.assertEqual(ev["action"], "none")

if __name__ == "__main__":
    unittest.main()
