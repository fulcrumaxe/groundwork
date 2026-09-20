"""Tests for the race-hunt exercise (type 37, F-14)."""
import unittest
from types import SimpleNamespace

from groundwork import racehunt as mod


def make_concept(name="record"):
    return SimpleNamespace(node_id="f", name=name, kind="function",
                           file="stats.py", line=3)


CODE = ("seen = []\n\ndef record(x):\n    global seen\n"
        "    seen.append(x)\n    return len(seen)")
# Line 4 (`global seen`) is the shared-state site.

CLEAN = "def add(a, b):\n    return a + b"


def make_exercise(code=CODE):
    return mod.generate("ex37", make_concept(), code.splitlines(), {})


def grade_ok(sub="4\nfix: copy it into a local", code=CODE):
    return mod.grade(make_exercise(code), sub)


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = make_exercise()
        self.assertEqual(e["type"], 37)
        self.assertEqual(e["type_name"], "race-hunt")
        self.assertEqual(e["bloom"], "analyse")
        self.assertTrue(e["front"])

    def test_grounded_global(self):
        e = make_exercise()
        self.assertTrue(e["payload"]["grounded"])
        self.assertEqual(e["payload"]["shared_line"], 4)
        self.assertEqual(e["payload"]["symbol"], "seen")
        self.assertIn("4: ", e["payload"]["numbered"])
        self.assertIn("4", e["back"])

    def test_ungrounded_clean_snippet(self):
        e = make_exercise(CLEAN)
        self.assertFalse(e["payload"]["grounded"])
        self.assertEqual(e["payload"]["shared_line"], 0)
        self.assertTrue(e["front"])

    def test_mutable_default_detected(self):
        code = "def push(x, items=[]):\n    items.append(x)\n    return items"
        e = make_exercise(code)
        self.assertTrue(e["payload"]["grounded"])
        self.assertEqual(e["payload"]["kind"], "mutable-default")

    def test_empty_snippet_still_builds(self):
        e = mod.generate("ex37", make_concept(), [], {})
        self.assertTrue(e["payload"]["grounded"])
        self.assertTrue(e["front"])
        self.assertEqual(len(e["hints"]), 3)

    def test_tolerates_suite_ctx(self):
        # Same generic ctx test_groundwork uses for every type: must not raise.
        ctx = {"runnable": CODE, "expected_output": "3",
               "tests": "x", "trace_var": "total", "trace_expected": ["2"],
               "buggy": "b", "bug_line": 2, "fixed": "f", "graph": None}
        e = mod.generate("ex37", make_concept(), CODE.splitlines(), ctx)
        self.assertTrue(e["front"])


class GradeTest(unittest.TestCase):
    def test_accept_line_and_fix(self):
        self.assertTrue(grade_ok()["pass"])

    def test_accept_lock_wording(self):
        self.assertTrue(grade_ok("line 4, guard it with a lock")["pass"])

    def test_accept_parameter_wording(self):
        self.assertTrue(grade_ok("4 — pass it as a parameter")["pass"])

    def test_accept_normalized_line_ref(self):
        self.assertTrue(grade_ok("L4: copy to a local")["pass"])

    def test_reject_wrong_line(self):
        result = grade_ok("5\nfix: local copy")
        self.assertFalse(result["pass"])
        self.assertIn("not the line", result["feedback"])

    def test_reject_missing_fix_keyword(self):
        result = grade_ok("4")
        self.assertFalse(result["pass"])
        self.assertIn("name the fix", result["feedback"])

    def test_reject_blank(self):
        self.assertFalse(grade_ok("   ")["pass"])

    def test_reject_no_line_number(self):
        result = grade_ok("the global state should be a local copy")
        self.assertFalse(result["pass"])

    def test_partial_credit_shape(self):
        self.assertEqual(grade_ok("5\nfix: local copy")["score"], 0.5)
        self.assertEqual(grade_ok("4")["score"], 0.5)

    def test_no_runner_needed(self):
        self.assertTrue(mod.grade(make_exercise(),
                                  "4\nfix: copy it into a local",
                                  None)["pass"])

    def test_ungrounded_card_fails_clean(self):
        result = mod.grade(make_exercise(CLEAN), "1\nfix: local copy")
        self.assertFalse(result["pass"])

    def test_never_raises(self):
        for exercise in (None, {}, {"payload": {}},
                         {"payload": {"shared_line": "zzz"}}):
            for submission in (None, "", "zzz", "4 fix copy"):
                result = mod.grade(exercise, submission, None)
                self.assertIn("pass", result)
                self.assertIn("score", result)
                self.assertIn("feedback", result)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        body = mod.render(make_exercise())
        self.assertIn("<textarea", body)
        self.assertIn("line:", body)
        self.assertIn("4: ", body)
        self.assertIn("stats.py:3", body)

    def test_render_escapes(self):
        concept = make_concept("<script>alert(1)</script>")
        body = mod.render(mod.generate("ex37", concept,
                                       CODE.splitlines(), {}))
        self.assertNotIn("<script>", body)
        self.assertIn("&lt;script&gt;", body)

    def test_render_tolerates_empty(self):
        self.assertIn("<textarea", mod.render({}))

    def test_status_anchor(self):
        self.assertIn("id='status-b7-racehunt'", mod.section_html())

    def test_tour_entry_shape(self):
        entry = mod.tour_entry()
        self.assertEqual(entry,
                         {"id": "racehunt-type", "kind": "feature",
                          "title": "Race-hunt",
                          "blurb": "Spot the shared mutable state: name the "
                                   "line plus the fix — local copy, lock, "
                                   "or parameter.",
                          "path": "/status",
                          "anchor": "status-b7-racehunt"})


if __name__ == "__main__":
    unittest.main()
