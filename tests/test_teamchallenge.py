"""Team challenges: own a subsystem together, aggregate only (F-129)."""
import unittest

from groundwork import emoji as emojimod
from groundwork import history as histmod
from groundwork import teamchallenge as mod
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


class TeamchallengeUnitTest(unittest.TestCase):
    def test_progress(self):
        self.assertEqual(mod.progress(0, 0), 0)
        self.assertEqual(mod.progress(1, 2), 50)
        self.assertEqual(mod.progress(2, 1), 100)
        self.assertEqual(mod.progress("x", None), 0)
        self.assertEqual(mod.progress(-1, 5), 0)

    def test_challenges_hostile_is_empty(self):
        self.assertEqual(mod.challenges("/nonexistent.db"), [])
        self.assertEqual(mod.section_html("/nonexistent.db"), "")


class TeamchallengeEffectTest(unittest.TestCase):
    def test_section_with_data_is_aggregate_only(self):
        _tmp, db, _server, _out = make_module("team mod")
        _own(db, _cid(db))
        body = mod.section_html(db)
        self.assertIn("id='teamchallenge'", body)
        self.assertIn("1/1 owned", body)
        import re
        lowered = body.casefold()
        self.assertIn("no ranking", lowered)
        for banned in ("leaderboard", "#1", "1st", "ranked"):
            self.assertNotIn(banned, lowered)
        self.assertEqual(
            [w for w in re.findall(r"[a-z#0-9]+", lowered) if w == "rank"],
            [])

    def test_done_stamp_when_subsystem_owned(self):
        _tmp, db, _server, _out = make_module("team done mod")
        _own(db, _cid(db))
        self.assertIn("<b>Complete</b>", mod.section_html(db))

    def test_caller_history_gains_section(self):
        _tmp, db, _server, _out = make_module("team caller mod")
        _own(db, _cid(db))
        self.assertIn("id='teamchallenge'", histmod.history_html(db))

    def test_empty_db_keeps_legacy_bytes(self):
        import tempfile
        from pathlib import Path
        from groundwork import db as dbmod
        tmp = Path(tempfile.mkdtemp(prefix="gw-teamempty-"))
        db = str(tmp / "empty.db")
        dbmod.init_db(db)
        self.assertEqual(mod.section_html(db), "")
        self.assertNotIn("teamchallenge", histmod.history_html(db))


class TeamchallengeShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["path"], "/reviews")

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])


if __name__ == "__main__":
    unittest.main()
