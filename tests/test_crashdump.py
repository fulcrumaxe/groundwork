"""Tests for the crash-triage exercise (type 61, F-38)."""
import unittest
from types import SimpleNamespace

from groundwork import crashdump as mod


def make_concept(name="add"):
    return SimpleNamespace(node_id="c", name=name, kind="function",
                           file="calc.py", line=1)


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
    p = e["payload"]
    return f"frame={p['crash_frame']}\nfix={p['fix']}"


def decoy_for(e):
    p = e["payload"]
    return next(f[0] for f in p["frames"] if f[0] != p["crash_frame"])


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex61", make_concept(), ["x = 1"], fixture_ctx())
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (61, "crash-triage", "analyse"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_traceback_shape(self):
        e = mod.generate("ex61", make_concept(), ["x = 1"], fixture_ctx())
        p = e["payload"]
        self.assertIn("Traceback (most recent call last):", p["traceback"])
        self.assertIn(p["error"], p["traceback"])
        self.assertIn(p["crash_frame"], p["traceback"])
        self.assertGreaterEqual(len(p["frames"]), 3)
        self.assertLessEqual(len(p["frames"]), 5)
        self.assertIn(p["fix"], mod.FIXES)

    def test_deterministic(self):
        a = mod.generate("ex61", make_concept(), ["x = 1"], fixture_ctx())
        b = mod.generate("ex61", make_concept(), ["x = 1"], fixture_ctx())
        self.assertEqual(a["payload"], b["payload"])
        self.assertEqual(a["front"], b["front"])

    def test_never_none_never_raises(self):
        # Always plantable: even hostile inputs yield a real card.
        for args in [(None, None, None, None),
                     ("ex61", None, [], {}),
                     ("ex61", make_concept(), None, None)]:
            e = mod.generate(*args)
            self.assertIsNotNone(e)
            self.assertTrue(e["front"])


class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.generate("ex61", make_concept(), ["x = 1"], fixture_ctx())
        r = mod.grade(e, answer_for(e))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_answer_shapes_accepted(self):
        e = mod.generate("ex61", make_concept(), ["x = 1"], fixture_ctx())
        p = e["payload"]
        variants = [
            f"{p['crash_frame']}\n{p['fix']}",
            f"{p['crash_frame']}, {p['fix']}",
            f"  '{p['crash_frame']}'  \n  \"{p['fix']}\"  ",
            f"FRAME: {p['crash_frame'].upper()}\nFIX: {p['fix']}",
        ]
        for v in variants:
            r = mod.grade(e, v)
            self.assertTrue(r["pass"], v)

    def test_decoy_frame_fails(self):
        e = mod.generate("ex61", make_concept(), ["x = 1"], fixture_ctx())
        r = mod.grade(e, f"{decoy_for(e)}\n{e['payload']['fix']}")
        self.assertFalse(r["pass"])

    def test_wrong_fix_fails(self):
        e = mod.generate("ex61", make_concept(), ["x = 1"], fixture_ctx())
        other = next(f for f in mod.FIXES if f != e["payload"]["fix"])
        r = mod.grade(e, f"{e['payload']['crash_frame']}\n{other}")
        self.assertFalse(r["pass"])

    def test_frame_only_fails(self):
        e = mod.generate("ex61", make_concept(), ["x = 1"], fixture_ctx())
        self.assertFalse(mod.grade(e, e["payload"]["crash_frame"])["pass"])

    def test_dump_never_passes(self):
        # Pasting the whole traceback (which contains the frame name inside
        # `File ... in <frame>` lines plus the error) never isolates it.
        e = mod.generate("ex61", make_concept(), ["x = 1"], fixture_ctx())
        for bad in [e["payload"]["traceback"], e["front"],
                    e["payload"]["error"]]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"], bad[:60])

    def test_hostile_never_raises(self):
        e = mod.generate("ex61", make_concept(), ["x = 1"], fixture_ctx())
        for bad_ex, bad_sub in [({}, "x"), (e, None), (e, ""),
                                (e, "drop table; --"), (None, None),
                                ({"payload": {}}, "1"),
                                (e, "frame=\nfix=")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex61", make_concept(), ["x = 1"], fixture_ctx())
        body = mod.render(e)
        self.assertIn("name='answer'", body)
        self.assertIn("How grading works", body)
        self.assertIn("calc.py:1", body)

    def test_render_escapes(self):
        e = mod.generate("ex61", make_concept(name="<b>"), ["x = 1"],
                         fixture_ctx())
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b10-crashdump'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "crash-triage")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["anchor"], "status-b10-crashdump")


if __name__ == "__main__":
    unittest.main()
