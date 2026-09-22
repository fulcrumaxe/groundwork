"""Optimal review-time suggestions (F-92)."""
import unittest

from groundwork import peaktime as ptmod

from test_web import handler_for, make_module


def _rows():
    return ([(5, "2020-01-01T19:00:00Z")] * 4
            + [(5, "2020-01-02T20:00:00Z")]
            + [(1, "2020-01-01T07:00:00Z")] * 2)


class PeaktimeTest(unittest.TestCase):
    def test_evening_biased_suggests_evening(self):
        got = ptmod.suggest(_rows())
        self.assertEqual(got["window"], "evening")
        self.assertEqual(got["n"], 5)

    def test_morning_biased_suggests_morning(self):
        rows = [(5, "2020-01-01T07:00:00Z")] * 3
        self.assertEqual(ptmod.suggest(rows)["window"], "morning")

    def test_below_threshold_falls_back(self):
        for rows in ([], None, [(5, "2020-01-01T19:00:00Z")] * 2):
            got = ptmod.suggest(rows)
            self.assertIsNone(got["window"])
            self.assertEqual(got["label"], "no peak yet")
            self.assertEqual(ptmod.banner_html(rows), "")

    def test_bucket_boundaries(self):
        self.assertEqual(ptmod.bucket_for(5), "morning")
        self.assertEqual(ptmod.bucket_for(11), "midday")
        self.assertEqual(ptmod.bucket_for(17), "evening")
        self.assertEqual(ptmod.bucket_for(23), "night")
        self.assertEqual(ptmod.bucket_for(0), "night")
        self.assertEqual(ptmod.bucket_for("nope"), "morning")

    def test_garbage_rows_skipped(self):
        table = ptmod.summarize([None, 42, ("x", "y"), ("5", None)])
        self.assertEqual(sum(v["n"] for v in table.values()), 0)

    def test_min_attempts_gate(self):
        rows = [(5, "2020-01-01T19:00:00Z"), (1, "2020-01-01T19:00:00Z")]
        self.assertIsNone(ptmod.suggest(rows)["window"])


class CallerEffectTest(unittest.TestCase):
    def test_fresh_due_renders_as_today(self):
        tmp, db, server, out = make_module("peak mod")
        h = handler_for(db)
        body = h.due_html()
        self.assertNotIn("id='peaktime'", body)

    def test_banner_names_window(self):
        out = ptmod.banner_html(_rows())
        self.assertIn("id='peaktime'", out)
        self.assertIn("evening", out)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{ptmod.STATUS_ANCHOR}'",
                      ptmod.section_html())
        e = ptmod.tour_entry()
        self.assertEqual(e["id"], "recall-peak-time")
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["anchor"], ptmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
