"""Difficulty-vote exercise weights (I-146)."""
import unittest

from groundwork import diffweights as mod


def _card(cid, tier, concept="c"):
    return {"id": cid, "concept_id": concept, "tier": tier}


class WeightsTest(unittest.TestCase):
    def test_easy_favors_create(self):
        w = mod.weights_for("easy")
        self.assertGreater(w["create"], w["recall"])

    def test_hard_favors_recall(self):
        w = mod.weights_for("hard")
        self.assertGreater(w["recall"], w["create"])

    def test_just_is_uniform(self):
        w = mod.weights_for("just")
        self.assertEqual(len(set(w.values())), 1)

    def test_hostile_is_uniform(self):
        w = mod.weights_for("medium")
        self.assertEqual(len(set(w.values())), 1)

    def test_tally_plurality(self):
        w = mod.weights_for({"easy": 0, "just": 1, "hard": 3})
        self.assertGreater(w["recall"], w["create"])

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "improvement")
        self.assertEqual(entry["anchor"], mod.STATUS_ANCHOR)


class OrderTest(unittest.TestCase):
    def test_hard_recall_leads(self):
        cards = [_card("a", "create", "c"), _card("b", "recall", "c")]
        out = mod.order_due(cards, {"c": "hard"})
        self.assertEqual([c["id"] for c in out], ["b", "a"])

    def test_easy_create_leads(self):
        cards = [_card("a", "recall", "c"), _card("b", "create", "c")]
        out = mod.order_due(cards, {"c": "easy"})
        self.assertEqual([c["id"] for c in out], ["b", "a"])

    def test_no_votes_keeps_order(self):
        cards = [_card("a", "create", "c"), _card("b", "recall", "c")]
        self.assertEqual(mod.order_due(cards, {}), cards)
        self.assertEqual(mod.order_due(cards, None), cards)

    def test_hostile_keeps_order(self):
        cards = [_card("a", "create", "c")]
        self.assertEqual(mod.order_due(cards, "nope"), cards)
        self.assertEqual(mod.order_due(None, {}), [])
        self.assertEqual(mod.order_due("nope", {}), [])

    def test_concepts_keep_relative_order(self):
        cards = [_card("a", "create", "c1"), _card("b", "recall", "c2")]
        out = mod.order_due(cards, {"c1": "hard", "c2": "hard"})
        self.assertEqual([c["id"] for c in out], ["a", "b"])


class CallerEffectTest(unittest.TestCase):
    def test_live_votes_reorder_live_tallies(self):
        from test_web import make_module
        from groundwork import db as dbmod
        from groundwork import diffvote as dvmod
        _tmp, db, _server, _out = make_module("diffweights caller")
        con = dbmod.connect(db)
        try:
            target = con.execute(
                "SELECT id FROM concepts").fetchall()[0]["id"]
        finally:
            con.close()
        res = dvmod.record(db, target, "hard")
        self.assertNotIn("error", res)
        # Recorded votes flow through tallies into the reorder.
        tallies = dvmod.tallies(db, [target])
        cards = [{"id": "x", "concept_id": target, "tier": "create"},
                 {"id": "y", "concept_id": target, "tier": "recall"}]
        out = mod.order_due(cards, tallies)
        self.assertEqual([c["id"] for c in out], ["y", "x"])


if __name__ == "__main__":
    unittest.main()
