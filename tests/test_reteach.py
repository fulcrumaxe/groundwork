"""Spaced teaching (F-90)."""
import unittest

from groundwork import reteach as rtmod

from test_web import handler_for, make_module


class DueForReteachTest(unittest.TestCase):
    def test_boundary(self):
        self.assertTrue(rtmod.due_for_reteach("2020-01-01", now="2020-01-31"))
        self.assertFalse(rtmod.due_for_reteach("2020-01-03", now="2020-01-31"))
        self.assertFalse(rtmod.due_for_reteach("", now="2020-01-31"))
        self.assertFalse(rtmod.due_for_reteach(None, now="2020-01-31"))
        self.assertFalse(rtmod.due_for_reteach("nope", now="2020-01-31"))
        self.assertFalse(rtmod.due_for_reteach("2020-01-01", now="nope"))


class PickTest(unittest.TestCase):
    def test_oldest_first_and_garbage(self):
        rows = [{"name": "b", "first_seen": "2020-01-01", "recording": "x"},
                {"name": "a", "first_seen": "2019-12-01", "recording": "y"},
                {"name": "fresh", "first_seen": "2020-01-30", "recording": "z"},
                "nope", None]
        out = rtmod.pick_reteach(rows, now="2020-02-01")
        self.assertEqual([r["name"] for r in out], ["a", "b"])
        self.assertEqual(rtmod.pick_reteach(None), [])
        self.assertEqual(rtmod.pick_reteach("nope"), [])


class FirstsTest(unittest.TestCase):
    def test_earliest_wins(self):
        rows = [("add", "2020-01-05", "second try"),
                ("add", "2020-01-01", "first words"),
                ("sub", "2020-01-03", "s")]
        got = rtmod.first_attempts(rows)
        by_name = {r["name"]: r for r in got}
        self.assertEqual(by_name["add"]["first_seen"], "2020-01-01")
        self.assertEqual(by_name["add"]["recording"], "first words")
        self.assertEqual(rtmod.first_attempts(None), [])


class CompareTest(unittest.TestCase):
    def test_overlap_and_empty(self):
        got = rtmod.compare_recordings("totals two numbers",
                                       "totals two numbers fast")
        self.assertIn("totals", got["shared"])
        self.assertGreater(got["growth"], 0)
        self.assertEqual(got["verdict"], "growing")
        self.assertEqual(rtmod.compare_recordings("", "x")["verdict"],
                         "no-comparison")
        self.assertEqual(rtmod.compare_recordings(None, None)["verdict"],
                         "no-comparison")


class BoxTest(unittest.TestCase):
    def test_empty_renders_nothing(self):
        self.assertEqual(rtmod.reteach_box_html([]), "")
        self.assertEqual(rtmod.reteach_box_html(None), "")

    def test_due_renders_quote_and_prompt(self):
        out = rtmod.reteach_box_html([{"name": "add",
                                       "recording": "totals <b>nums"}])
        self.assertIn("id='reteach'", out)
        self.assertIn("totals &lt;b&gt;nums", out)
        self.assertIn("Explain add again", out)


class CallerEffectTest(unittest.TestCase):
    def test_fresh_due_has_no_reteach_box(self):
        tmp, db, server, out = make_module("reteach mod")
        h = handler_for(db)
        body = h.due_html()
        self.assertNotIn("id='reteach'", body)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{rtmod.STATUS_ANCHOR}'",
                      rtmod.section_html())
        e = rtmod.tour_entry()
        self.assertEqual(e["id"], "reteach-30d")
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["anchor"], rtmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
