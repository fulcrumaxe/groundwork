"""Tests for naming-fluency drills (type 80, F-76)."""
import json
import unittest
from types import SimpleNamespace

from groundwork import nameguess as mod


def make_snippet():
    return [
        "def greet(name='world'):",
        '    """Greet a user by name."""',
        "    return 'hi ' + name",
        "",
        "def add(a=2, b=3):",
        '    """Add two numbers."""',
        "    return a + b",
    ]


def make_concept(name="greet", file="app.py"):
    return SimpleNamespace(node_id="c", name=name, kind="func",
                           file=file, line=4)


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex80", make_concept(), make_snippet(), {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (80, "naming-fluency", "understand"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])
        self.assertEqual(len(e["payload"]["choices"]), 4)
        self.assertIn(e["payload"]["answer"], e["payload"]["choices"])

    def test_never_none(self):
        for args in [("ex80", make_concept(), make_snippet(), {}),
                     ("ex80", make_concept(), make_snippet(),
                      {"commit": "abc"}),
                     (None, None, None, None),
                     ("ex80", make_concept(), ["x = 1"], {})]:
            e = mod.generate(*args)
            self.assertIsNotNone(e)
            self.assertTrue(e["front"])

    def test_ungrounded_skipped_shape(self):
        e = mod.generate("ex80", make_concept(), ["x = 1"], {})
        self.assertFalse(e["payload"]["grounded"])

    def test_deterministic(self):
        a = mod.generate("ex80", make_concept(), make_snippet(), {})
        b = mod.generate("ex80", make_concept(), make_snippet(), {})
        self.assertEqual(a["payload"], b["payload"])

    def test_private_defs_skipped(self):
        snip = ["def _helper(x):", '    """Do internal work."""',
                "    return x"]
        e = mod.generate("ex80", make_concept(name="_helper"), snip, {})
        self.assertFalse(e["payload"]["grounded"])


class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.generate("ex80", make_concept(), make_snippet(), {})
        r = mod.grade(e, e["payload"]["answer"])
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_case_and_punctuation_tolerant(self):
        e = mod.generate("ex80", make_concept(), make_snippet(), {})
        r = mod.grade(e, "  " + e["payload"]["answer"].upper() + ".")
        self.assertTrue(r["pass"])

    def test_wrong_choice_fails(self):
        e = mod.generate("ex80", make_concept(), make_snippet(), {})
        wrong = next(c for c in e["payload"]["choices"]
                     if c != e["payload"]["answer"])
        r = mod.grade(e, wrong)
        self.assertFalse(r["pass"])
        self.assertEqual(r["score"], 0.0)
        self.assertIn(e["payload"]["answer"], r["feedback"])

    def test_empty_and_garbage_fail_closed(self):
        e = mod.generate("ex80", make_concept(), make_snippet(), {})
        for bad in ["", "   ", None]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertEqual(r["score"], 0.0)

    def test_hostile_never_raises(self):
        e = mod.generate("ex80", make_concept(), make_snippet(), {})
        for bad_ex, bad_sub in [({}, "x"), (e, None),
                                ({"payload": {}}, "def f(): pass"),
                                (None, None)]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex80", make_concept(), make_snippet(), {})
        body = mod.render(e)
        self.assertIn("radio", body)
        self.assertIn("How grading works", body)
        self.assertIn("app.py:4", body)
        self.assertIn(e["payload"]["signature"], body)

    def test_render_escapes(self):
        e = mod.generate("ex80", make_concept(file="a<b>.py"),
                         make_snippet(), {})
        self.assertIn("a&lt;b&gt;.py", mod.render(e))

    def test_status_anchor(self):
        self.assertIn("id='status-b18-nameguess'", mod.section_html())

    def test_tour_entry(self):
        self.assertEqual(mod.tour_entry(),
                         {"id": "naming-fluency", "kind": "feature",
                          "title": "Naming fluency",
                          "blurb": "Guess what a name does before reading "
                                   "its docstring — prediction then verify.",
                          "path": "/status",
                          "anchor": "status-b18-nameguess"})

    def test_disclosure(self):
        from groundwork import grading as gradingmod
        self.assertIn("exact choice",
                      gradingmod.disclosure(80).lower())


class EffectTest(unittest.TestCase):
    """Behavioral effect: type 80 flows pipeline→Due with grading honored."""

    def test_due_flow_with_grading(self):
        from groundwork import cards as cardsmod
        from groundwork import exercises as exmod
        e = exmod.generate(80, "ex080", make_concept(), make_snippet(),
                           {"commit": ""})
        self.assertEqual(e["type_name"], "naming-fluency")
        shown = exmod.render(e)
        self.assertIn(e["payload"]["answer"], shown)
        ok = exmod.grade(e, e["payload"]["answer"])
        self.assertTrue(ok["pass"])
        bad = exmod.grade(e, next(
            c for c in e["payload"]["choices"]
            if c != e["payload"]["answer"]))
        self.assertFalse(bad["pass"])
        card = {"id": "ex080", "exercise_type": "80",
                "payload": json.dumps(e["payload"])}
        widget = cardsmod.answer_widget(card)
        self.assertIn("Submit", widget)  # generic else, no new branch

    def test_legacy_types_untouched(self):
        from groundwork import exercises as exmod
        from groundwork import webhook as webhookmod
        w = webhookmod.generate("ex72", make_concept(), ["x = 1"], {})
        self.assertEqual(w["type"], 72)
        self.assertTrue(
            webhookmod.grade(w, w["payload"]["reference"])["pass"])
        s = exmod.generate(15, "ex015", make_concept(), make_snippet(), {})
        self.assertEqual(s["type"], 15)

    def test_legacy_no_data_fallback(self):
        thin = mod.generate("ex080", make_concept(), [], {})
        self.assertFalse(thin["payload"]["grounded"])  # pipeline skips


if __name__ == "__main__":
    unittest.main()
