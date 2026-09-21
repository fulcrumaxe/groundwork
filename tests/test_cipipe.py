"""Tests for the CI pipeline authoring exercise (type 65, F-42)."""
import unittest
from types import SimpleNamespace

from groundwork import cipipe as mod


def make_concept(name="checkout"):
    return SimpleNamespace(node_id="c", name=name, kind="service",
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


GOOD = ("on:\n  push:\n    branches: [main]\njobs:\n  test:\n"
        "    runs-on: ubuntu-latest\n    steps:\n"
        "      - uses: actions/checkout@v4\n      - run: pytest\n")


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex65", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (65, "cipipe", "create"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_fixture_ctx_emits(self):
        e = mod.generate("ex65", make_concept(), ["x = 1"], fixture_ctx())
        self.assertTrue(e["front"])

    def test_workflow_deterministic(self):
        a = mod.generate("ex65", make_concept(), ["x = 1"], {})
        b = mod.generate("ex65", make_concept(), ["x = 1"], {})
        self.assertEqual(a["payload"]["workflow"], b["payload"]["workflow"])
        self.assertTrue(a["payload"]["workflow"].startswith("ci-"))

    def test_thin_input_still_returns_card(self):
        e = mod.generate("ex65", None, [], {})
        self.assertIsNotNone(e)
        self.assertFalse(e["payload"]["grounded"])
        self.assertTrue(e["front"])

    def test_never_raises(self):
        e = mod.generate(None, None, None, None)
        self.assertIsNotNone(e)
        self.assertTrue(e["front"])


class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.generate("ex65", make_concept(), ["x = 1"], {})
        r = mod.grade(e, GOOD)
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_missing_on_fails(self):
        e = mod.generate("ex65", make_concept(), ["x = 1"], {})
        bad = "\n".join(l for l in GOOD.splitlines()
                        if not l.startswith(("on:", "  push", "    branches")))
        r = mod.grade(e, bad)
        self.assertFalse(r["pass"])
        self.assertEqual(r["score"], 0.0)

    def test_job_without_steps_fails(self):
        e = mod.generate("ex65", make_concept(), ["x = 1"], {})
        bad = ("on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n")
        r = mod.grade(e, bad)
        self.assertFalse(r["pass"])

    def test_step_without_run_or_uses_fails(self):
        e = mod.generate("ex65", make_concept(), ["x = 1"], {})
        bad = ("on:\n  push:\njobs:\n  test:\n    runs-on: ubuntu-latest\n"
               "    steps:\n      - name: hello\n")
        self.assertFalse(mod.grade(e, bad)["pass"])

    def test_tab_indent_fails(self):
        e = mod.generate("ex65", make_concept(), ["x = 1"], {})
        bad = GOOD.replace("  push:", "\tpush:")
        self.assertFalse(mod.grade(e, bad)["pass"])

    def test_no_partial_credit(self):
        e = mod.generate("ex65", make_concept(), ["x = 1"], {})
        # Everything right except one step's key: still 0.0.
        bad = GOOD.replace("- uses: actions/checkout@v4",
                           "- name: checkout")
        r = mod.grade(e, bad)
        self.assertFalse(r["pass"])
        self.assertEqual(r["score"], 0.0)

    def test_empty_and_garbage_fail_closed(self):
        e = mod.generate("ex65", make_concept(), ["x = 1"], {})
        for bad in ["", "   ", "hello world", None]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertEqual(r["score"], 0.0)

    def test_hostile_never_raises(self):
        e = mod.generate("ex65", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [({}, "x"), (e, None),
                                ({"payload": {}}, "on: x"),
                                (None, None)]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex65", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("How grading works", body)
        self.assertIn("app.py:3", body)

    def test_render_escapes(self):
        e = mod.generate("ex65", make_concept(name="<b>"), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b11-cipipe'", mod.section_html())

    def test_tour_entry(self):
        self.assertEqual(mod.tour_entry(),
                         {"id": "cipipe", "kind": "feature",
                          "title": "CI pipeline",
                          "blurb": "Author a push-triggered CI pipeline — static dry-run lint, no partial credit.",
                          "path": "/status", "anchor": "status-b11-cipipe"})


if __name__ == "__main__":
    unittest.main()
