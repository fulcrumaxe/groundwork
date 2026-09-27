"""Scratch runs: execute a draft without recording an attempt (I-185)."""
import json
import sqlite3
import unittest

from groundwork import cards as cardsmod
from groundwork import scratchrun as mod

from test_web import make_module


def _card(etype="12"):
    return {"id": "sc1", "exercise_type": etype,
            "payload": json.dumps({"tests": "assert True"})}


def _reviews(db):
    con = sqlite3.connect(db)
    try:
        return con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    finally:
        con.close()


class ButtonTest(unittest.TestCase):
    def test_button_posts_to_scratch_via_formaction(self):
        out = mod.button_html("c9")
        self.assertIn("formaction='/cards/c9/scratch'", out)
        self.assertIn("type='submit'", out)
        self.assertIn("Run without submitting", out)

    def test_hostile_id_is_empty(self):
        self.assertEqual(mod.button_html(""), "")
        self.assertEqual(mod.button_html(None), "")

    def test_code_etype_gate(self):
        for t in ("12", "14", "19", "20", "23"):
            self.assertTrue(mod.is_code_card(_card(t)), t)
        for t in ("1", "2", "3", "4", "8", "11", "99"):
            self.assertFalse(mod.is_code_card(_card(t)), t)
        self.assertFalse(mod.is_code_card(None))
        self.assertFalse(mod.is_code_card({}))

    def test_enhance_identity_off_code(self):
        body = "<p>legacy</p>"
        self.assertIs(mod.enhance(_card("1"), "c", body), body)
        self.assertIs(mod.enhance(_card("8"), "c", body), body)
        self.assertIs(mod.enhance(None, "c", body), body)

    def test_enhance_appends_on_code(self):
        out = mod.enhance(_card("12"), "c9", "<p>ed</p>")
        self.assertIn("<p>ed</p>", out)
        self.assertIn("/cards/c9/scratch", out)


class CallerEffectTest(unittest.TestCase):
    def test_due_code_card_gains_scratch_button_inside_form(self):
        out = cardsmod.answer_widget(_card("12"), 0, "/due")
        self.assertIn("formaction='/cards/sc1/scratch'", out)
        form = out.split("<form")[1].split("</form>")[0]
        self.assertIn("formaction=", form)  # inside the answer form

    def test_non_code_card_has_no_scratch_button(self):
        out = cardsmod.answer_widget(_card("1"), 0, "/due")
        self.assertNotIn("/scratch", out)

    def test_scratch_run_shows_output_and_records_nothing(self):
        tmp, db, server, out = make_module("scratch mod")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        before = _reviews(db)
        body = mod.page_for(db, card["id"], "print(40 + 2)", "/due", 4)
        self.assertIsNotNone(body)
        self.assertIn("42", body)
        self.assertIn("Not recorded", body)
        self.assertIn("print(40 + 2)", body)  # draft prefilled
        self.assertIn(f"/cards/{card['id']}/review", body)
        self.assertEqual(_reviews(db), before)  # no review row written

    def test_scratch_run_shows_errors_honestly(self):
        tmp, db, server, out = make_module("scratch err mod")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        body = mod.page_for(db, card["id"], "print(1/0)", "/due", 3)
        self.assertIn("ZeroDivisionError", body)
        self.assertIn("Not recorded", body)

    def test_unknown_card_is_none(self):
        tmp, db, server, out = make_module("scratch unknown mod")
        self.assertIsNone(mod.page_for(db, "nope", "print(1)"))
        self.assertIsNone(mod.page_for("/nonexistent/x.db", "c", "print(1)"))

    def test_hostile_inputs_never_raise(self):
        tmp, db, server, out = make_module("scratch hostile mod")
        self.assertIsNone(mod.page_for(db, None, None))
        body = mod.page_for(db, server.tool_list_due_reviews(
            {"limit": 1})["due"][0]["id"], None, None, "x")
        self.assertIn("(no output)", body)


class ShapeTest(unittest.TestCase):
    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual((e["id"], e["kind"], e["path"], e["anchor"]),
                         ("scratch-runs", "improvement",
                          "/status", mod.STATUS_ANCHOR))


if __name__ == "__main__":
    unittest.main()
