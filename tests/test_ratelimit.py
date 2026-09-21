"""Tests for the rate-limit design exercise (type 71, F-48)."""
import unittest
from types import SimpleNamespace

from groundwork import ratelimit as mod


def make_concept(name="login"):
    return SimpleNamespace(node_id="c", name=name, kind="endpoint",
                           file="limits.py", line=4)


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


PASS_ANSWER = (
    "scope=10/min per IP plus 1000/min global\n"
    "window=60s fixed window\n"
    "burst=token bucket, burst 5\n"
    "retry=429 with Retry-After: 60\n"
    "why=per-IP stops a single credential-stuffing abuser while the "
    "global cap guards total capacity; Retry-After forces backoff so "
    "legitimate users recover"
)

FAIL_ANSWER = (
    "scope=100/min global\n"
    "window=minute\n"
    "burst=none\n"
    "retry=429\n"
    "why=simple"
)


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex71", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (71, "ratelimit", "evaluate"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_never_none_fixture_and_hostile(self):
        e = mod.generate("ex71", make_concept(), ["x = 1"], fixture_ctx())
        self.assertTrue(e["front"])
        e = mod.generate(None, None, None, None)
        self.assertIsNotNone(e)
        self.assertTrue(e["front"])

    def test_deterministic(self):
        a = mod.generate("ex71", make_concept(), ["x = 1"], {})
        b = mod.generate("ex71", make_concept(), ["x = 1"], {})
        self.assertEqual(a["payload"]["profile"], b["payload"]["profile"])

    def test_profile_sweep_covers_two(self):
        seen = {mod.generate(f"ex{i}", make_concept(), ["x"], {})["payload"]["profile"]
                for i in range(20)}
        self.assertGreaterEqual(len(seen), 2)


class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.generate("ex71", make_concept(), ["x = 1"], {})
        r = mod.grade(e, PASS_ANSWER)
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_each_point_fails_independently(self):
        cases = [
            PASS_ANSWER.replace("per IP plus", "plus"),  # scope loses per-key
            PASS_ANSWER.replace("window=60s fixed window", "window=short"),
            PASS_ANSWER.replace("token bucket, burst 5", "nothing"),
            PASS_ANSWER.replace("Retry-After: 60", "later"),
        ]
        for bad in cases:
            e = mod.generate("ex71", make_concept(), ["x = 1"], {})
            r = mod.grade(e, bad)
            self.assertTrue(r["score"] < 1.0, bad)

    def test_why_only_garbage_fails(self):
        e = mod.generate("ex71", make_concept(), ["x = 1"], {})
        bad = PASS_ANSWER.replace(
            "why=per-IP stops a single credential-stuffing abuser while the "
            "global cap guards total capacity; Retry-After forces backoff so "
            "legitimate users recover", "why=simple")
        r = mod.grade(e, bad)
        self.assertEqual(r["score"], 0.8)
        self.assertTrue(r["pass"])

    def test_partial_credit(self):
        e = mod.generate("ex71", make_concept(), ["x = 1"], {})
        mid = ("\n".join(PASS_ANSWER.splitlines()[:3])
               + "\nretry=429\nwhy=simple\n")
        r = mod.grade(e, mid)
        self.assertEqual(r["score"], 0.6)
        self.assertTrue(r["pass"])
        r = mod.grade(e, FAIL_ANSWER)
        self.assertEqual(r["score"], 0.0)
        self.assertFalse(r["pass"])

    def test_empty_garbage_none_fail_closed(self):
        e = mod.generate("ex71", make_concept(), ["x = 1"], {})
        for bad in ["", "hello world", None]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertEqual(r["score"], 0.0)

    def test_hostile_never_raises(self):
        e = mod.generate("ex71", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [(None, None), ({}, "x"),
                                ({"payload": {}}, "scope=x")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex71", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("key=value", body)
        self.assertIn("scope", body)
        self.assertIn("How grading works", body)
        self.assertIn("limits.py:4", body)

    def test_render_escapes(self):
        e = mod.generate("ex71", make_concept(name="<b>"), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b11-ratelimit'", mod.section_html())

    def test_tour_entry(self):
        self.assertEqual(mod.tour_entry(),
                         {"id": "rate-limit-it", "kind": "feature",
                          "title": "Rate-limit it",
                          "blurb": "Pick per-key + global limits, a window, burst handling, and 429 + Retry-After — rubric-graded with partial credit.",
                          "path": "/status", "anchor": "status-b11-ratelimit"})


if __name__ == "__main__":
    unittest.main()
