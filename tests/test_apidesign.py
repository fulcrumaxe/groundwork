"""Tests for the api-design exercise (type 40, F-17)."""
import unittest
from types import SimpleNamespace

from groundwork import apidesign as mod


def make_concept(name="fetch_user"):
    return SimpleNamespace(node_id="f", name=name, kind="function",
                           file="users.py", line=1)


CODE = "def fetch_user(user_id, timeout=30) -> dict:\n    return {}"


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex40", make_concept(), CODE.splitlines(), {})
        self.assertEqual(e["type"], 40)
        self.assertEqual(e["type_name"], "api-design")
        self.assertEqual(e["bloom"], "create")
        self.assertTrue(e["front"])

    def test_reference_points(self):
        e = mod.generate("ex40", make_concept(), CODE.splitlines(), {})
        p = e["payload"]
        self.assertEqual(p["func"], "fetch_user")
        self.assertEqual(p["required"], ["user_id", "timeout"])
        self.assertEqual(p["defaults"], {"timeout": "30"})
        self.assertTrue(p["want_return"])
        self.assertTrue(p["grounded"])
        self.assertIn("def fetch_user(user_id, timeout=30)", e["back"])

    def test_unparseable_still_builds(self):
        e = mod.generate("ex40", make_concept(), ["not python (("], {})
        self.assertFalse(e["payload"]["grounded"])
        self.assertTrue(e["front"])
        self.assertEqual(len(e["hints"]), 3)

    def test_tolerates_suite_ctx(self):
        # Same generic ctx test_groundwork uses for every type: must not raise.
        ctx = {"runnable": CODE, "expected_output": "x",
               "tests": "x", "trace_var": "total", "trace_expected": ["2"],
               "buggy": "b", "bug_line": 2, "fixed": "f", "graph": None}
        e = mod.generate("ex40", make_concept(), CODE.splitlines(), ctx)
        self.assertTrue(e["front"])


def grade_ok(code=CODE, sub="def fetch_user(user_id, timeout=30) -> dict:\n    ..."):
    e = mod.generate("ex40", make_concept(), code.splitlines(), {})
    return mod.grade(e, sub)


class GradeTest(unittest.TestCase):
    def test_accept_correct(self):
        r = grade_ok()
        self.assertTrue(r["pass"])
        self.assertEqual(r["score"], 1.0)

    def test_extra_params_still_pass(self):
        r = grade_ok(sub="def fetch_user(user_id, timeout=30, verbose=False) -> dict:\n    ...")
        self.assertTrue(r["pass"])

    def test_partial_missing_param_and_return(self):
        r = grade_ok(sub="def fetch_user(user_id):\n    ...")
        self.assertFalse(r["pass"])
        self.assertGreater(r["score"], 0.0)
        self.assertLess(r["score"], 0.5)

    def test_reject_wrong_default(self):
        r = grade_ok(sub="def fetch_user(user_id, timeout=5) -> dict:\n    ...")
        self.assertFalse(r["pass"])

    def test_reject_wrong_name(self):
        r = grade_ok(sub="def get_user(user_id, timeout=30) -> dict:\n    ...")
        self.assertFalse(r["pass"])

    def test_reject_missing_return(self):
        r = grade_ok(sub="def fetch_user(user_id, timeout=30):\n    ...")
        self.assertFalse(r["pass"])

    def test_reject_blank(self):
        self.assertFalse(grade_ok(sub="   ")["pass"])

    def test_reject_unparseable(self):
        r = grade_ok(sub="def fetch_user(((:")
        self.assertFalse(r["pass"])
        self.assertIn("parse", r["feedback"])

    def test_reject_no_def(self):
        self.assertFalse(grade_ok(sub="fetch_user(user_id)")["pass"])

    def test_no_runner_needed(self):
        e = mod.generate("ex40", make_concept(), CODE.splitlines(), {})
        self.assertTrue(mod.grade(
            e, "def fetch_user(user_id, timeout=30) -> dict:\n    ...", None)["pass"])

    def test_never_raises(self):
        e = mod.generate("ex40", make_concept(), CODE.splitlines(), {})
        for bad_ex, bad_sub in [({}, "def f(): ..."), (e, None),
                                (None, None), ({"payload": {}}, "def f(): ...")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex40", make_concept(), CODE.splitlines(), {})
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("def fetch_user(", body)
        self.assertIn("users.py:1", body)

    def test_render_escapes(self):
        e = mod.generate("ex40", make_concept(name="<b>"), CODE.splitlines(), {})
        body = mod.render(e)
        self.assertNotIn("<b>", body)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b7-apidesign'", mod.section_html())


if __name__ == "__main__":
    unittest.main()
