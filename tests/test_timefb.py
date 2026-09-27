"""Timeout feedback tailored: infinite-loop vs too-slow (I-183)."""
import unittest
from types import SimpleNamespace

from groundwork import exercises as exmod
from groundwork import timefb as mod


def _res(ok=False, stdout="", stderr="timeout"):
    return SimpleNamespace(ok=ok, stdout=stdout, stderr=stderr)


class IsTimeoutTest(unittest.TestCase):
    def test_failed_stamped_run_is_timeout(self):
        self.assertTrue(mod.is_timeout(_res()))

    def test_ok_run_printing_timeout_is_not(self):
        self.assertFalse(mod.is_timeout(_res(ok=True, stderr="timeout")))

    def test_plain_failure_is_not(self):
        self.assertFalse(
            mod.is_timeout(_res(stderr="Traceback: NameError")))

    def test_hostile_input_is_not(self):
        self.assertFalse(mod.is_timeout(None))
        self.assertFalse(mod.is_timeout({}))
        self.assertFalse(mod.is_timeout("timeout"))


class ClassifyTest(unittest.TestCase):
    def test_repeated_output_is_loop(self):
        out = "x\n" * 30
        self.assertEqual(
            mod.classify(_res(stdout=out), "while True:\n    print('x')"),
            "loop")

    def test_huge_quiet_volume_is_loop(self):
        out = "".join(f"line {i}\n" for i in range(500))
        self.assertEqual(
            mod.classify(_res(stdout=out), "for i in range(10**9): print(i)"),
            "loop")

    def test_while_true_without_break_is_loop(self):
        self.assertEqual(
            mod.classify(_res(), "while True:\n    x += 1"), "loop")

    def test_partial_progress_is_slow(self):
        out = "PASS t1\nPASS t2\n"
        self.assertEqual(
            mod.classify(_res(stdout=out), "def f(n):\n    return sum(range(n))"),
            "slow")

    def test_bounded_for_only_is_slow(self):
        self.assertEqual(
            mod.classify(_res(), "def f(n):\n    return sum(range(n * n))"),
            "slow")

    def test_quiet_recursion_is_slow(self):
        code = "def fib(n):\n    return n if n < 2 else fib(n-1) + fib(n-2)"
        self.assertEqual(mod.classify(_res(), code), "slow")

    def test_while_with_break_is_unknown(self):
        self.assertEqual(
            mod.classify(_res(), "while n > 0:\n    n -= 1\n    break"),
            "unknown")

    def test_empty_submission_is_unknown(self):
        self.assertEqual(mod.classify(_res(), ""), "unknown")
        self.assertEqual(mod.classify(_res(), None), "unknown")

    def test_non_timeout_is_unknown(self):
        self.assertEqual(
            mod.classify(_res(ok=True, stdout="x\n" * 30,
                               stderr=""), "while True:\n    pass"),
            "unknown")

    def test_hostile_never_raises(self):
        self.assertEqual(mod.classify(None, None), "unknown")
        self.assertEqual(mod.classify({}, 123), "unknown")


class HintTextTest(unittest.TestCase):
    def test_loop_names_evidence(self):
        hint = mod.hint_text(_res(stdout="x\n" * 30),
                             "while True:\n    print('x')")
        self.assertIn("30 lines", hint)
        self.assertIn("infinite loop", hint)

    def test_slow_mentions_time_limit(self):
        hint = mod.hint_text(_res(), "def f(n):\n    return sum(range(n))")
        self.assertIn("too slow", hint)

    def test_input_clause_only_with_input_call(self):
        plain = mod.hint_text(_res(), "def f(n):\n    return sum(range(n))")
        self.assertNotIn("input()", plain)
        waiting = mod.hint_text(_res(), "name = input()\nprint(name)")
        self.assertIn("no keyboard", waiting)

    def test_unknown_is_blank(self):
        self.assertEqual(
            mod.hint_text(_res(), "while n > 0:\n    n -= 1\n    break"), "")
        self.assertEqual(mod.hint_text(None, None), "")


class CallerEffectTest(unittest.TestCase):
    def _grade(self, submission, stdout=""):
        ex = {"id": "g1", "type": 12, "concept_id": "c",
              "payload": {"tests": "assert True"}}
        runner = SimpleNamespace(
            run=lambda code: _res(stdout=stdout))
        return exmod.grade(ex, submission, runner)

    def test_loop_timeout_gains_loop_line(self):
        res = self._grade("while True:\n    print('x')", "x\n" * 30)
        self.assertFalse(res["pass"])
        self.assertIn("Output:", res["feedback"])
        self.assertIn("infinite loop", res["feedback"])

    def test_slow_timeout_gains_slow_line(self):
        res = self._grade("def f(n):\n    return sum(range(n))")
        self.assertFalse(res["pass"])
        self.assertIn("Output:  timeout", res["feedback"])
        self.assertIn("too slow", res["feedback"])

    def test_ambiguous_timeout_legacy_byte_identical(self):
        res = self._grade("while n > 0:\n    n -= 1\n    break")
        self.assertEqual(res["feedback"], "Output:  timeout")

    def test_plain_failure_untouched(self):
        # Unknown error (no timeout stamp, no known name): neither the
        # loop/slow hint (I-183) nor the plain-language hint (I-184)
        # fires, so legacy feedback stays byte-identical.
        ex = {"id": "g1", "type": 12, "concept_id": "c",
              "payload": {"tests": "assert True"}}
        runner = SimpleNamespace(
            run=lambda code: _res(stdout="", stderr="MyCustomError: x"))
        res = exmod.grade(ex, "print(x)", runner)
        self.assertEqual(res["feedback"], "Output:  MyCustomError: x")


class StatusSectionTest(unittest.TestCase):
    def test_anchored_subsection(self):
        body = mod.section_html()
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", body)
        self.assertIn("groundwork/timefb.py", body)
        self.assertIn("infinite-loop nudge", body)

    def test_tour_entry(self):
        entry = mod.tour_entry()
        self.assertEqual(entry["id"], "timeout-loop-or-slow")
        self.assertEqual(entry["kind"], "improvement")
        self.assertEqual(entry["anchor"], mod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
