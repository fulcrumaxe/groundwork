"""Tests for the rollback-plan exercise (type 48, F-25)."""
import unittest
from types import SimpleNamespace

from groundwork import rollback as mod


def make_concept(name="checkout"):
    return SimpleNamespace(node_id="c", name=name, kind="service",
                           file="deploy.py", line=3)


GENERIC_CTX = {"runnable": "x", "expected_output": "x", "tests": "x",
               "trace_var": "total", "trace_expected": ["2"],
               "buggy": "b", "bug_line": 2, "fixed": "f", "graph": None}


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex48", make_concept(), ["x"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (48, "rollback-plan", "evaluate"))
        self.assertTrue(e["front"])

    def test_payload_grounded(self):
        e = mod.generate("ex48", make_concept(), ["x"], {})
        p = e["payload"]
        self.assertTrue(p["grounded"])
        self.assertEqual(len(p["steps"]), 5)
        self.assertEqual(sorted(p["order"]), [0, 1, 2, 3, 4])
        self.assertIn("checkout", " ".join(p["solution"]))

    def test_fallback_never_raises(self):
        e = mod.generate("ex48", None, None, None)
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_tolerates_suite_ctx(self):
        e = mod.generate("ex48", make_concept(), ["x"], GENERIC_CTX)
        self.assertTrue(e["front"])


def answer_for(e):
    return " ".join(str(i + 1) for i in e["payload"]["order"])


class GradeTest(unittest.TestCase):
    def test_exact_accept(self):
        e = mod.generate("ex48", make_concept(), ["x"], {})
        r = mod.grade(e, answer_for(e))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_swapped_reject_partial(self):
        e = mod.generate("ex48", make_concept(), ["x"], {})
        o = e["payload"]["order"]
        bad = [o[1], o[0]] + o[2:]
        r = mod.grade(e, " ".join(str(i + 1) for i in bad))
        self.assertFalse(r["pass"])
        self.assertGreater(r["score"], 0.0)
        self.assertLess(r["score"], 1.0)

    def test_hostile_never_raises(self):
        e = mod.generate("ex48", make_concept(), ["x"], {})
        for bad_ex, bad_sub in [({}, "1 2 3 4 5"), (e, None), (e, ""),
                                (e, "drop table; --"), (e, "1 1 1 1 1"),
                                (None, None), ({"payload": {}}, "1 2")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex48", make_concept(), ["x"], {})
        body = mod.render(e)
        self.assertIn("<ol>", body)
        self.assertIn("name='answer'", body)
        self.assertIn("How grading works", body)
        self.assertIn("deploy.py:3", body)

    def test_render_escapes(self):
        e = mod.generate("ex48", make_concept(name="<b>"), ["x"], {})
        body = mod.render(e)
        # Concept text is escaped; the only literal <b> is step numbering.
        self.assertIn("&lt;b&gt;", body)
        self.assertNotIn("`<b>`", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b8-rollback'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "rollback-type")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["anchor"], "status-b8-rollback")


if __name__ == "__main__":
    unittest.main()
