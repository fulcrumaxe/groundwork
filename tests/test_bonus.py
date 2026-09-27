"""Bonus attempts skip FSRS/mastery/review persistence (I-192)."""
import sqlite3
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path

from groundwork import bonus as mod
from groundwork import db as dbmod
from groundwork import mcp as mcplib
from groundwork import northstar as northstarmod
from groundwork import ownership as ownmod
from groundwork import sched as schedmod

from test_web import make_module


def _probe_db():
    """Fresh DB mirroring test_batch15: owned/stable card, review 8d ago."""
    tmp = Path(tempfile.mkdtemp(prefix="gw-bonus-"))
    db = str(tmp / "bonus.db")
    dbmod.init_db(db)
    past = (schedmod.utcnow() - timedelta(days=8)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    future = (schedmod.utcnow() + timedelta(days=30)).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
    con = sqlite3.connect(db)
    try:
        con.execute(
            "INSERT INTO modules(id, task_summary, repo, commit_range)"
            " VALUES(?,?,?,?)", ("m1", "bonus mod", ".", "x"))
        con.execute(
            "INSERT INTO concepts(id, module_id, name)"
            " VALUES(?,?,?)", ("m1:c1", "m1", "loops"))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front,"
            " back, stability, difficulty, due)"
            " VALUES(?,?,?,?,?,?,?,?)",
            ("m1:c1:ex1", "m1:c1", "12", "trace it", "traced",
             30.0, 0.5, future))
        con.executemany(
            "INSERT INTO reviews(card_id, grade, confidence,"
            " reviewed_at) VALUES(?,?,?,?)",
            [("m1:c1:ex1", 5, 4, past)] * 2)
        con.commit()
    finally:
        con.close()
    return db


def _stats(db):
    """All persisted stat surfaces bonus must leave untouched."""
    con = dbmod.connect(db)
    try:
        card = dict(con.execute(
            "SELECT stability, difficulty, retrievability, due, lapses,"
            " last_probe FROM cards WHERE id=?",
            ("m1:c1:ex1",)).fetchone())
        mastery = con.execute(
            "SELECT mastery FROM concepts WHERE id=?",
            ("m1:c1",)).fetchone()[0]
        n = con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
        avg = con.execute("SELECT AVG(grade) FROM reviews").fetchone()[0]
        omap = ownmod.owned_map(con, "m1")
    finally:
        con.close()
    snap = northstarmod.snapshot(db)
    return {"card": card, "mastery": mastery, "reviews": n,
            "avg": avg, "owned_attempts": omap["m1:c1"][0],
            "northstar_attempts": snap["attempts"]}


class PolicyTest(unittest.TestCase):
    def test_either_channel_excludes(self):
        self.assertFalse(mod.should_exclude(False, False))
        self.assertTrue(mod.should_exclude(True, False))
        self.assertTrue(mod.should_exclude(False, True))
        self.assertTrue(mod.should_exclude(True, True))

    def test_hostile_fails_closed_to_persist(self):
        for args in ((None, None), ("", 0), (0, []), (None, "")):
            self.assertFalse(mod.should_exclude(*args), args)

    def test_from_body_flag_table(self):
        self.assertTrue(mod.from_body("answer=5&bonus=1"))
        self.assertTrue(mod.from_body("bonus=true"))
        self.assertTrue(mod.from_body("bonus=YES&confidence=4"))
        self.assertTrue(mod.from_body("a=1&bonus=on"))
        self.assertFalse(mod.from_body("answer=5&confidence=4"))
        self.assertFalse(mod.from_body("bonus=0"))
        self.assertFalse(mod.from_body("bonus=2"))
        self.assertFalse(mod.from_body(""))
        self.assertFalse(mod.from_body(None))
        self.assertFalse(mod.from_body(123))
        self.assertFalse(mod.from_body({}))

    def test_bonus_inside_answer_text_is_not_a_flag(self):
        self.assertFalse(mod.from_body("answer=bonus%3D1&confidence=3"))
        self.assertFalse(mod.from_body("answer_text=bonus%3Dtrue"))


class ProbeExclusionTest(unittest.TestCase):
    def test_probe_answer_grades_but_persists_nothing(self):
        db = _probe_db()
        server = mcplib.MCPServer(db)
        due = server.tool_list_due_reviews({"limit": 20})["due"]
        probe = next(c for c in due if c["id"] == "m1:c1:ex1")
        self.assertEqual(probe["probe"], 7)  # bonus-class membership
        before = _stats(db)
        self.assertIsNone(before["card"]["last_probe"])
        r = server.submit_review("m1:c1:ex1", "xxx", 3)
        self.assertNotIn("error", r)
        self.assertTrue(r["bonus"])
        self.assertEqual(r["grade"], 1)  # grading still ran
        self.assertTrue(r["result"]["feedback"])
        self.assertEqual(r["points"], 0)
        self.assertEqual(r["next_due"], before["card"]["due"])
        after = _stats(db)
        for key in ("stability", "difficulty", "retrievability",
                    "due", "lapses"):
            self.assertEqual(after["card"][key], before["card"][key],
                             key)
        self.assertEqual(after["mastery"], before["mastery"])
        self.assertEqual(after["reviews"], before["reviews"])
        self.assertEqual(after["avg"], before["avg"])
        self.assertEqual(after["owned_attempts"],
                         before["owned_attempts"])
        self.assertEqual(after["northstar_attempts"],
                         before["northstar_attempts"])
        self.assertTrue(after["card"]["last_probe"])  # cycle closes


class ExplicitBonusTest(unittest.TestCase):
    def test_bonus_kwarg_excludes_without_probe_stamp(self):
        tmp, db, server, out = make_module("bonus explicit mod")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        con = sqlite3.connect(db)
        try:
            stored_due = con.execute(
                "SELECT due FROM cards WHERE id=?",
                (card["id"],)).fetchone()[0]
        finally:
            con.close()
        r = server.submit_review(card["id"], "5", 4, bonus=True)
        self.assertTrue(r["bonus"])
        self.assertEqual(r["grade"], 5)
        self.assertEqual(r["points"], 0)
        # next_due echoes the STORED due (the Due-list display due is
        # transformed by quiet-hours deferral); both freeze on bonus.
        self.assertEqual(r["next_due"], stored_due)
        con = sqlite3.connect(db)
        try:
            n = con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
            row = con.execute(
                "SELECT stability, last_probe FROM cards WHERE id=?",
                (card["id"],)).fetchone()
            mastery = con.execute(
                "SELECT mastery FROM concepts").fetchone()[0]
        finally:
            con.close()
        self.assertEqual(n, 0)
        self.assertEqual(row[0], 1.0)
        self.assertIsNone(row[1])
        self.assertEqual(mastery, 0.0)


class VariantBonusTest(unittest.TestCase):
    """I-191 siblings are bonus by id; due still flows (parent-added)."""

    def test_variant_answer_freezes_stats_but_moves_due(self):
        from groundwork import similar as simmod
        tmp = Path(tempfile.mkdtemp(prefix="gw-bonus-variant-"))
        db = str(tmp / "v.db")
        dbmod.init_db(db)
        con = sqlite3.connect(db)
        try:
            con.execute("INSERT INTO modules(id, task_summary, repo)"
                        " VALUES(?,?,?)", ("m1", "vmod", "."))
            con.execute("INSERT INTO concepts(id, module_id, name)"
                        " VALUES(?,?,?)", ("m1:add", "m1", "add"))
            con.commit()
        finally:
            con.close()
        import json
        payload = {"func": "add", "signature": "add(a, b)",
                   "choices": ["add(a, b)", "add(b, a)", "add(...)"],
                   "answer": "add(a, b)"}
        con = sqlite3.connect(db)
        try:
            con.execute("INSERT INTO cards(id, concept_id, exercise_type,"
                        " front, back, payload) VALUES(?,?,?,?,?,?)",
                        ("m1:ex001", "m1:add", "7", "f", "b",
                         json.dumps(payload)))
            con.commit()
        finally:
            con.close()
        server = mcplib.MCPServer(db)
        # Fail the parent: mints the sibling (I-191).
        out = server.submit_review("m1:ex001", "add(b, a)", 3)
        self.assertFalse(out["result"]["pass"])
        vid = "m1:ex001~sim1"
        self.assertTrue(simmod.is_variant(vid))
        con = sqlite3.connect(db)
        try:
            due_before = con.execute(
                "SELECT due FROM cards WHERE id=?", (vid,)).fetchone()[0]
            n_before = con.execute(
                "SELECT COUNT(*) FROM reviews").fetchone()[0]
            stab_before = con.execute(
                "SELECT stability FROM cards WHERE id=?",
                (vid,)).fetchone()[0]
        finally:
            con.close()
        # Answer the variant: grades, but stats frozen.
        r = server.submit_review(vid, "add(a, b)", 4)
        self.assertNotIn("error", r)
        self.assertTrue(r["bonus"])
        self.assertTrue(r["result"]["pass"])
        self.assertEqual(r["points"], 0)
        con = sqlite3.connect(db)
        try:
            row = con.execute(
                "SELECT stability, difficulty, due, last_probe FROM cards"
                " WHERE id=?", (vid,)).fetchone()
            n_after = con.execute(
                "SELECT COUNT(*) FROM reviews").fetchone()[0]
            mastery = con.execute(
                "SELECT mastery FROM concepts WHERE id=?",
                ("m1:add",)).fetchone()[0]
        finally:
            con.close()
        self.assertEqual(n_after, n_before)  # no review row
        self.assertEqual(row[0], stab_before)  # stability frozen
        self.assertEqual(row[1], 0.5)  # difficulty frozen
        self.assertIsNone(row[3])  # no probe stamp on variants
        self.assertNotEqual(row[2], due_before)  # due flows: no barnacle
        self.assertEqual(r["next_due"], row[2])
        # Parent mastery moved only for the parent's own fail, never
        # for the variant pass (1 fail at grade 1: 0.2 * 0.3).
        self.assertAlmostEqual(mastery, (1 / 5.0) * 0.3)

    def test_variant_fail_mints_no_nested_variant(self):
        from groundwork import similar as simmod
        tmp = Path(tempfile.mkdtemp(prefix="gw-bonus-nested-"))
        db = str(tmp / "n.db")
        dbmod.init_db(db)
        con = sqlite3.connect(db)
        try:
            con.execute("INSERT INTO modules(id, task_summary, repo)"
                        " VALUES(?,?,?)", ("m1", "nmod", "."))
            con.execute("INSERT INTO concepts(id, module_id, name)"
                        " VALUES(?,?,?)", ("m1:add", "m1", "add"))
            con.commit()
        finally:
            con.close()
        import json
        payload = {"func": "add", "signature": "add(a, b)",
                   "choices": ["add(a, b)", "add(b, a)", "add(...)"],
                   "answer": "add(a, b)"}
        con = sqlite3.connect(db)
        try:
            con.execute("INSERT INTO cards(id, concept_id, exercise_type,"
                        " front, back, payload) VALUES(?,?,?,?,?,?)",
                        ("m1:ex001", "m1:add", "7", "f", "b",
                         json.dumps(payload)))
            con.commit()
        finally:
            con.close()
        server = mcplib.MCPServer(db)
        server.submit_review("m1:ex001", "add(b, a)", 3)
        r = server.submit_review("m1:ex001~sim1", "add(b, a)", 2)
        self.assertFalse(r["result"]["pass"])
        self.assertEqual(r.get("similar", ""), "")
        self.assertFalse(simmod.is_variant("m1:ex001"))
        self.assertTrue(simmod.is_variant(None) is False)
        con = sqlite3.connect(db)
        try:
            ids = [row[0] for row in con.execute(
                "SELECT id FROM cards").fetchall()]
        finally:
            con.close()
        self.assertEqual(sorted(ids), ["m1:ex001", "m1:ex001~sim1"])


class LegacyPathTest(unittest.TestCase):
    def test_default_and_explicit_false_persist(self):
        tmp, db, server, out = make_module("bonus legacy mod")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        r = server.submit_review(card["id"], "5", 4)
        self.assertFalse(r["bonus"])
        self.assertEqual(r["points"], 4)
        r2 = server.submit_review(card["id"], "5", 4, bonus=False)
        self.assertFalse(r2["bonus"])
        con = sqlite3.connect(db)
        try:
            n = con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
            stab = con.execute(
                "SELECT stability FROM cards WHERE id=?",
                (card["id"],)).fetchone()[0]
            mastery = con.execute(
                "SELECT mastery FROM concepts").fetchone()[0]
        finally:
            con.close()
        self.assertEqual(n, 2)
        self.assertGreater(stab, 1.0)
        self.assertGreater(mastery, 0.0)


class ShapeTest(unittest.TestCase):
    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual((e["id"], e["kind"], e["path"], e["anchor"]),
                         ("bonus-attempts", "improvement",
                          "/status", mod.STATUS_ANCHOR))


if __name__ == "__main__":
    unittest.main()
