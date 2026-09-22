"""Printable lesson handout (I-119)."""
import unittest

from groundwork import handout as homod

from test_web import handler_for, make_module


def _lesson():
    return {"concept_id": "m:add", "name": "add", "kind": "function",
            "file": "calc.py", "line": 1,
            "summary": "add() totals two numbers via its defaults.",
            "docstring": "", "callers": [], "callees": [],
            "key_lines": "total = a + b", "source": "def add(a, b):\n    return a + b\n",
            "how": ["Read the defaults."],
            "worked": "add() -> 5"}


class EmptyFallbackTest(unittest.TestCase):
    def test_empty_lessons_fall_back(self):
        self.assertEqual(homod.handout_html({}), homod.EMPTY_HTML)
        self.assertEqual(homod.handout_html("nope"), homod.EMPTY_HTML)
        self.assertEqual(homod.handout_html({"summary": ""}), homod.EMPTY_HTML)
        self.assertEqual(homod.page_for(":memory:", "nope", "add"),
                         homod.EMPTY_HTML)


class CssTest(unittest.TestCase):
    def test_print_rules_embedded(self):
        css = homod.handout_css()
        self.assertIn("@media print", css)
        self.assertIn("handout", css)
        self.assertNotIn("<style", css)


class DocTest(unittest.TestCase):
    def test_doc_has_summary_how_and_minutes(self):
        out = homod.handout_html({"summary": "a <b>lesson",
                                  "how": ["step one"]}, name="N")
        self.assertIn("<!DOCTYPE html>", out)
        self.assertIn("a &lt;b&gt;lesson", out)
        self.assertIn("step one", out)
        self.assertIn("min", out)
        self.assertNotIn("<b>lesson", out)


class MinutesTest(unittest.TestCase):
    def test_long_summary_estimates_two_minutes(self):
        out = homod.handout_html({"summary": "word " * 400}, name="N")
        self.assertIn("2 min", out)


class CallerEffectTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("handout mod")
        self.mid = self.out["module_id"]
        self.h = handler_for(self.db)

    def test_module_page_links_handout_per_lesson(self):
        body = self.h.module_html(self.mid)
        self.assertIn("handout-link", body)
        self.assertIn(f"/modules/{self.mid}/handout/", body)

    def test_handout_page_serves_doc(self):
        con_cards = self.server.tool_list_due_reviews({"limit": 5})["due"]
        self.assertTrue(con_cards)
        import sqlite3
        con = sqlite3.connect(self.db)
        try:
            concepts = con.execute(
                "SELECT id, name FROM concepts WHERE module_id=?",
                (self.mid,)).fetchall()
        finally:
            con.close()
        node = concepts[0][0].split(":", 1)[1]  # module_html node form
        out = homod.page_for(self.db, self.mid, node)
        self.assertIn("<!DOCTYPE html>", out)
        self.assertIn("@media print", out)
        self.assertEqual(homod.page_for(self.db, self.mid, "no-such-node"),
                         homod.EMPTY_HTML)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{homod.STATUS_ANCHOR}'",
                      homod.section_html())
        e = homod.tour_entry()
        self.assertEqual(e["id"], "lesson-handout")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["anchor"], homod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
