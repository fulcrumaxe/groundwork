"""Growth rings: one ring per owned concept (F-103)."""
import unittest

from groundwork import db as dbmod
from groundwork import growrings as mod
from groundwork import ownhead as ownmod

from test_web import handler_for, make_module


def _own_fixture(summary="growrings mod"):
    tmp, db, server, out = make_module(summary)
    con = dbmod.connect(db)
    try:
        cid = con.execute("SELECT id FROM concepts LIMIT 1").fetchone()[0]
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back)"
            " VALUES('growrings-c1', ?, '19', 'q', 'a')", (cid,))
        for _ in range(2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, reviewed_at)"
                " VALUES('growrings-c1', 5, 4, '2026-01-02T10:00:00Z')")
        con.commit()
    finally:
        con.close()
    return tmp, db, server, out


class RingsTest(unittest.TestCase):
    def test_ring_per_owned(self):
        svg = mod.rings_svg(3, 9)
        self.assertEqual(svg.count("<circle"), 3)
        self.assertIn("3 of 9", svg)

    def test_zero_owned_stump_only(self):
        svg = mod.rings_svg(0, 4)
        self.assertEqual(svg.count("<circle"), 1)
        self.assertIn("0 of 4", svg)

    def test_overflow_capped_with_note(self):
        svg = mod.rings_svg(mod.MAX_RINGS + 5, mod.MAX_RINGS + 5)
        self.assertEqual(svg.count("<circle"), mod.MAX_RINGS)
        self.assertIn("+5 more rings", svg)

    def test_no_concepts_empty(self):
        self.assertEqual(mod.rings_svg(0, 0), "")
        self.assertEqual(mod.rings_svg(None, None), "")

    def test_hostile_never_raises(self):
        self.assertEqual(mod.ring_count(None), 0)
        self.assertEqual(mod.ring_count("x"), 0)
        self.assertEqual(mod.rings_svg("x", "y"), "")


class SectionTest(unittest.TestCase):
    def test_section_always_anchored(self):
        _tmp, db, _s, _o = make_module("growrings anchor")
        body = mod.section_html(db)
        self.assertIn("id='growth-rings-head'", body)

    def test_section_counts_match_headline(self):
        _tmp, db, _s, _o = _own_fixture()
        c = ownmod.counts(db)
        body = mod.section_html(db)
        self.assertIn(f"{c['owned']} of {c['concepts']}", body)

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(), {
            "id": "growth-rings", "kind": "feature",
            "title": "Growth rings",
            "blurb": ("One ring per owned concept — your proof, counted "
                      "in wood."),
            "path": "/reviews", "anchor": "growth-rings-head"})


class CallerEffectTest(unittest.TestCase):
    def test_history_carries_rings(self):
        _tmp, db, server, _o = make_module("growrings caller")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        body = handler_for(db).history_html()
        self.assertIn("id='growth-rings-head'", body)
        self.assertIn("id='growth-rings'", body)

    def test_empty_history_still_anchored(self):
        _tmp, db, _s, _o = make_module("growrings empty")
        body = handler_for(db).history_html()
        self.assertIn("id='growth-rings-head'", body)


if __name__ == "__main__":
    unittest.main()
