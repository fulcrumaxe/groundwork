"""Timezone-explicit timestamps with title tooltips (I-26)."""
import unittest

from groundwork import tztime as mod

from test_web import handler_for, make_module


class StampTest(unittest.TestCase):
    def test_recent_relative_with_utc_title(self):
        body = mod.stamp_html("2026-01-05T10:00:00Z")
        self.assertIn("<time datetime='2026-01-05T10:00:00Z'", body)
        self.assertIn("(UTC)", body)

    def test_old_absolute_carries_utc_suffix(self):
        body = mod.stamp_html("2020-01-05T10:00:00Z")
        self.assertIn("2020-01-05 UTC", body)
        self.assertIn("(UTC)", body)

    def test_day_cells(self):
        body = mod.day_html("2026-01-05")
        self.assertIn("<time datetime='2026-01-05'", body)
        self.assertIn("(UTC)", body)

    def test_hostile_never_raises(self):
        for bad in (None, "", "not-a-date", 12345, [], {}):
            with self.subTest(bad=bad):
                out = mod.stamp_html(bad)
                self.assertIn("<time", out)
                self.assertIn("unknown", out)
                out = mod.day_html(bad)
                self.assertIn("<time", out)

    def test_escapes_hostile_raw(self):
        body = mod.stamp_html("2026-01-05' onmouseover='x")
        self.assertNotIn("onmouseover='x'", body.replace(
            "title='unknown date (UTC)'", ""))

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(), {
            "id": "timezone-stamps", "kind": "improvement",
            "title": "Timezone-explicit stamps",
            "blurb": ("Hover any attempt time for the exact UTC instant "
                      "— no more guessing zones."),
            "path": "/reviews", "anchor": "timestamps"})


class CallerEffectTest(unittest.TestCase):
    def test_attempt_rows_carry_utc_titles(self):
        _tmp, db, server, _o = make_module("tztime caller")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        body = handler_for(db).history_html()
        self.assertIn("(UTC)", body)
        self.assertIn("id='timestamps'", body)

    def test_coverage_dates_wrapped(self):
        _tmp, db, server, _o = make_module("tztime coverage")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        body = handler_for(db).history_html()
        self.assertIn("id='coverage'", body)
        self.assertRegex(body, r"<time datetime='\d{4}-\d{2}-\d{2}'")


if __name__ == "__main__":
    unittest.main()
