"""Open-source contributor ladder from owned proofs (F-192)."""
import sqlite3
import unittest

from groundwork import osslader as mod
from groundwork import db as dbmod
from groundwork import ownership as ownmod

from test_web import handler_for, make_module


def _rows(names):
    return [{"cid": f"m:n{i}", "name": n} for i, n in enumerate(names)]


def _map(lessons):
    return {L["concept_id"]: L for L in lessons}


def _chain():
    return [
        {"concept_id": "nA", "name": "A", "needs": []},
        {"concept_id": "nB", "name": "B", "needs": ["A"]},
        {"concept_id": "nC", "name": "C", "needs": ["B"]},
    ]


class RungTest(unittest.TestCase):
    def test_no_owned_is_newcomer(self):
        self.assertEqual(mod.rung_for(0, 5), 0)

    def test_empty_module_is_newcomer(self):
        self.assertEqual(mod.rung_for(0, 0), 0)

    def test_first_owned_is_first_patch(self):
        self.assertEqual(mod.rung_for(1, 5), 1)

    def test_half_owned_is_contributor(self):
        self.assertEqual(mod.rung_for(2, 4), 2)
        self.assertEqual(mod.rung_for(3, 5), 2)

    def test_below_half_stays_first_patch(self):
        self.assertEqual(mod.rung_for(1, 4), 1)
        self.assertEqual(mod.rung_for(1, 2), 1)

    def test_all_owned_is_subsystem_owner(self):
        self.assertEqual(mod.rung_for(5, 5), 3)
        self.assertEqual(mod.rung_for(1, 1), 3)

    def test_hostile_counts_are_newcomer(self):
        for n, t in ((None, 5), ("x", 5), (2, "y"), (None, None)):
            self.assertEqual(mod.rung_for(n, t), 0)


class LadderTest(unittest.TestCase):
    def test_rung_names_and_flags(self):
        lad = mod.ladder_for(_rows(["A", "B", "C", "D"]),
                             {"m:n0": (2, True)})
        self.assertEqual((lad["rung"], lad["rung_name"]), (1, "First patch"))
        self.assertEqual((lad["owned_n"], lad["total"]), (1, 4))
        self.assertEqual([r["reached"] for r in lad["rungs"]],
                         [True, True, False, False])
        self.assertEqual([r["current"] for r in lad["rungs"]],
                         [False, True, False, False])

    def test_next_prefers_unowned_entry_point(self):
        lad = mod.ladder_for(_rows(["A", "B", "C"]), {}, _map(_chain()))
        self.assertEqual(lad["next"], {"name": "A", "node": "n0"})

    def test_next_follows_graph_not_definition_order(self):
        lad = mod.ladder_for(_rows(["C", "B", "A"]), {}, _map(_chain()))
        self.assertEqual(lad["next"]["name"], "A")

    def test_next_falls_back_to_definition_order(self):
        lad = mod.ladder_for(_rows(["C", "B", "A"]), {})
        self.assertEqual(lad["next"]["name"], "C")

    def test_all_owned_has_no_next(self):
        owned = {f"m:n{i}": (2, True) for i in range(2)}
        lad = mod.ladder_for(_rows(["A", "B"]), owned)
        self.assertEqual(lad["rung_name"], "Subsystem owner")
        self.assertIsNone(lad["next"])

    def test_hostile_input_never_raises(self):
        for bad in (None, "x", 5, [], {}, {"n": "junk"}):
            self.assertEqual(mod.ladder_for(bad)["rung"], 0)
            self.assertEqual(mod.ladder_html(bad), "")


class CallerEffectTest(unittest.TestCase):
    def _own(self, db, mid):
        con = dbmod.connect(db)
        try:
            cid = con.execute("SELECT id FROM concepts WHERE module_id=?",
                              (mid,)).fetchone()[0]
            card = con.execute("SELECT id FROM cards WHERE concept_id=?",
                               (cid,)).fetchone()[0]
            con.execute("UPDATE cards SET exercise_type=? WHERE id=?",
                        (ownmod.ownership_types()[0], card))
            for _ in range(2):
                con.execute(
                    "INSERT INTO reviews(card_id, grade, confidence,"
                    " reviewed_at) VALUES(?, 5, 4, '2026-09-20T10:00:00Z')",
                    (card,))
            con.commit()
        finally:
            con.close()

    def test_newcomer_sees_ladder_with_good_first_issue(self):
        """Behavioral effect: module page gains a contributor ladder."""
        tmp, db, server, out = make_module("osslader mod")
        body = handler_for(db).module_html(out["module_id"])
        self.assertIn("id='oss-ladder'", body)
        self.assertIn("Rung 1 of 4", body)
        self.assertIn("Newcomer", body)
        self.assertIn("Good first issue", body)

    def test_owned_subsystem_shows_top_rung(self):
        tmp, db, server, out = make_module("osslader owned mod")
        self._own(db, out["module_id"])
        body = handler_for(db).module_html(out["module_id"])
        self.assertIn("id='oss-ladder'", body)
        self.assertIn("Subsystem owner", body)
        self.assertNotIn("Good first issue", body)

    def test_conceptless_module_renders_unchanged(self):
        """Legacy fallback: no concepts, no block."""
        tmp, db, server, out = make_module("osslader legacy mod")
        con = sqlite3.connect(db)
        try:
            con.execute("DELETE FROM concepts WHERE module_id=?",
                        (out["module_id"],))
            con.commit()
        finally:
            con.close()
        body = handler_for(db).module_html(out["module_id"])
        self.assertNotIn("id='oss-ladder'", body)
        self.assertEqual(mod.ladder_html([]), "")


class ShapeTest(unittest.TestCase):
    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual((e["id"], e["kind"], e["path"], e["anchor"]),
                         ("oss-contributor-ladder", "feature",
                          "/status", mod.STATUS_ANCHOR))


if __name__ == "__main__":
    unittest.main()
