"""Tests for the metrics-reading exercise (type 59, F-36)."""
import unittest
from types import SimpleNamespace

from groundwork import metrics as mod


def make_concept(name="checkout"):
    return SimpleNamespace(node_id="c", name=name, kind="service",
                           file="deploy.py", line=3)


def fixture_ctx():
    return {"runnable": "def add(a=2, b=3):\n    return a + b",
            "expected_output": "5",
            "tests": "_out = repr(add())\nassert _out == '5'\nprint('OK')",
            "trace_var": "total", "trace_expected": ["2", "5"],
            "buggy": "def add(a=2, b=3):\n    return a - b", "bug_line": 2,
            "fixed": "def add(a=2, b=3):\n    return a + b",
            "graph": None}


def answer_for(e):
    return e["payload"]["answer"]


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex59", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (59, "metrics-reading", "analyse"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_fixture_ctx_never_none(self):
        # test_all_types_generate contract: real card, truthy front.
        c = SimpleNamespace(node_id="f", name="add", kind="function",
                            file="calc.py", line=1)
        e = mod.generate("ex59", c, ["def add(a=2, b=3):"], fixture_ctx())
        self.assertIsNotNone(e)
        self.assertTrue(e["front"])

    def test_deterministic(self):
        a = mod.generate("ex59", make_concept(), ["x = 1"], {})
        b = mod.generate("ex59", make_concept(), ["other"], {"commit": "z"})
        self.assertEqual(a["payload"]["answer"], b["payload"]["answer"])
        self.assertEqual(a["front"], b["front"])

    def test_exactly_one_regression(self):
        e = mod.generate("ex59", make_concept(), ["x = 1"], {})
        kinds = [g["kind"] for g in e["payload"]["graphs"]]
        self.assertEqual(sorted(kinds).count("regress"), 1)
        self.assertEqual(len(e["payload"]["graphs"]), 3)
        self.assertEqual(e["payload"]["choices"], ["A", "B", "C"])

    def test_regression_direction(self):
        for ex_id in ("a", "b", "c", "d", "e"):
            e = mod.generate(ex_id, make_concept(), [], {})
            for g in e["payload"]["graphs"]:
                if g["kind"] == "regress":
                    self.assertNotAlmostEqual(g["pre"], g["post"],
                                              delta=abs(g["pre"]) * 0.2)

    def test_never_raises(self):
        for args in [(None, None, None, None),
                     ("x", None, [], {}),
                     ("x", make_concept(), None, None)]:
            try:
                mod.generate(*args)
            except Exception as e:  # noqa: BLE001
                self.fail(f"generate raised on {args!r}: {e!r}")


class GradeTest(unittest.TestCase):
    def test_correct_letter_passes(self):
        e = mod.generate("ex59", make_concept(), ["x = 1"], {})
        r = mod.grade(e, answer_for(e))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_case_and_prefix_normalized(self):
        e = mod.generate("ex59", make_concept(), ["x = 1"], {})
        ans = answer_for(e)
        for variant in [ans.lower(), f"  {ans}  ", f"graph {ans.lower()}",
                        f"option {ans}", f"{ans}."]:
            self.assertTrue(mod.grade(e, variant)["pass"], variant)

    def test_distractor_letters_fail(self):
        e = mod.generate("ex59", make_concept(), ["x = 1"], {})
        for letter in ("A", "B", "C"):
            if letter != answer_for(e):
                self.assertFalse(mod.grade(e, letter)["pass"], letter)

    def test_dump_and_garbage_fail_closed(self):
        e = mod.generate("ex59", make_concept(), ["x = 1"], {})
        bad = [e["front"], "ABC", "all three", "D", "1", "",
               "graph A and graph B", "the latency one"]
        for sub in bad:
            if mod.normalize_letter(sub) == answer_for(e):
                continue  # a normalized hit is a real answer, not garbage
            self.assertFalse(mod.grade(e, sub)["pass"], repr(sub))

    def test_hostile_never_raises(self):
        e = mod.generate("ex59", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [({}, "A"), (e, None), (e, ""),
                                (e, "drop table; --"), (None, None),
                                ({"payload": {}}, "B"),
                                ({"payload": {"answer": "Z"}}, "Z")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex59", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn('type="radio"', body)
        self.assertIn('value="A"', body)
        self.assertIn("How grading works", body)
        self.assertIn("deploy.py:3", body)

    def test_render_escapes(self):
        e = mod.generate("ex59", make_concept(name="<b>"), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b10-metrics'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "metrics-reading")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["anchor"], "status-b10-metrics")


if __name__ == "__main__":
    unittest.main()
