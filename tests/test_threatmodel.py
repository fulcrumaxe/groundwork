"""Tests for the threat-model exercise (type 49, F-26)."""
import unittest
from types import SimpleNamespace

from groundwork import threatmodel as mod


def make_concept(name="run_cmd"):
    return SimpleNamespace(node_id="c", name=name, kind="function",
                           file="ops.py", line=3)


EVIL = ("def run_cmd(user_input, user):\n"
        "    cmd = \"convert %s\" % user_input\n"
        "    os.system(cmd)\n"
        "    return cmd\n")

CLEAN = ("def add(a, b):\n"
         "    total = a + b\n"
         "    return total\n")

GENERIC_CTX = {"runnable": "x", "expected_output": "x", "tests": "x",
               "trace_var": "total", "trace_expected": ["2"],
               "buggy": "b", "bug_line": 2, "fixed": "f", "graph": None}


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex49", make_concept(), [EVIL], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (49, "threat-model", "analyse"))
        self.assertTrue(e["front"])

    def test_surface_derived(self):
        e = mod.generate("ex49", make_concept(), [EVIL], {})
        self.assertTrue(e["payload"]["grounded"])
        labels = " ".join(e["payload"]["items"]).lower()
        self.assertIn("command injection", labels)
        self.assertIn("unvalidated", labels)
        self.assertIn("authorization", labels)

    def test_no_surface_yields_ungrounded_card(self):
        # Never None (all-types-generate contract): no surface is an
        # ungrounded card the pipeline drops.
        for snippet in ([CLEAN], [""], None):
            e = mod.generate("ex49", make_concept(), snippet, {})
            self.assertTrue(e["front"])
            self.assertFalse(e["payload"]["grounded"])
            self.assertEqual(e["payload"]["items"], [])

    def test_never_raises_never_none(self):
        e = mod.generate("ex49", None, None, None)
        self.assertTrue(e["front"])
        self.assertFalse(e["payload"]["grounded"])
        e = mod.generate("ex49", make_concept(), ["def f(:\n  ???"], {})
        self.assertTrue(e["front"])

    def test_tolerates_suite_ctx(self):
        e = mod.generate("ex49", make_concept(), [EVIL], GENERIC_CTX)
        self.assertTrue(e["front"])

    def test_deterministic(self):
        a = mod.generate("ex49", make_concept(), [EVIL], {})
        b = mod.generate("ex49", make_concept(), [EVIL], {})
        self.assertEqual(a["payload"]["items"], b["payload"]["items"])


def answer_for(e):
    return "\n".join(e["payload"]["items"])


class GradeTest(unittest.TestCase):
    def test_exact_accept(self):
        e = mod.generate("ex49", make_concept(), [EVIL], {})
        r = mod.grade(e, answer_for(e))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_tolerant_accept(self):
        e = mod.generate("ex49", make_concept(), [EVIL], {})
        sub = "\n".join("  " + i.upper().replace(":", "") + "!!"
                        for i in e["payload"]["items"])
        r = mod.grade(e, sub)
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_partial_credit(self):
        e = mod.generate("ex49", make_concept(), [EVIL], {})
        self.assertGreaterEqual(len(e["payload"]["items"]), 2)
        r = mod.grade(e, e["payload"]["items"][0])
        self.assertGreater(r["score"], 0.0)
        self.assertLess(r["score"], 1.0)
        # EVIL yields 3 items; one of three is below the half bar.
        if len(e["payload"]["items"]) > 2:
            self.assertFalse(r["pass"])
        else:
            self.assertTrue(r["pass"])

    def test_hostile_never_raises(self):
        e = mod.generate("ex49", make_concept(), [EVIL], {})
        for bad_ex, bad_sub in [({}, "command injection"), (e, None),
                                (e, ""), (e, "drop table; --"),
                                (e, "the weather is nice"),
                                (None, None), ({"payload": {}}, "x")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)
            self.assertIn("feedback", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex49", make_concept(), [EVIL], {})
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("name='answer'", body)
        self.assertIn("How grading works", body)
        self.assertIn("ops.py:3", body)

    def test_render_escapes(self):
        e = mod.generate("ex49", make_concept(name="<b>"), [EVIL], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b9-threatmodel'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "threat-model")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["anchor"], "status-b9-threatmodel")


if __name__ == "__main__":
    unittest.main()
