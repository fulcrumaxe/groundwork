"""Tests for the perf-fix exercise (type 35, F-12)."""
import unittest
from types import SimpleNamespace

from groundwork import perffix as mod


def make_concept(name="total"):
    return SimpleNamespace(node_id="f", name=name, kind="function",
                           file="agg.py", line=1)


ORIGINAL = ("def total(xs):\n"
            "    out = 0\n"
            "    for x in xs:\n"
            "        for y in x:\n"
            "            out += y\n"
            "    return out")
# max_nesting 2 + 2 loops = complexity 4, target 3.

TESTS = ("_r = total([[1, 2], [3]])\n"
         "assert _r == 6, f'FAIL: {_r}'\nprint('OK')")

IMPROVED = "def total(xs):\n    return sum(y for x in xs for y in x)"
BROKEN = "def total(xs):\n    return 0"


class FakeRunner:
    def __init__(self, ok=True, stdout="OK\n", stderr=""):
        self.ok = ok
        self.stdout = stdout
        self.stderr = stderr
        self.seen = []

    def run(self, code):
        self.seen.append(code)
        return SimpleNamespace(ok=self.ok, stdout=self.stdout,
                               stderr=self.stderr)


def make_exercise(code=ORIGINAL, tests=TESTS):
    ctx = {"runnable": code}
    if tests:
        ctx["tests"] = tests
    return mod.generate("ex35", make_concept(), code.splitlines(), ctx)


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = make_exercise()
        self.assertEqual(e["type"], 35)
        self.assertEqual(e["type_name"], "perf-fix")
        self.assertEqual(e["bloom"], "modify")
        self.assertTrue(e["front"])

    def test_shape(self):
        e = make_exercise()
        self.assertEqual(e["payload"]["score"], 4)
        self.assertEqual(e["payload"]["target"], 3)
        self.assertEqual(e["payload"]["loops"], 2)
        self.assertTrue(e["payload"]["grounded"])
        self.assertEqual(len(e["hints"]), 3)
        self.assertIn("total", e["back"])

    def test_ungrounded_without_tests(self):
        e = make_exercise(tests="")
        self.assertFalse(e["payload"]["grounded"])
        self.assertTrue(e["front"])

    def test_ungrounded_flat_code(self):
        e = mod.generate("ex35", make_concept(), ["x = 1"],
                         {"runnable": "x = 1", "tests": "t"})
        self.assertFalse(e["payload"]["grounded"])

    def test_tolerates_suite_ctx(self):
        # Same generic ctx test_groundwork uses for every type: must not raise.
        ctx = {"runnable": ORIGINAL, "expected_output": "6",
               "tests": TESTS, "trace_var": "out", "trace_expected": ["6"],
               "buggy": "b", "bug_line": 2, "fixed": "f", "graph": None}
        e = mod.generate("ex35", make_concept(), ORIGINAL.splitlines(), ctx)
        self.assertTrue(e["front"])


class GradeTest(unittest.TestCase):
    def test_accept_improved_and_green(self):
        r = mod.grade(make_exercise(), IMPROVED, FakeRunner())
        self.assertTrue(r["pass"])
        self.assertEqual(r["score"], 1.0)

    def test_reject_unimproved(self):
        r = mod.grade(make_exercise(), ORIGINAL, FakeRunner())
        self.assertFalse(r["pass"])
        self.assertIn("3", r["feedback"])

    def test_reject_broken_behavior(self):
        bad = FakeRunner(ok=False, stdout="AssertionError: FAIL: 0\n")
        r = mod.grade(make_exercise(), BROKEN, bad)
        self.assertFalse(r["pass"])
        self.assertIn("tests fail", r["feedback"])

    def test_reject_unparseable(self):
        r = mod.grade(make_exercise(), "def total(:\n  ???", FakeRunner())
        self.assertFalse(r["pass"])

    def test_reject_missing_func(self):
        r = mod.grade(make_exercise(), "def other(xs):\n    return 1",
                      FakeRunner())
        self.assertFalse(r["pass"])
        self.assertIn("total", r["feedback"])

    def test_reject_blank(self):
        r = mod.grade(make_exercise(), "   ", FakeRunner())
        self.assertFalse(r["pass"])

    def test_no_runner_with_tests_fails(self):
        r = mod.grade(make_exercise(), IMPROVED, None)
        self.assertFalse(r["pass"])

    def test_no_tests_passes_on_complexity(self):
        r = mod.grade(make_exercise(tests=""), IMPROVED, None)
        self.assertTrue(r["pass"])

    def test_never_raises(self):
        bad_exercises = [{}, {"payload": {}}, {"payload": {"score": "x"}},
                         {"payload": None}, None]
        bad_subs = ["", "   ", "\x00", "def (:", None, 12345]
        for ex in bad_exercises:
            for sub in bad_subs:
                try:
                    r = mod.grade(ex, sub, FakeRunner())
                except Exception as exc:  # noqa: BLE001 — probe must surface
                    self.fail(f"grade raised on {ex!r}/{sub!r}: {exc}")
                self.assertIn("pass", r)
                self.assertIsInstance(r["pass"], bool)


class GuardTest(unittest.TestCase):
    def test_emits_needs_tests(self):
        self.assertTrue(mod.emits({"tests": "t"}))
        self.assertFalse(mod.emits({}))
        self.assertFalse(mod.emits(None))


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        body = mod.render(make_exercise())
        self.assertIn("<textarea", body)
        self.assertIn("Complexity 4", body)
        self.assertIn("target 3", body)
        self.assertIn("agg.py:1", body)

    def test_render_escapes(self):
        e = make_exercise()
        e["front"] = "<script>alert(1)</script>"
        self.assertNotIn("<script>", mod.render(e))

    def test_status_anchor(self):
        self.assertIn("id='status-b7-perffix'", mod.section_html())


if __name__ == "__main__":
    unittest.main()
