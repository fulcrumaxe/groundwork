"""Refactor behavior-diff: measured equivalence on samples (I-172)."""
import unittest
from types import SimpleNamespace

from groundwork import behavdiff as bdmod
from groundwork import exercises as exmod


HARNESS = ("_out = repr(add(2, 3))\n"
           "assert _out == '5', f'FAIL: {_out}'\nprint('OK')")

REF = "def add(a, b):\n    return a + b"
SAME = "def add(a, b):\n    total = a + b\n    return total"
DIFF = "def add(a, b):\n    return a - b"


def _stub(mapping, harness_ok=True, harness_out="OK\n", harness_err=""):
    """Harness runs -> harness result; print(repr(..)) probes -> mapped out."""
    def _run(code):
        if "print(repr(" in code:
            for marker, out in mapping:
                if marker in code:
                    return SimpleNamespace(ok=True, stdout=out, stderr="")
            return SimpleNamespace(ok=False, stdout="", stderr="boom")
        return SimpleNamespace(ok=harness_ok, stdout=harness_out,
                               stderr=harness_err)
    return SimpleNamespace(run=_run)


MATCH_MAP = [("total = a + b", "5"), ("return a + b", "5")]
SPLIT_MAP = [("return a + b", "5"), ("return a - b", "-1")]


class SampleCallsTest(unittest.TestCase):
    def test_harness_call_extracted(self):
        self.assertEqual(bdmod.sample_calls(HARNESS), ["add(2, 3)"])

    def test_assert_literal_never_a_sample(self):
        self.assertEqual(
            bdmod.sample_calls("assert _out == 'repr(x)'\nprint('OK')"), [])

    def test_multiple_deduped_and_capped(self):
        tests = ("_out = repr(f(1))\n_out = repr(g(2))\n"
                 "_out = repr(f(1))\nprint('OK')")
        self.assertEqual(bdmod.sample_calls(tests), ["f(1)", "g(2)"])
        self.assertEqual(bdmod.sample_calls(tests, cap=1), ["f(1)"])

    def test_hostile_is_empty(self):
        for bad in (None, "", "   ", 42, ["x"], "print('hi')",
                    "_out = repr(   )", "_out = repr(def broken)"):
            self.assertEqual(bdmod.sample_calls(bad), [])


class MeasureTest(unittest.TestCase):
    def test_probe_shape_and_last_line(self):
        seen = {}

        def _run(code):
            seen["code"] = code
            return SimpleNamespace(ok=True, stdout="noise\n5\n", stderr="")
        out = bdmod.measure(SimpleNamespace(run=_run), REF, "add(2, 3)")
        self.assertEqual(out, "5")
        self.assertEqual(seen["code"], REF + "\nprint(repr(add(2, 3)))")

    def test_unmeasurable_is_none(self):
        bad = SimpleNamespace(run=lambda c: SimpleNamespace(
            ok=False, stdout="", stderr="x"))
        self.assertIsNone(bdmod.measure(bad, REF, "add(2, 3)"))
        self.assertIsNone(bdmod.measure(None, REF, "add(2, 3)"))
        self.assertIsNone(bdmod.measure(_stub([]), "", "add(2, 3)"))
        self.assertIsNone(bdmod.measure(_stub([]), REF, ""))
        self.assertIsNone(bdmod.measure(object(), REF, "add(2, 3)"))


class GradeExtraTest(unittest.TestCase):
    def test_match_lists_measured_outputs(self):
        out = bdmod.grade_extra({"reference": REF, "tests": HARNESS},
                                SAME, _stub(MATCH_MAP))
        self.assertIn("Behavior matches on 1 sample input (measured):", out)
        self.assertIn("[x] add(2, 3) -> 5", out)

    def test_mismatch_pairs_both_sides(self):
        out = bdmod.grade_extra({"reference": REF, "tests": HARNESS},
                                DIFF, _stub(SPLIT_MAP))
        self.assertIn("Behavior differs on 1 of 1 sample input", out)
        self.assertIn("reference 5 vs yours -1", out)

    def test_quiet_when_unmeasurable(self):
        self.assertEqual(bdmod.grade_extra({}, SAME, _stub(MATCH_MAP)), "")
        self.assertEqual(bdmod.grade_extra(
            {"reference": REF}, SAME, _stub(MATCH_MAP)), "")
        self.assertEqual(bdmod.grade_extra(
            {"tests": HARNESS}, SAME, _stub(MATCH_MAP)), "")
        self.assertEqual(bdmod.grade_extra(
            {"reference": REF, "tests": HARNESS}, SAME, _stub([])), "")
        self.assertEqual(bdmod.grade_extra(
            {"reference": REF, "tests": HARNESS}, SAME, None), "")

    def test_hostile_never_raises(self):
        self.assertEqual(bdmod.grade_extra(None, None, None), "")
        self.assertEqual(bdmod.grade_extra("x", SAME, _stub(MATCH_MAP)), "")
        self.assertEqual(bdmod.sample_rows(REF, SAME, HARNESS, None), [])
        self.assertEqual(bdmod.rows_html(None), "")
        self.assertEqual(bdmod.rows_html([]), "")
        self.assertEqual(bdmod.rows_html([None, "x"]), "")


class RowsHtmlTest(unittest.TestCase):
    def test_marks_and_escapes(self):
        rows = [{"call": "f('<b>')", "ref": "1", "sub": "2", "match": False},
                {"call": "g(1)", "ref": "1", "sub": "1", "match": True}]
        out = bdmod.rows_html(rows)
        self.assertIn("class='behavdiff'", out)
        self.assertIn("[ ]", out)
        self.assertIn("[x]", out)
        self.assertIn("&lt;b&gt;", out)
        self.assertNotIn("<b>", out)


class CallerEffectTest(unittest.TestCase):
    # Behavioral-effect: real exmod.grade type-19 path with legacy pinned.

    def test_type19_pass_appends_measured_diff(self):
        ex = {"type": 19,
              "payload": {"reference": REF, "tests": HARNESS}}
        res = exmod.grade(ex, SAME, _stub(MATCH_MAP))
        self.assertTrue(res["pass"])
        self.assertTrue(res["feedback"].startswith("Tests pass.\n"))
        self.assertIn("Behavior matches on 1 sample input (measured):",
                      res["feedback"])
        self.assertIn("[x] add(2, 3) -> 5", res["feedback"])

    def test_type19_fail_appends_divergence(self):
        ex = {"type": 19,
              "payload": {"reference": REF, "tests": HARNESS}}
        res = exmod.grade(ex, DIFF, _stub(
            SPLIT_MAP, harness_ok=False, harness_out="",
            harness_err="AssertionError: FAIL: '-1'"))
        self.assertFalse(res["pass"])
        self.assertIn("Output:", res["feedback"])
        self.assertIn("Behavior differs on 1 of 1 sample input",
                      res["feedback"])
        self.assertIn("reference 5 vs yours -1", res["feedback"])

    def test_type19_no_tests_legacy_byte_identical(self):
        ex = {"type": 19, "payload": {"reference": REF}}
        res = exmod.grade(ex, SAME, _stub(MATCH_MAP))
        self.assertEqual(res["feedback"], "Tests pass.")

    def test_types_12_and_23_untouched(self):
        for t in (12, 23):
            ex = {"type": t,
                  "payload": {"reference": REF, "tests": HARNESS}}
            res = exmod.grade(ex, SAME, _stub(MATCH_MAP))
            self.assertEqual(res["feedback"], "Tests pass.")


class StatusTourAsciiTest(unittest.TestCase):
    def test_anchor_tour_css(self):
        self.assertIn(f"id='{bdmod.STATUS_ANCHOR}'",
                      bdmod.section_html())
        self.assertNotIn("<style", bdmod.diff_css())
        e = bdmod.tour_entry()
        self.assertEqual(e["id"], "refactor-behavior-diff")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["path"], "/status")
        self.assertEqual(e["anchor"], bdmod.STATUS_ANCHOR)

    def test_user_strings_ascii_only(self):
        blob = (bdmod.grade_extra({"reference": REF, "tests": HARNESS},
                                  SAME, _stub(MATCH_MAP))
                + bdmod.grade_extra({"reference": REF, "tests": HARNESS},
                                    DIFF, _stub(SPLIT_MAP))
                + bdmod.section_html()
                + bdmod.tour_entry()["blurb"])
        blob.encode("ascii")
        for needle in ("[x]", "[ ]", "->"):
            self.assertIn(needle, blob)


if __name__ == "__main__":
    unittest.main()
