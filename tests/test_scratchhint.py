"""Scratch runs unlock hints without touching grades (I-186)."""
import json
import sqlite3
import unittest

from groundwork import scratchhint as mod
from groundwork import scratchrun as scratchmod
from groundwork import web as webmod

from test_web import make_module


HINTS = ["nudge: reread the defaults", "pointer: trace the total line",
         "worked: add() returns 2 + 3 = 5"]


def _set_hints(db, cid, hints):
    con = sqlite3.connect(db)
    try:
        con.execute("UPDATE cards SET payload=? WHERE id=?",
                    (json.dumps({"hints": hints}), cid))
        con.commit()
    finally:
        con.close()


def _reviews(db):
    con = sqlite3.connect(db)
    try:
        return con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    finally:
        con.close()


def _due_card_id(server):
    return server.tool_list_due_reviews({"limit": 1})["due"][0]["id"]


class ParseTest(unittest.TestCase):
    def test_absent_or_empty_is_zero(self):
        self.assertEqual(mod.parse_count(""), 0)
        self.assertEqual(mod.parse_count(None), 0)
        self.assertEqual(mod.parse_count("answer=x&confidence=3"), 0)

    def test_valid_count(self):
        self.assertEqual(mod.parse_count("answer=x&scratches=2"), 2)
        self.assertEqual(mod.parse_count("scratches=0"), 0)

    def test_hostile_fails_closed(self):
        self.assertEqual(mod.parse_count("scratches=abc"), 0)
        self.assertEqual(mod.parse_count("scratches=-3"), 0)
        self.assertEqual(mod.parse_count("scratches="), 0)
        self.assertEqual(mod.parse_count(12345), 0)
        self.assertEqual(mod.parse_count(["scratches=2"]), 0)

    def test_absurd_clamps(self):
        self.assertEqual(mod.parse_count("scratches=500"), mod.MAX_PRIOR)


class EffectiveTest(unittest.TestCase):
    def test_first_scratch_counts_one(self):
        self.assertEqual(mod.effective_attempts(0, 0), 1)

    def test_graded_plus_scratches(self):
        self.assertEqual(mod.effective_attempts(2, 3), 6)

    def test_hostile_fails_closed(self):
        self.assertEqual(mod.effective_attempts(None, "x"), 1)
        self.assertEqual(mod.effective_attempts(-5, -2), 1)


class UnlockTest(unittest.TestCase):
    def test_first_scratch_unlocks_second_tier(self):
        tmp, db, server, out = make_module("scratchhint first")
        cid = _due_card_id(server)
        _set_hints(db, cid, HINTS)
        body = mod.unlock_html(db, cid, 0)
        self.assertIn(HINTS[0], body)
        self.assertIn(HINTS[1], body)
        self.assertNotIn(HINTS[2], body)
        self.assertIn("Scratch run 1", body)
        self.assertIn("not graded", body)
        self.assertIn("2 of 3 hints", body)
        self.assertIn("graded attempts still 0", body)

    def test_second_scratch_unlocks_all(self):
        tmp, db, server, out = make_module("scratchhint second")
        cid = _due_card_id(server)
        _set_hints(db, cid, HINTS)
        body = mod.unlock_html(db, cid, 1)
        for h in HINTS:
            self.assertIn(h, body)
        self.assertIn("Scratch run 2", body)

    def test_graded_attempts_add_to_scratches(self):
        tmp, db, server, out = make_module("scratchhint graded")
        cid = _due_card_id(server)
        _set_hints(db, cid, HINTS)
        server.submit_review(cid, "5", 4)
        body = mod.unlock_html(db, cid, 0)
        for h in HINTS:
            self.assertIn(h, body)
        self.assertIn("graded attempts still 1", body)

    def test_no_hints_is_empty_legacy(self):
        tmp, db, server, out = make_module("scratchhint legacy")
        cid = _due_card_id(server)
        self.assertEqual(mod.unlock_html(db, cid, 0), "")
        self.assertEqual(mod.unlock_html(db, cid, 5), "")

    def test_unknown_card_or_db_is_empty(self):
        tmp, db, server, out = make_module("scratchhint unknown")
        self.assertEqual(mod.unlock_html(db, "nope", 0), "")
        self.assertEqual(mod.unlock_html("/nonexistent/x.db", "c", 0), "")
        self.assertEqual(mod.unlock_html(db, None, None), "")

    def test_unlock_writes_nothing(self):
        tmp, db, server, out = make_module("scratchhint nowrite")
        cid = _due_card_id(server)
        _set_hints(db, cid, HINTS)
        before = _reviews(db)
        mod.unlock_html(db, cid, 0)
        mod.unlock_html(db, cid, 2)
        self.assertEqual(_reviews(db), before)


class AgainTest(unittest.TestCase):
    def test_posts_incremented_count_with_draft(self):
        out = mod.again_html("c9", "print(1)", "/due", 4, 1)
        self.assertIn("action='/cards/c9/scratch'", out)
        self.assertIn("name='scratches' value='2'", out)
        self.assertIn("print(1)", out)
        self.assertIn("Run again without submitting", out)

    def test_draft_is_escaped(self):
        out = mod.again_html("c9", "<b>&", "/due", 3, 0)
        self.assertIn("&lt;b&gt;&amp;", out)
        self.assertNotIn("<b>&", out)

    def test_hostile_inputs(self):
        self.assertEqual(mod.again_html("", "x"), "")
        self.assertEqual(mod.again_html(None, "x"), "")
        out = mod.again_html("c9", None, None, "x", "y")
        self.assertIn("value='1'", out)  # fail-closed to run 1


class CallerEffectTest(unittest.TestCase):
    def test_scratch_page_unlocks_and_records_nothing(self):
        tmp, db, server, out = make_module("scratchhint caller")
        cid = _due_card_id(server)
        _set_hints(db, cid, HINTS)
        before = _reviews(db)
        body = scratchmod.page_for(
            db, cid, "print(40 + 2)", "/due", 4,
            "answer=print(40+%2B+2)&scratches=1")
        self.assertIsNotNone(body)
        self.assertIn("42", body)
        self.assertIn(HINTS[2], body)  # run 2 unlocks the worked step
        self.assertIn("Run again without submitting", body)
        self.assertIn("name='scratches' value='2'", body)
        self.assertIn("Submit for real", body)  # grade path still offered
        self.assertEqual(_reviews(db), before)

    def test_no_hint_page_has_no_unlock_or_again(self):
        tmp, db, server, out = make_module("scratchhint nohint")
        cid = _due_card_id(server)
        body = scratchmod.page_for(db, cid, "print(1)", "/due", 3)
        self.assertNotIn("Scratch run 1", body)
        self.assertNotIn("Run again", body)
        self.assertNotIn("id='hints'", body)
        self.assertIn("Not recorded", body)

    def test_grading_input_ignores_scratch_count(self):
        answer, conf, origin = webmod._parse_review_form(
            "answer=x&confidence=4&origin=/due&scratches=5")
        self.assertEqual((answer, conf, origin), ("x", 4, "/due"))


class ShapeTest(unittest.TestCase):
    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual((e["id"], e["kind"], e["path"], e["anchor"]),
                         ("scratch-hint-unlock", "improvement",
                          "/status", mod.STATUS_ANCHOR))


if __name__ == "__main__":
    unittest.main()
