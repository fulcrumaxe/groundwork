"""Explain-it party trick (F-111)."""
import unittest

from groundwork import partytrick as mod

from test_web import handler_for, make_module


def _own(db, cid):
    """Two modify/create passes on one card of the concept."""
    from groundwork import db as dbmod
    from groundwork import ownership as ownmod
    etype = ownmod.ownership_types()[0]
    con = dbmod.connect(db)
    try:
        card = con.execute(
            "SELECT id FROM cards WHERE concept_id=? LIMIT 1",
            (cid,)).fetchone()[0]
        con.execute("UPDATE cards SET exercise_type=? WHERE id=?",
                    (etype, card))
        for _ in range(2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at) VALUES(?, 5, 4, '2026-09-20T10:00:00Z')",
                (card,))
        con.commit()
        return card
    finally:
        con.close()


def _cid(db):
    from groundwork import db as dbmod
    con = dbmod.connect(db)
    try:
        return con.execute("SELECT id FROM concepts").fetchall()[0]["id"]
    finally:
        con.close()


class PickTest(unittest.TestCase):
    def test_locked_when_nothing_owned(self):
        _tmp, db, _s, _out = make_module("partytrick locked")
        self.assertIsNone(mod.pick(db, seed=1))
        body = mod.section_html(db, seed=1)
        self.assertIn("No party tricks yet", body)
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", body)

    def test_picks_owned_concept(self):
        _tmp, db, _s, _out = make_module("partytrick owned")
        cid = _cid(db)
        _own(db, cid)
        got = mod.pick(db, seed=1)
        self.assertIsNotNone(got)
        self.assertEqual(got["cid"], cid)
        body = mod.section_html(db, seed=1)
        self.assertIn("Explain it to me", body)
        self.assertIn("#lesson-", body)

    def test_prompt_names_concept(self):
        self.assertIn("loops", mod.prompt_for("loops"))

    def test_hostile_never_raises(self):
        self.assertIsNone(mod.pick("/nonexistent.db"))
        self.assertIn(mod.STATUS_ANCHOR, mod.section_html("/nonexistent.db"))

    def test_status_anchor_and_tour(self):
        self.assertIn("status-b23-partytrick",
                      mod.status_section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "feature")
        self.assertEqual(entry["path"], "/due")


class CallerEffectTest(unittest.TestCase):
    def test_due_page_carries_section(self):
        _tmp, db, _s, _out = make_module("partytrick due")
        body = handler_for(db).due_html()
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", body)

    def test_due_page_deals_owned_trick(self):
        _tmp, db, _s, _out = make_module("partytrick dealt")
        _own(db, _cid(db))
        body = handler_for(db).due_html()
        self.assertIn("Explain it to me", body)


if __name__ == "__main__":
    unittest.main()
