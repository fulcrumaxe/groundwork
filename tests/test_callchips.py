"""Click-to-order chips for call-path-trace cards (I-173)."""
import json
import unittest

from groundwork import callchips as mod
from groundwork import cards as cardsmod
from groundwork import emoji as emojimod
from groundwork import exercises as exmod
from groundwork import parkeys as parkeysmod


def _card(etype=10, lines=None, solution=None):
    lines = ["serve", "grade", "store"] if lines is None else lines
    if solution is None:
        solution = ["serve", "grade", "store"]
    return {"id": "c1", "exercise_type": etype, "concept": "grade",
            "payload": json.dumps({"lines": lines, "solution": solution})}


class CallchipsUnitTest(unittest.TestCase):
    def test_tap_appends_in_order(self):
        self.assertEqual(mod.tap("", 0, 3), "0")
        self.assertEqual(mod.tap("0", 2, 3), "0 2")
        self.assertEqual(mod.tap("0 2", 1, 3), "0 2 1")

    def test_tap_retap_unpicks(self):
        self.assertEqual(mod.tap("0 2", 0, 3), "2")
        self.assertEqual(mod.tap("2", 2, 3), "")

    def test_tap_out_of_range_is_noop(self):
        self.assertEqual(mod.tap("0", 9, 3), "0")
        self.assertEqual(mod.tap("0", -1, 3), "0")

    def test_tap_bad_input_fails_closed(self):
        self.assertEqual(mod.tap(None, "x", 3), "")
        self.assertEqual(mod.tap("0 1", 2, None), "")

    def test_parse_order_drops_bad_and_dupes(self):
        self.assertEqual(mod.parse_order("2 0 x 9", 3), [2, 0])
        self.assertEqual(mod.parse_order("1 1 0", 3), [1, 0])
        self.assertEqual(mod.parse_order(None, 3), [])

    def test_chips_html_escapes_and_syncs(self):
        out = mod.chips_html("c1", ["<serve>", "grade"])
        self.assertIn("&lt;serve&gt;", out)
        self.assertEqual(out.count("<script>"), 1)  # only the sync block
        self.assertIn("data-cc='0'", out)
        self.assertIn("data-cc='clear'", out)
        self.assertIn("__ccInit", out)
        self.assertIn('input[name="answer"]', out)
        self.assertIn('input[name="answer_text"]', out)
        self.assertNotIn("name='", out)  # chips post no new fields

    def test_chips_html_empty_is_legacy(self):
        self.assertEqual(mod.chips_html("c1", []), "")
        self.assertEqual(mod.chips_html("c1", None), "")


class CallchipsEffectTest(unittest.TestCase):
    def test_caller_widget_gains_chips_with_typing_fallback(self):
        out = cardsmod.answer_widget(_card(), 0, "/due")
        review = out.split("</form>")[0]  # review form, not giveup
        self.assertIn("data-cc", out)
        self.assertIn("name='answer_text'", out)  # typed fallback stays
        # Single submission path: one hidden answer + one typed box.
        self.assertEqual(review.count("name='answer'"), 1)
        self.assertEqual(out.count("name='answer_text'"), 1)

    def test_caller_widget_parsons_untouched(self):
        out = cardsmod.answer_widget(_card(etype=11), 0, "/due")
        self.assertNotIn("data-cc", out)
        self.assertIn("name='answer_text'", out)

    def test_caller_widget_empty_lines_is_legacy(self):
        card = _card(lines=[], solution=[])
        out = cardsmod.answer_widget(card, 0, "/due")
        self.assertNotIn("data-cc", out)
        self.assertIn(parkeysmod.block_html("c1", []), out)

    def test_tapped_order_grades_through_real_grader(self):
        ex = {"type": 10, "payload": {"lines": ["serve", "grade", "store"],
                                      "solution": ["serve", "grade", "store"]}}
        good = mod.tap(mod.tap(mod.tap("", 0, 3), 1, 3), 2, 3)
        self.assertEqual(good, "0 1 2")
        self.assertTrue(exmod.grade(ex, good)["pass"])
        bad = mod.tap(mod.tap(mod.tap("", 2, 3), 1, 3), 0, 3)
        self.assertFalse(exmod.grade(ex, bad)["pass"])


class CallchipsShapeTest(unittest.TestCase):
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
