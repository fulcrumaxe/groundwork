"""Knowledge garden: repo map blooming as you learn (F-104)."""
import unittest

from groundwork import db as dbmod
from groundwork import knowngarden as mod

from test_web import handler_for, make_module


def _own_fixture(summary="knowngarden mod"):
    tmp, db, server, out = make_module(summary)
    con = dbmod.connect(db)
    try:
        cid = con.execute("SELECT id FROM concepts LIMIT 1").fetchone()[0]
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back)"
            " VALUES('knowngarden-c1', ?, '19', 'q', 'a')", (cid,))
        for _ in range(2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, reviewed_at)"
                " VALUES('knowngarden-c1', 5, 4, '2026-01-02T10:00:00Z')")
        con.commit()
    finally:
        con.close()
    return tmp, db, server, out


class StageTest(unittest.TestCase):
    def test_stages(self):
        self.assertEqual(mod.stage_of(0, 3), "seed")
        self.assertEqual(mod.stage_of(1, 3), "sprout")
        self.assertEqual(mod.stage_of(3, 3), "bloom")
        self.assertEqual(mod.stage_of(0, 0), "seed")

    def test_hostile_seed(self):
        for bad in (None, "x", (None, None)):
            self.assertEqual(mod.stage_of(bad, 3), "seed")
            self.assertEqual(mod.stage_of(1, bad), "seed")

    def test_plot_stages_render(self):
        self.assertIn("plot seed", mod.plot_html("m", "s", 0, 2))
        self.assertIn("plot sprout", mod.plot_html("m", "s", 1, 2))
        self.assertIn("plot bloom", mod.plot_html("m", "s", 2, 2))
        self.assertIn("/modules/m", mod.plot_html("m", "s", 2, 2))

    def test_plot_hostile_empty(self):
        self.assertEqual(mod.plot_html(None, None, None, None), "")


class BedsTest(unittest.TestCase):
    def test_beds_group_by_repo(self):
        body = mod.beds_for([("r1", "m1", "one", 0, 2),
                             ("r1", "m2", "two", 2, 2),
                             ("r2", "m3", "three", 1, 1)])
        self.assertIn("<h3>r1</h3>", body)
        self.assertIn("<h3>r2</h3>", body)
        self.assertIn("plot bloom", body)

    def test_empty_rows_empty(self):
        for bad in (None, [], "x"):
            self.assertEqual(mod.beds_for(bad), "")

    def test_stats_from_fixture(self):
        _tmp, db, _s, _o = _own_fixture()
        stats = mod.garden_stats(db)
        self.assertEqual(len(stats), 1)
        _repo, _mid, _sum, owned, total = stats[0]
        self.assertEqual((owned, total), (1, 1))

    def test_stats_hostile_empty(self):
        self.assertEqual(mod.garden_stats(None), [])
        self.assertEqual(mod.garden_stats("/no/such/db.sqlite"), [])


class SectionTest(unittest.TestCase):
    def test_section_always_anchored(self):
        _tmp, db, _s, _o = make_module("knowngarden anchor")
        body = mod.section_html(db)
        self.assertIn("id='knowledge-garden'", body)
        self.assertIn("plot seed", body)

    def test_owned_module_blooms(self):
        _tmp, db, _s, _o = _own_fixture("knowngarden bloom")
        self.assertIn("plot bloom", mod.section_html(db))

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(), {
            "id": "knowledge-garden", "kind": "feature",
            "title": "Knowledge garden",
            "blurb": ("Your repo map in bloom — every module a plot, "
                      "every owned concept a petal."),
            "path": "/reviews", "anchor": "knowledge-garden"})


class CallerEffectTest(unittest.TestCase):
    def test_history_carries_garden(self):
        _tmp, db, server, _o = make_module("knowngarden caller")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        body = handler_for(db).history_html()
        self.assertIn("id='knowledge-garden'", body)

    def test_empty_history_still_anchored(self):
        _tmp, db, _s, _o = make_module("knowngarden empty")
        body = handler_for(db).history_html()
        self.assertIn("id='knowledge-garden'", body)


if __name__ == "__main__":
    unittest.main()
