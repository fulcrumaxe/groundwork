"""F-5 dependency-injection swap (type 27) tests, unittest style."""
import unittest
from types import SimpleNamespace

from groundwork import diretro as dmod

BODY = ("def fetch_total(db):\n"
        "    rows = db.query('SELECT total')\n"
        "    stamp = today()\n"
        "    return sum(rows)")

GOOD = ("def fetch_total(db, today=today):\n"
        "    rows = db.query('SELECT total')\n"
        "    stamp = today()\n"
        "    return sum(rows)")


def make_concept(name="fetch_total"):
    return SimpleNamespace(node_id=f"calc.py:{name}", name=name,
                           kind="function", file="calc.py", line=10)


def make_exercise(body=BODY, tests="", **kw):
    ctx = {"runnable": body, "tests": tests}
    ctx.update(kw)
    return dmod.generate("ex27", make_concept(), body.splitlines(), ctx)


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
        self.assertEqual(dmod.TYPE_NUM, 27)
        self.assertEqual(dmod.TYPE_NAME, "dependency-injection")
        self.assertEqual(dmod.BLOOM, "modify")

    def test_generate_infers_dep_and_param(self):
        ex = make_exercise()
        self.assertEqual(ex["type"], 27)
        self.assertEqual(ex["payload"]["dep"], "today")
        self.assertEqual(ex["payload"]["param"], "today")
        self.assertTrue(ex["front"])
        self.assertEqual(len(ex["hints"]), 3)

    def test_generate_honors_ctx_overrides(self):
        ex = make_exercise(dep="db", dep_param="conn")
        self.assertEqual(ex["payload"]["dep"], "db")
        self.assertEqual(ex["payload"]["param"], "conn")
        self.assertIn("conn=db", ex["payload"]["reference"])

    def test_generate_fallback_card_ungrounded(self):
        plain = "def add(a=2, b=3):\n    return a + b"
        ex = make_exercise(body=plain)
        self.assertTrue(ex["front"])
        self.assertFalse(ex["payload"]["grounded"])
        self.assertEqual(ex["payload"]["tests"], "")

    def test_fallback_dep_never_grounds(self):
        # A harness without a real hardcoded dep is no card: the
        # fallback name ("today") would teach a phantom dependency.
        plain = "def add(a=2, b=3):\n    return a + b"
        ex = make_exercise(body=plain, tests="assert True")
        self.assertEqual(ex["payload"]["dep"], "today")
        self.assertFalse(ex["payload"]["grounded"])

    def test_reference_keeps_old_callers(self):
        ex = make_exercise()
        ref = ex["payload"]["reference"]
        fn = dmod._func_node(ref, "fetch_total")
        self.assertTrue(dmod._has_default_param(fn, "today"))
        self.assertTrue(dmod._default_mentions(fn, "today", "today"))
        ns = {"today": lambda: "2026-01-01"}

        class DB:
            def query(self, _q):
                return [1, 2]

        exec(ref, ns)  # noqa: S102 - test fixture, not app code
        self.assertEqual(ns["fetch_total"](DB()), 3)


class GradeTest(unittest.TestCase):
    def test_grade_accepts_injected(self):
        self.assertTrue(dmod.grade(make_exercise(), GOOD)["pass"])

    def test_grade_rejects_missing_param(self):
        res = dmod.grade(make_exercise(), BODY)
        self.assertFalse(res["pass"])
        self.assertIn("today", res["feedback"])

    def test_grade_rejects_none_default(self):
        bad = GOOD.replace("today=today", "today=None")
        res = dmod.grade(make_exercise(), bad)
        self.assertFalse(res["pass"])
        self.assertIn("old callers", res["feedback"].lower())
        self.assertIn("today", res["feedback"])

    def test_grade_rejects_syntax_error(self):
        res = dmod.grade(make_exercise(), "def broken(:")
        self.assertFalse(res["pass"])

    def test_grade_harness_green_and_red(self):
        harness = "assert True\nprint('OK')"
        ex = make_exercise(tests=harness)
        self.assertTrue(dmod.grade(ex, GOOD, FakeRunner())["pass"])
        bad = dmod.grade(ex, GOOD, FakeRunner(ok=False, stdout="FAIL x"))
        self.assertFalse(bad["pass"])

    def test_grade_needs_runner_for_harness(self):
        ex = make_exercise(tests="assert True")
        res = dmod.grade(ex, GOOD, None)
        self.assertFalse(res["pass"])
        self.assertIn("sandbox", res["feedback"])


class RenderMetaTest(unittest.TestCase):
    def test_render_escapes_and_prefills(self):
        ex = make_exercise()
        ex["front"] = "<b>bold</b> " + ex["front"]
        body = dmod.render(ex)
        self.assertNotIn("<b>bold</b>", body)
        self.assertIn("&lt;b&gt;bold&lt;/b&gt;", body)
        self.assertIn("<textarea", body)
        self.assertIn("db.query", body)

    def test_section_html_anchor(self):
        self.assertIn("id='status-b6-diretro'", dmod.section_html(""))

    def test_tour_entry_shape(self):
        e = dmod.tour_entry()
        self.assertEqual(e["kind"], "feature")
        self.assertTrue(e["title"] and e["blurb"])
        self.assertEqual((e["path"], e["anchor"]),
                         ("/status", "status-b6-diretro"))


if __name__ == "__main__":
    unittest.main()
