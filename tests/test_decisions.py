"""Decision quotes in lessons (I-110): agent rationale where it matters."""
import unittest

from groundwork import decisions as decmod
from groundwork import tour as tourmod

from test_web import handler_for, make_module


class DecisionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("dec mod")
        self.mid, _ = tourmod.targets(self.db)
        self.server.dispatch("annotate_decision",
                             {"repo": "r", "symbol": "calc.add",
                              "chosen": "total", "rejected": "sum",
                              "reason": "reads better"})

    def test_match_by_symbol_suffix(self):
        self.assertTrue(decmod._matches("add", "calc.add"))
        self.assertFalse(decmod._matches("add", "calc.added"))

    def test_quote_block_renders(self):
        matches = decmod.matches_for_module(self.db, ["add", "other"])
        self.assertTrue(matches["add"])
        out = decmod.lesson_block("add", matches["add"], anchor=True)
        self.assertIn("id='decisions'", out)
        self.assertIn("total", out)

    def test_empty_state_keeps_anchor(self):
        out = decmod.lesson_block("other", [], anchor=True)
        self.assertIn("id='decisions'", out)
        self.assertIn("No recorded agent decisions", out)

    def test_module_page_carries_quotes(self):
        out = handler_for(self.db).module_html(self.mid)
        self.assertIn("id='decisions'", out)


if __name__ == "__main__":
    unittest.main()
