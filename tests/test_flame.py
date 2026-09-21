"""Tests for the flame-graph reading exercise (type 60, F-37)."""
import unittest
from types import SimpleNamespace

from groundwork import flame as mod


def make_concept(name="checkout"):
    return SimpleNamespace(node_id="c", name=name, kind="service",
                           file="deploy.py", line=3)


def answer_for(e):
    return f"frame={e['payload']['dominant']}\nwhy={e['payload']['why']}"


FIXTURE_CTX = {"runnable": "def add(a=2, b=3):\n    return a + b",
               "expected_output": "5",
               "tests": "_out = repr(add())\nassert _out == '5'\nprint('OK')",
               "trace_var": "total", "trace_expected": ["2", "5"],
               "buggy": "def add(a=2, b=3):\n    return a - b", "bug_line": 2,
               "fixed": "def add(a=2, b=3):\n    return a + b"}


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex60", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (60, "flamegraph-reading", "analyse"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_fixture_ctx_never_none(self):
        # test_all_types_generate contract: real card, truthy front.
        c = SimpleNamespace(node_id="f", name="add", kind="function",
                            file="calc.py", line=1)
        e = mod.generate("ex60", c,
                         ["def add(a=2, b=3):", "    total = a + b",
                          "    return total"], dict(FIXTURE_CTX))
        self.assertIsNotNone(e)
        self.assertTrue(e["front"])

    def test_deterministic_and_single_dominant(self):
        a = mod.generate("ex60", make_concept(), ["x = 1"], {})
        b = mod.generate("ex60", make_concept(), ["x = 1"], {})
        self.assertEqual(a["payload"], b["payload"])
        shares = sorted((p for _, p in a["payload"]["frames"]),
                          reverse=True)
        self.assertEqual(sum(shares), 100)
        self.assertGreaterEqual(shares[0] - shares[1], 15)

    def test_five_frames_head_dominates_sweep(self):
        # The dominance contract must hold for every seed, not just
        # the fixture ex_id: five frames, exact 100, head strictly
        # dominant with a >= 15 gap and a >= 5 floor elsewhere.
        for i in range(300):
            frames, dominant = mod._frames(f"sweep-{i}", "checkout")
            self.assertEqual(len(frames), 5)
            names = [n for n, _ in frames]
            self.assertEqual(len(set(names)), 5)
            shares = sorted((p for _, p in frames), reverse=True)
            self.assertEqual(sum(shares), 100)
            self.assertGreaterEqual(shares[0] - shares[1], 15)
            self.assertGreaterEqual(shares[-1], 5)
            self.assertEqual(dominant, "checkout")
            self.assertEqual(frames[0][0], dominant)

    def test_no_name_returns_none(self):
        self.assertIsNone(mod.generate("ex60", None, [], {}))
        self.assertIsNone(mod.generate("ex60", None, None, None))

    def test_never_raises(self):
        self.assertIsNone(mod.generate(None, None, None, None))


class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.generate("ex60", make_concept(), ["x = 1"], {})
        r = mod.grade(e, answer_for(e))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_two_line_form_passes(self):
        e = mod.generate("ex60", make_concept(), ["x = 1"], {})
        d = e["payload"]["dominant"]
        r = mod.grade(e, f"{d}\nwidest")
        self.assertTrue(r["pass"])

    def test_frame_normalized(self):
        e = mod.generate("ex60", make_concept(), ["x = 1"], {})
        d = e["payload"]["dominant"]
        for variant in [f"frame=`{d}`\nwhy=widest",
                        f"frame=  {d.upper()}  \nwhy=Widest"]:
            self.assertTrue(mod.grade(e, variant)["pass"], variant)

    def test_non_dominant_frame_fails(self):
        e = mod.generate("ex60", make_concept(), ["x = 1"], {})
        others = [n for n, _ in e["payload"]["frames"]
                  if n != e["payload"]["dominant"]]
        self.assertTrue(others)
        r = mod.grade(e, f"frame={others[0]}\nwhy=widest")
        self.assertFalse(r["pass"])

    def test_wrong_why_fails_despite_right_frame(self):
        e = mod.generate("ex60", make_concept(), ["x = 1"], {})
        d = e["payload"]["dominant"]
        for bad in ("tallest", "leftmost", "fastest"):
            self.assertFalse(mod.grade(e, f"frame={d}\nwhy={bad}")["pass"], bad)

    def test_frame_alone_fails_closed(self):
        e = mod.generate("ex60", make_concept(), ["x = 1"], {})
        d = e["payload"]["dominant"]
        self.assertFalse(mod.grade(e, f"frame={d}")["pass"])
        self.assertFalse(mod.grade(e, d)["pass"])

    def test_dump_and_substring_must_not_pass(self):
        e = mod.generate("ex60", make_concept(), ["x = 1"], {})
        d = e["payload"]["dominant"]
        self.assertFalse(mod.grade(e, e["front"])["pass"])
        self.assertFalse(mod.grade(e, f"frame=xx{d}yy\nwhy=widest")["pass"])

    def test_hostile_never_raises(self):
        e = mod.generate("ex60", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [({}, "x"), (e, None), (e, ""),
                                (e, "drop table; --"), (None, None),
                                ({"payload": {}}, "1")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)

    def test_never_raises_fuzz(self):
        import random
        rng = random.Random(60)
        e = mod.generate("ex60", make_concept(), ["x = 1"], {})
        frames = [n for n, _ in e["payload"]["frames"]]
        for _ in range(50):
            sub = rng.choice([f"frame={rng.choice(frames)}\nwhy={rng.choice(['widest', 'tallest', 'leftmost', 'zzz'])}",
                              "garbage", "", "frame=\nwhy=", "1,2,3"])
            r = mod.grade(e, sub)
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex60", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("name='frame'", body)
        self.assertIn("name='why'", body)
        self.assertIn("How grading works", body)
        self.assertIn("deploy.py:3", body)

    def test_render_escapes(self):
        e = mod.generate("ex60", make_concept(name="<b>"), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b10-flame'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "flamegraph-reading")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["anchor"], "status-b10-flame")


if __name__ == "__main__":
    unittest.main()
