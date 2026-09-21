"""Tests for the input-validation audit exercise (type 51, F-28)."""
import unittest
from types import SimpleNamespace

from groundwork import inputaudit as mod


def make_concept(name="handle"):
    return SimpleNamespace(node_id="c", name=name, kind="function",
                           file="app.py", line=3)


RISKY = ["def handle(query, count):",
         "    if count < 0:",
         '        raise ValueError("bad")',
         "    return eval(query)"]

SAFE = ["def load(path):",
        "    import re",
        '    if not re.match(r"^/safe/", path):',
        '        raise ValueError("bad")',
        "    return open(path)"]


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex51", make_concept(), RISKY, {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (51, "input-validation", "analyse"))
        self.assertTrue(e["front"])

    def test_checklist_unvalidated_only(self):
        e = mod.generate("ex51", make_concept(), RISKY, {})
        names = [it["name"] for it in e["payload"]["checklist"]]
        self.assertEqual(names, ["query"])  # count is if-guarded
        self.assertEqual(e["payload"]["checklist"][0]["sink"], "eval")
        self.assertTrue(e["payload"]["grounded"])

    def test_validated_yields_ungrounded(self):
        e = mod.generate("ex51", make_concept(), SAFE, {})
        self.assertEqual(e["payload"]["checklist"], [])
        self.assertFalse(e["payload"]["grounded"])

    def test_no_function_returns_none(self):
        self.assertIsNone(mod.generate("ex51", make_concept(), ["x = 1"], {}))
        self.assertIsNone(mod.generate("ex51", make_concept(), ["def ("], {}))

    def test_never_raises(self):
        self.assertIsNone(mod.generate("ex51", None, None, None))
        e = mod.generate("ex51", make_concept(), RISKY, None)
        self.assertTrue(e["front"])


class GradeTest(unittest.TestCase):
    def setUp(self):
        self.ex = mod.generate("ex51", make_concept(), RISKY, {})

    def test_exact_accept(self):
        r = mod.grade(self.ex, "query")
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_normalization(self):
        r = mod.grade(self.ex, "  QUERY  ")
        self.assertTrue(r["pass"])
        r = mod.grade(self.ex, "0=query")
        self.assertTrue(r["pass"])

    def test_partial_and_extras(self):
        multi = mod.generate("ex51", make_concept(),
                             ["def f(a, b):",
                              "    eval(a)",
                              "    exec(b)"], {})
        r = mod.grade(multi, "a")
        self.assertFalse(r["pass"])
        self.assertEqual(r["score"], 0.5)
        r = mod.grade(multi, "a\nb\nzzz")
        self.assertFalse(r["pass"])
        self.assertAlmostEqual(r["score"], 2 / 3)

    def test_hostile_never_raises(self):
        for bad_ex, bad_sub in [({}, "query"), (self.ex, None),
                                (self.ex, ""), (self.ex, "   "),
                                (None, None), ({"payload": {}}, "query"),
                                (self.ex, "eval; drop --")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex51", make_concept(), RISKY, {})
        body = mod.render(e)
        self.assertIn("name='answer'", body)
        self.assertIn("How grading works", body)
        self.assertIn("app.py:3", body)

    def test_render_escapes(self):
        e = mod.generate("ex51", make_concept(name="<b>"), RISKY, {})
        self.assertIn("&lt;b&gt;", mod.render(e))

    def test_status_anchor(self):
        self.assertIn("id='status-b9-inputaudit'", mod.section_html())
        self.assertIn("id='status-b9-inputaudit'", mod.section_html("x"))

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "input-validation-audit")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["path"], "/status")
        self.assertEqual(t["anchor"], "status-b9-inputaudit")


if __name__ == "__main__":
    unittest.main()
