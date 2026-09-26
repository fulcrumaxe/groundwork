"""Anti-streak pledge (F-124): the why behind never counting streaks."""
import unittest

from test_web import make_module

from groundwork import antistreak as antistreakmod
from groundwork import history as histmod


class PledgeTest(unittest.TestCase):
    def test_three_reasons(self):
        rs = antistreakmod.reasons()
        self.assertEqual(len(rs), 3)
        for title, body in rs:
            self.assertTrue(title and body)

    def test_pledge_line(self):
        self.assertEqual(antistreakmod.pledge(), "We never count streaks.")

    def test_static_copy_is_safe(self):
        out = antistreakmod.history_section()
        self.assertNotIn("<script", out)
        self.assertIn("streak", out.lower())

    def test_history_section_anchor(self):
        self.assertIn(f"id='{antistreakmod.ANCHOR}'",
                      antistreakmod.history_section())

    def test_status_anchor(self):
        body = antistreakmod.section_html()
        self.assertIn(f"id='{antistreakmod.STATUS_ANCHOR}'", body)
        self.assertIn("antistreak.py", body)

    def test_tour_entry_shape(self):
        e = antistreakmod.tour_entry()
        self.assertEqual("feature", e["kind"])
        self.assertEqual("/reviews", e["path"])
        self.assertEqual(antistreakmod.ANCHOR, e["anchor"])


class CallerEffectTest(unittest.TestCase):
    def test_empty_history_answers_why_no_streak(self):
        _tmp, db, _s, _out = make_module("antistreak empty")
        body = histmod.history_html(db)
        self.assertIn(f"id='{antistreakmod.ANCHOR}'", body)
        self.assertIn("We never count streaks.", body)

    def test_active_history_keeps_pledge(self):
        _tmp, db, server, _out = make_module("antistreak active")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        body = histmod.history_html(db)
        self.assertIn(f"id='{antistreakmod.ANCHOR}'", body)
        self.assertIn("intervals, not chains", body)


if __name__ == "__main__":
    unittest.main()
