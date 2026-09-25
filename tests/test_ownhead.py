"""Concepts-owned headline counter (F-102)."""
import unittest

from groundwork import db as dbmod
from groundwork import history as histmod
from groundwork import ownhead as mod

from test_web import handler_for, make_module


def _own_fixture(summary="ownhead mod"):
    """Fixture DB with one concept owned: a modify card + 2 passes."""
    tmp, db, server, out = make_module(summary)
    con = dbmod.connect(db)
    try:
        cid = con.execute("SELECT id FROM concepts LIMIT 1").fetchone()[0]
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back)"
            " VALUES('ownhead-c1', ?, '19', 'q', 'a')", (cid,))
        for _ in range(2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at) VALUES('ownhead-c1', 5, 4,"
                " '2026-01-02T10:00:00Z')")
        con.commit()
    finally:
        con.close()
    return tmp, db, server, out


class CountsTest(unittest.TestCase):
    def test_fresh_fixture_zero_owned(self):
        _tmp, db, _s, _o = make_module("ownhead fresh")
        c = mod.counts(db)
        self.assertEqual(c["owned"], 0)
        self.assertGreaterEqual(c["concepts"], 1)

    def test_modify_passes_count_as_owned(self):
        _tmp, db, _s, _o = _own_fixture()
        c = mod.counts(db)
        self.assertEqual(c["owned"], 1)
        self.assertGreaterEqual(c["concepts"], 1)

    def test_single_pass_not_owned(self):
        tmp, db, server, out = make_module("ownhead single")
        con = dbmod.connect(db)
        try:
            cid = con.execute(
                "SELECT id FROM concepts LIMIT 1").fetchone()[0]
            con.execute(
                "INSERT INTO cards(id, concept_id, exercise_type, front,"
                " back) VALUES('ownhead-1x', ?, '19', 'q', 'a')", (cid,))
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at) VALUES('ownhead-1x', 5, 4,"
                " '2026-01-02T10:00:00Z')")
            con.commit()
        finally:
            con.close()
        self.assertEqual(mod.counts(db)["owned"], 0)

    def test_hostile_yields_zeros(self):
        self.assertEqual(mod.counts(None), {"owned": 0, "concepts": 0})
        self.assertEqual(mod.counts("/no/such/db.sqlite"),
                         {"owned": 0, "concepts": 0})


class RenderTest(unittest.TestCase):
    def test_headline_always_anchored(self):
        _tmp, db, _s, _o = make_module("ownhead anchor")
        body = mod.headline_html(db)
        self.assertIn("id='owned-headline'", body)
        self.assertIn("0 concepts owned", body)

    def test_headline_names_owned_count(self):
        _tmp, db, _s, _o = _own_fixture("ownhead named")
        body = mod.headline_html(db)
        self.assertIn("id='owned-headline'", body)
        self.assertIn("<b>1 concept owned</b>", body)

    def test_headline_never_streaks(self):
        _tmp, db, _s, _o = make_module("ownhead streak")
        self.assertNotIn("streak", mod.headline_html(db).lower()
                         .replace("streaks are never counted", ""))

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(), {
            "id": "owned-headline", "kind": "feature",
            "title": "Concepts owned, up top",
            "blurb": ("History opens with the concepts you can prove — "
                      "streaks are never counted."),
            "path": "/reviews", "anchor": "owned-headline"})


class CallerEffectTest(unittest.TestCase):
    def test_history_opens_with_headline(self):
        _tmp, db, server, _o = make_module("ownhead caller")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        body = handler_for(db).history_html()
        self.assertIn("id='owned-headline'", body)
        self.assertLess(body.index("owned-headline"),
                        body.index("id='calibration'"))

    def test_history_headline_counts_owned(self):
        _tmp, db, _s, _o = _own_fixture("ownhead caller owned")
        body = handler_for(db).history_html()
        self.assertIn("<b>1 concept owned</b>", body)


if __name__ == "__main__":
    unittest.main()
