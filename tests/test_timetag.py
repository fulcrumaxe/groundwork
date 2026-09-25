"""Unify all timestamps into <time datetime> (I-93)."""
import unittest

from groundwork import timetag as mod

from test_web import handler_for, make_module


class RouterTest(unittest.TestCase):
    def test_instant_routes_relative(self):
        body = mod.stamp("2026-01-05T10:00:00Z")
        self.assertIn("<time datetime='2026-01-05T10:00:00Z'", body)
        self.assertIn("(UTC)", body)

    def test_day_routes_short(self):
        body = mod.stamp("2026-01-05")
        self.assertIn("<time datetime='2026-01-05'", body)
        self.assertIn("(UTC)", body)

    def test_missing_never_blank(self):
        for bad in (None, "", [], {}):
            with self.subTest(bad=bad):
                out = mod.stamp(bad)
                self.assertIn("<time", out)
                self.assertIn("unknown", out)

    def test_hostile_never_raises(self):
        out = mod.stamp("'<script>alert(1)</script>")
        self.assertNotIn("<script>alert", out)
        self.assertIn("<time", out)

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(), {
            "id": "one-stamp", "kind": "improvement",
            "title": "One stamp everywhere",
            "blurb": ("Every date on every page is a real <time> element "
                      "— hover for the exact instant."),
            "path": "/reviews", "anchor": "attempts"})


class UnifyTest(unittest.TestCase):
    def test_history_days_wrapped(self):
        _tmp, db, server, _o = make_module("timetag days")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        body = handler_for(db).history_html()
        self.assertRegex(body, r"<time datetime='\d{4}-\d{2}-\d{2}'")

    def test_no_bare_day_cells_on_history(self):
        import re
        _tmp, db, server, _o = make_module("timetag bare")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        body = handler_for(db).history_html()
        bare = re.findall(r"<td>(\d{4}-\d{2}-\d{2})</td>", body)
        self.assertEqual(bare, [])

    def test_sections_use_unified_stamps(self):
        from groundwork import learnresume as lrmod
        from groundwork import milestones as msmod
        _tmp, db, _s, _o = make_module("timetag sections")
        for section in (lrmod.section_html(db), msmod.section_html(db)):
            self.assertNotRegex(section, r"<td>\d{4}-\d{2}-\d{2}</td>")


if __name__ == "__main__":
    unittest.main()
