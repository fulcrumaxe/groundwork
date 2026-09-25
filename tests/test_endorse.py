"""Skill endorsements by your own delayed tests (F-110)."""
import unittest

from groundwork import db as dbmod
from groundwork import endorse as mod

from test_web import handler_for, make_module


def _delayed_fixture():
    tmp, db, server, out = make_module("endorse mod")
    con = dbmod.connect(db)
    try:
        cid = con.execute("SELECT id FROM concepts LIMIT 1").fetchone()[0]
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back)"
            " VALUES('endorse-c1', ?, '19', 'q', 'a')", (cid,))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
            " prev_stability) VALUES('endorse-c1', 5, 4,"
            " '2026-01-05T10:00:00Z', 30.0)")
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
            " prev_stability) VALUES('endorse-c1', 4, 4,"
            " '2026-02-05T10:00:00Z', 45.0)")
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at,"
            " prev_stability) VALUES('endorse-c1', 5, 4,"
            " '2026-01-02T10:00:00Z', 1.0)")
        con.commit()
    finally:
        con.close()
    return tmp, db, server, out


class EndorseTest(unittest.TestCase):
    def test_delayed_passes_endorse(self):
        _tmp, db, _s, _o = _delayed_fixture()
        rows = mod.endorsements(db)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["skill"], "modify")
        self.assertEqual(rows[0]["proofs"], 2)
        self.assertEqual(rows[0]["latest"], "2026-02-05")

    def test_fresh_passes_never_endorse(self):
        _tmp, db, server, _o = make_module("endorse fresh")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        self.assertEqual(mod.endorsements(db), [])
        self.assertIn("No endorsements yet", mod.section_html(db))

    def test_failed_delayed_no_endorsement(self):
        tmp, db, server, out = make_module("endorse fail")
        con = dbmod.connect(db)
        try:
            cid = con.execute(
                "SELECT id FROM cards LIMIT 1").fetchone()[0]
            con.execute(
                "INSERT INTO reviews(card_id, grade, reviewed_at,"
                " prev_stability) VALUES(?, 2, '2026-01-05T10:00:00Z', 30)",
                (cid,))
            con.commit()
        finally:
            con.close()
        self.assertEqual(mod.endorsements(db), [])

    def test_hostile_empty(self):
        self.assertEqual(mod.endorsements(None), [])
        self.assertEqual(mod.endorsements("/no/such.sqlite"), [])

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(), {
            "id": "skill-endorsements", "kind": "feature",
            "title": "Skill endorsements",
            "blurb": ("Endorsed by your own delayed tests — references "
                      "from your future self."),
            "path": "/reviews", "anchor": "endorsements"})


class CallerEffectTest(unittest.TestCase):
    def test_history_carries_endorsements(self):
        _tmp, db, server, _o = make_module("endorse caller")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        body = handler_for(db).history_html()
        self.assertIn("id='endorsements'", body)
        self.assertIn("No endorsements yet", body)

    def test_endorsed_history_names_skill(self):
        _tmp, db, _s, _o = _delayed_fixture()
        body = handler_for(db).history_html()
        self.assertIn("Endorsed: modify", body)


if __name__ == "__main__":
    unittest.main()
