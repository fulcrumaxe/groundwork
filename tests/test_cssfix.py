"""Tests for the css-fix exercise (type 56, F-33)."""
import unittest
from types import SimpleNamespace

from groundwork import cssfix as mod


def make_concept(name="layout"):
    return SimpleNamespace(node_id="c", name=name, kind="style",
                           file="style.css", line=3)


GENERIC_CTX = {"runnable": "x", "expected_output": "x", "tests": "x",
               "trace_var": "total", "trace_expected": ["2"],
               "buggy": "b", "bug_line": 2, "fixed": "f", "graph": None}


def answer_for(e):
    p = e["payload"]
    lines = "\n".join(f"  {k}: {v};" for k, v in p["spec"].items())
    return f"{p['selector']} {{\n{lines}\n}}"


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex56", make_concept(), ["x"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (56, "css-fix", "modify"))
        self.assertTrue(e["front"])

    def test_payload_grounded(self):
        e = mod.generate("ex56", make_concept(), ["x"], {})
        p = e["payload"]
        self.assertTrue(p["grounded"])
        self.assertEqual(p["required"], list(p["spec"]))
        self.assertGreaterEqual(len(p["spec"]), 3)
        self.assertIn(p["selector"], e["back"])

    def test_deterministic(self):
        a = mod.generate("ex56", make_concept(), ["x"], {})
        b = mod.generate("ex56", make_concept(), ["x"], {})
        self.assertEqual(a["payload"], b["payload"])

    def test_fallback_never_raises(self):
        e = mod.generate("ex56", None, None, None)
        self.assertTrue(e["front"] and e["payload"]["grounded"])

    def test_tolerates_suite_ctx(self):
        e = mod.generate("ex56", make_concept(), ["x"], GENERIC_CTX)
        self.assertTrue(e["front"])


class ParseTest(unittest.TestCase):
    def test_bare_list_and_block(self):
        self.assertEqual(mod.parse_declarations("display: flex; gap: 16px"),
                         {"display": "flex", "gap": "16px"})
        self.assertEqual(
            mod.parse_declarations(".x {\n display: FLEX ;\n}"),
            {"display": "flex"})

    def test_garbage_never_raises(self):
        for bad in ["", ";;;", "{{{{", "no colon here", None, 123]:
            self.assertEqual(mod.parse_declarations(bad), {})


class GradeTest(unittest.TestCase):
    def test_exact_accept(self):
        e = mod.generate("ex56", make_concept(), ["x"], {})
        r = mod.grade(e, answer_for(e))
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_tolerant_accept(self):
        e = mod.generate("ex56", make_concept(), ["x"], {})
        p = e["payload"]
        noisy = "\n".join(f"  {k.upper()} :  {v.upper()}  ;"
                          for k, v in p["spec"].items())
        r = mod.grade(e, noisy)
        self.assertTrue(r["pass"])

    def test_harmless_extras_capped(self):
        e = mod.generate("ex56", make_concept(), ["x"], {})
        ok = answer_for(e).replace("}", "  color: red;\n}")
        self.assertTrue(mod.grade(e, ok)["pass"])
        bad = answer_for(e).replace(
            "}", "  a: 1; b: 2; c: 3;\n}")
        r = mod.grade(e, bad)
        self.assertFalse(r["pass"])
        self.assertIn("extra", r["feedback"])

    def test_missing_and_wrong_reject_first_mismatch(self):
        e = mod.generate("ex56", make_concept(), ["x"], {})
        p = e["payload"]
        prop = p["required"][0]
        missing = "\n".join(f"{k}: {v};" for k, v in p["spec"].items()
                            if k != prop)
        r = mod.grade(e, missing)
        self.assertFalse(r["pass"])
        self.assertIn(prop, r["feedback"])
        self.assertIn("Missing", r["feedback"])
        wrong = answer_for(e).replace(
            f"{prop}: {p['spec'][prop]}", f"{prop}: bogus-value", 1)
        r = mod.grade(e, wrong)
        self.assertFalse(r["pass"])
        self.assertIn(prop, r["feedback"])

    def test_hostile_never_raises(self):
        e = mod.generate("ex56", make_concept(), ["x"], {})
        for bad_ex, bad_sub in [({}, "display: flex"), (e, None), (e, ""),
                                (e, "drop table; --"), (e, "{{{"),
                                (None, None), ({"payload": {}}, "a: b")]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex56", make_concept(), ["x"], {})
        body = mod.render(e)
        self.assertIn("<textarea name='answer'", body)
        self.assertIn("<pre>", body)
        self.assertIn("How grading works", body)
        self.assertIn("style.css:3", body)

    def test_render_hides_expected_values(self):
        # The required-property list must name properties, never values:
        # values are the answer and live only in the payload.
        e = mod.generate("ex56", make_concept(), ["x"], {})
        body = mod.render(e)
        for prop in e["payload"]["required"]:
            self.assertIn(f"<code>{prop}</code>", body)
        self.assertNotIn("</code>: <code>", body)

    def test_render_escapes(self):
        e = mod.generate("ex56", make_concept(name="<b>"), ["x"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b9-cssfix'", mod.section_html())

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "css-layout-fix")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual((t["path"], t["anchor"]),
                         ("/status", "status-b9-cssfix"))


if __name__ == "__main__":
    unittest.main()
