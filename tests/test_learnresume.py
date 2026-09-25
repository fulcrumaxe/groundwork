"""Learning resume: verified skills per repo (F-109)."""
import unittest

from groundwork import db as dbmod
from groundwork import learnresume as mod

from test_web import handler_for, make_module


def _own_fixture(delayed=False):
    tmp, db, server, out = make_module("learnresume mod")
    con = dbmod.connect(db)
    try:
        cid = con.execute("SELECT id FROM concepts LIMIT 1").fetchone()[0]
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back)"
            " VALUES('learnresume-c1', ?, '19', 'q', 'a')", (cid,))
        stab = 30.0 if delayed else 1.0
        for day in ("2026-01-02T10:00:00Z", "2026-01-05T10:00:00Z"):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at, prev_stability)"
                " VALUES('learnresume-c1', 5, 4, ?, ?)", (day, stab))
        con.commit()
    finally:
        con.close()
    return tmp, db, server, out


class SkillsTest(unittest.TestCase):
    def test_empty_no_skills(self):
        _tmp, db, _s, _o = make_module("learnresume empty")
        self.assertEqual(mod.skills(db), {})
        self.assertIn("No verified skills", mod.section_html(db))

    def test_owned_concept_verifies_skill(self):
        _tmp, db, _s, _o = _own_fixture()
        table = mod.skills(db)
        self.assertEqual(len(table), 1)
        repo = next(iter(table))
        skills = {s["skill"] for s in table[repo]}
        self.assertIn("modify", skills)
        row = next(s for s in table[repo] if s["skill"] == "modify")
        self.assertFalse(row["delayed"])
        self.assertEqual(row["first"], "2026-01-02")

    def test_delayed_proof_flagged(self):
        _tmp, db, _s, _o = _own_fixture(delayed=True)
        table = mod.skills(db)
        row = next(s for s in next(iter(table.values()))
                   if s["skill"] == "modify")
        self.assertTrue(row["delayed"])

    def test_attempts_alone_never_verify(self):
        _tmp, db, server, _o = make_module("learnresume attempts")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        # Fixture cards are recall/explain: one pass, never owned.
        self.assertEqual(mod.skills(db), {})

    def test_hostile_empty(self):
        self.assertEqual(mod.skills(None), {})
        self.assertEqual(mod.skills("/no/such.sqlite"), {})

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(), {
            "id": "learning-resume", "kind": "feature",
            "title": "Learning resume",
            "blurb": ("Your verified skills per repo — references "
                      "written by your own proof."),
            "path": "/reviews", "anchor": "learning-resume"})


class CallerEffectTest(unittest.TestCase):
    def test_history_carries_resume(self):
        _tmp, db, server, _o = make_module("learnresume caller")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        body = handler_for(db).history_html()
        self.assertIn("id='learning-resume'", body)

    def test_empty_history_still_anchored(self):
        _tmp, db, _s, _o = make_module("learnresume empty2")
        body = handler_for(db).history_html()
        self.assertIn("id='learning-resume'", body)


if __name__ == "__main__":
    unittest.main()
