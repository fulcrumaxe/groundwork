"""Still-with-us reading nudge (I-144)."""
import unittest

from groundwork import readnudge as mod

from test_web import handler_for, make_module


class NudgeTest(unittest.TestCase):
    def test_threshold(self):
        self.assertTrue(mod.should_nudge(0, 600))
        self.assertTrue(mod.should_nudge(0, 3600))
        self.assertFalse(mod.should_nudge(0, 599))

    def test_hostile_reads_false(self):
        self.assertFalse(mod.should_nudge("x", "y"))
        self.assertFalse(mod.should_nudge(None, None))
        self.assertFalse(mod.should_nudge(0, 100, idle="x"))
        self.assertFalse(mod.should_nudge(0, 100, idle=0))

    def test_banner_shape(self):
        body = mod.nudge_html()
        self.assertIn("id='readnudge'", body)
        self.assertIn("Still with us?", body)
        self.assertIn("hidden", body)
        self.assertIn("600", body)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "improvement")
        self.assertEqual(entry["anchor"], mod.STATUS_ANCHOR)


class CallerEffectTest(unittest.TestCase):
    def test_module_page_carries_nudge(self):
        _tmp, db, _s, out = make_module("readnudge caller")
        body = handler_for(db).module_html(out["module_id"])
        self.assertIn("id='readnudge'", body)
        self.assertIn("data-readnudge", body)


if __name__ == "__main__":
    unittest.main()
