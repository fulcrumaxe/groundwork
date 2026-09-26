"""Learner-vs-expected output diff: side-by-side on mismatch (I-157)."""
import unittest
from types import SimpleNamespace

from groundwork import exercises as exmod
from groundwork import outdiff as odmod


def _type8(expected="a\nB", code="print('a')\nprint('B')"):
    return {"type": 8, "payload": {"code": code, "expected": expected}}


def _runner(stdout="a\nB", ok=True):
    return SimpleNamespace(run=lambda code: SimpleNamespace(ok=ok, stdout=stdout))


class NormalizeTest(unittest.TestCase):
    def test_none_is_empty(self):
        self.assertEqual(odmod.normalize_output(None), "")

    def test_crlf_normalized(self):
        self.assertEqual(odmod.normalize_output("a\r\nb\rc"), "a\nb\nc")

    def test_non_string_coerced(self):
        self.assertEqual(odmod.normalize_output(42), "42")


class MatchQuietTest(unittest.TestCase):
    def test_identical_is_quiet(self):
        self.assertFalse(odmod.has_mismatch("a\n", "a\n"))
        self.assertIsNone(odmod.first_mismatch("a\n", "a\n"))
        self.assertEqual(odmod.mismatch_text("a\n", "a\n"), "")
        self.assertEqual(odmod.mismatch_html("a\n", "a\n"), "")

    def test_rejects_garbage(self):
        self.assertFalse(odmod.has_mismatch(None, None))
        self.assertEqual(odmod.mismatch_text(None, None), "")
        self.assertEqual(odmod.mismatch_html(None, None), "")
        self.assertEqual(odmod.rows(None, None), [])


class RowsTest(unittest.TestCase):
    def test_replace_pairs_lines(self):
        got, want = "a\nb\n", "a\nB\n"
        self.assertTrue(odmod.has_mismatch(got, want))
        self.assertEqual(odmod.first_mismatch(got, want), 2)
        rs = odmod.rows(got, want)
        self.assertTrue(rs[0][4])
        self.assertEqual(rs[1], (2, 2, "b", "B", False))

    def test_missing_side_uses_none(self):
        rs = odmod.rows("a\nb\n", "a\n")
        self.assertEqual(rs[1], (2, None, "b", None, False))


class MismatchTextTest(unittest.TestCase):
    def test_names_first_row_both_sides(self):
        out = odmod.mismatch_text("a\nb\n", "a\nB\n")
        self.assertIn("row 2", out)
        self.assertIn("yours", out)
        self.assertIn("expected", out)
        self.assertIn("'b'", out)
        self.assertIn("'B'", out)

    def test_cap_truncates(self):
        got = "\n".join(f"g{i}" for i in range(30))
        want = "\n".join(f"w{i}" for i in range(30))
        out = odmod.mismatch_text(got, want, cap=5)
        self.assertIn("more differing rows", out)


class MismatchHtmlTest(unittest.TestCase):
    def test_renders_both_columns(self):
        out = odmod.mismatch_html("a\nb\n", "a\nB\n")
        self.assertIn("class='outdiff'", out)
        self.assertIn("yours", out)
        self.assertIn("expected", out)

    def test_escapes_markup(self):
        out = odmod.mismatch_html("x = '<b>'\n", "x = '<i>'\n")
        self.assertIn("&lt;b&gt;", out)
        self.assertNotIn("<b>", out)

    def test_cap_bounds_rows(self):
        got = "\n".join(f"g{i}" for i in range(100))
        want = "\n".join(f"w{i}" for i in range(100))
        out = odmod.mismatch_html(got, want, cap=10)
        self.assertLessEqual(out.count("<tr class="), 10)


class CallerEffectTest(unittest.TestCase):
    def test_grade_pass_legacy_byte_identical(self):
        res = exmod.grade(_type8(), "a\nB", _runner())
        self.assertTrue(res["pass"])
        self.assertEqual(res["feedback"], "Prediction matches.")

    def test_grade_stale_reference_untouched(self):
        res = exmod.grade(_type8(), "a\nb", _runner(stdout="zzz"))
        self.assertFalse(res["pass"])
        self.assertEqual(res["feedback"],
                         "Reference no longer reproduces; flagged stale.")

    def test_grade_mismatch_appends_side_by_side(self):
        res = exmod.grade(_type8(), "a\nb", _runner())
        self.assertFalse(res["pass"])
        self.assertIn("Actual output:", res["feedback"])
        self.assertIn("row 2", res["feedback"])
        self.assertIn("yours", res["feedback"])

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{odmod.STATUS_ANCHOR}'",
                      odmod.section_html())
        self.assertNotIn("<style", odmod.diff_css())
        e = odmod.tour_entry()
        self.assertEqual(e["id"], "output-mismatch-diff")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["anchor"], odmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
