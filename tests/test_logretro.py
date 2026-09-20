"""Logging-retrofit exercises: checklist generation and grading (F-7)."""
import unittest
from types import SimpleNamespace

from groundwork import logretro as logretromod


def make_concept(name="add"):
    return SimpleNamespace(node_id="f", name=name, kind="function",
                           file="calc.py", line=1)


SNIPPET = ["def add(a, b):",
           "    try:",
           "        return a + b",
           "    except TypeError:",
           "        raise ValueError('bad')"]


class PickLinesTest(unittest.TestCase):
    def test_finds_all_four_kinds_in_order(self):
        items = logretromod.pick_lines(SNIPPET)
        self.assertEqual([i["kind"] for i in items],
                         ["entry", "exit", "except", "raise"])
        self.assertEqual([i["level"] for i in items],
                         ["debug", "debug", "warning", "error"])

    def test_skips_comments_and_blank_lines(self):
        items = logretromod.pick_lines(["# return early", "", "x = 1"])
        self.assertEqual(items, [])

    def test_caps_at_four_items(self):
        snippet = ["def f():"] + ["    return 1"] * 6
        self.assertEqual(len(logretromod.pick_lines(snippet)), 4)


class GenerateTest(unittest.TestCase):
    def test_shape_matches_plugin_contract(self):
        e = logretromod.generate("ex29", make_concept(), SNIPPET, {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]), (29, "logging-retrofit", "analyse"))
        self.assertEqual(len(e["hints"]), 3)
        self.assertTrue(e["front"] and e["back"])
        self.assertTrue(e["payload"]["grounded"])
        self.assertEqual(len(e["payload"]["checklist"]), 4)

    def test_fallback_flags_ungrounded(self):
        e = logretromod.generate("ex29b", make_concept(), ["x = 1"], {})
        self.assertFalse(e["payload"]["grounded"])
        self.assertEqual(len(e["payload"]["checklist"]), 1)

    def test_type_number_is_29(self):
        self.assertEqual(logretromod.TYPE_NUM, 29)


class GradeTest(unittest.TestCase):
    def setUp(self):
        self.ex = logretromod.generate("ex29", make_concept(), SNIPPET, {})

    def test_accepts_canonical_levels(self):
        r = logretromod.grade(self.ex, "0=debug\n1=debug\n2=warning\n3=error")
        self.assertTrue(r["pass"])
        self.assertEqual(r["score"], 1.0)

    def test_accepts_aliases_and_case(self):
        r = logretromod.grade(self.ex, "0=DBG\n1=Debug\n2=WARN\n3=exception")
        self.assertTrue(r["pass"])

    def test_rejects_wrong_level_with_partial_credit(self):
        r = logretromod.grade(self.ex, "0=debug\n1=debug\n2=warning\n3=warning")
        self.assertFalse(r["pass"])
        self.assertEqual(r["score"], 0.75)
        self.assertIn("3", r["feedback"])

    def test_rejects_empty_with_format_hint(self):
        r = logretromod.grade(self.ex, "   ")
        self.assertFalse(r["pass"])
        self.assertIn("id=level", r["feedback"])

    def test_accepts_single_line_comma_form(self):
        r = logretromod.grade(self.ex, "0=debug, 1=debug, 2=warning, 3=error")
        self.assertTrue(r["pass"])

    def test_single_item_accepts_bare_level(self):
        one = logretromod.generate("ex1", make_concept(), ["x = 1"], {})
        self.assertTrue(logretromod.grade(one, "debug")["pass"])
        self.assertFalse(logretromod.grade(one, "error")["pass"])


class RenderTest(unittest.TestCase):
    def test_escapes_and_shows_form(self):
        e = logretromod.generate("ex29", make_concept("<b>add</b>"), SNIPPET, {})
        body = logretromod.render(e)
        self.assertNotIn("<b>add</b>", body)
        self.assertIn("<textarea", body)
        self.assertIn("0=debug", body)

    def test_section_anchor(self):
        self.assertIn("id='status-b6-logretro'", logretromod.section_html(""))


if __name__ == "__main__":
    unittest.main()
