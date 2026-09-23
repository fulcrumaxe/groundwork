"""Boredom detection (F-97): too-easy streak jumps one Bloom rung."""
import unittest

from groundwork import boredom as mod
from groundwork import db as dbmod

from test_web import make_module


class RungTest(unittest.TestCase):
    def test_order(self):
        self.assertLess(mod.rung_index("recall"), mod.rung_index("apply"))
        self.assertLess(mod.rung_index("apply"), mod.rung_index("create"))

    def test_next_rung(self):
        self.assertEqual(mod.next_rung("recall"), "understand")
        self.assertEqual(mod.next_rung("apply"), "analyse")

    def test_top_and_unknown(self):
        self.assertEqual(mod.next_rung("create"), "")
        self.assertEqual(mod.next_rung("nope"), "")
        self.assertEqual(mod.rung_index(None), -1)

    def test_tier_of_prefers_key_then_exercise_type(self):
        self.assertEqual(mod.tier_of({"tier": "Apply"}), "apply")
        self.assertEqual(mod.tier_of({"exercise_type": "1"}), "recall")
        self.assertEqual(mod.tier_of({"exercise_type": "5"}), "explain")
        self.assertEqual(mod.tier_of({"exercise_type": "10"}), "apply")
        self.assertEqual(mod.tier_of({}), "")
        self.assertEqual(mod.tier_of(None), "")


class BoredTest(unittest.TestCase):
    def test_streak_bored(self):
        self.assertTrue(mod.is_bored([3, 4, 4, 5]))

    def test_broken_streak_not_bored(self):
        self.assertFalse(mod.is_bored([4, 4, 2, 5, 5]))

    def test_no_data_fallback(self):
        for bad in (None, [], {}, "x", [None, "z"]):
            self.assertFalse(mod.is_bored(bad))

    def test_custom_needed(self):
        self.assertTrue(mod.is_bored([5], needed=1))
        self.assertFalse(mod.is_bored([5], needed=2))


class SuggestTest(unittest.TestCase):
    def test_bored_jumps_one_rung(self):
        self.assertEqual(mod.suggest_rung("apply", [4, 5, 5]), "analyse")

    def test_not_bored_stays(self):
        self.assertEqual(mod.suggest_rung("apply", [2, 5]), "apply")

    def test_no_data_stays(self):
        self.assertEqual(mod.suggest_rung("apply", None), "apply")
        self.assertEqual(mod.suggest_rung("apply", []), "apply")

    def test_top_stays(self):
        self.assertEqual(mod.suggest_rung("create", [5, 5, 5]), "create")

    def test_unknown_empty(self):
        self.assertEqual(mod.suggest_rung("nope", [5, 5, 5]), "")


class PromoteTest(unittest.TestCase):
    def _cards(self):
        return [{"concept_id": "a", "tier": "recall"},
                {"concept_id": "b", "tier": "apply"}]

    def test_bored_concept_first(self):
        out = mod.promote(self._cards(), {"b": [4, 5, 5]})
        self.assertEqual([c["concept_id"] for c in out], ["b", "a"])

    def test_next_rung_card_leads_its_concept(self):
        cards = [{"id": "r", "concept_id": "a", "exercise_type": "1"},
                 {"id": "e", "concept_id": "a", "exercise_type": "5"},
                 {"id": "x", "concept_id": "b", "exercise_type": "1"}]
        out = mod.promote(cards, {"a": [5, 5, 5]})
        self.assertEqual([c["id"] for c in out], ["e", "r", "x"])

    def test_no_data_keeps_order(self):
        cards = self._cards()
        self.assertEqual(mod.promote(cards, None), cards)
        self.assertEqual(mod.promote(cards, {}), cards)

    def test_hostile_keeps_order(self):
        self.assertEqual(mod.promote(None), [])
        self.assertEqual(mod.promote("x"), [])


class BadgeTest(unittest.TestCase):
    def test_badge_when_bored(self):
        html = mod.badge_html("apply", [4, 5, 5])
        self.assertIn("analyse", html)
        self.assertIn("Too easy", html)

    def test_no_badge_no_data(self):
        for bad in (None, [], {}):
            self.assertEqual(mod.badge_html("apply", bad), "")

    def test_no_badge_top_rung(self):
        self.assertEqual(mod.badge_html("create", [5, 5, 5]), "")


class CallerEffectTest(unittest.TestCase):
    """Due queue promotes a bored concept's next-rung card first."""

    def test_bored_concept_surfaces_explain_first(self):
        tmp, db, server, out = make_module("boredom queue mod")
        before = [c["id"] for c in
                  server.tool_list_due_reviews({"limit": 20})["due"]]
        recall = [c for c in server.tool_list_due_reviews(
            {"limit": 20})["due"]
            if str(c.get("exercise_type")) == "1"][0]["id"]
        for _ in range(3):
            server.submit_review(recall, "5", 4)
        after = server.tool_list_due_reviews({"limit": 20})["due"]
        kinds = {c["id"]: str(c.get("exercise_type")) for c in after}
        first = after[0]["id"]
        # The explain-words card (type 5) leads after three aces.
        self.assertEqual(kinds[first], "5")
        self.assertNotEqual([c["id"] for c in after], before)

    def test_calm_queue_keeps_order(self):
        # Broken streak on real queue shapes: promote() is a no-op.
        tmp, db, server, out = make_module("boredom calm mod")
        cards = server.tool_list_due_reviews({"limit": 20})["due"]
        recall = [c for c in cards
                  if str(c.get("exercise_type")) == "1"][0]["id"]
        server.submit_review(recall, "5", 4)
        server.submit_review(recall, "2", 4)
        queue = server.tool_list_due_reviews({"limit": 20})["due"]
        con = dbmod.connect(db)
        try:
            rows = con.execute(
                "SELECT cards.concept_id, reviews.grade FROM reviews"
                " JOIN cards ON cards.id = reviews.card_id"
                " ORDER BY reviews.id").fetchall()
        finally:
            con.close()
        hist = {}
        for cid, grade in rows:
            hist.setdefault(cid, []).append(grade)
        self.assertEqual(mod.promote(queue, hist), queue)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())
        self.assertIn("boredom", mod.section_html())
        e = mod.tour_entry()
        self.assertEqual(e, {
            "id": "boredom-detection",
            "kind": "feature",
            "title": "Boredom detection",
            "blurb": "Acing reviews in a row jumps one Bloom rung up "
                     "instead of more same-level drills.",
            "path": "/status",
            "anchor": "status-b21-boredom",
        })


if __name__ == "__main__":
    unittest.main()
