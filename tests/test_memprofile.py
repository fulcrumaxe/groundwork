"""Tests for the memory-profile reading exercise (type 36, F-13)."""
import unittest
from types import SimpleNamespace

from groundwork import memprofile as mod


def make_concept(name="build", file="calc.py", line=1):
    return SimpleNamespace(node_id="f", name=name, kind="function",
                           file=file, line=line)


CODE = ["def build(n):",
        "    xs = [i * i for i in range(n)]",
        "    total = sum(xs)",
        "    return total"]


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex36", make_concept(), CODE, {})
        self.assertEqual(e["type"], 36)
        self.assertEqual(e["type_name"], "memory-profile")
        self.assertEqual(e["bloom"], "analyse")
        self.assertTrue(e["front"])

    def test_snapshot_consistent_with_snippet(self):
        e = mod.generate("ex36", make_concept(), CODE, {})
        snap = e["payload"]["snapshot"]
        self.assertTrue(2 <= len(snap) <= 6)
        top = snap[0]
        self.assertEqual(e["payload"]["answer"], f"calc.py:{top['line']}")
        self.assertEqual(e["payload"]["top_lineno"], top["line"])
        # Self-consistent ranking: top row strictly biggest.
        self.assertTrue(all(top["kb"] > r["kb"] for r in snap[1:]))
        # Every frame names the concept function and a snippet line.
        codes = [c.strip() for c in CODE if c.strip()]
        for r in snap:
            self.assertIn("build", r["frame"])
            self.assertIn(r["code"], [c[:80] for c in codes])
        self.assertIn(e["payload"]["answer"], e["back"])

    def test_deterministic_top(self):
        a = mod.generate("ex36", make_concept(), CODE, {})
        b = mod.generate("ex36", make_concept(), CODE, {})
        self.assertEqual(a["payload"]["answer"], b["payload"]["answer"])

    def test_tolerates_suite_ctx(self):
        ctx = {"runnable": "\n".join(CODE), "expected_output": "5",
               "tests": "x", "trace_var": "total", "trace_expected": ["2"],
               "buggy": "b", "bug_line": 2, "fixed": "f", "graph": None}
        e = mod.generate("ex36", make_concept(), CODE, ctx)
        self.assertTrue(e["front"])
        self.assertEqual(len(e["hints"]), 3)

    def test_empty_snippet_builds(self):
        e = mod.generate("ex36", make_concept(), [], {})
        self.assertTrue(e["payload"]["answer"])
        self.assertTrue(e["front"])


def fresh(ex_id="ex36", code=CODE):
    return mod.generate(ex_id, make_concept(), code, {})


def grade_ok(sub, ex_id="ex36", code=CODE):
    e = fresh(ex_id, code)
    return mod.grade(e, sub), e


class GradeTest(unittest.TestCase):
    def test_accept_exact(self):
        e = fresh()
        r = mod.grade(e, e["payload"]["answer"])
        self.assertTrue(r["pass"])
        self.assertEqual(r["score"], 1.0)

    def test_accept_normalized(self):
        e = fresh()
        r = mod.grade(e, "  `" + e["payload"]["answer"].upper() + "`  ")
        self.assertTrue(r["pass"])

    def test_accept_bare_top_lineno(self):
        e = fresh()
        r = mod.grade(e, str(e["payload"]["top_lineno"]))
        self.assertTrue(r["pass"])

    def test_reject_near_miss_second_row(self):
        e = fresh()
        snap = e["payload"]["snapshot"]
        second = next(s for s in snap
                      if s["line"] != e["payload"]["top_lineno"])
        bad = f"calc.py:{second['line']}"
        self.assertFalse(mod.grade(e, bad)["pass"])

    def test_reject_wrong_file(self):
        e = fresh()
        bad = "other.py:%d" % e["payload"]["top_lineno"]
        if bad.lower() != e["payload"]["answer"].lower():
            self.assertFalse(mod.grade(e, bad)["pass"])

    def test_reject_blank(self):
        self.assertFalse(grade_ok("   ")[0]["pass"])

    def test_no_runner_needed(self):
        e = mod.generate("ex36", make_concept(), CODE, {})
        self.assertTrue(
            mod.grade(e, e["payload"]["answer"], None)["pass"])

    def test_never_raises(self):
        e = mod.generate("ex36", make_concept(), CODE, {})
        for bad_ex, bad_sub in [(None, "calc.py:2"), ({}, "calc.py:2"),
                                ({"payload": {}}, "calc.py:2"),
                                (e, None), (e, 12345)]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertIn("pass", r)
            self.assertIn("score", r)
            self.assertIn("feedback", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget_and_escaping(self):
        evil = ["def build(n):",
                "    xs = <script>alert(1)</script> + [i for i in range(n)]",
                "    return xs"]
        e = mod.generate("ex36", make_concept(), evil, {})
        body = mod.render(e)
        self.assertIn("<table>", body)
        self.assertIn("name='answer'", body)
        self.assertIn("calc.py:1", body)
        self.assertNotIn("<script>alert(1)</script>", body)
        self.assertIn("&lt;script&gt;", body)

    def test_render_never_raises(self):
        self.assertIn("article", mod.render({}))

    def test_status_anchor(self):
        self.assertIn("id='status-b7-memprofile'", mod.section_html())


if __name__ == "__main__":
    unittest.main()
