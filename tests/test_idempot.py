"""Tests for the idempotency double-run exercise (type 70, F-47)."""
import unittest
from types import SimpleNamespace

from groundwork import idempot as mod


def make_concept(name="charge"):
    return SimpleNamespace(node_id="c", name=name, kind="handler",
                           file="handlers.py", line=9)


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


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex70", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (70, "idempotency-fix", "modify"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_fixture_ctx_card(self):
        e = mod.generate("ex70", make_concept(), ["x = 1"], fixture_ctx())
        self.assertTrue(e["front"])

    def test_key_deterministic(self):
        a = mod.generate("ex70", make_concept(), ["x = 1"], {})
        b = mod.generate("ex70", make_concept(), ["x = 1"], {})
        self.assertEqual(a["payload"]["key"], b["payload"]["key"])
        self.assertTrue(a["payload"]["key"].startswith("evt-"))

    def test_never_none_never_raises(self):
        for args in [(None, None, None, None), ("ex70", None, [], {})]:
            e = mod.generate(*args)
            self.assertIsNotNone(e)
            self.assertFalse(e["payload"]["grounded"])
            self.assertTrue(e["front"])


class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.generate("ex70", make_concept(), ["x = 1"], {})
        handler = e["payload"]["handler"]
        for ans in mod.E2E:
            named = ans.replace("def handle(", f"def {handler}(", 1)
            r = mod.grade(e, named)
            self.assertTrue(r["pass"] and r["score"] == 1.0, named)

    def test_starter_fails(self):
        e = mod.generate("ex70", make_concept(), ["x = 1"], {})
        r = mod.grade(e, e["payload"]["starter"])
        self.assertFalse(r["pass"])

    def test_noop_fails(self):
        e = mod.generate("ex70", make_concept(), ["x = 1"], {})
        func = e["payload"]["handler"]
        r = mod.grade(e, f"def {func}(store, event, emit):\n    pass\n")
        self.assertFalse(r["pass"])

    def test_constant_fails(self):
        e = mod.generate("ex70", make_concept(), ["x = 1"], {})
        func = e["payload"]["handler"]
        r = mod.grade(e, f"def {func}(store, event, emit):\n"
                         "    store[\"x\"] = 1\n")
        self.assertFalse(r["pass"])

    def test_unconditional_append_fails(self):
        e = mod.generate("ex70", make_concept(), ["x = 1"], {})
        func = e["payload"]["handler"]
        bad = (f"def {func}(store, event, emit):\n"
               "    store.setdefault(\"log\", []).append(event[\"item\"])\n"
               "    emit(\"charged\")\n")
        self.assertFalse(mod.grade(e, bad)["pass"])

    def test_no_partial_credit(self):
        e = mod.generate("ex70", make_concept(), ["x = 1"], {})
        func = e["payload"]["handler"]
        bad = (f"def {func}(store, event, emit):\n"
               "    store.setdefault(\"log\", []).append(event[\"item\"])\n")
        r = mod.grade(e, bad)
        self.assertFalse(r["pass"])
        self.assertEqual(r["score"], 0.0)

    def test_empty_and_garbage_fail_closed(self):
        e = mod.generate("ex70", make_concept(), ["x = 1"], {})
        for bad in ["", "   ", "hello world", None, "def broken(:"]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertEqual(r["score"], 0.0)

    def test_hostile_never_raises(self):
        e = mod.generate("ex70", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [({}, "x"), (e, None),
                                ({"payload": {}}, "def f(): pass"),
                                (None, None)]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex70", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("How grading works", body)
        self.assertIn("handlers.py:9", body)
        self.assertIn("def charge(store", body)

    def test_render_escapes(self):
        e = mod.generate("ex70", make_concept(name="<b>"), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b11-idempot'", mod.section_html())

    def test_tour_entry(self):
        self.assertEqual(mod.tour_entry(),
                         {"id": "idempotency-double-run", "kind": "feature",
                          "title": "Idempotency double-run",
                          "blurb": "Make the handler re-runnable — the grader runs it twice and both runs must agree.",
                          "path": "/status", "anchor": "status-b11-idempot"})


if __name__ == "__main__":
    unittest.main()
