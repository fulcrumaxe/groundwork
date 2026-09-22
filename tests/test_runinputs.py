"""Worked-example own-inputs widget (I-106)."""
import unittest

from groundwork import lessons as lesmod
from groundwork import runinputs as rimod

from test_web import handler_for, make_module


def _lesson(call="add(2, 3)"):
    return {"concept_id": "c", "name": "add", "kind": "function",
            "file": "calc.py", "line": 1,
            "summary": "add() totals two numbers via its defaults.",
            "docstring": "", "callers": [], "callees": [],
            "key_lines": "", "source": "def add(a, b):\n    return a + b\n",
            "how": ["Read the defaults.", "Trace the total."],
            "worked": {"call": call, "output": "5"}}


class ParseCallTest(unittest.TestCase):
    def test_literal_call(self):
        self.assertEqual(rimod.parse_call("add(2, 3)"),
                         {"func": "add", "args": ["2", "3"]})

    def test_rejections(self):
        for bad in ("", "   ", "obj.m(1)", "f(*a)", "f(x + 1)",
                    "f(1, 2, 3, 4, 5, 6, 7)", None, 42, ["f()"]):
            self.assertEqual(rimod.parse_call(bad), {}, bad)
        self.assertEqual(rimod.parse_call("greet()"),
                         {"func": "greet", "args": []})

    def test_string_args_round_trip(self):
        self.assertEqual(rimod.parse_call("greet('bob')"),
                         {"func": "greet", "args": ["'bob'"]})


class VariantsTest(unittest.TestCase):
    def test_int_neighbors(self):
        self.assertEqual(rimod.suggest_variants("add", ["2", "3"]),
                         ["add(1, 3)", "add(3, 3)"])

    def test_capped(self):
        self.assertLessEqual(
            len(rimod.suggest_variants("f", ["1", "2", "3"])),
            rimod.MAX_VARIANTS)

    def test_garbage_in(self):
        self.assertEqual(rimod.suggest_variants("", []), [])
        self.assertEqual(rimod.suggest_variants("f", ["x + 1"]), [])


class EscapeTest(unittest.TestCase):
    def test_call_escaped(self):
        html_out = rimod.runinputs_html(
            _lesson("greet('<script>alert(1)</script>')"))
        self.assertNotIn("<script>alert", html_out)
        self.assertIn("&lt;script&gt;", html_out)


class CallerEffectTest(unittest.TestCase):
    def test_rendered_lesson_carries_widget(self):
        html_out = lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/")
        self.assertIn("id='runinputs'", html_out)
        self.assertIn("value='2'", html_out)
        self.assertIn("localStorage", html_out)
        self.assertIn("ri-out", html_out)

    def test_module_page_carries_widget(self):
        _tmp, db, _server, out = make_module("runinputs page mod")
        body = handler_for(db).module_html(out["module_id"])
        self.assertIn("id='runinputs'", body)


class LegacyFallbackTest(unittest.TestCase):
    def test_no_worked_means_no_widget(self):
        lesson = _lesson()
        del lesson["worked"]
        base = lesmod.render_levels(lesson, 0.0, 0, "auto", "/")
        self.assertNotIn("runinputs", base)
        self.assertEqual(rimod.runinputs_html({}), "")
        self.assertEqual(rimod.runinputs_html("nope"), "")
        self.assertEqual(rimod.runinputs_html({"worked": {"call": "obj.m(1)"}}),
                         "")

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{rimod.STATUS_ANCHOR}'",
                      rimod.section_html())
        e = rimod.tour_entry()
        self.assertEqual(e["kind"], "improvement")
        self.assertTrue(e["path"] and e["anchor"])


if __name__ == "__main__":
    unittest.main()
