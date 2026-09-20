"""Tests for the changelog-entry exercise (type 43, F-20)."""
import unittest
from types import SimpleNamespace

from groundwork import changelog as mod


def make_concept(name="fetch_user"):
    return SimpleNamespace(node_id="f", name=name, kind="function",
                           file="users.py", line=1)


CODE = "def fetch_user(user_id):\n    return {}"
GOOD = "### Added\n- `fetch_user` now lets you look up any user by id."


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex43", make_concept(), CODE.splitlines(), {})
        self.assertEqual(e["type"], 43)
        self.assertEqual(e["type_name"], "changelog-entry")
        self.assertEqual(e["bloom"], "create")
        self.assertTrue(e["front"])

    def test_payload_section_and_keyword(self):
        e = mod.generate("ex43", make_concept(), CODE.splitlines(), {})
        self.assertEqual(e["payload"]["section"], "Added")
        self.assertEqual(e["payload"]["keyword"], "fetch_user")
        self.assertTrue(e["payload"]["grounded"])
        self.assertIn("### Added", e["back"])

    def test_fix_cues_pick_fixed(self):
        e = mod.generate("ex43", make_concept("fix_login"), ["x = 1"], {})
        self.assertEqual(e["payload"]["section"], "Fixed")

    def test_unparseable_still_builds(self):
        e = mod.generate("ex43", make_concept(), ["not python (("], {})
        self.assertTrue(e["payload"]["grounded"])
        self.assertTrue(e["front"])
        self.assertEqual(len(e["hints"]), 3)

    def test_tolerates_suite_ctx(self):
        ctx = {"runnable": CODE, "expected_output": "x",
               "tests": "x", "trace_var": "total", "trace_expected": ["2"],
               "buggy": "b", "bug_line": 2, "fixed": "f", "graph": None}
        e = mod.generate("ex43", make_concept(), CODE.splitlines(), ctx)
        self.assertTrue(e["front"])


def grade_ok(code=CODE, sub=GOOD):
    e = mod.generate("ex43", make_concept(), code.splitlines(), {})
    return mod.grade(e, sub)


class GradeTest(unittest.TestCase):
    def test_accept_correct(self):
        r = grade_ok()
        self.assertTrue(r["pass"])
        self.assertEqual(r["score"], 1.0)

    def test_reject_wrong_section(self):
        r = grade_ok(sub="### Fixed\n- `fetch_user` now lets you look up any user by id.")
        self.assertFalse(r["pass"])

    def test_reject_missing_keyword(self):
        r = grade_ok(sub="### Added\n- now lets you look up any user by id quickly.")
        self.assertFalse(r["pass"])

    def test_reject_concept_fragment(self):
        # Naming only "user" does not name `fetch_user`.
        r = grade_ok(sub="### Added\n- the user lookup now returns faster for you.")
        self.assertFalse(r["pass"])

    def test_partial_short_line(self):
        r = grade_ok(sub="### Added\n- `fetch_user` now rocks.")
        self.assertFalse(r["pass"])
        self.assertGreater(r["score"], 0.0)
        self.assertLess(r["score"], 1.0)

    def test_reject_blank(self):
        self.assertFalse(grade_ok(sub="   ")["pass"])

    def test_no_runner_needed(self):
        e = mod.generate("ex43", make_concept(), CODE.splitlines(), {})
        self.assertTrue(mod.grade(e, GOOD, None)["pass"])

    def test_hostile_never_raises(self):
        e = mod.generate("ex43", make_concept(), CODE.splitlines(), {})
        for bad_ex, bad_sub in [({}, GOOD), (e, None), (None, None),
                                ({"payload": {}}, GOOD),
                                (e, "<script>alert(1)</script>"), (e, 12345)]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex43", make_concept(), CODE.splitlines(), {})
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("### Added", body)
        self.assertIn("users.py:1", body)
        self.assertIn("How grading works", body)

    def test_render_escapes(self):
        e = mod.generate("ex43", make_concept(name="<b>"), CODE.splitlines(), {})
        body = mod.render(e)
        self.assertNotIn("<b>", body)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b8-changelog'", mod.section_html())


if __name__ == "__main__":
    unittest.main()
