"""Tests for fuzz-target triage exercise (type 34, F-11)."""
import unittest
from types import SimpleNamespace

from groundwork import fuzztriage as mod


CODE = "def ratio(a, b):\n    return a / b"
BUGGY = "def ratio(a, b):\n    return a // b"
CRASH = "ratio(1, 0)"


def make_concept(name="ratio"):
    return SimpleNamespace(node_id="f", name=name, kind="function",
                           file="calc.py", line=1)


def make_ctx(**kw):
    ctx = {"buggy": BUGGY, "bug_line": 2, "fixed": CODE,
           "crash_call": CRASH, "fault": "b=0"}
    ctx.update(kw)
    return ctx


def make_ex(**kw):
    payload = {"code": BUGGY, "func": "ratio", "crash_call": CRASH,
               "reported": CRASH, "crash_line": 2, "fault": "b=0",
               "grounded": True}
    payload.update(kw)
    return {"id": "x", "type": 34, "payload": payload}


class FakeCrashRunner:
    """ok=False means the reference still crashes (card is live)."""

    def __init__(self, ok=False):
        self.ok = ok

    def run(self, code):
        return SimpleNamespace(ok=self.ok, stdout="", stderr="")


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex34", make_concept(), CODE.splitlines(),
                         make_ctx())
        self.assertEqual(e["type"], 34)
        self.assertEqual(e["type_name"], "fuzz-triage")
        self.assertEqual(e["bloom"], "analyse")
        self.assertTrue(e["front"])
        self.assertIn(CRASH, e["back"])

    def test_grounded_with_breaking_mutation(self):
        e = mod.generate("ex34", make_concept(), CODE.splitlines(),
                         make_ctx())
        self.assertTrue(e["payload"]["grounded"])
        self.assertEqual(e["payload"]["crash_call"], CRASH)
        self.assertEqual(e["payload"]["crash_line"], 2)

    def test_ungrounded_without_buggy(self):
        e = mod.generate("ex34", make_concept(), CODE.splitlines(),
                         {"runnable": CODE})
        self.assertFalse(e["payload"]["grounded"])
        self.assertTrue(e["front"])

    def test_tolerates_suite_ctx(self):
        # Same generic ctx test_groundwork uses for every type: must not raise.
        ctx = make_ctx(**{"runnable": CODE, "expected_output": "2",
                          "tests": "x", "trace_var": "total",
                          "trace_expected": ["2"], "graph": None})
        e = mod.generate("ex34", make_concept(), CODE.splitlines(), ctx)
        self.assertTrue(e["front"])


class GradeTest(unittest.TestCase):
    def test_accept_exact_repro_call(self):
        self.assertTrue(mod.grade(make_ex(), CRASH)["pass"])

    def test_accept_call_with_line(self):
        self.assertTrue(mod.grade(make_ex(), "ratio(1, 0) @ line 2")["pass"])

    def test_accept_crash_line_alone(self):
        self.assertTrue(mod.grade(make_ex(), "line 2")["pass"])

    def test_accept_whitespace_variants(self):
        self.assertTrue(mod.grade(make_ex(), "ratio( 1, 0 )")["pass"])

    def test_reject_wrong_call(self):
        self.assertFalse(mod.grade(make_ex(), "ratio(4, 2)")["pass"])

    def test_reject_wrong_line(self):
        self.assertFalse(mod.grade(make_ex(), "line 1")["pass"])

    def test_reject_blank(self):
        self.assertFalse(mod.grade(make_ex(), "   ")["pass"])

    def test_no_runner_needed(self):
        self.assertTrue(mod.grade(make_ex(), CRASH, None)["pass"])

    def test_live_crasher_confirmed(self):
        self.assertTrue(
            mod.grade(make_ex(), CRASH, FakeCrashRunner(ok=False))["pass"])

    def test_stale_when_reference_no_longer_crashes(self):
        got = mod.grade(make_ex(), CRASH, FakeCrashRunner(ok=True))
        self.assertFalse(got["pass"])
        self.assertIn("stale", got["feedback"])


class GuardTest(unittest.TestCase):
    def test_emits_only_with_buggy(self):
        self.assertTrue(mod.emits(make_ctx()))
        self.assertFalse(mod.emits({"runnable": CODE}))
        self.assertFalse(mod.emits({}))
        self.assertFalse(mod.emits(None))


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex34", make_concept(), CODE.splitlines(),
                         make_ctx())
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("ratio(1, 0)", body)
        self.assertIn("calc.py:1", body)

    def test_render_escapes(self):
        e = make_ex(**{"reported": "<img src=x>",
                       "code": "a<b", "crash_call": CRASH})
        e.update({"front": "<b>hi</b>", "concept": "<c>",
                  "type_name": "fuzz-triage", "file": "f",
                  "line": 1, "hints": ["<h>"]})
        body = mod.render(e)
        self.assertNotIn("<img src=x>", body)
        self.assertIn("&lt;img", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b7-fuzztriage'", mod.section_html())

    def test_never_raises(self):
        for ex, sub in [(None, None), ({}, ""), ({"payload": None}, None),
                        (make_ex(), None), ({"payload": {"crash_line": "x"}},
                         "???")]:
            got = mod.grade(ex, sub)
            self.assertIn("pass", got)


if __name__ == "__main__":
    unittest.main()
