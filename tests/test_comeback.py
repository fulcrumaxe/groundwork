"""Comeback path after 30 idle days (F-123): gentle recap, no shame."""
import unittest

from test_web import handler_for, make_module

from groundwork import comeback as cmod


def _row(name, when):
    return {"name": name, "reviewed_at": when}


class IdleDaysTest(unittest.TestCase):
    def test_boundary_29_no_30_yes(self):
        self.assertFalse(cmod.is_comeback("2026-08-22", "2026-09-20"))
        self.assertTrue(cmod.is_comeback("2026-08-21", "2026-09-20"))
        self.assertTrue(cmod.is_comeback("2026-01-01", "2026-09-20"))

    def test_idle_days_count(self):
        self.assertEqual(cmod.idle_days("2026-09-01", "2026-09-20"), 19)
        self.assertEqual(cmod.idle_days("2026-09-20", "2026-09-20"), 0)

    def test_hostile_inputs_fail_closed(self):
        for bad in (None, "", "not-a-date", 42, [], {}):
            self.assertIsNone(cmod.idle_days(bad, "2026-09-20"))
            self.assertFalse(cmod.is_comeback(bad, "2026-09-20"))
        self.assertIsNone(cmod.idle_days("2026-09-01", "junk"))
        self.assertFalse(cmod.is_comeback("2026-09-01", "junk"))

    def test_future_last_seen_clamps_zero(self):
        self.assertEqual(cmod.idle_days("2026-09-21", "2026-09-20"), 0)
        self.assertFalse(cmod.is_comeback("2026-09-21", "2026-09-20"))


class LastSeenTest(unittest.TestCase):
    def test_newest_wins(self):
        rows = [_row("a", "2026-07-01T10:00:00Z"),
                _row("b", "2026-08-15T10:00:00Z")]
        self.assertEqual(cmod.last_seen_from(rows), "2026-08-15T10:00:00Z")

    def test_skips_malformed(self):
        self.assertEqual(cmod.last_seen_from([{}, {"reviewed_at": "junk"},
                                              None, 42]), "")
        self.assertEqual(cmod.last_seen_from([]), "")
        self.assertEqual(cmod.last_seen_from(None), "")


class RecapItemsTest(unittest.TestCase):
    def test_newest_distinct_capped(self):
        rows = [_row("a", "2026-08-01"), _row("b", "2026-08-10"),
                _row("a", "2026-08-20"), _row("c", "2026-08-05")]
        out = cmod.recap_items(rows, limit=2)
        self.assertEqual([i["name"] for i in out], ["a", "b"])

    def test_bad_limit_falls_back(self):
        rows = [_row("a", "2026-08-01")]
        self.assertEqual(len(cmod.recap_items(rows, limit="junk")), 1)
        self.assertEqual(cmod.recap_items(rows, limit=0), [])

    def test_hostile_rows_skipped(self):
        self.assertEqual(cmod.recap_items([{}, None, ("", "junk")]), [])


class BoxTest(unittest.TestCase):
    def test_hidden_when_active_or_unknown(self):
        self.assertEqual(cmod.comeback_box_html("2026-09-19", "2026-09-20"), "")
        self.assertEqual(cmod.comeback_box_html("", "2026-09-20"), "")
        self.assertEqual(cmod.comeback_box_html(None, "2026-09-20"), "")
        self.assertEqual(cmod.comeback_box_html("junk", "2026-09-20"), "")

    def test_gentle_recap_when_away(self):
        rows = [_row("fractions", "2026-07-01T10:00:00Z")]
        body = cmod.comeback_box_html(rows=rows, now="2026-09-20")
        self.assertIn("id='comeback'", body)
        self.assertIn("Welcome back", body)
        self.assertIn("fractions", body)
        self.assertIn("mode=one", body)
        self.assertNotIn("streak lost", body)
        self.assertNotIn("overdue", body.lower())

    def test_escapes_names(self):
        body = cmod.comeback_box_html("2026-01-01", "2026-09-20",
                                      items=[{"name": "<b>x</b>"}])
        self.assertNotIn("<b>x</b>", body)
        self.assertIn("&lt;b&gt;", body)

    def test_rows_derive_last_seen(self):
        rows = [_row("a", "2026-01-05T00:00:00Z")]
        self.assertIn("away", cmod.comeback_box_html(rows=rows,
                                                     now="2026-09-20"))

    def test_status_and_tour_shape(self):
        self.assertIn(f"id='{cmod.STATUS_ANCHOR}'", cmod.section_html())
        self.assertIn("groundwork/comeback.py", cmod.section_html())
        self.assertEqual(cmod.tour_entry(), {
            "id": "comeback-30d", "kind": "feature",
            "title": "Comeback after time away",
            "blurb": ("Away 30 days? A gentle recap greets you — no shame, "
                      "one card restarts the loop."),
            "path": "/status", "anchor": cmod.STATUS_ANCHOR})


class CallerEffectTest(unittest.TestCase):
    def test_active_library_renders_no_banner(self):
        _tmp, db, _s, _out = make_module("comeback active")
        due = handler_for(db).due_html()
        self.assertNotIn("id='comeback'", due)

    def test_caller_row_shape_composes_to_banner(self):
        # The exact rows due_html passes: name/reviewed_at dicts folded
        # from its already-fetched first_rows.
        rows = [_row("fractions", "2026-07-01T10:00:00Z")]
        body = cmod.comeback_box_html(rows=rows, now="2026-09-20")
        self.assertIn("id='comeback'", body)


if __name__ == "__main__":
    unittest.main()
