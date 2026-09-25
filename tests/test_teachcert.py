"""Teaching certificates (F-112)."""
import unittest
from datetime import timedelta

from groundwork import teachcert as mod

from test_web import handler_for, make_module


def _own(db, cid, when):
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
                " reviewed_at) VALUES(?, 5, 4, ?)", (card, when))
        con.commit()
    finally:
        con.close()


def _cid(db):
    from groundwork import db as dbmod
    con = dbmod.connect(db)
    try:
        return con.execute("SELECT id FROM concepts").fetchall()[0]["id"]
    finally:
        con.close()


class CertTest(unittest.TestCase):
    def test_empty_db_fallback(self):
        _tmp, db, _s, _out = make_module("teachcert empty")
        self.assertEqual(mod.certificates(db), [])
        body = mod.section_html(db)
        self.assertIn("teaching-certificates", body)
        self.assertIn("No certificates yet", body)

    def test_full_pack_issues(self):
        from groundwork import sched as schedmod
        _tmp, db, _s, _out = make_module("teachcert full")
        cid = _cid(db)
        _own(db, cid, "2026-09-20T10:00:00Z")
        certs = mod.certificates(db)
        self.assertEqual(len(certs), 1)
        self.assertEqual(certs[0]["coverage"], 1.0)
        self.assertEqual(len(mod.eligible(db)), 1)
        body = mod.section_html(db)
        self.assertIn("Teaching certificate", body)

    def test_delayed_seal(self):
        from groundwork import sched as schedmod
        old = schedmod.iso(schedmod.utcnow() - timedelta(days=30))
        _tmp, db, _s, _out = make_module("teachcert delayed")
        _own(db, _cid(db), old)
        certs = mod.certificates(db)
        self.assertTrue(certs[0]["delayed"])
        self.assertIn("delayed-verified", mod.section_html(db))

    def test_hostile_never_raises(self):
        self.assertEqual(mod.certificates("/nonexistent.db"), [])
        self.assertEqual(mod.eligible("/nonexistent.db"), [])
        self.assertIn("teaching-certificates",
                      mod.section_html("/nonexistent.db"))

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "feature")
        self.assertEqual(entry["path"], "/reviews")


class CallerEffectTest(unittest.TestCase):
    def test_history_renders_anchor(self):
        from groundwork import history as histmod
        _tmp, db, _s, _out = make_module("teachcert history")
        body = histmod.history_html(db)
        self.assertIn("teaching-certificates", body)

    def test_history_lists_certificate(self):
        from groundwork import history as histmod
        _tmp, db, _s, _out = make_module("teachcert listed")
        _own(db, _cid(db), "2026-09-20T10:00:00Z")
        body = histmod.history_html(db)
        self.assertIn("Teaching certificate", body)


if __name__ == "__main__":
    unittest.main()
