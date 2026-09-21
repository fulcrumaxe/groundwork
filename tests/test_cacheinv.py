"""Tests for the cache-invalidation exercise (type 69, F-46)."""
import unittest
from types import SimpleNamespace

from groundwork import cacheinv as mod


def make_concept(name="lookup"):
    return SimpleNamespace(node_id="c", name=name, kind="cache",
                           file="cache.py", line=7)


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


def good_for(e):
    return " ".join(e["payload"]["answer"])


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex69", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (69, "cache-invalidation", "analyse"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_fixture_ctx_never_none(self):
        e = mod.generate("ex69", make_concept(), ["x = 1"], fixture_ctx())
        self.assertTrue(e["front"])

    def test_deterministic(self):
        a = mod.generate("ex69", make_concept(), ["x = 1"], {})
        b = mod.generate("ex69", make_concept(), ["x = 1"], {})
        self.assertEqual(a["payload"]["paths"], b["payload"]["paths"])
        self.assertEqual(a["payload"]["answer"], b["payload"]["answer"])
        self.assertEqual(len(a["payload"]["answer"]), 2)

    def test_no_surface_yields_ungrounded_card(self):
        e = mod.generate("ex69", None, [], {})
        self.assertIsNotNone(e)
        self.assertFalse(e["payload"]["grounded"])
        self.assertTrue(e["front"])

    def test_never_raises(self):
        e = mod.generate(None, None, None, None)
        self.assertIsNotNone(e)


class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.generate("ex69", make_concept(), ["x = 1"], {})
        r = mod.grade(e, good_for(e))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_missing_point_fails(self):
        e = mod.generate("ex69", make_concept(), ["x = 1"], {})
        bad = e["payload"]["answer"][0]
        r = mod.grade(e, bad)
        self.assertFalse(r["pass"])
        self.assertIn(e["payload"]["answer"][1], r["feedback"])

    def test_hot_path_over_invalidation_fails(self):
        e = mod.generate("ex69", make_concept(), ["x = 1"], {})
        hot = e["payload"]["hot"][0]
        bad = good_for(e) + " " + hot
        r = mod.grade(e, bad)
        self.assertFalse(r["pass"])
        self.assertIn(hot, r["feedback"])

    def test_no_partial_credit(self):
        e = mod.generate("ex69", make_concept(), ["x = 1"], {})
        bad = e["payload"]["answer"][0]
        r = mod.grade(e, bad)
        self.assertFalse(r["pass"])
        self.assertEqual(r["score"], 0.0)

    def test_empty_and_garbage_fail_closed(self):
        e = mod.generate("ex69", make_concept(), ["x = 1"], {})
        for bad in ["", "   ", "hello", None]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertEqual(r["score"], 0.0)

    def test_hostile_never_raises(self):
        e = mod.generate("ex69", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [({}, "x"), (e, None),
                                ({"payload": {}}, "A B"),
                                (None, None)]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex69", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("checkbox", body)
        self.assertIn("How grading works", body)
        self.assertIn("cache.py:7", body)

    def test_render_escapes(self):
        e = mod.generate("ex69", make_concept(name="<b>"), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b11-cacheinv'", mod.section_html())

    def test_tour_entry(self):
        self.assertEqual(mod.tour_entry(),
                         {"id": "cache-invalidation", "kind": "feature",
                          "title": "Cache invalidation",
                          "blurb": "Name every mutation path that busts a cached value — exact set, no hot-path busts.",
                          "path": "/status", "anchor": "status-b11-cacheinv"})


if __name__ == "__main__":
    unittest.main()
