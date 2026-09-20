"""Type-annotation retrofit exercises (F-8, type 31)."""
import unittest

from groundwork import typeanno as tamod


class FakeConcept:
    node_id = "m:double"
    name = "double"
    kind = "function"
    file = "gym/coach.py"
    line = 10


CODE = "def double(n: int) -> int:\n    return n * 2\n"


def make_ex(code=CODE, name="double"):
    c = FakeConcept()
    c.name = name
    return tamod.generate("ex001", c, code.splitlines(), {"commit": "abc"})


class GenerateTest(unittest.TestCase):
    def test_type_number_and_bloom(self):
        ex = make_ex()
        self.assertEqual(ex["type"], 31)
        self.assertEqual(ex["type_name"], "type-annotation")
        self.assertEqual(ex["bloom"], "apply")

    def test_strips_annotations_grounded(self):
        ex = make_ex()
        p = ex["payload"]
        self.assertTrue(p["grounded"])
        self.assertNotIn(": int", p["stripped"])
        self.assertNotIn("-> int", p["stripped"])
        self.assertEqual(p["annotations"], {"n": "int"})
        self.assertEqual(p["returns"], "int")

    def test_ungrounded_without_annotations(self):
        ex = make_ex("def double(n):\n    return n * 2\n")
        self.assertFalse(ex["payload"]["grounded"])

    def test_unparseable_snippet_ungrounded(self):
        ex = make_ex("def double(:\n  broken\n")
        self.assertFalse(ex["payload"]["grounded"])

    def test_skips_self_param(self):
        ex = make_ex("class A:\n    def go(self, x: str) -> str:\n        return x\n", "go")
        self.assertNotIn("self", ex["payload"]["annotations"])


class GradeTest(unittest.TestCase):
    def test_accepts_exact_reference(self):
        r = tamod.grade(make_ex(), CODE)
        self.assertTrue(r["pass"])
        self.assertEqual(r["score"], 1.0)

    def test_accepts_alias_spellings(self):
        sub = "def double(n: Integer) -> typing.List[int]:\n    return [n]\n"
        ex = make_ex("def double(n: int) -> list[int]:\n    return [n]\n")
        self.assertTrue(tamod.grade(ex, sub)["pass"])

    def test_rejects_wrong_annotation_partial_credit(self):
        r = tamod.grade(make_ex(), "def double(n: str) -> int:\n    return n * 2\n")
        self.assertFalse(r["pass"])
        self.assertEqual(r["score"], 0.5)

    def test_rejects_missing_annotation(self):
        r = tamod.grade(make_ex(), "def double(n):\n    return n * 2\n")
        self.assertFalse(r["pass"])
        self.assertIn("n", r["feedback"])

    def test_rejects_unparseable(self):
        r = tamod.grade(make_ex(), "def double(:\n")
        self.assertFalse(r["pass"])
        self.assertEqual(r["score"], 0.0)

    def test_needs_no_runner(self):
        r = tamod.grade(make_ex(), CODE, runner=None)
        self.assertTrue(r["pass"])


class RenderStatusTest(unittest.TestCase):
    def test_render_has_form_and_code(self):
        body = tamod.render(make_ex())
        self.assertIn("<textarea", body)
        self.assertIn("double", body)

    def test_section_html_anchor(self):
        body = tamod.section_html("")
        self.assertIn("id='status-b6-typeanno'", body)


if __name__ == "__main__":
    unittest.main()
