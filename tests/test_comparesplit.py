"""Side-by-side compare panes with synced scrolling (I-169)."""
import json
import unittest

from groundwork import cards as cardsmod
from groundwork import comparesplit as mod
from groundwork import emoji as emojimod

FRONT = ("Two versions of `add`. First line of your answer: A or B.\n"
         "**Version A:**\n```python\nx = 1\ny = 2\n```\n\n"
         "**Version B:**\n```python\nx = 1\ny = 3\n```")


def _card(front):
    return {"id": "v22", "exercise_type": 22,
            "payload": json.dumps({"answer": "B"}), "front": front}


class ComparesplitUnitTest(unittest.TestCase):
    def test_parse_versions_extracts_both(self):
        a, b = mod.parse_versions(FRONT)
        self.assertEqual(a, "x = 1\ny = 2")
        self.assertEqual(b, "x = 1\ny = 3")

    def test_parse_versions_fails_closed(self):
        self.assertEqual(mod.parse_versions("no versions here"), ("", ""))
        self.assertEqual(mod.parse_versions(""), ("", ""))
        self.assertEqual(mod.parse_versions(None), ("", ""))

    def test_panes_escape_both_sides(self):
        out = mod.panes_html("<x>", "<y>")
        self.assertIn("&lt;x&gt;", out)
        self.assertIn("&lt;y&gt;", out)
        self.assertNotIn("<x>", out.replace("<pre>", "").replace(
            "<span class='csplit-diff'>", ""))

    def test_panes_align_and_mark_diffs(self):
        out = mod.panes_html("x = 1\ny = 2", "x = 1\ny = 3")
        self.assertEqual(out.count("<pre>"), 2)
        self.assertIn("csplit-diff", out)
        self.assertIn("y = 2", out)
        self.assertIn("y = 3", out)

    def test_panes_blank_is_empty(self):
        self.assertEqual(mod.panes_html("", ""), "")
        self.assertEqual(mod.panes_html(None, None), "")

    def test_sync_script_links_both_ways(self):
        out = mod.panes_html("a", "b", uid="cs9")
        self.assertIn("id='cs9a'", out)
        self.assertIn("id='cs9b'", out)
        self.assertIn("scrollTop", out)
        self.assertIn("scrollLeft", out)

    def test_uid_sanitized(self):
        out = mod.panes_html("a", "b", uid="a'b\"<c>")
        self.assertIn("id='abca'", out)

    def test_css_has_no_style_tag(self):
        self.assertNotIn("<style>", mod.split_css())
        self.assertIn(".csplit-pane", mod.split_css())


class ComparesplitEffectTest(unittest.TestCase):
    def test_caller_widget_gains_panes_with_textarea(self):
        out = cardsmod.answer_widget(_card(FRONT), 0, "/due")
        self.assertIn("csplit", out)
        self.assertIn("First line: A or B", out)
        self.assertIn("Submit explanation", out)

    def test_caller_widget_no_versions_is_legacy(self):
        out = cardsmod.answer_widget(_card("plain front"), 0, "/due")
        self.assertNotIn("csplit", out)
        self.assertIn("First line: A or B", out)

    def test_other_types_untouched(self):
        card = {"id": "e5", "exercise_type": 5, "payload": json.dumps({}),
                "front": FRONT}
        out = cardsmod.answer_widget(card, 0, "/due")
        self.assertNotIn("csplit", out)


class ComparesplitShapeTest(unittest.TestCase):
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
