"""Honest Give-up path: blank submits lapse and reschedule sooner (I-159)."""
import sqlite3
import unittest
from datetime import datetime, timezone

from test_web import make_module

from groundwork import giveup as mod
from groundwork import sched as schedmod


def _now():
    return datetime(2026, 9, 26, 12, 0, 0, tzinfo=timezone.utc)


class IsGiveupTest(unittest.TestCase):
    def test_blank_forms_are_giveups(self):
        self.assertTrue(mod.is_giveup(""))
        self.assertTrue(mod.is_giveup("   "))
        self.assertTrue(mod.is_giveup(None))
        self.assertTrue(mod.is_giveup("\t\n "))

    def test_real_attempts_untouched_legacy(self):
        self.assertFalse(mod.is_giveup("0"))
        self.assertFalse(mod.is_giveup("3"))
        self.assertFalse(mod.is_giveup("some explanation"))
        self.assertFalse(mod.is_giveup(0))

    def test_never_raises(self):
        self.assertFalse(mod.is_giveup(object()))


class NextLapsesTest(unittest.TestCase):
    def test_increments(self):
        self.assertEqual(mod.next_lapses(0), 1)
        self.assertEqual(mod.next_lapses(2), 3)

    def test_fail_closed(self):
        self.assertEqual(mod.next_lapses(None), 1)
        self.assertEqual(mod.next_lapses("x"), 1)
        self.assertEqual(mod.next_lapses(-4), 1)


class ApplyGiveupTest(unittest.TestCase):
    def test_records_lapse_and_honest_zero(self):
        out = mod.apply_giveup(4.0, 0.5, 0, now=_now())
        self.assertEqual(out["grade"], 0)
        self.assertEqual(out["lapses"], 1)

    def test_increments_existing_lapses(self):
        out = mod.apply_giveup(4.0, 0.5, 2, now=_now())
        self.assertEqual(out["lapses"], 3)

    def test_matches_sched_grade_zero(self):
        out = mod.apply_giveup(4.0, 0.5, 0, now=_now())
        exp = schedmod.review_card(4.0, 0.5, 0, now=_now())
        self.assertEqual(out["stability"], exp["stability"])
        self.assertEqual(out["due"], exp["due"])

    def test_schedules_sooner_than_a_pass(self):
        fail = mod.apply_giveup(4.0, 0.5, 0, now=_now())
        ok = schedmod.review_card(4.0, 0.5, 5, now=_now())
        self.assertLess(fail["stability"], 4.0)
        self.assertLessEqual(fail["due"], ok["due"])

    def test_bad_card_numbers_fail_closed(self):
        out = mod.apply_giveup(None, "x", "y", now=_now())
        self.assertEqual(out["lapses"], 1)
        self.assertEqual(out["grade"], 0)
        self.assertIn("due", out)

    def test_history_rides_through(self):
        out = mod.apply_giveup(4.0, 0.5, 0, now=_now(),
                               grades=[5, 4, 0])
        exp = schedmod.review_card(4.0, 0.5, 0, now=_now(),
                                   grades=[5, 4, 0])
        self.assertEqual(out["due"], exp["due"])


class CopyTest(unittest.TestCase):
    def test_lapse_line_counts(self):
        self.assertIn("1 lapse", mod.lapse_line(1))
        self.assertIn("3 lapses", mod.lapse_line(3))
        self.assertIn("sooner", mod.lapse_line(0))


class HooksTest(unittest.TestCase):
    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.section_html())
        self.assertIn("groundwork/giveup.py",
                      mod.section_html())

    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual("improvement", e["kind"])
        self.assertEqual(mod.STATUS_ANCHOR, e["anchor"])
        for key in ("id", "title", "blurb", "path", "anchor"):
            self.assertTrue(e[key])


class CallerContractTest(unittest.TestCase):
    def test_giveup_form_posts_blank_answer(self):
        from groundwork import cards as cardsmod
        card = {"id": "ex1", "exercise_type": 5, "front": "f",
                "back": "b", "payload": "{}"}
        widget = cardsmod.answer_widget(card)
        self.assertIn("name='answer' value=''", widget)
        self.assertIn("Give up", widget)
        self.assertTrue(mod.is_giveup(""))


class EffectTest(unittest.TestCase):
    def test_surrender_persists_lapse_and_reschedules(self):
        tmp, db, server, out = make_module("giveup live")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        con = sqlite3.connect(db)
        try:
            before = con.execute(
                "SELECT stability, lapses, due FROM cards WHERE id=?",
                (card["id"],)).fetchone()
        finally:
            con.close()
        res = server.submit_review(card["id"], "", 1)
        self.assertEqual(res["grade"], 0)
        self.assertIn("lapse", res["result"]["feedback"])
        con = sqlite3.connect(db)
        try:
            after = con.execute(
                "SELECT stability, lapses, due FROM cards WHERE id=?",
                (card["id"],)).fetchone()
        finally:
            con.close()
        self.assertEqual(after[1], (before[1] or 0) + 1)
        self.assertLess(after[0], before[0])

    def test_second_surrender_increments_again(self):
        tmp, db, server, out = make_module("giveup twice")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "", 1)
        server.submit_review(card["id"], "", 1)
        con = sqlite3.connect(db)
        try:
            lapses = con.execute(
                "SELECT lapses FROM cards WHERE id=?",
                (card["id"],)).fetchone()[0]
        finally:
            con.close()
        self.assertEqual(lapses, 2)


if __name__ == "__main__":
    unittest.main()
