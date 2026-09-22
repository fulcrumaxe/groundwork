"""Tests for the mastery interview exercise (type 73, F-69)."""
import json
import unittest
from types import SimpleNamespace

from groundwork import interview as mod


def make_concept(name="grade"):
    return SimpleNamespace(node_id="c", name=name, kind="function",
                           file="grading.py", line=17)


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.gen_mastery_interview("ex73", make_concept(), ["x = 1"], {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (73, "mastery-interview", "evaluate"))
        self.assertIn("aloud", e["front"])
        self.assertTrue(e["payload"]["grounded"])

    def test_never_none_legacy_fallback(self):
        # Legacy no-data path pinned: thin input yields an ungrounded
        # card, never None, never raises.
        for args in [("ex73", make_concept(), ["x = 1"], {}),
                     (None, None, None, None)]:
            e = mod.gen_mastery_interview(*args)
            self.assertIsNotNone(e)
            self.assertTrue(e["front"] and e["back"])
        thin = mod.gen_mastery_interview("ex73", None, [], {})
        self.assertFalse(thin["payload"]["grounded"])

    def test_deterministic(self):
        a = mod.gen_mastery_interview("ex73", make_concept(), ["x = 1"], {})
        b = mod.gen_mastery_interview("ex73", make_concept(), ["x = 1"], {})
        self.assertEqual(a["payload"]["rubric"], b["payload"]["rubric"])


class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.gen_mastery_interview("ex73", make_concept(), ["x = 1"], {})
        r = mod.grade(e, " ".join(e["payload"]["rubric"]))
        self.assertTrue(r["pass"])
        self.assertGreaterEqual(r["score"], 0.5)

    def test_empty_and_garbage_fail_closed(self):
        e = mod.gen_mastery_interview("ex73", make_concept(), ["x = 1"], {})
        for bad in ["", "   ", None]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertEqual(r["score"], 0.0)
        r = mod.grade(e, "unrelated words here")
        self.assertFalse(r["pass"])
        self.assertLess(r["score"], 0.5)

    def test_hostile_never_raises(self):
        e = mod.gen_mastery_interview("ex73", make_concept(), ["x = 1"], {})
        for bad_ex, bad_sub in [({}, "x"), (e, None),
                                ({"payload": {}}, "def f(): pass"),
                                (None, None)]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class EffectTest(unittest.TestCase):
    def test_due_flow_renders_with_grading_honored(self):
        # Effect: a generated type-73 card renders in the due flow with
        # grading honored.
        from groundwork import cards as cardsmod
        from groundwork import grading as gradingmod
        e = mod.gen_mastery_interview("ex73", make_concept(), ["x = 1"], {})
        card = {"id": "ex73", "exercise_type": "73",
                "payload": json.dumps(
                    {"hints": e["hints"], "rubric": e["payload"]["rubric"]}),
                "front": e["front"], "back": e["back"],
                "concept_id": "c", "due": "", "stability": 0.0,
                "difficulty": 0.0, "retrievability": 0.0, "lapses": 0}
        widget = cardsmod.answer_widget(card)
        self.assertIn("Submit", widget)
        self.assertIn("How grading works", widget)
        self.assertIn("half the key points",
                      gradingmod.disclosure(73))
        self.assertTrue(
            mod.grade(e, " ".join(e["payload"]["rubric"]))["pass"])

    def test_legacy_types_untouched(self):
        # Legacy types keep their contracts: disclosure + grading bar.
        from groundwork import grading as gradingmod
        from groundwork import exercises as exmod
        self.assertEqual(
            gradingmod.disclosure(5),
            "Your words must cover at least half the key points; "
            "missing points are listed in the feedback.")
        legacy = {"type": 5, "payload": {"rubric": ["alpha", "beta"]}}
        self.assertTrue(exmod.grade(legacy, "alpha beta")["pass"])
        self.assertFalse(exmod.grade(legacy, "nothing here")["pass"])


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.gen_mastery_interview("ex73", make_concept(), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("<textarea", body)
        self.assertIn("How grading works", body)
        self.assertIn("grading.py:17", body)

    def test_render_escapes(self):
        e = mod.gen_mastery_interview("ex73", make_concept(name="<b>"),
                                      ["x = 1"], {})
        self.assertIn("&lt;b&gt;", mod.render(e))

    def test_section_html_anchor(self):
        self.assertIn("id='status-b18-interview'", mod.section_html())

    def test_tour_entry_shape(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "mastery-interview")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["path"], "/status")
        self.assertEqual(t["anchor"], "status-b18-interview")


if __name__ == "__main__":
    unittest.main()
