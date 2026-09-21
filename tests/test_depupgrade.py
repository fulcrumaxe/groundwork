"""Tests for the dependency-upgrade exercise (type 62, F-39)."""
import unittest
from types import SimpleNamespace

from groundwork import depupgrade as mod


def make_concept(name="checkout"):
    return SimpleNamespace(node_id="c", name=name, kind="service",
                           file="deploy.py", line=3)


def suite_ctx():
    # Fixture ctx mirrored from tests/test_groundwork.py
    # test_all_types_generate: generate() must deal a real card here.
    from groundwork import graph as graphmod
    return {"runnable": "def add(a=2, b=3):\n    return a + b",
            "expected_output": "5",
            "tests": "_out = repr(add())\nassert _out == '5'\nprint('OK')",
            "trace_var": "total", "trace_expected": ["2", "5"],
            "buggy": "def add(a=2, b=3):\n    return a - b", "bug_line": 2,
            "fixed": "def add(a=2, b=3):\n    return a + b",
            "graph": graphmod.Graph()}


def answer_for(e):
    return e["payload"]["fixed"]


def old_for(e):
    return e["payload"]["old_caller"]


def card_for_key(key):
    """First deterministic card dealing the given catalog key."""
    for i in range(1000):
        e = mod.generate(f"ex62-{key}-{i}", make_concept(), ["x = 1"], {})
        if e["payload"]["key"] == key:
            return e
    raise AssertionError(f"no card deals {key}")


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex62", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (62, "dep-upgrade", "modify"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_suite_ctx_deals_real_card(self):
        snip = ["def add(a=2, b=3):", "    total = a + b", "    return total"]
        e = mod.generate("ex62", make_concept(name="add"), snip, suite_ctx())
        self.assertIsNotNone(e)
        self.assertTrue(e["front"])

    def test_deterministic_from_ex_id(self):
        a = mod.generate("ex62", make_concept(), ["x = 1"], {})
        b = mod.generate("ex62", make_concept(), ["x = 1"], {})
        self.assertEqual(a["payload"]["key"], b["payload"]["key"])
        self.assertEqual(a["payload"]["fixed"], b["payload"]["fixed"])
        self.assertEqual(a["front"], b["front"])

    def test_catalog_covers_four_breaks(self):
        seen = {mod.generate(f"ex62-{i}", make_concept(), ["x = 1"], {})["payload"]["key"]
                for i in range(40)}
        self.assertEqual(seen, {"renamed-kwarg", "removed-function",
                                "return-shape", "required-arg"})

    def test_no_surface_returns_none(self):
        self.assertIsNone(mod.generate("ex62", None, [], {}))
        self.assertIsNone(mod.generate("ex62", None, None, None))

    def test_never_raises_fuzz(self):
        c = make_concept()
        for args in [("x", None, None, None), ("x", c, None, None),
                     ("x", "not-a-concept", ["  "], {}),
                     ("x", c, [None, 123], {"commit": None}),
                     (None, None, None, None)]:
            try:
                mod.generate(*args)
            except Exception as exc:  # noqa: BLE001
                self.fail(f"generate{args} raised {exc!r}")


class GradeTest(unittest.TestCase):
    def test_round_trip_pass_with_migrated_caller(self):
        for key in ("renamed-kwarg", "removed-function",
                    "return-shape", "required-arg"):
            e = card_for_key(key)
            r = mod.grade(e, answer_for(e))
            self.assertTrue(r["pass"] and r["score"] == 1.0, key)

    def test_unmigrated_caller_fails_every_entry(self):
        for key in ("renamed-kwarg", "removed-function",
                    "return-shape", "required-arg"):
            e = card_for_key(key)
            r = mod.grade(e, old_for(e))
            self.assertFalse(r["pass"], key)

    def test_runner_ignored(self):
        e = mod.generate("ex62", make_concept(), ["x = 1"], {})
        self.assertTrue(mod.grade(e, answer_for(e), runner=None)["pass"])
        self.assertTrue(mod.grade(e, answer_for(e), runner=object())["pass"])

    def test_leftover_old_api_fails(self):
        for i in range(200):
            e = mod.generate(f"ex62-{i}", make_concept(), ["x = 1"], {})
            if e["payload"]["old"]:
                break
        mixed = answer_for(e) + "\n" + old_for(e)
        r = mod.grade(e, mixed)
        self.assertFalse(r["pass"])
        self.assertEqual(r["score"], 0.0)

    def test_empty_and_garbage_fail_closed(self):
        e = mod.generate("ex62", make_concept(), ["x = 1"], {})
        for bad in ["", "   ", "drop table; --", "lorem ipsum dolor"]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"], repr(bad))

    def test_hostile_never_raises(self):
        e = mod.generate("ex62", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [({}, "x"), (e, None), (None, None),
                                ({"payload": {}}, "x"),
                                ({"payload": {"new": []}}, "x")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex62", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("name='answer'", body)
        self.assertIn("How grading works", body)
        self.assertIn("no sandbox", body)
        self.assertIn("deploy.py:3", body)

    def test_render_escapes(self):
        e = mod.generate("ex62", make_concept(name="<b>"), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b10-depupgrade'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t, {"id": "dep-upgrade", "kind": "feature",
                             "title": "Dependency upgrade",
                             "blurb": "Migrate a caller across a breaking pin bump — new-API shape in, old shape out.",
                             "path": "/status", "anchor": "status-b10-depupgrade"})


if __name__ == "__main__":
    unittest.main()
