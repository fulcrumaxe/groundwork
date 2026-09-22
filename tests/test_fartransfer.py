"""Tests for the far-transfer challenge (type 75, F-71)."""
import json
import unittest
from types import SimpleNamespace
from groundwork import fartransfer as mod

def make_concept(name="answer_widget"):
    return SimpleNamespace(node_id="c", name=name, kind="function",
                           file="groundwork/cards.py", line=79)

class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.gen_fartransfer("ex75", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (75, "far-transfer", "create"))
        self.assertTrue(e["front"] and e["back"] and e["payload"]["check"])
    def test_never_none(self):
        for args in [("ex75", make_concept(), ["x = 1"], {}),
                     (None, None, None, None)]:
            e = mod.gen_fartransfer(*args)
            self.assertIsNotNone(e)
            self.assertTrue(e["front"] and e["back"])
    def test_deterministic(self):
        a = mod.gen_fartransfer("ex75", make_concept(), ["x = 1"], {})
        b = mod.gen_fartransfer("ex75", make_concept(), ["x = 1"], {})
        self.assertEqual(a["payload"], b["payload"])
    def test_distinct_ids_diverge(self):
        seen = {mod.gen_fartransfer(f"ex75-{i}", make_concept(), ["x = 1"], {})["back"]
                for i in range(12)}
        self.assertGreater(len(seen), 1)  # pairs x directions vary

class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.gen_fartransfer("ex75", make_concept(), ["x = 1"], {})
        r = mod.grade(e, e["payload"]["reference"])
        self.assertTrue(r["pass"] and r["score"] == 1.0)
    def test_dropped_behavior_fails(self):
        e = mod.gen_fartransfer("ex75", make_concept(), ["x = 1"], {})
        r = mod.grade(e, "const nums = raw;")
        self.assertFalse(r["pass"])
        self.assertLess(r["score"], 1.0)
    def test_empty_and_garbage_fail_closed(self):
        e = mod.gen_fartransfer("ex75", make_concept(), ["x = 1"], {})
        for bad in ["", "   ", "hello world", None, "def broken(:"]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertEqual(r["score"], 0.0)
    def test_hostile_never_raises(self):
        e = mod.gen_fartransfer("ex75", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [({}, "x"), (e, None),
                                ({"payload": {}}, "const x = 1;"),
                                (None, None)]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)

class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.gen_fartransfer("ex75", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("How grading works", body)
        self.assertIn("groundwork/cards.py:79", body)
    def test_render_escapes(self):
        e = mod.gen_fartransfer("ex75", make_concept(name="<b>"), ["x = 1"], {})
        self.assertIn("&lt;b&gt;", mod.render(e))
    def test_status_anchor(self):
        self.assertIn("id='status-b18-fartransfer'", mod.section_html())
    def test_tour_entry(self):
        self.assertEqual(mod.tour_entry(),
                         {"id": "far-transfer", "kind": "feature",
                          "title": "Far-transfer challenge",
                          "blurb": "Port a pattern to the other language — Python to JS/TS or back — with every behavior intact.",
                          "path": "/status", "anchor": "status-b18-fartransfer"})

class EffectTest(unittest.TestCase):
    """Type 75 renders in the due flow, grades, and leaves legacy types alone."""
    def test_due_flow_widget_and_grading(self):
        from groundwork import cards as cardsmod
        from groundwork import grading as gradingmod
        e = mod.gen_fartransfer("ex75", make_concept(), ["x = 1"], {})
        card = {"id": "ex75", "exercise_type": "75",
                "payload": json.dumps({"hints": e["hints"]})}
        widget = cardsmod.answer_widget(card)
        self.assertIn("name='answer'", widget)  # generic else branch, no new widget code
        self.assertIn("Give up", widget)
        self.assertIn(gradingmod.disclosure(75), widget)  # disclosure honored
        self.assertNotEqual(gradingmod.disclosure(75),
                            "Graded like its exercise family.")
        self.assertTrue(mod.grade(e, e["payload"]["reference"])["pass"])
    def test_legacy_fallback_pinned(self):
        from groundwork import cards as cardsmod
        from groundwork import exercises as exmod
        self.assertEqual(exmod.TYPES[1], ("flashcard", "recall"))  # legacy TYPES untouched
        legacy = {"id": "ex1", "exercise_type": "1",
                  "payload": json.dumps({"hints": []})}
        self.assertIn("Submit rating", cardsmod.answer_widget(legacy))

if __name__ == "__main__":
    unittest.main()
