"""Error-handling retrofit exercises (F-6, type 28)."""
import unittest
from types import SimpleNamespace

from groundwork import errbranch as errmod
from groundwork import sandbox as sbmod

BASE = "def ratio(a, b):\n    return a / b\n"
FIXED = "def ratio(a, b):\n    if b == 0:\n        return None\n    return a / b\n"
WRONG = "def ratio(a, b):\n    return 0\n"
TESTS = ("assert ratio(4, 2) == 2.0\n"
         "try:\n"
         "    _r = ratio(1, 0)\n"
         "except ZeroDivisionError:\n"
         "    print('FAIL: unhandled ZeroDivisionError')\n"
         "else:\n"
         "    assert _r is None, 'FAIL: expected None on zero divisor'\n"
         "print('OK')")


def make_concept():
    return SimpleNamespace(node_id="f", name="ratio", kind="function",
                           file="calc.py", line=1)


def make_ex(code=BASE, tests=TESTS):
    return {"id": "e28", "type": 28,
            "payload": {"code": code, "tests": tests, "fault": "b=0",
                        "grounded": bool(tests)}}


class GenerateTest(unittest.TestCase):
    def test_type_identity(self):
        e = errmod.generate("e1", make_concept(), BASE.splitlines(), {})
        self.assertEqual(e["type"], 28)
        self.assertEqual(e["type_name"], "error-branch")
        self.assertEqual(e["bloom"], "analyse")
        self.assertTrue(e["front"])

    def test_grounded_with_tests(self):
        e = errmod.generate("e1", make_concept(), BASE.splitlines(),
                            {"runnable": BASE, "tests": TESTS,
                             "fault": "b=0"})
        self.assertTrue(e["payload"]["grounded"])
        self.assertEqual(e["payload"]["fault"], "b=0")

    def test_ungrounded_without_tests(self):
        e = errmod.generate("e1", make_concept(), BASE.splitlines(), {})
        self.assertFalse(e["payload"]["grounded"])

    def test_module_constants(self):
        self.assertEqual(errmod.TYPE_NUM, 28)
        self.assertEqual(errmod.BLOOM, "analyse")


class GradeTest(unittest.TestCase):
    def setUp(self):
        self.runner = sbmod.SandboxRunner()

    def test_accept_fixed(self):
        self.assertTrue(
            errmod.grade(make_ex(), FIXED, self.runner)["pass"])

    def test_reject_unmodified_base(self):
        got = errmod.grade(make_ex(), BASE, self.runner)
        self.assertFalse(got["pass"])

    def test_reject_wrong_fix(self):
        got = errmod.grade(make_ex(), WRONG, self.runner)
        self.assertFalse(got["pass"])

    def test_reject_without_runner(self):
        got = errmod.grade(make_ex(), FIXED, None)
        self.assertFalse(got["pass"])
        self.assertIn("sandbox", got["feedback"].lower())

    def test_reject_without_harness(self):
        got = errmod.grade(make_ex(tests=""), FIXED, self.runner)
        self.assertFalse(got["pass"])

    def test_reject_syntax_error(self):
        got = errmod.grade(make_ex(), "def ratio(:\n", self.runner)
        self.assertFalse(got["pass"])
        self.assertIn("parse", got["feedback"].lower())

    def test_stale_when_base_already_passes(self):
        got = errmod.grade(make_ex(code=FIXED), FIXED, self.runner)
        self.assertFalse(got["pass"])
        self.assertIn("stale", got["feedback"].lower())


class RenderTest(unittest.TestCase):
    def test_render_has_form_and_anchor(self):
        e = errmod.generate("e1", make_concept(), BASE.splitlines(),
                            {"runnable": BASE, "tests": TESTS})
        body = errmod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("ratio", body)
        self.assertIn("calc.py", body)

    def test_section_html_anchor(self):
        self.assertIn("status-b6-errbranch", errmod.section_html())


if __name__ == "__main__":
    unittest.main()
