"""Interview loop: study plan plus proof report (F-161)."""
import unittest

from groundwork import db as dbmod
from groundwork import history as histmod
from groundwork import interviewloop as mod
from groundwork import ownership as ownmod

from test_web import make_module


def _earn_owned(db):
    con = dbmod.connect(db)
    try:
        cid = con.execute("SELECT id FROM concepts LIMIT 1").fetchone()[0]
        card = con.execute(
            "SELECT id FROM cards WHERE concept_id=? LIMIT 1",
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


def _pass_interview(db):
    con = dbmod.connect(db)
    try:
        card = con.execute(
            "SELECT id FROM cards ORDER BY rowid DESC LIMIT 1").fetchone()[0]
        con.execute("UPDATE cards SET exercise_type='73' WHERE id=?", (card,))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at)"
            " VALUES(?, 5, 4, '2026-09-21T10:00:00Z')", (card,))
        con.commit()
    finally:
        con.close()


class PlanTest(unittest.TestCase):
    def test_plan_orders_weakest_first(self):
        tmp, db, server, out = make_module("interview plan mod")
        plan = mod.plan_for(db)
        self.assertEqual(len(plan["steps"]), 1)
        self.assertIn("weakest", plan["steps"][0]["reason"])

    def test_cap_and_size(self):
        tmp, db, server, out = make_module("interview cap mod")
        self.assertEqual(mod.plan_for(db, size=0)["steps"], [])
        self.assertLessEqual(len(mod.plan_for(db, size=99)["steps"]), 12)

    def test_hostile_never_raises(self):
        self.assertEqual(mod.plan_for("/nonexistent/x.db")["steps"], [])
        self.assertEqual(mod.proof_for("/nonexistent/x.db")["rows"], [])
        self.assertEqual(mod.scope_repo("/nonexistent/x.db"), "")
        self.assertEqual(mod.scope_repo(None), "")
        self.assertIn("interview-loop", mod.loop_html("/nonexistent/x.db"))


class CallerEffectTest(unittest.TestCase):
    def test_history_gains_loop_with_live_proof(self):
        """Behavioral effect: History proof differs with live data."""
        tmp, db, server, out = make_module("interview live mod")
        before = histmod.history_html(db)
        self.assertIn("id='interview-loop'", before)
        self.assertIn("0/1 owned", before)
        _earn_owned(db)
        _pass_interview(db)
        after = histmod.history_html(db)
        self.assertIn("id='interview-loop'", after)
        self.assertIn("1/1 owned", after)
        self.assertIn("1 interviews", after)

    def test_fresh_db_anchor_stable(self):
        tmp, db, server, out = make_module("interview fresh mod")
        body = histmod.history_html(db)
        self.assertIn("id='interview-loop'", body)


class ShapeTest(unittest.TestCase):
    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(set(e),
                         {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual((e["id"], e["kind"], e["path"], e["anchor"]),
                         ("interview-loop", "feature", "/reviews",
                          "interview-loop"))


if __name__ == "__main__":
    unittest.main()
