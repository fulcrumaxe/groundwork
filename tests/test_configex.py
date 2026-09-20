"""F-16 config extraction (type 39) tests, unittest style."""
import unittest
from types import SimpleNamespace

from groundwork import configex as mod

BODY = "def total(n):\n    return n * 0.2 + 5\n"

EXTRACTED = ("DISCOUNT = 0.2\nFEE = 5\n\n\n"
             "def total(n):\n    return n * DISCOUNT + FEE\n")

CONFIG_STYLE = ("CONFIG = {'discount': 0.2, 'fee': 5}\n\n\n"
                "def total(n):\n"
                "    return n * CONFIG['discount'] + CONFIG['fee']\n")

BROKEN = ("DISCOUNT = 0.2\nFEE = 5\n\n\n"
          "def total(n):\n    return n * DISCOUNT + FEE + 1\n")

HARNESS = ("_out = repr(total(10))\n"
           "assert _out == '7.0', f'FAIL: {_out}'\nprint('OK')")


def make_concept(name="total"):
    return SimpleNamespace(node_id=f"calc.py:{name}", name=name,
                           kind="function", file="calc.py", line=10)


def make_exercise(body=BODY, tests=HARNESS, **kw):
    ctx = {"runnable": body, "tests": tests}
    ctx.update(kw)
    return mod.generate("ex39", make_concept(), body.splitlines(), ctx)


class FakeRunner:
    def __init__(self, ok=True, stdout="OK"):
        self.ok = ok
        self.stdout = stdout
        self.seen = []

    def run(self, code):
        self.seen.append(code)
        return SimpleNamespace(ok=self.ok, stdout=self.stdout, stderr="")


class GenerateTest(unittest.TestCase):
    def test_type_constants(self):
        self.assertEqual(mod.TYPE_NUM, 39)
        self.assertEqual(mod.TYPE_NAME, "config-extract")
        self.assertEqual(mod.BLOOM, "modify")
        self.assertEqual(mod.AREA_KEY, "configex")

    def test_generate_shape(self):
        ex = make_exercise()
        self.assertEqual(ex["type"], 39)
        self.assertEqual(ex["type_name"], "config-extract")
        self.assertEqual(ex["bloom"], "modify")
        self.assertTrue(ex["front"])
        self.assertTrue(ex["back"])
        self.assertEqual(len(ex["hints"]), 3)
        p = ex["payload"]
        for key in ("func", "original", "reference", "magics",
                    "consts", "tests", "grounded"):
            self.assertIn(key, p)
        self.assertTrue(p["grounded"])
        self.assertIn("0.2", p["magics"])
        self.assertIn("5", p["magics"])
        self.assertIn("total", ex["back"])

    def test_generate_ungrounded_without_tests(self):
        ex = make_exercise(tests="")
        self.assertFalse(ex["payload"]["grounded"])
        self.assertTrue(ex["front"])

    def test_generate_skips_trivia(self):
        plain = "def add(a, b):\n    return a + b\n"
        ex = make_exercise(body=plain)
        self.assertEqual(ex["payload"]["magics"], [])
        self.assertFalse(ex["payload"]["grounded"])

    def test_tolerates_suite_ctx(self):
        ctx = {"runnable": BODY, "tests": HARNESS,
               "expected_output": "7.0", "trace_var": "n",
               "trace_expected": ["1"], "buggy": "b", "bug_line": 2,
               "fixed": "f", "graph": None}
        ex = mod.generate("ex39", make_concept(), BODY.splitlines(), ctx)
        self.assertTrue(ex["front"])


class GradeTest(unittest.TestCase):
    def test_accept_extracted(self):
        self.assertTrue(
            mod.grade(make_exercise(), EXTRACTED, FakeRunner())["pass"])

    def test_accept_config_dict_style(self):
        self.assertTrue(
            mod.grade(make_exercise(), CONFIG_STYLE, FakeRunner())["pass"])

    def test_reject_unextracted(self):
        res = mod.grade(make_exercise(), BODY, FakeRunner())
        self.assertFalse(res["pass"])
        self.assertIn("0.2", res["feedback"])

    def test_reject_broken_behavior(self):
        res = mod.grade(make_exercise(), BROKEN,
                        FakeRunner(ok=False, stdout="FAIL: 8.0"))
        self.assertFalse(res["pass"])
        self.assertIn("Behavior", res["feedback"])

    def test_reject_constant_without_magic(self):
        other = ("LIMIT = 99\n\n\ndef total(n):\n    return n * 0.2 + 5\n")
        res = mod.grade(make_exercise(), other, FakeRunner())
        self.assertFalse(res["pass"])

    def test_reject_syntax_error(self):
        res = mod.grade(make_exercise(), "def broken(:", FakeRunner())
        self.assertFalse(res["pass"])

    def test_needs_runner_for_harness(self):
        res = mod.grade(make_exercise(), EXTRACTED, None)
        self.assertFalse(res["pass"])
        self.assertIn("sandbox", res["feedback"])

    def test_ast_only_pass_without_tests(self):
        ex = make_exercise(tests="")
        self.assertTrue(mod.grade(ex, EXTRACTED, None)["pass"])


class GuardTest(unittest.TestCase):
    def test_emits_with_harness(self):
        self.assertTrue(mod.should_emit({"tests": HARNESS}))

    def test_skips_without_harness(self):
        self.assertFalse(mod.should_emit({}))
        self.assertFalse(mod.should_emit(None))


class RenderMetaTest(unittest.TestCase):
    def test_render_escapes_and_prefills(self):
        ex = make_exercise()
        ex["front"] = "<b>bold</b> " + ex["front"]
        body = mod.render(ex)
        self.assertNotIn("<b>bold</b>", body)
        self.assertIn("&lt;b&gt;bold&lt;/b&gt;", body)
        self.assertIn("<textarea", body)
        self.assertIn("0.2", body)
        self.assertIn("calc.py:10", body)

    def test_section_html_anchor(self):
        self.assertIn("id='status-b7-configex'", mod.section_html())
        self.assertIn("id='status-b7-configex'", mod.section_html("/tmp/x.db"))

    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(e["id"], "configex-type")
        self.assertEqual(e["kind"], "feature")
        self.assertTrue(e["title"] and e["blurb"])
        self.assertEqual((e["path"], e["anchor"]),
                         ("/status", "status-b7-configex"))


class NeverRaisesTest(unittest.TestCase):
    def test_generate_empty(self):
        c = SimpleNamespace(node_id="", name="", kind="", file="", line=0)
        mod.generate("ex39", c, [], {})

    def test_grade_empty(self):
        res = mod.grade({}, None, None)
        self.assertFalse(res["pass"])

    def test_render_empty(self):
        self.assertIn("<article>", mod.render({}))


if __name__ == "__main__":
    unittest.main()
