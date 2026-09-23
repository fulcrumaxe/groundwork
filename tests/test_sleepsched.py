"""Sleep-aware scheduling (F-93): new cards never land late at night."""
import unittest
from datetime import datetime, timezone

from groundwork import db as dbmod
from groundwork import sched as schedmod
from groundwork import sleepsched as smod

from test_web import make_module

NIGHT = datetime(2026, 1, 2, 2, 0, 0, tzinfo=timezone.utc)


class QuietHoursTest(unittest.TestCase):
    def test_night_hour_is_quiet(self):
        self.assertTrue(smod.in_quiet_hours(hour=23))
        self.assertTrue(smod.in_quiet_hours(hour=3))

    def test_day_hour_is_not_quiet(self):
        self.assertFalse(smod.in_quiet_hours(hour=12))
        self.assertFalse(smod.in_quiet_hours(hour=7))

    def test_unparseable_never_defers(self):
        self.assertFalse(smod.in_quiet_hours(now="not-a-time"))
        self.assertFalse(smod.in_quiet_hours(hour="nope"))


class AdjustDueTest(unittest.TestCase):
    def test_night_due_moves_to_morning(self):
        self.assertEqual(
            smod.adjust_due("2026-01-02T03:15:00Z"),
            "2026-01-02T07:00:00Z")

    def test_day_due_passes_through(self):
        due = "2026-01-02T14:00:00Z"
        self.assertEqual(smod.adjust_due(due), due)

    def test_legacy_bad_input_unchanged(self):
        self.assertEqual(smod.adjust_due("garbage"), "garbage")
        self.assertIsNone(smod.adjust_due(None))
        self.assertEqual(smod.adjust_due(42), 42)

    def test_morning_after_late_review(self):
        self.assertEqual(
            smod.morning_after_late_review("2026-01-02T02:00:00Z"),
            "2026-01-02T07:00:00Z")


class DeferNightNewTest(unittest.TestCase):
    def test_behavioral_effect_new_card_deferred_reviewed_kept(self):
        cards = [
            {"id": "new1", "due": "2026-01-02T02:00:00Z"},
            {"id": "old1", "due": "2026-01-02T02:00:00Z",
             "grade": 4, "reviewed_at": "2026-01-01T10:00:00Z"},
        ]
        out = smod.defer_night_new(cards)
        self.assertEqual(out[0]["due"], "2026-01-02T07:00:00Z")
        self.assertEqual(out[1]["due"], "2026-01-02T02:00:00Z")
        self.assertEqual(cards[0]["due"], "2026-01-02T02:00:00Z")

    def test_reviewed_ids_set_decides_newness(self):
        cards = [{"id": "n", "due": "2026-01-02T02:00:00Z"},
                 {"id": "r", "due": "2026-01-02T02:00:00Z"}]
        out = smod.defer_night_new(cards, reviewed_ids={"r"})
        self.assertEqual(out[0]["due"], "2026-01-02T07:00:00Z")
        self.assertEqual(out[1]["due"], "2026-01-02T02:00:00Z")

    def test_day_queue_unchanged(self):
        cards = [{"id": "n", "due": "2026-01-02T15:00:00Z"}]
        self.assertEqual(smod.defer_night_new(cards), cards)

    def test_is_new_card_guards_shapes(self):
        self.assertFalse(smod.is_new_card("nope"))
        self.assertTrue(smod.is_new_card({}))
        self.assertFalse(smod.is_new_card({"grades": [4, 5]}))

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{smod.STATUS_ANCHOR}'", smod.section_html())
        e = smod.tour_entry()
        self.assertEqual(e["id"], "sleep-aware-scheduling")
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["anchor"], smod.STATUS_ANCHOR)


class CallerEffectTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("sleep mod")
        dbmod.init_db(self.db)
        cards = self.server.tool_list_due_reviews({"limit": 20})["due"]
        self.card_id = cards[0]["id"]
        orig = schedmod.utcnow
        schedmod.utcnow = lambda: NIGHT
        self.addCleanup(setattr, schedmod, "utcnow", orig)

    def _stored_due(self, card_id):
        con = dbmod.connect(self.db)
        try:
            return con.execute("SELECT due FROM cards WHERE id=?",
                               (card_id,)).fetchone()[0]
        finally:
            con.close()

    def test_first_night_review_stores_morning_due(self):
        self.server.submit_review(self.card_id, "5", 4)
        self.assertTrue(self._stored_due(self.card_id).endswith(
            "T07:00:00Z"))

    def test_repeat_night_review_keeps_scheduler_due(self):
        self.server.submit_review(self.card_id, "5", 4)
        self.server.submit_review(self.card_id, "5", 4)
        self.assertTrue(self._stored_due(self.card_id).endswith(
            "T02:00:00Z"))

    def test_queue_listing_defers_only_new_cards(self):
        con = dbmod.connect(self.db)
        try:
            con.execute("UPDATE cards SET due='2026-01-02T02:00:00Z'")
            con.commit()
        finally:
            con.close()
        before = {c["id"]: c["due"] for c in
                  self.server.tool_list_due_reviews({"limit": 20})["due"]}
        self.assertEqual(before[self.card_id], "2026-01-02T07:00:00Z")
        self.server.submit_review(self.card_id, "5", 4)
        con = dbmod.connect(self.db)
        try:
            con.execute("UPDATE cards SET due='2026-01-02T02:00:00Z'"
                        " WHERE id=?", (self.card_id,))
            con.commit()
        finally:
            con.close()
        after = {c["id"]: c["due"] for c in
                 self.server.tool_list_due_reviews({"limit": 20})["due"]}
        self.assertEqual(after[self.card_id], "2026-01-02T02:00:00Z")


if __name__ == "__main__":
    unittest.main()
