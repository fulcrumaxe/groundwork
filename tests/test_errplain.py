"""Sandbox errors in plain language: known names translate, unknown pass through (I-184)."""
import unittest
from types import SimpleNamespace

from groundwork import errplain as epmod
from groundwork import exercises as exmod


def _tb(last):
    return ("Traceback (most recent call last):\n"
            '  File "<string>", line 1, in <module>\n'
            f"{last}\n")


def _type12():
    return {"type": 12, "payload": {"tests": "assert f() == 2"}}


def _runner(ok, stdout="", stderr=""):
    return SimpleNamespace(
        run=lambda code: SimpleNamespace(ok=ok, stdout=stdout, stderr=stderr))


class TableTest(unittest.TestCase):
    def test_every_entry_has_plain_and_fix(self):
        self.assertGreaterEqual(len(epmod.KNOWN), 10)
        for name, (plain, fix) in epmod.KNOWN.items():
            self.assertTrue(plain.strip(), name)
            self.assertTrue(fix.strip(), name)

    def test_spot_check_meanings(self):
        self.assertIn("never defined",
                      epmod.hint_text(_tb("NameError: name 'x' is not defined")))
        self.assertIn("past its end",
                      epmod.hint_text(_tb("IndexError: list index out of range")))
        self.assertIn("Fix direction:",
                      epmod.hint_text(_tb("KeyError: 'email'")))


class ParseTest(unittest.TestCase):
    def test_last_line_wins_on_chained_traceback(self):
        chained = ("ValueError: bad\n"
                   "During handling of the above exception, another occurred:\n"
                   "TypeError: unsupported\n")
        self.assertEqual(epmod.error_name(chained), "TypeError")

    def test_syntax_caret_lines_skipped(self):
        stderr = ('  File "<string>", line 1\n    def f(:\n          ^\n'
                  "SyntaxError: invalid syntax\n")
        self.assertEqual(epmod.last_error_line(stderr),
                         "SyntaxError: invalid syntax")
        self.assertIn("could not be read", epmod.hint_text(stderr))

    def test_explain_shape(self):
        found = epmod.explain(_tb("ZeroDivisionError: division by zero"))
        self.assertEqual(found["name"], "ZeroDivisionError")
        self.assertIn("divides by zero", found["plain"])
        self.assertTrue(found["fix"])


class UnknownPassthroughTest(unittest.TestCase):
    def test_unknown_names_render_exactly_as_today(self):
        for stderr in (_tb("MyCustomError: boom"),
                       _tb("StopIteration"),
                       _tb("KeyboardInterrupt"),
                       "timeout",
                       "node not installed",
                       "",
                       "FAIL: expected 2, got 3"):
            self.assertEqual(epmod.hint_text(stderr), "", stderr)
            self.assertIsNone(epmod.explain(stderr), stderr)
            self.assertEqual(epmod.hint_html(stderr), "", stderr)
            self.assertEqual(epmod.error_name(stderr), "", stderr)

    def test_timeout_sentinel_left_for_i183(self):
        self.assertEqual(epmod.hint_text("timeout"), "")


class NeverRaisesTest(unittest.TestCase):
    def test_hostile_input(self):
        for bad in (None, 0, 42, [], {}, object()):
            self.assertEqual(epmod.hint_text(bad), "")
            self.assertIsNone(epmod.explain(bad))
            self.assertEqual(epmod.hint_html(bad), "")
            self.assertEqual(epmod.last_error_line(bad), "")
            self.assertEqual(epmod.error_name(bad), "")


class CallerEffectTest(unittest.TestCase):
    def test_grade_pass_byte_identical(self):
        res = exmod.grade(_type12(), "x", _runner(True, stdout="ok"))
        self.assertTrue(res["pass"])
        self.assertEqual(res["feedback"], "Tests pass.")

    def test_grade_known_error_appends_plain_line(self):
        stderr = _tb("NameError: name 'total' is not defined")
        res = exmod.grade(_type12(), "x", _runner(False, stderr=stderr))
        self.assertFalse(res["pass"])
        legacy = f"Output: {''.strip()[:300]} {stderr[:300]}"
        self.assertTrue(res["feedback"].startswith(legacy))
        self.assertIn("NameError in plain words", res["feedback"])
        self.assertIn("never defined", res["feedback"])
        self.assertIn("Fix direction:", res["feedback"])

    def test_grade_unknown_error_legacy_fallback(self):
        stderr = _tb("MyCustomError: boom")
        res = exmod.grade(_type12(), "x", _runner(False, stderr=stderr))
        self.assertFalse(res["pass"])
        self.assertEqual(res["feedback"], f"Output: {''[:300]} {stderr[:300]}")

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{epmod.STATUS_ANCHOR}'", epmod.section_html())
        self.assertIn("errplain", epmod.section_html())
        e = epmod.tour_entry()
        self.assertEqual(e["id"], "sandbox-errors-plain")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["anchor"], epmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
