"""Tests for the commit-message exercise (type 42, F-19)."""
import unittest
from types import SimpleNamespace

from groundwork import commitmsg as mod


def make_concept(name="fetch_user"):
    return SimpleNamespace(node_id="f", name=name, kind="function",
                           file="users.py", line=1)


DIFF = ("-def fetch_user(uid):\n+def fetch_user(user_id, timeout=30):\n"
        " retry on timeout for flaky auth")


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex42", make_concept(), DIFF.splitlines(), {})
        self.assertEqual(e["type"], 42)
        self.assertEqual(e["type_name"], "commit-message")
        self.assertEqual(e["bloom"], "create")
        self.assertTrue(e["front"])

    def test_payload_keywords(self):
        e = mod.generate("ex42", make_concept(), DIFF.splitlines(), {})
        self.assertIn("fetch", e["payload"]["what"])
        self.assertTrue(e["payload"]["why"])
        self.assertTrue(e["payload"]["grounded"])
        self.assertLessEqual(len(e["payload"]["reference"]), 72)

    def test_diff_ctx_preferred(self):
        ctx = {"diff_lines": ["+retry on timeout"], "decisions": [{"note": "flaky auth retry"}]}
        e = mod.generate("ex42", make_concept(), ["other"], ctx)
        self.assertIn("retry", e["front"].lower())

    def test_unparseable_still_builds(self):
        e = mod.generate("ex42", make_concept(), ["not python (("], {})
        self.assertTrue(e["front"])
        self.assertEqual(len(e["hints"]), 3)

    def test_tolerates_suite_ctx(self):
        ctx = {"runnable": DIFF, "expected_output": "x", "tests": "x",
               "trace_var": "total", "trace_expected": ["2"],
               "buggy": "b", "bug_line": 2, "fixed": "f", "graph": None}
        e = mod.generate("ex42", make_concept(), DIFF.splitlines(), ctx)
        self.assertTrue(e["front"])


def grade_ok(sub=None):
    e = mod.generate("ex42", make_concept(), DIFF.splitlines(),
                     {"decisions": [{"note": "flaky auth retry"}]})
    # The card's why keywords are flaky/auth (from the decision note);
    # a passing subject must name them, as the front instructs.
    good = "Update fetch for flaky auth"
    return mod.grade(e, good if sub is None else sub)


class GradeTest(unittest.TestCase):
    def test_accept_correct(self):
        r = grade_ok()
        self.assertTrue(r["pass"])
        self.assertEqual(r["score"], 1.0)

    def test_partial_missing_why(self):
        r = grade_ok("Update fetch user timeout handling")
        self.assertFalse(r["pass"])
        self.assertGreater(r["score"], 0.0)
        self.assertLess(r["score"], 1.0)
        self.assertIn("why", r["feedback"].lower())

    def test_reject_past_tense(self):
        self.assertFalse(grade_ok("Updated fetch for retry")["pass"])

    def test_reject_too_long(self):
        self.assertFalse(grade_ok("Update fetch for retry " + "x" * 70)["pass"])

    def test_reject_blank(self):
        self.assertFalse(grade_ok("   ")["pass"])

    def test_hostile_submission(self):
        e = mod.generate("ex42", make_concept(), DIFF.splitlines(), {})
        for bad in ["<script>alert(1)</script>", "x" * 5000, "Update", "\n\n\n"]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)

    def test_never_raises(self):
        e = mod.generate("ex42", make_concept(), DIFF.splitlines(), {})
        for bad_ex, bad_sub in [({}, "Update x for y"), (e, None),
                                (None, None), ({"payload": {}}, "Update x for y")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex42", make_concept(), DIFF.splitlines(), {})
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("How grading works", body)
        self.assertIn("users.py:1", body)

    def test_render_escapes(self):
        e = mod.generate("ex42", make_concept(name="<b>"), ["<script>"], {})
        body = mod.render(e)
        self.assertNotIn("<script>", body)
        self.assertIn("&lt;script&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b8-commitmsg'", mod.section_html())

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(),
                         {"id": "commitmsg-type", "kind": "feature",
                          "title": "Commit-message authorship",
                          "blurb": "Summarize a diff as a commit message: imperative subject naming the what and the why.",
                          "path": "/status", "anchor": "status-b8-commitmsg"})


if __name__ == "__main__":
    unittest.main()
