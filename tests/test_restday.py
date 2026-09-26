"""Rest-day affirmations (F-122): breaks framed as consolidation."""
import unittest
from datetime import datetime, timezone

from test_web import handler_for, make_module

from groundwork import restday as mod


def _now():
    return datetime(2026, 9, 26, 12, 0, 0, tzinfo=timezone.utc)


def _rows(*dates):
    return [(5, f"{d}T10:00:00Z") for d in dates]


class IdleDaysTest(unittest.TestCase):
    def test_counts_days_since_newest(self):
        self.assertEqual(mod.idle_days_from_rows(_rows("2026-09-25"), _now()), 1)
        self.assertEqual(
            mod.idle_days_from_rows(_rows("2026-09-20", "2026-09-24"), _now()), 2)

    def test_same_day_is_zero(self):
        self.assertEqual(mod.idle_days_from_rows(_rows("2026-09-26"), _now()), 0)

    def test_no_rows_never_raises(self):
        self.assertEqual(mod.idle_days_from_rows([], _now()), 0)
        self.assertEqual(mod.idle_days_from_rows(None, _now()), 0)
        self.assertEqual(mod.idle_days_from_rows("junk", _now()), 0)


class RestDayTest(unittest.TestCase):
    def test_empty_queue_after_idle_day_is_rest(self):
        self.assertTrue(mod.is_rest_day(0, 1))
        self.assertTrue(mod.is_rest_day([], 3))

    def test_nonempty_queue_is_never_rest(self):
        self.assertFalse(mod.is_rest_day(2, 5))
        self.assertFalse(mod.is_rest_day([{"id": "c1"}], 5))

    def test_same_day_clear_is_not_rest(self):
        self.assertFalse(mod.is_rest_day(0, 0))

    def test_hostile_never_raises_never_rest(self):
        self.assertFalse(mod.is_rest_day(None, None))
        self.assertFalse(mod.is_rest_day("nope", object()))
        self.assertFalse(mod.is_rest_day(-1, -2))


class AffirmationTest(unittest.TestCase):
    def test_rest_day_returns_consolidation_line(self):
        msg = mod.affirmation_for(0, 1)
        self.assertIn("consolidat", msg)

    def test_lines_rotate_by_idle_days(self):
        msgs = {mod.affirmation_for(0, d) for d in (1, 2, 3)}
        self.assertEqual(msgs, set(mod.REST_LINES))

    def test_fallback_is_empty_string(self):
        self.assertEqual(mod.affirmation_for(2, 5), "")
        self.assertEqual(mod.affirmation_for(0, 0), "")
        self.assertEqual(mod.affirmation_for(None, None), "")
        self.assertEqual(mod.affirmation_for("junk", object()), "")

    def test_no_streak_no_stats_language(self):
        for d in (1, 2, 3, 30):
            msg = mod.affirmation_for(0, d).lower()
            self.assertNotIn("streak", msg)
            self.assertNotIn("accuracy", msg)
            self.assertNotIn("pledge", msg)


class HtmlTest(unittest.TestCase):
    def test_rest_banner_shape(self):
        body = mod.restday_html(0, 1)
        self.assertIn(f"id='{mod.SECTION_ANCHOR}'", body)
        self.assertIn("consolidat", body)

    def test_fallback_renders_nothing(self):
        self.assertEqual(mod.restday_html(2, 5), "")
        self.assertEqual(mod.restday_html(0, 0), "")
        self.assertEqual(mod.restday_html(None, None), "")

    def test_fallback_composes_byte_identical(self):
        page = "<div id='queue'>all clear</div>"
        self.assertEqual(page + mod.restday_html(1, 0), page)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "feature")
        self.assertEqual(entry["path"], "/status")
        self.assertEqual(entry["anchor"], mod.STATUS_ANCHOR)


class CallerEffectTest(unittest.TestCase):
    def test_busy_queue_renders_no_banner(self):
        _tmp, db, _s, _out = make_module("restday busy")
        due = handler_for(db).due_html()
        self.assertNotIn(f"id='{mod.SECTION_ANCHOR}'", due)

    def test_caller_inputs_compose_to_banner(self):
        # The exact values due_html appends: empty queue + idle rows.
        idle = mod.idle_days_from_rows(_rows("2026-09-20"), _now())
        self.assertGreaterEqual(idle, 1)
        body = mod.restday_html(0, idle)
        self.assertIn(f"id='{mod.SECTION_ANCHOR}'", body)


if __name__ == "__main__":
    unittest.main()
