"""Line-by-line lesson version diff (I-116)."""
import unittest

from groundwork import lessondiff as ldmod
from groundwork import lessons as lesmod


def _lesson(**over):
    lesson = {"concept_id": "c", "name": "add", "kind": "function",
              "file": "calc.py", "line": 1,
              "summary": "add() totals two numbers via its defaults.",
              "docstring": "", "callers": [], "callees": [],
              "key_lines": "", "source": "def add(a, b):\n    return a + b\n",
              "how": ["Read the defaults."],
              "worked": None}
    lesson.update(over)
    return lesson


def _changed():
    return _lesson(before="def add(a, b):\n    return a - b\n")


class HasChangesTest(unittest.TestCase):
    def test_identical_is_quiet(self):
        self.assertFalse(ldmod.has_changes("a\n", "a\n"))
        self.assertEqual(ldmod.diff_html("a\n", "a\n"), "")
        self.assertEqual(ldmod.lesson_block(_lesson()), "")

    def test_rejects_garbage(self):
        for bad in (None, 42, ["a"], {"a": 1}):
            self.assertEqual(ldmod.lesson_block(bad), "")
        self.assertEqual(ldmod.diff_html(None, None), "")
        self.assertFalse(ldmod.has_changes(None, None))


class DiffHtmlTest(unittest.TestCase):
    def test_changed_pair_renders_rows(self):
        out = ldmod.lesson_block(_changed())
        self.assertIn("lessondiff", out)
        self.assertIn("return a - b", out)
        self.assertIn("+1", out)
        self.assertIn("−1", out)

    def test_escapes_markup(self):
        out = ldmod.diff_html("x = '<b>'\n", "x = '<i>'\n")
        self.assertIn("&lt;b&gt;", out)
        self.assertNotIn("<b>", out)

    def test_cap_bounds_rows(self):
        before = "\n".join(f"old{i}" for i in range(200))
        after = "\n".join(f"new{i}" for i in range(200))
        out = ldmod.diff_html(before, after, cap=10)
        self.assertLessEqual(out.count("<tr class="), 10)


class CallerEffectTest(unittest.TestCase):
    def test_render_levels_legacy_byte_identical(self):
        base = lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/")
        self.assertNotIn("lessondiff", base)

    def test_render_levels_shows_diff_after_banner(self):
        out = lesmod.render_levels(_changed(), 0.0, 0, "auto", "/")
        self.assertIn("lessondiff", out)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{ldmod.STATUS_ANCHOR}'",
                      ldmod.section_html())
        self.assertNotIn("<style", ldmod.diff_css())
        e = ldmod.tour_entry()
        self.assertEqual(e["id"], "lesson-version-diff")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["anchor"], ldmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
