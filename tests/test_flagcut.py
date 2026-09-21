"""Tests for the flag-cut exercise (type 66, F-43)."""
import unittest
from types import SimpleNamespace

from groundwork import flagcut as mod


def make_concept(name="checkout"):
    return SimpleNamespace(node_id="c", name=name, kind="pricing",
                           file="app.py", line=3)


def fixture_ctx():
    # Same shape as tests/test_groundwork.py test_all_types_generate.
    from groundwork import graph as graphmod
    return {"runnable": "def add(a=2, b=3):\n    return a + b",
            "expected_output": "5",
            "tests": "_out = repr(add())\nassert _out == '5'\nprint('OK')",
            "trace_var": "total", "trace_expected": ["2", "5"],
            "buggy": "def add(a=2, b=3):\n    return a - b", "bug_line": 2,
            "fixed": "def add(a=2, b=3):\n    return a + b",
            "graph": graphmod.Graph()}


def runner():
    from groundwork import sandbox as sbmod
    return sbmod.SandboxRunner()


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex66", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (66, "flag-cut", "modify"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_fixture_ctx_never_none(self):
        e = mod.generate("ex66", make_concept(), ["x = 1"], fixture_ctx())
        self.assertTrue(e["front"])

    def test_flag_deterministic(self):
        a = mod.generate("ex66", make_concept(), ["x = 1"], {})
        b = mod.generate("ex66", make_concept(), ["x = 1"], {})
        self.assertEqual(a["payload"]["flag"], b["payload"]["flag"])
        self.assertRegex(a["payload"]["flag"], r"^[A-Z][A-Z0-9_]+$")

    def test_found_flag_used(self):
        e = mod.generate("ex66", make_concept(),
                         ["if BETA_MODE:", "    out = 1"], {})
        self.assertEqual(e["payload"]["flag"], "BETA_MODE")
        self.assertFalse(e["payload"]["seeded"])

    def test_seeded_when_no_flag(self):
        e = mod.generate("ex66", make_concept(), ["x = 1"], {})
        self.assertTrue(e["payload"]["seeded"])
        self.assertRegex(e["payload"]["flag"], r"^FLAG_[0-9A-F]{4}$")

    def test_never_raises(self):
        e = mod.generate(None, None, None, None)
        self.assertIsNotNone(e)
        self.assertTrue(e["front"])


class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.generate("ex66", make_concept(), ["x = 1"], {})
        r = mod.grade(e, e["payload"]["reference"], runner())
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_flag_in_code_fails(self):
        e = mod.generate("ex66", make_concept(), ["x = 1"], {})
        self.assertFalse(mod.grade(e, e["payload"]["original"],
                                   runner())["pass"])

    def test_flag_in_comment_fails(self):
        e = mod.generate("ex66", make_concept(), ["x = 1"], {})
        ref = e["payload"]["reference"]
        flag = e["payload"]["flag"]
        bad = ref + f"# still mentions {flag}\n"
        r = mod.grade(e, bad, runner())
        self.assertFalse(r["pass"])

    def test_flag_in_string_fails(self):
        e = mod.generate("ex66", make_concept(), ["x = 1"], {})
        ref = e["payload"]["reference"]
        flag = e["payload"]["flag"]
        bad = ref + f'x = "{flag}"\n'
        self.assertFalse(mod.grade(e, bad, runner())["pass"])

    def test_live_branch_dropped_fails(self):
        e = mod.generate("ex66", make_concept(), ["x = 1"], {})
        func = e["payload"]["func"]
        # Flag gone but behavior wrong: constant answer.
        bad = f"def {func}(x):\n    return 0\n"
        r = mod.grade(e, bad, runner())
        self.assertFalse(r["pass"])

    def test_no_partial_credit(self):
        e = mod.generate("ex66", make_concept(), ["x = 1"], {})
        func = e["payload"]["func"]
        bad = f"def {func}(x):\n    return 0\n"
        r = mod.grade(e, bad, runner())
        self.assertFalse(r["pass"])
        self.assertEqual(r["score"], 0.0)

    def test_empty_and_garbage_fail_closed(self):
        e = mod.generate("ex66", make_concept(), ["x = 1"], {})
        for bad in ["", "   ", "hello world", None, "def broken(:"]:
            r = mod.grade(e, bad, runner())
            self.assertFalse(r["pass"])
            self.assertEqual(r["score"], 0.0)

    def test_no_runner_fails_closed(self):
        e = mod.generate("ex66", make_concept(), ["x = 1"], {})
        r = mod.grade(e, e["payload"]["reference"], None)
        self.assertFalse(r["pass"])

    def test_hostile_never_raises(self):
        e = mod.generate("ex66", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [({}, "x"), (e, None),
                                ({"payload": {}}, "def f(): pass"),
                                (None, None)]:
            r = mod.grade(bad_ex, bad_sub, runner())
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex66", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("How grading works", body)
        self.assertIn("app.py:3", body)

    def test_render_escapes(self):
        e = mod.generate("ex66", make_concept(name="<b>"), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b11-flagcut'", mod.section_html())

    def test_tour_entry(self):
        self.assertEqual(mod.tour_entry(),
                         {"id": "flag-cut", "kind": "feature",
                          "title": "Cut the stale flag",
                          "blurb": "Remove a dead feature-flag branch — grep gate plus green hidden tests.",
                          "path": "/status", "anchor": "status-b11-flagcut"})


if __name__ == "__main__":
    unittest.main()
