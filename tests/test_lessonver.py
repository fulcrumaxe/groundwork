"""Lesson-version banner (I-115)."""
import unittest

from groundwork import lessonver as lvmod
from groundwork import lessons as lesmod


def _lesson():
    return {"concept_id": "c", "name": "add", "kind": "function",
            "file": "calc.py", "line": 1,
            "summary": "add() totals two numbers via its defaults.",
            "docstring": "", "callers": [], "callees": [],
            "key_lines": "", "source": "def add(a, b):\n    return a + b\n",
            "how": ["Read the defaults."],
            "worked": None}


class NormalizeTest(unittest.TestCase):
    def test_no_commits_no_banner(self):
        self.assertEqual(lvmod.banner_html("", ""), "")
        self.assertEqual(lvmod.banner_html("abc1234", "abc1234"), "")

    def test_rejects_garbage(self):
        for bad in (None, 42, "HEAD", "main", "xyz", "a" * 41,
                    "<script>alert(1)</script>", ["abc1234"]):
            self.assertEqual(lvmod.banner_html(bad, ""), "")
            self.assertEqual(lvmod.normalize_commit(bad), "")


class ProvenanceTest(unittest.TestCase):
    def test_plain_provenance_without_current(self):
        out = lvmod.banner_html("abc1234")
        self.assertIn("Updated for commit", out)
        self.assertIn("<code>abc1234</code>", out)
        self.assertNotIn("moved on", out)

    def test_moved_on_names_both(self):
        out = lvmod.banner_html("abc1234abc1234abc1234abc1234abc1234abcd",
                                "def5678def5678def5678def5678def5678def5")
        self.assertIn("moved on", out)
        self.assertIn("<code>abc1234</code>", out)
        self.assertIn("<code>def5678</code>", out)
        self.assertNotIn("abc1234abc1234abc1234", out)


class NeedsBannerTest(unittest.TestCase):
    def test_matrix(self):
        self.assertTrue(lvmod.needs_banner("aaa1111", "bbb2222"))
        self.assertTrue(lvmod.needs_banner("aaa1111", ""))
        self.assertFalse(lvmod.needs_banner("aaa1111", "aaa1111"))
        self.assertFalse(lvmod.needs_banner("", "bbb2222"))
        self.assertFalse(lvmod.needs_banner("zzz", "bbb2222"))
        self.assertFalse(lvmod.needs_banner("aaa1111",
                                            "aaa1111..bbb2222"))

    def test_lesson_commit_of_prefers_lesson(self):
        self.assertEqual(lvmod.lesson_commit_of({"commit": "aaa1111"},
                                                "bbb2222"), "aaa1111")
        self.assertEqual(lvmod.lesson_commit_of({}, "aaa1111,bbb2222"),
                         "bbb2222")
        self.assertEqual(lvmod.lesson_commit_of({}, ""), "")
        self.assertEqual(lvmod.lesson_commit_of(None, ""), "")


class HeadCommitTest(unittest.TestCase):
    def test_outside_git_is_empty(self):
        import tempfile
        from groundwork import diff as diffmod
        tmp = tempfile.mkdtemp(prefix="gw-no-git-")
        self.assertEqual(diffmod.head_commit(tmp), "")

    def test_shape_when_present(self):
        import pathlib
        from groundwork import diff as diffmod
        got = diffmod.head_commit(pathlib.Path(__file__).resolve().parent)
        self.assertTrue(got == "" or (
            len(got) == 40 and lvmod.normalize_commit(got) == got))


class CallerEffectTest(unittest.TestCase):
    def test_render_levels_legacy_byte_identical(self):
        base = lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/")
        self.assertNotIn("lessonver", base)

    def test_render_levels_shows_banner(self):
        out = lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/",
                                   lesson_commit="aaa1111",
                                   current_commit="bbb2222")
        self.assertIn("lessonver", out)
        self.assertLess(out.index("lessonver"), out.index("Explain it"))
        same = lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/",
                                    lesson_commit="aaa1111",
                                    current_commit="aaa1111")
        self.assertNotIn("lessonver", same)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{lvmod.STATUS_ANCHOR}'",
                      lvmod.section_html())
        self.assertNotIn("<style", lvmod.banner_css())
        e = lvmod.tour_entry()
        self.assertEqual(e["id"], "lesson-version")
        self.assertEqual(e["anchor"], lvmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
