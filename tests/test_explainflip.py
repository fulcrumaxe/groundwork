"""I-102: explain-differently order toggle (groundwork/explainflip.py)."""
import unittest

from groundwork import explainflip as flipmod
from groundwork import explain as explainmod
from groundwork import lessons as lesmod


def _lesson(**kw):
    base = {"concept_id": "c", "name": "add", "kind": "function",
            "file": "calc.py", "line": 1, "summary": "Adds a and b.",
            "docstring": "", "callers": [], "callees": [],
            "key_lines": "", "source": "def add(a, b):\n    return a + b\n",
            "how": ["take a", "take b", "return total"], "worked": None,
            "dualcode": {"steps": [], "states": []}}
    base.update(kw)
    return base


def _worked_lesson():
    return _lesson(worked={"call": "add(2, 3)", "output": "5",
                           "trace": {"var": "total", "steps": [2, 5]}})


class NormalizeTest(unittest.TestCase):
    def test_default_and_unknown_fall_back_to_definition(self):
        for v in (None, "", "bogus", "DEFINITION ", 0, ["examples"]):
            self.assertEqual(flipmod.normalize_order(v), "definition")

    def test_examples_variants(self):
        for v in ("examples", "Example", "example-first"):
            self.assertEqual(flipmod.normalize_order(v), "examples")


class ReorderTest(unittest.TestCase):
    def test_definition_first_is_legacy_order(self):
        blocks = [{"h": "What it does", "b": "d"}, {"h": "Worked example", "b": "e"}]
        self.assertEqual(flipmod.reorder_blocks(blocks, "definition"), blocks)
        self.assertEqual(flipmod.reorder_blocks(blocks), blocks)

    def test_example_first_moves_narrated_front_stably(self):
        blocks = [{"h": "What it does", "b": "d"},
                  {"h": "How it works", "b": "h"},
                  {"h": "Worked example", "b": "e"}]
        out = flipmod.reorder_blocks(blocks, "examples")
        # Leading non-example block stays pinned (retrieval-probe rule).
        self.assertEqual([b["h"] for b in out],
                         ["What it does", "Worked example", "How it works"])
        lead_example = [{"h": "Worked example", "b": "e"},
                        {"h": "What it does", "b": "d"}]
        self.assertEqual(
            [b["h"] for b in flipmod.reorder_blocks(lead_example, "examples")],
            ["Worked example", "What it does"])

    def test_content_set_identical_in_both_orders(self):
        blocks = [{"h": "What it does", "b": "d"},
                  {"h": "Worked example", "b": "e"},
                  {"h": "Vocabulary", "b": "v"}]
        a = flipmod.reorder_blocks(blocks, "definition")
        b = flipmod.reorder_blocks(blocks, "examples")
        self.assertEqual(sorted(map(str, a)), sorted(map(str, b)))

    def test_no_examples_or_all_examples_unchanged(self):
        plain = [{"h": "Summary", "b": "s"}]
        self.assertEqual(flipmod.reorder_blocks(plain, "examples"), plain)

    def test_hostile_input_never_raises(self):
        self.assertEqual(flipmod.reorder_blocks(None, "examples"), None)
        self.assertEqual(flipmod.reorder_blocks([], "examples"), [])
        self.assertEqual(flipmod.reorder_blocks("nope", None), "nope")


class EffectTest(unittest.TestCase):
    """Same lesson renders definition-first by default, example-first with
    the param; content set identical in both (legacy no-data path pinned)."""

    def test_same_lesson_both_orders_identical_content(self):
        levels = explainmod.levels_for(_worked_lesson())
        lv = next(L for L in levels if L["n"] == 2)
        heads_default = [b["h"] for b in flipmod.reorder_blocks(lv["blocks"])]
        heads_flipped = [b["h"] for b in flipmod.reorder_blocks(lv["blocks"], "examples")]
        self.assertIn("Worked example", heads_default)
        self.assertEqual(heads_flipped[0], "Recall first")  # retrieval prompt stays put
        self.assertEqual(heads_flipped[1], "Worked example")
        self.assertLess(heads_flipped.index("Worked example"),
                        heads_default.index("Worked example"))
        self.assertEqual(sorted(heads_default), sorted(heads_flipped))

    def test_render_levels_default_unchanged_legacy_fallback(self):
        before = lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/")
        # Default keeps definition-first block order (legacy content path)
        # while gaining the always-on order toggle links.
        self.assertLess(before.index("What it does"),
                        before.index("Vocabulary"))
        self.assertIn("order=examples", before)
        self.assertIn("What it does", before)

    def test_toggle_marks_current_and_preserves_level(self):
        t = flipmod.toggle_html("/modules/m", "2", "examples")
        self.assertIn("order=definition", t)
        self.assertIn("level=2", t)
        self.assertIn("(you are here)", t)


if __name__ == "__main__":
    unittest.main()
