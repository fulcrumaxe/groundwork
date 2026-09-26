"""Parsons partial-order check: longest correct run (I-163)."""
import json
import unittest

from groundwork import cards as cardsmod
from groundwork import emoji as emojimod
from groundwork import parcheck as mod


def _card(lines, solution):
    return {"id": "c9", "exercise_type": 11,
            "payload": json.dumps({"lines": lines, "solution": solution})}


class ParcheckScanTest(unittest.TestCase):
    def test_empty_is_zero(self):
        self.assertEqual(mod.longest_correct_run([], ["a"]), (0, 0))
        self.assertEqual(mod.longest_correct_run([], []), (0, 0))

    def test_full_run(self):
        self.assertEqual(
            mod.longest_correct_run(["a", "b", "c"], ["a", "b", "c"]), (0, 3))

    def test_reversed_is_singletons(self):
        self.assertEqual(
            mod.longest_correct_run(["c", "b", "a"], ["a", "b", "c"]), (0, 1))

    def test_swap_finds_tail_block(self):
        self.assertEqual(
            mod.longest_correct_run(["a", "c", "b", "d", "e"],
                                    ["a", "b", "c", "d", "e"]), (3, 2))

    def test_ties_keep_earliest(self):
        self.assertEqual(
            mod.longest_correct_run(["a", "b", "x", "c", "d"],
                                    ["a", "b", "c", "d", "e"]), (0, 2))

    def test_unknown_items_break_runs(self):
        self.assertEqual(
            mod.longest_correct_run(["a", "z", "b"], ["a", "b"]), (0, 1))

    def test_hostile_fails_closed(self):
        for bad in (None, 5, "s", {"a": 1}):
            self.assertEqual(mod.longest_correct_run(bad, bad), (0, 0))

    def test_run_from_indices_resolves_like_grader(self):
        self.assertEqual(
            mod.run_from_indices([0, 2, 1], ["a", "b", "c"],
                                 ["a", "b", "c"]), (0, 1))
        self.assertEqual(mod.run_from_indices([9], ["a"], ["a"]), (0, 0))

    def test_truth_indices_map_to_data_i_space(self):
        self.assertEqual(
            mod.truth_indices(["b", "a", "c"], ["a", "b", "c"]), [1, 0, 2])
        self.assertEqual(mod.truth_indices(["a"], ["a", "z"]), [])

    def test_message(self):
        self.assertEqual(mod.message(3, 6), "longest correct run: 3 of 6")


class ParcheckWidgetTest(unittest.TestCase):
    def test_check_html_carries_button_slot_and_truth(self):
        out = mod.check_html("c9", ["b", "a"], ["a", "b"])
        self.assertIn("Check partial order", out)
        self.assertIn("type='button'", out)
        self.assertIn("<output id='pc-c9'", out)
        self.assertIn("id='ps-c9' value='1 0'", out)
        self.assertNotIn("name=", out)  # truth carrier never posts

    def test_check_html_empty_when_unmapped_or_off(self):
        self.assertEqual(mod.check_html("c", ["a"], ["z"]), "")
        self.assertEqual(mod.check_html("c", ["a"], ["a"], enabled=False), "")

    def test_js_scans_without_submitting(self):
        js = mod.check_js()
        self.assertIn("__parcheckInit", js)
        self.assertIn("ps-", js)
        self.assertNotIn("submit", js.lower())

    def test_caller_widget_gains_check(self):
        out = cardsmod.answer_widget(
            _card(["b = 1", "a = 2"], ["a = 2", "b = 1"]), 0, "/due")
        self.assertIn("data-parcheck", out)
        self.assertIn("id='pc-", out)
        self.assertIn("Check partial order", out)
        self.assertIn("__parcheckInit", out)

    def test_caller_widget_without_solution_is_legacy(self):
        out = cardsmod.answer_widget(_card(["a"], []), 0, "/due")
        self.assertNotIn("data-parcheck", out)
        self.assertNotIn("__parcheckInit", out)


class ParcheckShapeTest(unittest.TestCase):
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
