"""Incident-commander certification track (F-186)."""
import unittest
import uuid

from groundwork import cmdtrack as mod

from test_web import handler_for, make_module


def _cid(db):
    from groundwork import db as dbmod
    con = dbmod.connect(db)
    try:
        return con.execute("SELECT id FROM concepts").fetchall()[0]["id"]
    finally:
        con.close()


def _add_card(db, etype, front):
    from groundwork import db as dbmod
    cid = "cmd-%s" % uuid.uuid4().hex[:12]
    con = dbmod.connect(db)
    try:
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front)"
            " VALUES(?, ?, ?, ?)", (cid, _cid(db), str(etype), front))
        con.commit()
    finally:
        con.close()
    return cid


def _review(db, card, grade, when="2026-09-20T10:00:00Z"):
    from groundwork import db as dbmod
    con = dbmod.connect(db)
    try:
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at)"
            " VALUES(?, ?, 4, ?)", (card, grade, when))
        con.commit()
    finally:
        con.close()


def _set_mastery(db, value):
    from groundwork import db as dbmod
    con = dbmod.connect(db)
    try:
        con.execute("UPDATE concepts SET mastery=?", (value,))
        con.commit()
    finally:
        con.close()


def _state_map(db):
    return {s["key"]: s for s in mod.track_state(db)["stages"]}


class StateTest(unittest.TestCase):
    def test_fresh_db_replay_open_rest_locked(self):
        _tmp, db, _s, _out = make_module("cmdtrack fresh")
        st = mod.track_state(db)
        self.assertFalse(st["certified"])
        self.assertFalse(st["signal"])
        got = {s["key"]: s["status"] for s in st["stages"]}
        self.assertEqual(got, {"replay": "open", "diagnose": "locked",
                               "decide": "locked"})

    def test_two_passes_clear_one_pass_does_not(self):
        _tmp, db, _s, _out = make_module("cmdtrack gate")
        c = _add_card(db, 77, "CMDTRACK-REPLAY-1")
        _review(db, c, 5)
        self.assertEqual(_state_map(db)["replay"]["status"], "open")
        self.assertEqual(_state_map(db)["diagnose"]["status"], "locked")
        _review(db, c, 4, "2026-09-21T10:00:00Z")
        self.assertEqual(_state_map(db)["replay"]["status"], "cleared")
        self.assertEqual(_state_map(db)["diagnose"]["status"], "open")
        self.assertEqual(_state_map(db)["decide"]["status"], "locked")

    def test_banner_shows_live_mastery(self):
        _tmp, db, _s, _out = make_module("cmdtrack mastery")
        c = _add_card(db, 77, "CMDTRACK-REPLAY-1")
        _review(db, c, 5)
        _review(db, c, 5, "2026-09-21T10:00:00Z")
        _set_mastery(db, 0.8)
        self.assertIn("80%", mod.banner_html(db))

    def test_certified_when_all_clear(self):
        _tmp, db, _s, _out = make_module("cmdtrack certified")
        for etype in (77, 76, 48):
            c = _add_card(db, etype, f"CMDTRACK-{etype}")
            _review(db, c, 5)
            _review(db, c, 5, "2026-09-21T10:00:00Z")
        st = mod.track_state(db)
        self.assertTrue(st["certified"])
        self.assertIn("Incident-commander certified",
                      mod.banner_html(db))

    def test_hostile_never_raises(self):
        st = mod.track_state("/nonexistent.db")
        self.assertFalse(st["certified"])
        self.assertFalse(st["signal"])
        self.assertEqual(mod.banner_html("/nonexistent.db"), "")
        self.assertEqual(mod.apply_track("/nonexistent.db", None), (None, ""))
        self.assertEqual(mod.apply_track("/nonexistent.db", "junk"), ("junk", ""))

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())
        e = mod.tour_entry()
        self.assertEqual(e["id"], "commander-track")
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["path"], "/status")
        self.assertEqual(e["anchor"], mod.STATUS_ANCHOR)


class ApplyTrackEffectTest(unittest.TestCase):
    def test_legacy_no_data_fallback_pinned(self):
        _tmp, db, server, _out = make_module("cmdtrack legacy")
        due = server.tool_list_due_reviews({"limit": 20})["due"]
        self.assertTrue(due)
        queue, banner = mod.apply_track(db, due)
        self.assertEqual(queue, due)
        self.assertEqual(banner, "")

    def test_locked_stage_withheld_with_honest_notice(self):
        _tmp, db, _s, _out = make_module("cmdtrack withhold")
        c77 = _add_card(db, 77, "CMDTRACK-REPLAY-1")
        c76 = _add_card(db, 76, "CMDTRACK-DIAGNOSE-1")
        due = [{"id": c76, "exercise_type": "76"},
               {"id": c77, "exercise_type": "77"},
               {"id": "plain", "exercise_type": "1"}]
        queue, banner = mod.apply_track(db, due)
        self.assertEqual([c["id"] for c in queue], [c77, "plain"])
        self.assertIn("1 locked card withheld", banner)
        self.assertIn("until Diagnose opens", banner)

    def test_unlocked_stages_lead_in_order_rest_stable(self):
        _tmp, db, _s, _out = make_module("cmdtrack order")
        ids = {}
        for etype in (77, 76, 48):
            ids[etype] = _add_card(db, etype, f"CMDTRACK-{etype}")
        for etype in (77, 76):  # replay + diagnose cleared; decide open
            _review(db, ids[etype], 5)
            _review(db, ids[etype], 4, "2026-09-21T10:00:00Z")
        n1 = {"id": "n1", "exercise_type": "1", "front": "keep me"}
        n2 = {"id": "n2", "exercise_type": "2", "front": "keep me too"}
        due = [{"id": ids[48], "exercise_type": "48"}, n1,
               {"id": ids[76], "exercise_type": "76"},
               {"id": ids[77], "exercise_type": 77}, n2]
        queue, banner = mod.apply_track(db, due)
        self.assertEqual([c["id"] for c in queue],
                         [ids[77], ids[76], ids[48], "n1", "n2"])
        self.assertEqual(queue[3], n1)
        self.assertEqual(queue[4], n2)
        self.assertNotIn("withheld", banner)
        self.assertIn("commander-track", banner)


class CallerTest(unittest.TestCase):
    def test_due_html_legacy_path_pinned(self):
        _tmp, db, _s, _out = make_module("cmdtrack caller legacy")
        body = handler_for(db).due_html()
        self.assertIn("id='queue'", body)
        self.assertNotIn("commander-track", body)

    def test_due_html_shows_track_and_withholds_locked(self):
        _tmp, db, _s, _out = make_module("cmdtrack caller")
        _add_card(db, 77, "CMDTRACK-REPLAY-OPEN")
        _add_card(db, 48, "CMDTRACK-DECIDE-LOCKED")
        body = handler_for(db).due_html()
        self.assertIn("id='commander-track'", body)
        self.assertIn("CMDTRACK-REPLAY-OPEN", body)
        self.assertNotIn("CMDTRACK-DECIDE-LOCKED", body)


if __name__ == "__main__":
    unittest.main()
