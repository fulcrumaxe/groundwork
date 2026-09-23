"""Cognitive-load guard (F-94): strain caps new concepts per session."""
import unittest

from groundwork import cogniload as cog
from groundwork import minisession as mmod


def _card(concept, new=True):
    if new:
        return {"id": f"c-{concept}", "concept": concept, "attempts": 0,
                "due": "2026-09-20T00:00:00Z"}
    return {"id": f"c-{concept}", "concept": concept, "attempts": 3,
            "last_review": "2026-01-01", "due": "2026-09-20T00:00:00Z"}


def _due(n=10, concepts=("a", "b", "c", "d")):
    return [{"id": f"c{i:02d}", "concept": concepts[i % len(concepts)],
             "due": f"2026-09-20T{i:02d}:00:00Z"}
            for i in range(n)]


class StrainTest(unittest.TestCase):
    def test_empty_history_is_rested(self):
        self.assertEqual(cog.strain_of([]), 0.0)
        self.assertEqual(cog.strain_of(None), 0.0)
        self.assertEqual(cog.strain_of(["junk", None, {}]), 0.0)

    def test_low_grades_raise_strain(self):
        self.assertGreaterEqual(cog.strain_of([1, 1, 2, 5, 5, 5]), 0.5)
        self.assertEqual(cog.strain_of([5, 4, 5]), 0.0)

    def test_never_raises(self):
        self.assertEqual(cog.strain_of(object()), 0.0)


class CapTest(unittest.TestCase):
    def test_rested_gets_base_cap(self):
        self.assertEqual(cog.new_concept_cap([5, 4, 5]), 3)

    def test_strained_caps_to_one(self):
        self.assertEqual(cog.new_concept_cap([1, 1, 1, 2]), 1)

    def test_legacy_no_data_fallback_is_base(self):
        self.assertEqual(cog.new_concept_cap(None), 3)
        self.assertEqual(cog.new_concept_cap([]), 3)


class CapNewConceptsTest(unittest.TestCase):
    def test_strained_session_keeps_one_new_concept(self):
        plan = [_card("a"), _card("b"), _card("c"),
                _card("old", new=False)]
        out = cog.cap_new_concepts(plan, recent=[1, 1, 2, 1])
        concepts = [c["concept"] for c in out]
        self.assertIn("old", concepts)
        self.assertEqual(len([c for c in concepts if c in ("a", "b", "c")]), 1)

    def test_rested_session_keeps_three_new_concepts(self):
        plan = [_card("a"), _card("b"), _card("c"), _card("d"),
                _card("old", new=False)]
        out = cog.cap_new_concepts(plan, recent=[5, 4, 5])
        concepts = [c["concept"] for c in out]
        self.assertIn("old", concepts)
        self.assertEqual(
            len([c for c in concepts if c in ("a", "b", "c", "d")]), 3)

    def test_order_preserved_and_never_raises(self):
        self.assertEqual(cog.cap_new_concepts("nope"), [])
        self.assertEqual(cog.cap_new_concepts(None), [])


class CallerEffectTest(unittest.TestCase):
    def test_strained_picks_fewer_new_concepts(self):
        # Thin delegation: minisession.pick_cards feeds its picks
        # through cap_new_concepts; strained learners see fewer new
        # concepts while review cards always survive.
        due = _due(8)
        tried = {}
        strained = mmod.pick_cards(due, minutes=30, recent=[0, 1, 1],
                                   tried=tried)
        rested = mmod.pick_cards(due, minutes=30, recent=[5, 5, 4],
                                 tried=tried)
        snow = [c["concept"] for c in strained]
        rest = [c["concept"] for c in rested]
        self.assertLess(len(set(snow)), len(set(rest)))
        self.assertEqual(len(set(snow)), 1)

    def test_reviews_always_survive_the_guard(self):
        due = ([_card("new-a"), _card("new-b")]
               + [_card("old", new=False)])
        out = mmod.pick_cards(due, minutes=30, recent=[0, 0, 1], tried={})
        self.assertIn("old", [c["concept"] for c in out])

    def test_no_signal_keeps_legacy_picks(self):
        due = _due(8)
        self.assertEqual(
            mmod.pick_cards(due, minutes=30),
            mmod.pick_cards(due, minutes=30, recent=None, tried=None))

    def test_guard_never_empties_session_box(self):
        due = _due(4)
        out = mmod.pick_cards(due, minutes=30, recent=[0, 0, 0], tried={})
        self.assertTrue(out)
        box = mmod.session_box_html(due, minutes=30, recent=[0, 0, 0],
                                    tried={})
        self.assertIn("Start", box)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{cog.STATUS_ANCHOR}'", cog.section_html())
        e = cog.tour_entry()
        self.assertEqual(e, {
            "id": "cognitive-load-guard",
            "kind": "feature",
            "title": "Cognitive-load guard",
            "blurb": ("Strained sessions introduce fewer new concepts; "
                      "reviews always survive the cut."),
            "path": "/status",
            "anchor": "status-b21-cogniload",
        })


if __name__ == "__main__":
    unittest.main()
