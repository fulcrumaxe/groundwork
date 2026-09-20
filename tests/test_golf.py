"""Complexity-golf exercise plugin (F-4): metric, grade, render."""
import unittest
from types import SimpleNamespace

from groundwork import golf as golfmod

NESTED = ("def check(n):\n    if n > 0:\n        for i in range(n):\n"
          "            if i % 2 == 0:\n                print(i)\n    return n")
FLAT = "def check(n):\n    return n if n > 0 else 0"
SHALLOW = ("def check(n):\n    if n <= 0:\n        return n\n"
           "    for i in range(n):\n        print(i)\n    return n")
TESTS = "_out = repr(check(3))\nassert _out == '3'\nprint('OK')"


def _concept(name="check"):
    return SimpleNamespace(node_id="f:check", name=name, kind="function",
                           file="calc.py", line=1)


def _ex(code=NESTED, tests=""):
    return golfmod.generate("ex001", _concept(), code.splitlines(),
                            {"commit": "abc", "tests": tests})


class FakeRunner:
    def __init__(self, ok=True, stdout="OK"):
        self._ok, self._out = ok, stdout
        self.seen = ""

    def run(self, code):
        self.seen = code
        return SimpleNamespace(ok=self._ok, stdout=self._out, stderr="")


class MetricTest(unittest.TestCase):
    def test_scale(self):
        self.assertEqual(golfmod.max_nesting(FLAT), 0)
        self.assertEqual(golfmod.max_nesting("def f():\n    if x:\n        y"), 1)
        self.assertEqual(golfmod.max_nesting(SHALLOW), 1)
        self.assertEqual(golfmod.max_nesting(NESTED), 3)

    def test_unparseable_is_none(self):
        self.assertIsNone(golfmod.max_nesting("def broken(:\n"))

    def test_ignores_comprehensions_and_ternaries(self):
        code = "def f(xs):\n    return [x for x in xs if x]"
        self.assertEqual(golfmod.max_nesting(code), 0)


class GenerateTest(unittest.TestCase):
    def test_identity_and_target(self):
        ex = _ex()
        self.assertEqual(ex["type"], 26)
        self.assertEqual(ex["type_name"], "complexity-golf")
        self.assertEqual(ex["bloom"], "analyse")
        self.assertEqual(ex["payload"]["depth"], 3)
        self.assertEqual(ex["payload"]["target"], 2)
        self.assertTrue(ex["front"])

    def test_flat_code_is_ungrounded(self):
        ex = _ex(code=FLAT)
        self.assertEqual(ex["payload"]["depth"], 0)
        self.assertFalse(ex["payload"]["grounded"])

    def test_prefers_runnable_ctx(self):
        ex = golfmod.generate("ex2", _concept(), ["# stale"], {"tests": TESTS,
                              "runnable": NESTED})
        self.assertEqual(ex["payload"]["original"], NESTED)
        self.assertTrue(ex["payload"]["grounded"])

    def test_shallow_needs_no_card(self):
        ex = golfmod.generate("ex2", _concept(), SHALLOW.splitlines(),
                              {"tests": TESTS})
        self.assertFalse(ex["payload"]["grounded"])


class GradeTest(unittest.TestCase):
    def test_accepts_shallower_no_harness(self):
        r = golfmod.grade(_ex(), SHALLOW)
        self.assertTrue(r["pass"])
        self.assertEqual(r["score"], 1.0)

    def test_rejects_equal_depth(self):
        r = golfmod.grade(_ex(), NESTED)
        self.assertFalse(r["pass"])
        self.assertIn("3", r["feedback"])

    def test_rejects_missing_function(self):
        r = golfmod.grade(_ex(), "def other():\n    pass")
        self.assertFalse(r["pass"])
        self.assertIn("check", r["feedback"])

    def test_rejects_syntax_error(self):
        r = golfmod.grade(_ex(), "def check(:\n")
        self.assertFalse(r["pass"])
        self.assertIn("parse", r["feedback"])

    def test_exec_green_passes(self):
        r = golfmod.grade(_ex(tests=TESTS), SHALLOW,
                          FakeRunner(ok=True, stdout="OK"))
        self.assertTrue(r["pass"])

    def test_exec_red_fails_despite_metric(self):
        r = golfmod.grade(_ex(tests=TESTS), SHALLOW,
                          FakeRunner(ok=True, stdout="FAIL: bad"))
        self.assertFalse(r["pass"])
        self.assertIn("tests fail", r["feedback"])

    def test_tests_without_runner_fails(self):
        r = golfmod.grade(_ex(tests=TESTS), SHALLOW, None)
        self.assertFalse(r["pass"])
        self.assertIn("sandbox", r["feedback"].lower())


class RenderStatusTest(unittest.TestCase):
    def test_render_widgets_and_escaping(self):
        ex = _ex()
        ex["front"] = "<b>hi</b>"
        body = golfmod.render(ex)
        self.assertNotIn("<b>hi</b>", body)
        self.assertIn("textarea", body)
        self.assertIn("Max nesting 3", body)
        self.assertIn("Hint 1", body)

    def test_section_anchor(self):
        self.assertIn("id='status-b6-golf'", golfmod.section_html())


if __name__ == "__main__":
    unittest.main()
