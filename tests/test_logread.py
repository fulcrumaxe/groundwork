"""Tests for the log-reading exercise (type 58, F-35)."""
import unittest
from types import SimpleNamespace

from groundwork import logread as mod


def make_concept(name="checkout"):
    return SimpleNamespace(node_id="c", name=name, kind="service",
                           file="deploy.py", line=3)


def fixture_ctx():
    # Mirrors tests/test_groundwork.py test_all_types_generate: generate()
    # must return a real card with truthy front here, never None.
    from groundwork import graph as graphmod
    return {"runnable": "def add(a=2, b=3):\n    return a + b",
            "expected_output": "5",
            "tests": "_out = repr(add())\nassert _out == '5'\nprint('OK')",
            "trace_var": "total", "trace_expected": ["2", "5"],
            "buggy": "def add(a=2, b=3):\n    return a - b", "bug_line": 2,
            "fixed": "def add(a=2, b=3):\n    return a + b",
            "graph": graphmod.Graph()}


def answer_for(e):
    return e["payload"]["cause"]


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex58", make_concept(),
                         ["x = 1"], fixture_ctx())
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (58, "log-reading", "analyse"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_fixture_ctx_never_none(self):
        e = mod.generate("ex58", make_concept(),
                         ["def add(a=2, b=3):",
                          "    total = a + b",
                          "    return total"],
                         fixture_ctx())
        self.assertIsNotNone(e)
        self.assertTrue(e["front"])

    def test_grounded_on_error_snippet(self):
        e = mod.generate("ex58", make_concept(),
                         ["connect failed: connection refused on db:5432"],
                         {})
        self.assertEqual(e["payload"]["mode"], "grounded")
        self.assertEqual(e["payload"]["cause"],
                         "database connection refused")

    def test_synthesized_is_deterministic(self):
        a = mod.generate("ex58", make_concept(), ["x = 1"], {})
        b = mod.generate("ex58", make_concept(), ["x = 1"], {})
        self.assertEqual(a["payload"]["mode"], "synthesized")
        self.assertEqual(a["payload"]["cause"], b["payload"]["cause"])
        self.assertEqual(a["payload"]["log"], b["payload"]["log"])

    def test_log_has_cause_and_herrings(self):
        e = mod.generate("ex58", make_concept(), ["x = 1"], {})
        self.assertIn("FATAL", e["payload"]["log"])
        self.assertEqual(len(e["payload"]["herrings"]), 2)
        self.assertEqual(len(e["payload"]["choices"]), 6)

    def test_never_raises(self):
        for ex_id, concept, snippet, ctx in [
                (None, None, None, None), ("", None, [], {}),
                ("x", "not-a-namespace", [None, 1], "nope")]:
            try:
                mod.generate(ex_id, concept, snippet, ctx)
            except Exception as exc:  # noqa: BLE001
                self.fail(f"generate raised {exc!r}")


class GradeTest(unittest.TestCase):
    def test_exact_accept(self):
        e = mod.generate("ex58", make_concept(), ["x = 1"], {})
        r = mod.grade(e, answer_for(e))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_normalization_accepts_alias_case_quotes(self):
        e = mod.generate("ex58", make_concept(),
                         ["write failed: No space left on device"], {})
        self.assertEqual(e["payload"]["cause"], "disk full")
        for good in ("disk full", "  DISK FULL. ", '"disk full"',
                     "cause: disk full", "no space left", "ENOSPC"):
            self.assertTrue(mod.grade(e, good)["pass"], good)

    def test_red_herring_must_not_pass(self):
        e = mod.generate("ex58", make_concept(), ["x = 1"], {})
        for herring in e["payload"]["herrings"]:
            self.assertFalse(mod.grade(e, herring)["pass"], herring)
        # A WARN label naming no cause fails too.
        self.assertFalse(mod.grade(e, "deprecated v1 endpoint")["pass"])

    def test_wrong_cause_and_dump_must_not_pass(self):
        e = mod.generate("ex58", make_concept(), ["x = 1"], {})
        others = [c for c in e["payload"]["choices"]
                  if c != e["payload"]["cause"]]
        self.assertFalse(mod.grade(e, others[0])["pass"])
        self.assertFalse(mod.grade(e, e["payload"]["log"])["pass"])
        self.assertFalse(
            mod.grade(e, f"{e['payload']['cause']} plus extra words")["pass"])

    def test_empty_garbage_fail_closed(self):
        e = mod.generate("ex58", make_concept(), ["x = 1"], {})
        for bad in ("", "   ", "drop table; --", "???"):
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"], repr(bad))

    def test_hostile_never_raises(self):
        e = mod.generate("ex58", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [({}, "x"), (e, None), (None, None),
                                ({"payload": {}}, "disk full"),
                                ({"payload": {"cause": "nope"}}, "nope")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex58", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("name='answer'", body)
        self.assertIn("How grading works", body)
        self.assertIn("deploy.py:3", body)

    def test_render_escapes(self):
        e = mod.generate("ex58", make_concept(name="<b>"), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b10-logread'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t, {"id": "log-reading", "kind": "feature",
                             "title": "Log reading",
                             "blurb": "Diagnose an outage from logs alone — name the exact root cause, not a red herring.",
                             "path": "/status",
                             "anchor": "status-b10-logread"})


if __name__ == "__main__":
    unittest.main()
