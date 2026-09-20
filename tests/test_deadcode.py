"""Tests for the dead-code elimination exercise (type 38, F-15)."""
import unittest
from types import SimpleNamespace

from groundwork import deadcode as mod


def make_concept(name="total"):
    return SimpleNamespace(node_id="c", name=name, kind="function",
                           file="calc.py", line=1)


IMPORT_CODE = "import os\n\n\ndef total(xs):\n    return sum(xs)\n"
FUNC_CODE = "def total(xs):\n    return sum(xs)\n\n\ndef _stale():\n    return 0\n"
BRANCH_CODE = ("def total(xs):\n    if False:\n        return 0\n"
               "    return sum(xs)\n")
CLEAN_CODE = "def total(xs):\n    return sum(xs)\n"
TESTS = "assert total([1, 2]) == 3\nprint('OK')"


class FakeRunner:
    """Exec-based harness stand-in: asserts in `tests` decide green/red."""

    def run(self, code):
        try:
            exec(compile(code, "<sub>", "exec"), {})
        except AssertionError as exc:
            return SimpleNamespace(ok=True, stdout=f"FAIL: {exc}", stderr="")
        except Exception as exc:  # noqa: BLE001 — broken code is a red harness
            return SimpleNamespace(ok=False, stdout="", stderr=str(exc))
        return SimpleNamespace(ok=True, stdout="OK", stderr="")


class BoomRunner:
    def run(self, code):
        raise RuntimeError("sandbox down")


def make_ex(code, tests=TESTS):
    return mod.generate("ex38", make_concept(), code.splitlines(),
                        {"runnable": code, "tests": tests})


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = make_ex(FUNC_CODE)
        self.assertEqual(e["type"], 38)
        self.assertEqual(e["type_name"], "dead-code")
        self.assertEqual(e["bloom"], "modify")
        self.assertTrue(e["front"])
        self.assertEqual(len(e["hints"]), 3)

    def test_detects_unused_import(self):
        e = make_ex(IMPORT_CODE)
        self.assertEqual(e["payload"]["kind"], "import")
        self.assertEqual(e["payload"]["target"], "os")
        self.assertNotIn("import os", e["payload"]["reference"])

    def test_detects_uncalled_def(self):
        e = make_ex(FUNC_CODE)
        self.assertEqual(e["payload"]["kind"], "function")
        self.assertEqual(e["payload"]["target"], "_stale")
        self.assertNotIn("_stale", e["payload"]["reference"])
        self.assertIn("def total", e["payload"]["reference"])

    def test_detects_dead_branch(self):
        e = make_ex(BRANCH_CODE)
        self.assertEqual(e["payload"]["kind"], "branch")
        self.assertEqual(e["payload"]["target"], "if False")

    def test_seeds_helper_when_clean(self):
        e = make_ex(CLEAN_CODE)
        self.assertTrue(e["payload"]["seeded"])
        self.assertIn("def _unused_helper", e["payload"]["original"])
        self.assertNotIn("_unused_helper", e["payload"]["reference"])

    def test_grounded_needs_tests(self):
        self.assertTrue(make_ex(FUNC_CODE)["payload"]["grounded"])
        e = make_ex(FUNC_CODE, tests="")
        self.assertFalse(e["payload"]["grounded"])
        self.assertFalse(e["payload"]["seeded"])

    def test_tolerates_suite_ctx(self):
        # Same generic ctx test_groundwork uses for every type: must not raise.
        ctx = {"runnable": FUNC_CODE, "tests": TESTS,
               "expected_output": "3", "trace_var": "total",
               "trace_expected": ["3"], "buggy": "b", "bug_line": 2,
               "fixed": "f", "graph": None}
        e = mod.generate("ex38", make_concept(), FUNC_CODE.splitlines(), ctx)
        self.assertTrue(e["front"])

    def test_never_raises_on_garbage(self):
        e = mod.generate("x", SimpleNamespace(), [], {})
        self.assertTrue(e["front"])
        e = mod.generate("x", make_concept(), ["def broken(:"], {})
        self.assertTrue(e["front"])


class GuardTest(unittest.TestCase):
    def test_guard_key(self):
        self.assertEqual(mod.GUARD, "tests")

    def test_emits_needs_harness(self):
        self.assertFalse(mod.emits({}))
        self.assertFalse(mod.emits(None))
        self.assertTrue(mod.emits({"tests": TESTS}))


class GradeTest(unittest.TestCase):
    def test_accept_import_removed_green(self):
        e = make_ex(IMPORT_CODE)
        sub = "def total(xs):\n    return sum(xs)\n"
        self.assertTrue(mod.grade(e, sub, FakeRunner())["pass"])

    def test_reject_import_kept(self):
        r = mod.grade(make_ex(IMPORT_CODE), IMPORT_CODE, FakeRunner())
        self.assertFalse(r["pass"])
        self.assertIn("os", r["feedback"])

    def test_accept_function_removed_green(self):
        e = make_ex(FUNC_CODE)
        sub = "def total(xs):\n    return sum(xs)\n"
        self.assertTrue(mod.grade(e, sub, FakeRunner())["pass"])

    def test_reject_function_kept(self):
        r = mod.grade(make_ex(FUNC_CODE), FUNC_CODE, FakeRunner())
        self.assertFalse(r["pass"])
        self.assertIn("_stale", r["feedback"])

    def test_accept_branch_cut_green(self):
        e = make_ex(BRANCH_CODE)
        sub = "def total(xs):\n    return sum(xs)\n"
        self.assertTrue(mod.grade(e, sub, FakeRunner())["pass"])

    def test_reject_branch_kept(self):
        r = mod.grade(make_ex(BRANCH_CODE), BRANCH_CODE, FakeRunner())
        self.assertFalse(r["pass"])
        self.assertIn("if False", r["feedback"])

    def test_reject_pruned_but_harness_red(self):
        # Dead node gone, yet the kept function broke: must fail.
        e = make_ex(IMPORT_CODE)
        sub = "def total(xs):\n    return 0\n"
        r = mod.grade(e, sub, FakeRunner())
        self.assertFalse(r["pass"])
        self.assertIn("broke", r["feedback"])

    def test_reject_concept_deleted(self):
        e = make_ex(IMPORT_CODE)
        r = mod.grade(e, "x = 1\n", FakeRunner())
        self.assertFalse(r["pass"])
        self.assertIn("total", r["feedback"])

    def test_reject_blank_and_unparseable(self):
        e = make_ex(FUNC_CODE)
        self.assertFalse(mod.grade(e, "   ", FakeRunner())["pass"])
        self.assertFalse(mod.grade(e, "def broken(:", FakeRunner())["pass"])

    def test_no_runner_with_tests_fails(self):
        e = make_ex(FUNC_CODE)
        r = mod.grade(e, "def total(xs):\n    return sum(xs)\n", None)
        self.assertFalse(r["pass"])

    def test_no_tests_ast_only_passes(self):
        e = make_ex(FUNC_CODE, tests="")
        sub = "def total(xs):\n    return sum(xs)\n"
        self.assertTrue(mod.grade(e, sub, None)["pass"])

    def test_never_raises(self):
        self.assertFalse(mod.grade({}, None, None)["pass"])
        self.assertFalse(mod.grade({"payload": {}}, "???", FakeRunner())["pass"])
        e = make_ex(FUNC_CODE)
        r = mod.grade(e, "def total(xs):\n    return sum(xs)\n", BoomRunner())
        self.assertFalse(r["pass"])
        self.assertIsInstance(r["feedback"], str)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        body = mod.render(make_ex(FUNC_CODE))
        self.assertIn("<textarea", body)
        self.assertIn("def total", body)
        self.assertIn("calc.py:1", body)

    def test_render_escapes(self):
        evil = SimpleNamespace(node_id="c", name="<b>evil</b>",
                               kind="function", file="a<b>.py", line=1)
        e = mod.generate("ex38", evil, FUNC_CODE.splitlines(),
                         {"runnable": FUNC_CODE, "tests": TESTS})
        body = mod.render(e)
        self.assertNotIn("<b>evil</b>", body)
        self.assertIn("&lt;b&gt;evil&lt;/b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b7-deadcode'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "deadcode-type")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["path"], "/status")
        self.assertEqual(t["anchor"], "status-b7-deadcode")


if __name__ == "__main__":
    unittest.main()
