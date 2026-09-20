"""Tests for the property-test exercise (type 33, F-10)."""
import unittest
from types import SimpleNamespace

from groundwork import proptest as mod


def make_concept(name="add"):
    return SimpleNamespace(node_id="f", name=name, kind="function",
                           file="calc.py", line=1)


CODE = "def add(a, b):\n    return a + b"

CTX = {"runnable": CODE, "call": "add(2, 3)", "expected_output": "5"}

GOOD = "assert add(2, 3) == 5\nassert add(2, 3) == add(2, 3)"


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex33", make_concept(), CODE.splitlines(), dict(CTX))
        self.assertEqual(e["type"], 33)
        self.assertEqual(e["type_name"], "property-test")
        self.assertEqual(e["bloom"], "apply")
        self.assertTrue(e["front"])

    def test_grounded_reference(self):
        e = mod.generate("ex33", make_concept(), CODE.splitlines(), dict(CTX))
        self.assertTrue(e["payload"]["grounded"])
        self.assertIn("assert add(2, 3) == 5", e["payload"]["reference"])
        self.assertIn("assert", e["back"])

    def test_ungrounded_still_builds(self):
        e = mod.generate("ex33", make_concept(), CODE.splitlines(), {})
        self.assertFalse(e["payload"]["grounded"])
        self.assertTrue(e["front"])
        self.assertEqual(len(e["hints"]), 3)

    def test_tolerates_suite_ctx(self):
        # Same generic ctx test_groundwork uses for every type: must not raise.
        ctx = {"runnable": CODE, "call": "add(2, 3)", "expected_output": "5",
               "tests": "x", "trace_var": "total", "trace_expected": ["2"],
               "buggy": "b", "bug_line": 2, "fixed": "f", "graph": None}
        e = mod.generate("ex33", make_concept(), CODE.splitlines(), ctx)
        self.assertTrue(e["front"])

    def test_guard_predicate(self):
        self.assertTrue(mod.emits({"runnable": CODE}))
        self.assertFalse(mod.emits({}))
        self.assertFalse(mod.emits(None))


def grade_ok(code=CODE, sub=GOOD):
    return mod.grade({"id": "x", "type": 33,
                      "payload": {"code": code, "func": "add"}}, sub)


class GradeTest(unittest.TestCase):
    def test_accept_holding(self):
        self.assertTrue(grade_ok()["pass"])

    def test_reject_failing_invariant(self):
        r = grade_ok(sub="assert add(2, 3) == 6")
        self.assertFalse(r["pass"])

    def test_partial_credit(self):
        r = grade_ok(sub="assert add(2, 3) == 5\nassert add(2, 3) == 6")
        self.assertFalse(r["pass"])
        self.assertEqual(r["score"], 0.5)
        self.assertIn("1/2", r["feedback"])

    def test_reject_no_asserts(self):
        self.assertFalse(grade_ok(sub="add(2, 3) is 5")["pass"])

    def test_reject_not_calling_func(self):
        self.assertFalse(grade_ok(sub="assert 1 + 1 == 2")["pass"])

    def test_reject_blank(self):
        self.assertFalse(grade_ok(sub="   ")["pass"])

    def test_error_line_is_grade_not_crash(self):
        r = grade_ok(sub="assert add(1) == 2")
        self.assertFalse(r["pass"])
        self.assertIn("TypeError", r["feedback"])

    def test_syntax_error_is_grade_not_crash(self):
        r = grade_ok(sub="assert ===")
        self.assertFalse(r["pass"])

    def test_no_runner_needed(self):
        self.assertTrue(mod.grade(
            {"id": "x", "type": 33,
             "payload": {"code": CODE, "func": "add"}},
            GOOD, None)["pass"])

    def test_never_raises_on_bad_input(self):
        for bad_ex, bad_sub in [
                ({}, ""), (None, None), ({"payload": {}}, "assert x"),
                ({"payload": {"code": "def broken(:", "func": "f"}},
                 "assert f() == 1")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertIsInstance(r, dict)
            self.assertIn("pass", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex33", make_concept(), CODE.splitlines(), dict(CTX))
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("assert add(2, 3)", body)
        self.assertIn("calc.py:1", body)

    def test_render_escapes(self):
        e = mod.generate("ex33", make_concept(), ["def f():", "    return '<b>'"],
                         {"runnable": "def f():\n    return '<b>'",
                          "call": "f()", "expected_output": "'<b>'"})
        body = mod.render(e)
        self.assertNotIn("<b>", body)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b7-proptest'", mod.section_html())


if __name__ == "__main__":
    unittest.main()
