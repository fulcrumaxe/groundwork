"""Tests for the issue-repro exercise (type 44, F-21)."""
import unittest
from types import SimpleNamespace

from groundwork import repro as mod


CODE = "def ratio(a, b):\n    return a / b"
BUGGY = "def ratio(a, b):\n    return a // b"
REPRO = "assert ratio(1, 2) == 0.5"


def make_concept(name="ratio"):
    return SimpleNamespace(node_id="f", name=name, kind="function",
                           file="calc.py", line=1)


def make_ctx(**kw):
    ctx = {"buggy": BUGGY, "bug_line": 2, "fixed": CODE,
           "fault": "wrong operator"}
    ctx.update(kw)
    return ctx


def make_ex(**kw):
    payload = {"code": BUGGY, "func": "ratio", "bug_line": 2,
               "report": "Bug report", "fault": "wrong operator",
               "grounded": True, "max_lines": mod.MAX_LINES}
    payload.update(kw)
    return {"id": "x", "type": 44, "payload": payload}


class OktestRunner:
    """ok=True + clean output means the repro did NOT reproduce."""

    def __init__(self, ok=True, out="OK"):
        self.ok, self.out = ok, out

    def run(self, code):
        return SimpleNamespace(ok=self.ok, stdout=self.out, stderr="")


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex44", make_concept(), CODE.splitlines(), make_ctx())
        self.assertEqual(e["type"], 44)
        self.assertEqual(e["type_name"], "issue-repro")
        self.assertEqual(e["bloom"], "apply")
        self.assertTrue(e["front"])
        self.assertIn("Bug report", e["front"])

    def test_grounded_payload(self):
        e = mod.generate("ex44", make_concept(), CODE.splitlines(), make_ctx())
        p = e["payload"]
        self.assertTrue(p["grounded"])
        self.assertEqual(p["func"], "ratio")
        self.assertEqual(p["bug_line"], 2)
        self.assertIn("ratio", p["report"])

    def test_no_buggy_fallback(self):
        e = mod.generate("ex44", make_concept(), CODE.splitlines(),
                         {"runnable": CODE})
        self.assertFalse(e["payload"]["grounded"])
        self.assertTrue(e["front"])
        self.assertTrue(e["back"])

    def test_tolerates_suite_ctx(self):
        ctx = make_ctx(**{"runnable": CODE, "expected_output": "2",
                          "tests": "x", "trace_var": "total",
                          "trace_expected": ["2"], "graph": None})
        e = mod.generate("ex44", make_concept(), CODE.splitlines(), ctx)
        self.assertTrue(e["front"])


class GradeTest(unittest.TestCase):
    def test_accept_failing_run(self):
        self.assertTrue(mod.grade(make_ex(), REPRO, OktestRunner(ok=False))["pass"])

    def test_accept_fail_marker(self):
        r = mod.grade(make_ex(), REPRO, OktestRunner(ok=True, out="FAIL: 0 != 0.5"))
        self.assertTrue(r["pass"])

    def test_reject_clean_run(self):
        self.assertFalse(mod.grade(make_ex(), REPRO, OktestRunner(ok=True, out="OK"))["pass"])

    def test_runner_none_fails(self):
        self.assertFalse(mod.grade(make_ex(), REPRO, None)["pass"])

    def test_runner_error_fails(self):
        class Boom:
            def run(self, code):
                raise RuntimeError("down")
        self.assertFalse(mod.grade(make_ex(), REPRO, Boom())["pass"])

    def test_reject_blank(self):
        self.assertFalse(mod.grade(make_ex(), "   ", OktestRunner(ok=False))["pass"])

    def test_reject_unparseable(self):
        r = mod.grade(make_ex(), "assert ratio(((", OktestRunner(ok=False))
        self.assertFalse(r["pass"])

    def test_reject_bare_crash(self):
        self.assertFalse(mod.grade(make_ex(), "1/0", OktestRunner(ok=False))["pass"])

    def test_reject_bare_raise(self):
        self.assertFalse(mod.grade(make_ex(), "raise SystemExit(1)",
                                   OktestRunner(ok=False))["pass"])

    def test_reject_mention_without_call(self):
        # Names ratio only in a comment: no call, no proof.
        sub = "assert False  # ratio is broken"
        self.assertFalse(mod.grade(make_ex(), sub, OktestRunner(ok=False))["pass"])

    def test_reject_substring_without_call(self):
        # "operation" merely contains the letters r-a-t-i-o.
        sub = "x = operation_ratio = 1\nassert False"
        r = mod.grade(make_ex(), sub, OktestRunner(ok=False))
        self.assertFalse(r["pass"])

    def test_reject_overlong(self):
        big = "\n".join(f"assert ratio({i}, 2)" for i in range(mod.MAX_LINES + 1))
        r = mod.grade(make_ex(), big, OktestRunner(ok=False))
        self.assertFalse(r["pass"])
        self.assertIn("minimal", r["feedback"])

    def test_never_raises(self):
        for ex, sub in [(None, None), ({}, ""), ({"payload": None}, None),
                        (make_ex(), None), ({"payload": {"max_lines": "x"}}, REPRO)]:
            got = mod.grade(ex, sub, OktestRunner(ok=False))
            self.assertIn("pass", got)


class GuardTest(unittest.TestCase):
    def test_emits_only_with_buggy(self):
        self.assertTrue(mod.emits(make_ctx()))
        self.assertFalse(mod.emits({"runnable": CODE}))
        self.assertFalse(mod.emits({}))
        self.assertFalse(mod.emits(None))


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex44", make_concept(), CODE.splitlines(), make_ctx())
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("assert ratio(", body)
        self.assertIn("How grading works", body)
        self.assertIn("calc.py:1", body)

    def test_render_escapes(self):
        # report is not rendered; front/concept/hints are the escape surface.
        e = make_ex()
        e.update({"front": "<img src=x onerror=alert(1)>", "concept": "<c>",
                  "type_name": "issue-repro", "file": "f",
                  "line": 1, "hints": ["<h>script</h>"]})
        body = mod.render(e)
        self.assertNotIn("<img", body)
        self.assertIn("&lt;img", body)
        self.assertIn("&lt;h&gt;script", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b8-repro'", mod.section_html())


if __name__ == "__main__":
    unittest.main()
