"""Tests for the license-check exercise (type 63, F-40)."""
import unittest
from types import SimpleNamespace

from groundwork import licensecheck as mod


def make_concept(name="checkout"):
    return SimpleNamespace(node_id="c", name=name, kind="service",
                           file="deploy.py", line=3)


def fixture_ctx():
    from groundwork import graph as graphmod
    return {"runnable": "def add(a=2, b=3):\n    return a + b",
            "expected_output": "5",
            "tests": "_out = repr(add())\nassert _out == '5'\nprint('OK')",
            "trace_var": "total", "trace_expected": ["2", "5"],
            "buggy": "def add(a=2, b=3):\n    return a - b", "bug_line": 2,
            "fixed": "def add(a=2, b=3):\n    return a + b",
            "graph": graphmod.Graph()}


def answer_for(e):
    word = "OK" if e["payload"]["verdict"] == "ok" else "NOT-OK"
    return f"{word}\n{e['payload']['reason']}"


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex63", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (63, "license-check", "evaluate"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_fixture_ctx_yields_real_card(self):
        e = mod.generate("ex63", make_concept(), ["x = 1"], fixture_ctx())
        self.assertIsNotNone(e)
        self.assertTrue(e["front"])

    def test_deterministic_pick(self):
        a = mod.generate("ex63", make_concept(), ["x = 1"], {})
        b = mod.generate("ex63", make_concept(), ["x = 1"], {})
        self.assertEqual(a["payload"]["dep"], b["payload"]["dep"])
        self.assertEqual(a["payload"]["verdict"], b["payload"]["verdict"])

    def test_table_valid(self):
        self.assertGreaterEqual(len(mod.TABLE), 6)
        verdicts = {r[4] for r in mod.TABLE}
        self.assertEqual(verdicts, {"ok", "not-ok"})
        for row in mod.TABLE:
            self.assertIn(row[5], mod.REASONS)

    def test_never_raises_never_none(self):
        for args in [(None, None, None, None),
                     ("e", None, [], {}),
                     ("e", make_concept(), None, None)]:
            e = mod.generate(*args)
            self.assertIsNotNone(e)
            self.assertTrue(e["front"])


class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.generate("ex63", make_concept(), ["x = 1"], {})
        r = mod.grade(e, answer_for(e))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_reason_variants_accepted(self):
        e = mod.generate("ex63", make_concept(), ["x = 1"], {})
        v = "OK" if e["payload"]["verdict"] == "ok" else "NOT-OK"
        squashed = e["payload"]["reason"].replace("-", " ")
        r = mod.grade(e, f"{v.lower()} {squashed}")
        self.assertTrue(r["pass"])

    def test_flipped_verdict_fails(self):
        e = mod.generate("ex63", make_concept(), ["x = 1"], {})
        bad_v = "NOT-OK" if e["payload"]["verdict"] == "ok" else "OK"
        r = mod.grade(e, f"{bad_v}\n{e['payload']['reason']}")
        self.assertFalse(r["pass"])

    def test_wrong_reason_fails(self):
        e = mod.generate("ex63", make_concept(), ["x = 1"], {})
        other = next(r for r in mod.REASONS if r != e["payload"]["reason"])
        v = "OK" if e["payload"]["verdict"] == "ok" else "NOT-OK"
        self.assertFalse(mod.grade(e, f"{v}\n{other}")["pass"])

    def test_verdict_only_and_reason_only_fail(self):
        e = mod.generate("ex63", make_concept(), ["x = 1"], {})
        v = "OK" if e["payload"]["verdict"] == "ok" else "NOT-OK"
        self.assertFalse(mod.grade(e, v)["pass"])
        self.assertFalse(mod.grade(e, e["payload"]["reason"])["pass"])

    def test_empty_garbage_fail_closed(self):
        e = mod.generate("ex63", make_concept(), ["x = 1"], {})
        for bad in ["", "   ", "looks fine to me", "OK OK OK"]:
            self.assertFalse(mod.grade(e, bad)["pass"], bad)

    def test_hostile_never_raises(self):
        e = mod.generate("ex63", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [({}, "ok permissive"), (e, None),
                                (None, None), ({"payload": {}}, "ok")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex63", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("name='answer'", body)
        self.assertIn("How grading works", body)
        self.assertIn("AGPL-3.0", body)
        self.assertIn("deploy.py:3", body)
        for reason in mod.REASONS:
            self.assertIn(reason, body)

    def test_render_escapes(self):
        e = mod.generate("ex63", make_concept(name="<b>"), ["x = 1"], {})
        self.assertIn("&lt;b&gt;", mod.render(e))

    def test_status_anchor(self):
        self.assertIn("id='status-b10-licensecheck'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "license-check")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["anchor"], "status-b10-licensecheck")


if __name__ == "__main__":
    unittest.main()
