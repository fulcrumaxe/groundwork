"""Line-comment UI for code-review cards (I-168)."""
import json
import unittest

from groundwork import cards as cardsmod
from groundwork import emoji as emojimod
from groundwork import exercises as exmod
from groundwork import linecomment as mod


def _card(snippet=None):
    payload = {"snippet": snippet, "bug_line": 3,
               "rubric": ["helper", "3"]}
    if snippet is None:
        payload = {"bug_line": 0, "rubric": ["helper"]}
    return {"id": "r21", "exercise_type": 21,
            "payload": json.dumps(payload)}


class LinecommentUnitTest(unittest.TestCase):
    def test_serialize_notes(self):
        self.assertEqual(
            mod.serialize_notes([(3, "off-by-one"), (7, "naming")]),
            "L3: off-by-one\nL7: naming")
        self.assertEqual(mod.serialize_notes([(0, "x"), (2, "")]), "")
        self.assertEqual(mod.serialize_notes(None), "")

    def test_parse_notes(self):
        self.assertEqual(
            mod.parse_notes("L3: x\nplain legacy\nl7 - y"),
            [(3, "x"), (7, "y")])
        self.assertEqual(mod.parse_notes("bare legacy text"), [])
        self.assertEqual(mod.parse_notes(None), [])

    def test_round_trip(self):
        n = [(3, "x"), (7, "y")]
        self.assertEqual(mod.parse_notes(mod.serialize_notes(n)), n)

    def test_accused_line(self):
        self.assertEqual(mod.accused_line("L3: helper loops"), 3)
        self.assertEqual(mod.accused_line("line 5 broke"), 5)
        self.assertIsNone(mod.accused_line("no digits here"))

    def test_snippet_lines(self):
        self.assertEqual(mod.snippet_lines("1: a\n2: b"),
                         [(1, "a"), (2, "b")])
        self.assertEqual(mod.snippet_lines("a\nb"), [(1, "a"), (2, "b")])
        self.assertEqual(mod.snippet_lines(""), [])

    def test_review_html(self):
        out = mod.review_html("1: a")
        self.assertIn("lc-gut", out)
        self.assertIn("lc-note", out)
        self.assertIn("name='answer'", out)
        self.assertEqual(mod.review_html(""), "")
        self.assertEqual(mod.review_html(None), "")

    def test_grader_parity_l_format_passes(self):
        ex = {"type": 21, "payload": {"snippet": "1: a", "bug_line": 3,
                                      "rubric": ["helper", "3"]}}
        self.assertTrue(exmod.grade(ex, "L3: helper loops one past")["pass"])

    def test_grader_parity_legacy_verdicts_unchanged(self):
        ex = {"type": 21, "payload": {"snippet": "1: a", "bug_line": 3,
                                      "rubric": ["helper", "3"]}}
        self.assertTrue(exmod.grade(ex, "helper broke on line 3")["pass"])
        self.assertFalse(exmod.grade(ex, "helper")["pass"])


class LinecommentEffectTest(unittest.TestCase):
    def test_caller_widget_gains_line_comments(self):
        out = cardsmod.answer_widget(_card("1: a\n2: b"), 0, "/due")
        self.assertIn("lc-gut", out)
        self.assertIn("lc-note", out)
        self.assertIn("__lcInit", out)

    def test_caller_widget_no_snippet_is_legacy(self):
        out = cardsmod.answer_widget(_card(None), 0, "/due")
        self.assertNotIn("lc-gut", out)
        self.assertNotIn("__lcInit", out)
        self.assertIn("<textarea name='answer' rows='5' cols='70' "
                      "placeholder='Explain in your own words…'>"
                      "</textarea><br>", out)
        self.assertIn("<button>Submit explanation</button>", out)

    def test_branch_fallback_matches_shared_shape(self):
        card25 = {"id": "e25", "exercise_type": 25, "payload": json.dumps({})}
        legacy25 = cardsmod.answer_widget(card25, 0, "/due")
        legacy21 = cardsmod.answer_widget(_card(None), 0, "/due")
        # Same textarea + submit shape (only the dispute id differs).
        for needle in ("<textarea name='answer' rows='5' cols='70'",
                       "Submit explanation"):
            self.assertIn(needle, legacy21)
            self.assertIn(needle, legacy25)


class LinecommentShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "improvement")

    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])


if __name__ == "__main__":
    unittest.main()
