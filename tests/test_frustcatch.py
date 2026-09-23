"""Frustration relief (F-96): three fast fails earn an easier card."""
import unittest

from groundwork import db as dbmod
from groundwork import frustcatch as mod

from test_web import handler_for, make_module


class NormalizeTest(unittest.TestCase):
    def test_bare_grades_accepted(self):
        self.assertEqual(mod.normalize_attempts([1, 4]),
                         [{"grade": 1, "seconds": None},
                          {"grade": 4, "seconds": None}])

    def test_hostile_yields_empty(self):
        for bad in (None, {}, "x", 5, True):
            self.assertEqual(mod.normalize_attempts(bad), [])

    def test_grades_clamped(self):
        self.assertEqual(mod.normalize_attempts([{"grade": 9}])[0]["grade"], 5)


class FastFailTest(unittest.TestCase):
    def test_low_and_quick_is_fast_fail(self):
        self.assertTrue(mod.is_fast_fail({"grade": 1, "seconds": 30}))

    def test_pass_breaks_pattern(self):
        self.assertFalse(mod.is_fast_fail({"grade": 4, "seconds": 5}))

    def test_slow_fail_is_not_fast(self):
        self.assertFalse(mod.is_fast_fail({"grade": 1, "seconds": 600}))

    def test_untimed_fail_counts(self):
        self.assertTrue(mod.is_fast_fail({"grade": 0}))

    def test_hostile_is_not_fail(self):
        self.assertFalse(mod.is_fast_fail(None))


class StreakTest(unittest.TestCase):
    def test_three_tail_fails_frustrated(self):
        atts = [{"grade": 1, "seconds": 20}, {"grade": 0, "seconds": 15},
                {"grade": 2, "seconds": 40}]
        self.assertEqual(mod.tail_streak(atts), 3)
        self.assertTrue(mod.is_frustrated(atts))

    def test_pass_resets_tail(self):
        atts = [{"grade": 0}, {"grade": 0}, {"grade": 5}, {"grade": 1}]
        self.assertEqual(mod.tail_streak(atts), 1)
        self.assertFalse(mod.is_frustrated(atts))

    def test_two_fails_not_enough(self):
        self.assertFalse(mod.is_frustrated([{"grade": 1}, {"grade": 1}]))

    def test_no_data_legacy_calm(self):
        for bad in (None, {}, [], "x"):
            self.assertEqual(mod.tail_streak(bad), 0)
            self.assertFalse(mod.is_frustrated(bad))


class ReliefTest(unittest.TestCase):
    def test_calm_plan_is_legacy(self):
        plan = mod.relief_plan([{"grade": 4}])
        self.assertEqual(plan, {"frustrated": False, "streak": 0,
                               "easier": None, "message": ""})

    def test_frustrated_picks_easiest_other_card(self):
        cards = [{"id": "hard", "difficulty": 0.9},
                 {"id": "easy", "difficulty": 0.2},
                 {"id": "mid", "difficulty": 0.5}]
        plan = mod.relief_plan([{"grade": 1}, {"grade": 0}, {"grade": 1}],
                               cards, "hard")
        self.assertTrue(plan["frustrated"])
        self.assertEqual(plan["easier"]["id"], "easy")
        self.assertIn("easier", plan["message"])

    def test_no_cards_still_frustrated(self):
        plan = mod.relief_plan([1, 0, 2])
        self.assertTrue(plan["frustrated"])
        self.assertIsNone(plan["easier"])

    def test_encouragement_never_empty(self):
        self.assertTrue(mod.encouragement(3))
        self.assertTrue(mod.encouragement(None))


class RenderTest(unittest.TestCase):
    def test_banner_empty_is_legacy_fallback(self):
        for bad in (None, {}, {"frustrated": False}):
            self.assertEqual(mod.banner_html(bad), "")

    def test_banner_links_real_lesson_only(self):
        plan = mod.relief_plan([1, 0, 2], [{"id": "e1", "difficulty": 0.1}],
                               "h9")
        body = mod.banner_html(plan, "/modules/m#lesson-add")
        self.assertIn("relief", body)
        self.assertIn("/modules/m#lesson-add", body)
        # No URL, no link — never a dead href.
        self.assertNotIn("href", mod.banner_html(plan))

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(), {
            "id": "frustration-relief", "kind": "feature",
            "title": "Stuck? Take the easier card",
            "blurb": ("Three fast fails in a row earn a breather note and "
                      "an easier card on the same idea."),
            "path": "/status", "anchor": mod.STATUS_ANCHOR})


class CallerEffectTest(unittest.TestCase):
    """Grading consults relief_plan: three fast fails earn relief."""

    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("frust mod")
        dbmod.init_db(self.db)
        self.mid = self.out["module_id"]
        cards = self.server.tool_list_due_reviews({"limit": 20})["due"]
        ones = [c for c in cards if str(c.get("exercise_type")) == "1"]
        self.card_id = (ones or cards)[0]["id"]

    def test_three_fast_fails_earn_relief_with_easier_link(self):
        for _ in range(2):
            out = self.server.submit_review(self.card_id, "0", 3)
            self.assertEqual(out.get("relief", ""), "")
        out = self.server.submit_review(self.card_id, "0", 3)
        self.assertIn("relief", out.get("relief", ""))
        self.assertIn(f"/modules/{self.mid}#lesson-calc-py-add",
                      out["relief"])
        # The link target renders on the module page.
        body = handler_for(self.db).module_html(self.mid)
        self.assertIn("id='lesson-calc-py-add'", body)

    def test_calm_reviews_render_no_relief(self):
        out = self.server.submit_review(self.card_id, "5", 4)
        self.assertEqual(out.get("relief", ""), "")


if __name__ == "__main__":
    unittest.main()
