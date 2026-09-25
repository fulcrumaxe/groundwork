"""Mascot companion (F-117)."""
import unittest

from groundwork import mascot as mod

from test_web import handler_for, make_module


class MoodTest(unittest.TestCase):
    def test_resting_without_guilt(self):
        mood = mod.mood_for(0)
        self.assertEqual(mood["mood"], "resting")
        self.assertIn("ready when you are", mood["line"])
        for word in ("streak", "skipped", "lazy", "behind"):
            self.assertNotIn(word, mood["line"])

    def test_effort_ladder(self):
        self.assertEqual(mod.mood_for(1)["mood"], "warming")
        self.assertEqual(mod.mood_for(5)["mood"], "stride")
        self.assertEqual(mod.mood_for(12)["mood"], "deep")

    def test_never_mentions_wins(self):
        for n in (0, 1, 5, 12):
            line = mod.mood_for(n)["line"]
            for word in ("accuracy", "score", "streak", "win"):
                self.assertNotIn(word, line)

    def test_hostile_rests(self):
        self.assertEqual(mod.mood_for(None)["mood"], "resting")
        self.assertEqual(mod.mood_for("x")["mood"], "resting")
        self.assertEqual(mod.attempts_today("/nonexistent.db"), 0)

    def test_line_always_renders(self):
        body = mod.line_html("/nonexistent.db")
        self.assertIn(f"id='{mod.SECTION_ANCHOR}'", body)

    def test_css_has_no_style_tags(self):
        self.assertNotIn("<style", mod.mascot_css())

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "feature")
        self.assertEqual(entry["path"], "/due")


class CallerEffectTest(unittest.TestCase):
    def test_due_page_carries_mascot(self):
        _tmp, db, _s, _out = make_module("mascot due")
        body = handler_for(db).due_html()
        self.assertIn(f"id='{mod.SECTION_ANCHOR}'", body)
        self.assertIn("resting", body)

    def test_mascot_notices_attempts(self):
        from groundwork import db as dbmod
        _tmp, db, _s, _out = make_module("mascot effort")
        from groundwork import sched as schedmod
        now = schedmod.iso(schedmod.utcnow())
        con = dbmod.connect(db)
        try:
            card = con.execute("SELECT id FROM cards LIMIT 1").fetchone()[0]
            for _ in range(4):
                con.execute(
                    "INSERT INTO reviews(card_id, grade, confidence,"
                    " reviewed_at) VALUES(?, 3, 3, ?)", (card, now))
            con.commit()
        finally:
            con.close()
        body = handler_for(db).due_html()
        self.assertIn("in stride", body)


if __name__ == "__main__":
    unittest.main()
