"""Retry-wrong-blanks-only: correct blanks stay filled, wrong ones reopen (I-161)."""
import json
import sqlite3
import unittest

from test_web import make_module

from groundwork import retryblanks as mod


def card(cid="c1"):
    return {"id": cid, "exercise_type": 2,
            "payload": {"blanks": [{"id": 0, "answers": ["atlas"]},
                                   {"id": 1, "answers": ["compass"]},
                                   {"id": 2, "answers": ["sextant"]}]},
            "front": "Fill in the blanks", "back": "atlas compass sextant"}


def _cloze_card_id(db):
    con = sqlite3.connect(db)
    try:
        concept = con.execute("SELECT id FROM concepts LIMIT 1").fetchone()[0]
        cid = "cloze-retry-1"
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload) VALUES(?,?,?,?,?,?)",
            (cid, concept, "2", "Fill the blanks", "atlas compass sextant",
             json.dumps(card()["payload"])))
        con.commit()
    finally:
        con.close()
    return cid


class SplitBlanksTest(unittest.TestCase):
    def test_fallback_recompute_finds_wrong_id(self):
        correct, wrong = mod.split_blanks(card(), "0=atlas\n1=map\n2=sextant")
        self.assertEqual((correct, wrong), ([0, 2], [1]))

    def test_explicit_wrong_ids_win(self):
        correct, wrong = mod.split_blanks(card(), "0=WRONG\n1=map\n2=??", wrong_ids=[2])
        self.assertEqual((correct, wrong), ([0, 1], [2]))

    def test_explicit_empty_means_all_correct(self):
        self.assertEqual(mod.split_blanks(card(), "0=x", wrong_ids=[]), ([0, 1, 2], []))

    def test_garbage_wrong_ids_fall_back_to_recompute(self):
        correct, wrong = mod.split_blanks(card(), "0=atlas\n1=map\n2=sextant",
                                          wrong_ids="nonsense")
        self.assertEqual((correct, wrong), ([0, 2], [1]))

    def test_whitespace_normalized(self):
        correct, wrong = mod.split_blanks(card(), "0=  atlas \n1=compass\n2=sextant")
        self.assertEqual((correct, wrong), ([0, 1, 2], []))

    def test_no_blanks_gives_empty_pair(self):
        self.assertEqual(mod.split_blanks({"id": "c"}, "0=x"), ([], []))

    def test_legacy_answers_list_shape(self):
        legacy = {"id": "c", "payload": {"answers": ["atlas", "compass"]}}
        self.assertEqual(mod.split_blanks(legacy, "0=atlas\n1=map"), ([0], [1]))


class RetryFormTest(unittest.TestCase):
    def test_correct_locked_wrong_open(self):
        out = mod.retry_form(card(), "0=atlas\n1=map\n2=sextant")
        self.assertIn("name='b0'", out)
        self.assertIn("readonly", out)
        self.assertIn("value='atlas'", out)
        self.assertIn("name='b1'", out)
        self.assertIn("placeholder='retry blank 1'", out)
        self.assertNotIn("value='map'", out)

    def test_hidden_twin_carries_correct_value(self):
        out = mod.retry_form(card(), "0=atlas\n1=map\n2=sextant")
        self.assertIn("<input type='hidden' name='b0' value='atlas'>", out)

    def test_all_correct_needs_no_retry(self):
        self.assertEqual(mod.retry_form(card(), "0=atlas\n1=compass\n2=sextant"), "")

    def test_no_data_falls_back_to_full_reanswer(self):
        out = mod.retry_form(card(), "")
        for i in ("0", "1", "2"):
            self.assertIn(f"placeholder='retry blank {i}'", out)
        self.assertNotIn("readonly", out)

    def test_non_cloze_and_missing_blanks_yield_empty(self):
        self.assertEqual(mod.retry_form({"id": "c"}, "0=x"), "")
        self.assertEqual(mod.retry_form("not-a-dict", "0=x"), "")

    def test_values_are_escaped(self):
        evil = {"id": "c1", "payload": {"blanks": [{"id": 0, "answers": ["a"]}]}, }
        out = mod.retry_form(evil, "0=<script>alert(1)</script>", wrong_ids=[9 - 9])
        self.assertNotIn("<script>", out)

    def test_form_posts_to_review_route_with_origin(self):
        out = mod.retry_form(card(), "0=zzz\n1=map\n2=sextant", origin="/due")
        self.assertIn("action='/cards/c1/review'", out)
        self.assertIn("name='origin' value='/due'", out)


class HooksTest(unittest.TestCase):
    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual("improvement", e["kind"])
        self.assertEqual(mod.STATUS_ANCHOR, e["anchor"])
        for key in ("id", "title", "blurb", "path", "anchor"):
            self.assertTrue(e[key])


class EffectTest(unittest.TestCase):
    def test_missed_cloze_returns_retry_form(self):
        tmp, db, server, out = make_module("retry live")
        cid = _cloze_card_id(db)
        res = server.submit_review(cid, "0=atlas\n1=map\n2=sextant", 3)
        self.assertFalse(res["result"]["pass"])
        retry = res.get("retry", "")
        self.assertIn("Retry wrong blanks", retry)
        self.assertIn("value='atlas'", retry)
        self.assertIn("readonly", retry)
        self.assertIn("placeholder='retry blank 1'", retry)
        self.assertIn(f"action='/cards/{cid}/review'", retry)

    def test_clean_cloze_and_surrender_return_no_retry(self):
        tmp, db, server, out = make_module("retry clean")
        cid = _cloze_card_id(db)
        res = server.submit_review(cid, "0=atlas\n1=compass\n2=sextant", 3)
        self.assertTrue(res["result"]["pass"])
        self.assertEqual(res.get("retry", ""), "")
        res = server.submit_review(cid, "", 1)
        self.assertTrue(res["result"].get("revealed"))
        self.assertEqual(res.get("retry", ""), "")


if __name__ == "__main__":
    unittest.main()
