"""Tests for the bisect drill (type 45, F-22)."""
import unittest
from types import SimpleNamespace

from groundwork import bisect as mod


def make_concept(cid="c1", name="fetch_user"):
    return SimpleNamespace(node_id=cid, name=name, kind="function",
                           file="users.py", line=1)


SUITE_CTX = {"runnable": "x", "expected_output": "x", "tests": "x",
             "trace_var": "total", "trace_expected": ["2"],
             "buggy": "b", "bug_line": 2, "fixed": "f", "graph": None}


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex45", make_concept(), ["def f(): ..."], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]), (45, "bisect-drill", "analyse"))

    def test_payload_shape(self):
        e = mod.generate("ex45", make_concept(), [], {})
        p = e["payload"]
        self.assertEqual(len(p["commits"]), 6)
        results = [c["result"] for c in p["commits"]]
        b = p["breaking_index"]
        self.assertEqual(results, ["PASS"] * b + ["FAIL"] * (6 - b))
        self.assertGreaterEqual(b, 1)
        self.assertEqual(p["breaking_hash"], p["commits"][b]["hash"])

    def test_determinism(self):
        a = mod.generate("ex45", make_concept(), [], {})
        b = mod.generate("ex45", make_concept(), [], {})
        self.assertEqual(a["payload"], b["payload"])
        c = mod.generate("ex45", make_concept(cid="other"), [], {})
        self.assertNotEqual(a["payload"], c["payload"])

    def test_tolerates_suite_ctx(self):
        e = mod.generate("ex45", make_concept(), ["x"], SUITE_CTX)
        self.assertTrue(e["front"] and e["payload"]["commits"])


class GradeTest(unittest.TestCase):
    def _ex(self):
        return mod.generate("ex45", make_concept(), [], {})

    def test_accept_hash_and_index(self):
        e = self._ex()
        p = e["payload"]
        self.assertTrue(mod.grade(e, p["breaking_hash"])["pass"])
        self.assertTrue(mod.grade(e, p["breaking_hash"].upper())["pass"])
        self.assertTrue(mod.grade(e, str(p["breaking_index"]))["pass"])
        self.assertTrue(mod.grade(e, f"commit {p['breaking_hash']}")["pass"])

    def test_off_by_one_rejects(self):
        e = self._ex()
        b = e["payload"]["breaking_index"]
        for i in (b - 1, b + 1):
            if 0 <= i < 6:
                r = mod.grade(e, str(i))
                self.assertFalse(r["pass"])
                self.assertEqual(r["score"], 0.0)

    def test_fallback_card_has_no_answer(self):
        bad = {"id": "x", "type": 45,
               "payload": {"commits": [], "breaking_index": -1,
                           "breaking_hash": "", "grounded": True}}
        r = mod.grade(bad, "0")
        self.assertFalse(r["pass"])

    def test_hostile(self):
        e = self._ex()
        for bad in ["", "   ", None, "<script>", "PASS", "9999", "deadbeef",
                    {"hash": 1}, ["0"], "0; DROP TABLE cards"]:
            self.assertFalse(mod.grade(e, bad)["pass"])
        for bad_ex, bad_sub in [({}, "abc"), (None, None), ({"payload": {}}, "0")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex45", make_concept(), [], {})
        body = mod.render(e)
        self.assertIn("<table>", body)
        self.assertIn(e["payload"]["breaking_hash"], body)
        self.assertIn("How grading works", body)
        self.assertIn("users.py:1", body)

    def test_render_escapes(self):
        e = mod.generate("ex45", make_concept(name="<b>"), [], {})
        self.assertNotIn("<b>", mod.render(e))

    def test_status_anchor(self):
        self.assertIn("id='status-b8-bisect'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "bisect-type")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["anchor"], "status-b8-bisect")


if __name__ == "__main__":
    unittest.main()
