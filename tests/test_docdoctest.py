"""Tests for the doc-example doctest exercise (type 32, F-9)."""
import unittest
from types import SimpleNamespace

from groundwork import docdoctest as mod


def make_concept(name="add"):
    return SimpleNamespace(node_id="f", name=name, kind="function",
                           file="calc.py", line=1)


CODE = "def add(a, b):\n    return a + b"


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex32", make_concept(), CODE.splitlines(), {})
        self.assertEqual(e["type"], 32)
        self.assertEqual(e["type_name"], "doc-example")
        self.assertEqual(e["bloom"], "apply")
        self.assertTrue(e["front"])

    def test_grounded_reference(self):
        ctx = {"runnable": CODE, "expected_output": "5"}
        e = mod.generate("ex32", make_concept(), CODE.splitlines(), ctx)
        self.assertTrue(e["payload"]["grounded"])
        self.assertIn(">>> add()", e["payload"]["reference"])
        self.assertIn("5", e["back"])

    def test_ungrounded_still_builds(self):
        e = mod.generate("ex32", make_concept(), CODE.splitlines(), {})
        self.assertFalse(e["payload"]["grounded"])
        self.assertTrue(e["front"])
        self.assertEqual(len(e["hints"]), 3)

    def test_tolerates_suite_ctx(self):
        # Same generic ctx test_groundwork uses for every type: must not raise.
        ctx = {"runnable": CODE, "expected_output": "5",
               "tests": "x", "trace_var": "total", "trace_expected": ["2"],
               "buggy": "b", "bug_line": 2, "fixed": "f", "graph": None}
        e = mod.generate("ex32", make_concept(), CODE.splitlines(), ctx)
        self.assertTrue(e["front"])


def grade_ok(code=CODE, sub=">>> add(2, 3)\n5"):
    return mod.grade({"id": "x", "type": 32,
                      "payload": {"code": code, "func": "add"}}, sub)


class GradeTest(unittest.TestCase):
    def test_accept_correct(self):
        self.assertTrue(grade_ok()["pass"])

    def test_reject_wrong_output(self):
        self.assertFalse(grade_ok(sub=">>> add(2, 3)\n6")["pass"])

    def test_reject_no_prompts(self):
        self.assertFalse(grade_ok(sub="add(2, 3) is 5")["pass"])

    def test_reject_not_calling_func(self):
        self.assertFalse(grade_ok(sub=">>> 1 + 1\n2")["pass"])

    def test_reject_blank(self):
        self.assertFalse(grade_ok(sub="   ")["pass"])

    def test_no_runner_needed(self):
        self.assertTrue(mod.grade(
            {"id": "x", "type": 32,
             "payload": {"code": CODE, "func": "add"}},
            ">>> add(2, 3)\n5", None)["pass"])

    def test_ellipsis_accepted(self):
        code = "def who():\n    return 'Ada Lovelace'"
        e = {"id": "x", "type": 32,
             "payload": {"code": code, "func": "who"}}
        self.assertTrue(mod.grade(e, ">>> who()\n'Ada ...'")["pass"])

    def test_exception_example(self):
        code = "def boom():\n    raise ValueError('bad')"
        e = {"id": "x", "type": 32,
             "payload": {"code": code, "func": "boom"}}
        sub = ">>> boom()\nTraceback (most recent call last):\nValueError: bad"
        self.assertTrue(mod.grade(e, sub)["pass"])


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex32", make_concept(), CODE.splitlines(),
                         {"expected_output": "5"})
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("&gt;&gt;&gt; add()", body)
        self.assertIn("calc.py:1", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b6-docdoctest'", mod.section_html())


if __name__ == "__main__":
    unittest.main()
