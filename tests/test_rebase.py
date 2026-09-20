"""Tests for the rebase-resolve exercise (type 46, F-23)."""
import ast
import unittest
from types import SimpleNamespace

from groundwork import rebase as mod


def make_concept(name="total"):
    return SimpleNamespace(node_id="t", name=name, kind="function",
                           file="calc.py", line=1)


CODE = "def total(a, b):\n    s = a + b\n    return s"


def make_ex(**kw):
    e = mod.generate("ex46", make_concept(), CODE.splitlines(), {})
    if kw:
        e["payload"].update(kw)
    return e


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = make_ex()
        self.assertEqual(e["type"], 46)
        self.assertEqual(e["type_name"], "rebase-resolve")
        self.assertEqual(e["bloom"], "modify")
        self.assertTrue(e["front"])

    def test_payload(self):
        e = make_ex()
        p = e["payload"]
        self.assertEqual(p["func"], "total")
        self.assertNotEqual(p["ours"], p["theirs"])
        for m in ("<<<<<<<", "=======", ">>>>>>>"):
            self.assertIn(m, p["conflicted"])
        self.assertNotIn("<<<<<<<", p["reference"])
        ast.parse(p["reference"])
        self.assertTrue(p["grounded"])

    def test_unparseable_snippet_fallback(self):
        e = mod.generate("ex46", make_concept(), ["not python (("], {})
        p = e["payload"]
        self.assertTrue(e["front"])
        self.assertIn("<<<<<<<", p["conflicted"])
        ast.parse(p["reference"])
        self.assertTrue(p["grounded"])

    def test_tolerates_suite_ctx(self):
        ctx = {"runnable": CODE, "expected_output": "x", "tests": "x",
               "trace_var": "total", "trace_expected": ["2"],
               "buggy": "b", "bug_line": 2, "fixed": "f", "graph": None}
        e = mod.generate("ex46", make_concept(), CODE.splitlines(), ctx)
        self.assertTrue(e["front"])


class GradeTest(unittest.TestCase):
    def test_accept_reference(self):
        e = make_ex()
        r = mod.grade(e, e["payload"]["reference"], None)
        self.assertTrue(r["pass"])
        self.assertEqual(r["score"], 1.0)

    def test_reject_markers_left(self):
        e = make_ex()
        r = mod.grade(e, e["payload"]["conflicted"])
        self.assertFalse(r["pass"])
        self.assertIn("<<<<<<<", r["feedback"])

    def test_reject_dropped_side_partial(self):
        e = make_ex()
        theirs = e["payload"]["theirs"][0].strip()
        ref = "\n".join(l for l in e["payload"]["reference"].splitlines()
                        if l.strip() != theirs)
        r = mod.grade(e, ref)
        self.assertFalse(r["pass"])
        self.assertGreater(r["score"], 0.0)
        self.assertLess(r["score"], 1.0)
        # Feedback names the dropped line in whitespace-normalized form.
        self.assertIn(" ".join(theirs.split()), r["feedback"])

    def test_reject_dropped_ours(self):
        e = make_ex()
        ours = e["payload"]["ours"][0].strip()
        ref = "\n".join(l for l in e["payload"]["reference"].splitlines()
                        if l.strip() != ours)
        self.assertFalse(mod.grade(e, ref)["pass"])

    def test_reject_unparseable(self):
        e = make_ex()
        r = mod.grade(e, "def total(:\n    ???")
        self.assertFalse(r["pass"])
        self.assertIn("parse", r["feedback"])

    def test_reject_blank(self):
        self.assertFalse(mod.grade(make_ex(), "   ")["pass"])

    def test_reject_wrong_name(self):
        e = make_ex()
        ref = e["payload"]["reference"].replace("def total", "def subtotal")
        self.assertFalse(mod.grade(e, ref)["pass"])

    def test_hostile(self):
        e = make_ex()
        for bad in [None, "<<<<<<< x", "x" * 10000, 12345,
                    "def total(a, b):\n    import os; os.system('x')"]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)
        for bad_ex in [{}, None, {"payload": {}}]:
            r = mod.grade(bad_ex, e["payload"]["reference"])
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = make_ex()
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("<pre>", body)
        # Render escapes the markers (siblings escape all user text).
        self.assertIn("&lt;&lt;&lt;&lt;&lt;&lt;&lt;", body)
        self.assertNotIn("<<<<<<<", body)
        self.assertIn("How grading works", body)
        self.assertIn("calc.py:1", body)

    def test_render_escapes(self):
        e = mod.generate("ex46", make_concept(name="<b>"), CODE.splitlines(), {})
        body = mod.render(e)
        self.assertNotIn("<b>", body)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b8-rebase'", mod.section_html())

    def test_tour_entry_shape(self):
        t = mod.tour_entry()
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["path"], "/status")
        self.assertEqual(t["anchor"], "status-b8-rebase")


if __name__ == "__main__":
    unittest.main()
