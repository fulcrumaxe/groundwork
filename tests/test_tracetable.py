"""Trace tables: pre-filled step rows + per-cell feedback (I-165)."""
import json
import unittest
from types import SimpleNamespace

from groundwork import cards as cardsmod
from groundwork import emoji as emojimod
from groundwork import exercises as exmod
from groundwork import tracetable as mod


def _card(payload):
    return {"id": "t1", "exercise_type": 9,
            "payload": json.dumps(payload)}


class FakeRunner:
    def run(self, code):
        return SimpleNamespace(ok=True, stdout="", stderr="")


class TracetableUnitTest(unittest.TestCase):
    def test_per_cell_all_pass(self):
        rows = mod.per_cell(["1", "3", "9"], "1\n3\n9")
        self.assertEqual([r["passed"] for r in rows], [True, True, True])
        self.assertEqual([r["step"] for r in rows], [1, 2, 3])

    def test_per_cell_mixed(self):
        rows = mod.per_cell(["1", "3", "9"], "1\n4\n9")
        self.assertEqual([r["passed"] for r in rows], [True, False, True])
        self.assertEqual(rows[1]["want"], "3")
        self.assertEqual(rows[1]["given"], "4")

    def test_per_cell_accepts_single_line_lists(self):
        self.assertTrue(all(r["passed"]
                            for r in mod.per_cell(["1", "3", "9"], "1, 3, 9")))
        self.assertTrue(all(r["passed"]
                            for r in mod.per_cell(["1", "3", "9"], "1 3 9")))

    def test_per_cell_short_marks_missing_failed(self):
        rows = mod.per_cell(["1", "3", "9"], "1\n3")
        self.assertEqual(rows[2], {"step": 3, "passed": False,
                                  "given": "", "want": "9"})

    def test_per_cell_empty_is_empty(self):
        self.assertEqual(mod.per_cell([], "1"), [])
        self.assertEqual(mod.per_cell(None, "1"), [])
        self.assertEqual(mod.summary_line([]), "")

    def test_summary_line(self):
        rows = mod.per_cell(["1", "3", "9"], "1\n4\n9")
        out = mod.summary_line(rows)
        self.assertIn("2/3 steps right", out)
        self.assertIn("step 2: expected '3', you gave '4'", out)
        self.assertEqual(mod.summary_line(mod.per_cell(["1"], "1")),
                         "All 1 steps right.")

    def test_table_rows_prefill(self):
        out = mod.table_rows_html({"code": "x = 1\nx = x + 2", "var": "x",
                                   "expected": ["1", "3"]})
        self.assertIn("<th>Step</th>", out)
        self.assertIn("<code>x = 1</code>", out)
        self.assertIn("name='s0'", out)
        self.assertIn("name='s1'", out)

    def test_table_rows_empty_and_hostile(self):
        self.assertEqual(mod.table_rows_html({}), "")
        self.assertEqual(mod.table_rows_html({"expected": []}), "")
        out = mod.table_rows_html({"code": "<script>", "var": "x",
                                   "expected": ["1"]})
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_cells_html_escapes(self):
        out = mod.cells_html(mod.per_cell(["<b>"], "<i>"))
        self.assertNotIn("<b>", out)
        self.assertNotIn("<i>", out)
        self.assertIn("[!]", out)


class TracetableEffectTest(unittest.TestCase):
    def test_caller_widget_prefills_rows(self):
        out = cardsmod.answer_widget(
            _card({"code": "x = 1\nx = x + 2", "var": "x",
                   "expected": ["1", "3"]}), 0, "/due")
        self.assertIn("<code>x = 1</code>", out)
        self.assertIn("name='s0'", out)

    def test_caller_widget_no_expected_is_legacy(self):
        out = cardsmod.answer_widget(_card({"code": "x = 1"}), 0, "/due")
        self.assertNotIn("<code>", out)
        self.assertIn("<td>Value</td>", out)

    def test_grade_fail_appends_per_cell_detail(self):
        ex = {"type": 9, "payload": {"code": "x = 1\nx = x + 2", "var": "x",
                                    "expected": ["1", "3"]}}
        bad = exmod.grade(ex, "1\n4", FakeRunner())
        self.assertFalse(bad["pass"])
        self.assertTrue(bad["feedback"].startswith("Expected 2 steps;"))
        self.assertIn("1/2 steps right", bad["feedback"])

    def test_grade_pass_verdict_unchanged(self):
        ex = {"type": 9, "payload": {"expected": ["1", "3"]}}
        good = exmod.grade(ex, "1\n3", FakeRunner())
        self.assertTrue(good["pass"])
        self.assertEqual(good["feedback"], "Trace matches.")


class TracetableShapeTest(unittest.TestCase):
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
