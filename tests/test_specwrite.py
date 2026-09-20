"""Tests for the spec-writing exercise (type 41, F-18)."""
import unittest
from types import SimpleNamespace

from groundwork import specwrite as mod


def make_concept(name="fetch_user"):
    return SimpleNamespace(node_id="f", name=name, kind="function",
                           file="users.py", line=1)


CODE = ("def fetch_user(user_id, timeout=30):\n"
        "    if not user_id:\n"
        "        raise ValueError('bad id')\n"
        "    return {'id': user_id}")


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex41", make_concept(), CODE.splitlines(), {})
        self.assertEqual(e["type"], 41)
        self.assertEqual(e["type_name"], "spec-writing")
        self.assertEqual(e["bloom"], "create")
        self.assertTrue(e["front"])

    def test_checklist_points(self):
        e = mod.generate("ex41", make_concept(), CODE.splitlines(), {})
        p = e["payload"]
        self.assertTrue(p["grounded"])
        ids = [pt["id"] for pt in p["points"]]
        self.assertIn("names", ids)
        self.assertIn("param-user_id", ids)
        self.assertIn("returns", ids)
        self.assertIn("edge", ids)
        self.assertIn("fetch_user", e["back"])

    def test_unparseable_still_builds(self):
        e = mod.generate("ex41", make_concept(), ["not python (("], {})
        self.assertFalse(e["payload"]["grounded"])
        self.assertTrue(e["front"])
        self.assertEqual(len(e["hints"]), 3)

    def test_tolerates_suite_ctx(self):
        # Same generic ctx test_groundwork uses for every type: must not raise.
        ctx = {"runnable": CODE, "expected_output": "x",
               "tests": "x", "trace_var": "total", "trace_expected": ["2"],
               "buggy": "b", "bug_line": 2, "fixed": "f", "graph": None}
        e = mod.generate("ex41", make_concept(), CODE.splitlines(), ctx)
        self.assertTrue(e["front"])


def grade_ok(sub=("fetch_user takes user_id and timeout=30. "
                  "It returns the user dict. "
                  "On bad input it raises an error.")):
    e = mod.generate("ex41", make_concept(), CODE.splitlines(), {})
    return mod.grade(e, sub)


class GradeTest(unittest.TestCase):
    def test_accept_complete(self):
        r = grade_ok()
        self.assertTrue(r["pass"])
        self.assertEqual(r["score"], 1.0)

    def test_case_insensitive(self):
        r = grade_ok(sub=("FETCH_USER takes USER_ID and TIMEOUT. "
                          "It RETURNS the dict. Raises an ERROR on bad input."))
        self.assertTrue(r["pass"])

    def test_partial_missing_points(self):
        r = grade_ok(sub="fetch_user takes user_id.")
        self.assertFalse(r["pass"])
        self.assertGreater(r["score"], 0.0)
        self.assertLess(r["score"], 1.0)
        self.assertIn("Missing", r["feedback"])

    def test_reject_blank(self):
        self.assertFalse(grade_ok(sub="   ")["pass"])

    def test_hostile_submissions(self):
        e = mod.generate("ex41", make_concept(), CODE.splitlines(), {})
        for bad in ["<script>alert(1)</script>", "x" * 5000, "12345",
                    "def fetch_user(:", "{{7*7}}", "\x00\x01"]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)

    def test_no_runner_needed(self):
        e = mod.generate("ex41", make_concept(), CODE.splitlines(), {})
        self.assertTrue(mod.grade(e, grade_ok.__defaults__[0], None)["pass"])

    def test_never_raises(self):
        e = mod.generate("ex41", make_concept(), CODE.splitlines(), {})
        for bad_ex, bad_sub in [({}, "fetch_user x"), (e, None),
                                (None, None), ({"payload": {}}, "fetch_user")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex41", make_concept(), CODE.splitlines(), {})
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("How grading works", body)
        self.assertIn("checklist", body.lower())
        self.assertIn("users.py:1", body)

    def test_render_escapes(self):
        e = mod.generate("ex41", make_concept(name="<b>"), CODE.splitlines(), {})
        body = mod.render(e)
        self.assertNotIn("<b>", body)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b8-specwrite'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t, {"id": "specwrite-type", "kind": "feature",
                             "title": "Spec writing",
                             "blurb": "Write acceptance criteria for a function: every "
                                      "checkbox — inputs, returns, edge cases — must appear.",
                             "path": "/status", "anchor": "status-b8-specwrite"})


if __name__ == "__main__":
    unittest.main()
