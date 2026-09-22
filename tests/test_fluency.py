"""Tests for the reading-fluency drill (type 79, F-75)."""
import json
import unittest
from types import SimpleNamespace

from groundwork import fluency as mod


def make_concept(name="answer_widget"):
    return SimpleNamespace(node_id="c", name=name, kind="function",
                           file="groundwork/cards.py", line=79)


SNIPPET = ["def answer_widget(card, attempts=0):",
           "    etype = str(card['exercise_type'])",
           "    if etype == '1':",
           "        return rating_widget(card)",
           "    return generic_widget(card)"]


class GenerateTest(unittest.TestCase):
    def test_identity(self):
        e = mod.generate("ex79", make_concept(), SNIPPET, {})
        self.assertEqual((e["type"], e["type_name"], e["bloom"]),
                         (79, "reading-fluency", "understand"))
        self.assertTrue(e["front"] and e["payload"]["grounded"])
        self.assertEqual(len(e["payload"]["probes"]), 3)

    def test_never_none(self):
        for args in [("ex79", make_concept(), SNIPPET, {}),
                     ("ex79", make_concept(), SNIPPET, {"commit": "abc"}),
                     (None, None, None, None)]:
            e = mod.generate(*args)
            self.assertIsNotNone(e)
            self.assertTrue(e["front"])

    def test_thin_input_ungrounded(self):
        e = mod.generate("ex79", make_concept(name=""), [], {})
        self.assertFalse(e["payload"]["grounded"])

    def test_deterministic(self):
        a = mod.generate("ex79", make_concept(), SNIPPET, {})
        b = mod.generate("ex79", make_concept(), SNIPPET, {})
        self.assertEqual(a["payload"]["key"], b["payload"]["key"])

    def test_seed_stable_across_processes(self):
        import subprocess
        import sys
        code = ("import sys; sys.path.insert(0, '.');"
                "from groundwork import fluency as f;"
                "print(f._seed('ex79'))")
        outs = {subprocess.run([sys.executable, "-c", code],
                               capture_output=True, text=True,
                               check=True).stdout.strip() for _ in range(2)}
        self.assertEqual(len(outs), 1)


class GradeTest(unittest.TestCase):
    def test_round_trip_pass(self):
        e = mod.generate("ex79", make_concept(), SNIPPET, {})
        r = mod.grade(e, e["payload"]["reference"])
        self.assertTrue(r["pass"] and r["score"] == 1.0)

    def test_lowercase_and_spaced_accept(self):
        e = mod.generate("ex79", make_concept(), SNIPPET, {})
        key = e["payload"]["key"]
        r = mod.grade(e, " ".join(key.lower()))
        self.assertTrue(r["pass"])

    def test_keyed_lines_accept(self):
        e = mod.generate("ex79", make_concept(), SNIPPET, {})
        key = e["payload"]["key"]
        r = mod.grade(e, "\n".join(f"{i}={c}" for i, c in enumerate(key)))
        self.assertTrue(r["pass"])

    def test_wrong_letters_partial(self):
        e = mod.generate("ex79", make_concept(), SNIPPET, {})
        key = e["payload"]["key"]
        flip = "A" if key[0] != "A" else "B"
        r = mod.grade(e, flip + key[1:])
        self.assertFalse(r["pass"])
        self.assertAlmostEqual(r["score"], (len(key) - 1) / len(key))
        self.assertIn("Probe(s) 1", r["feedback"])

    def test_empty_and_garbage_fail_closed(self):
        e = mod.generate("ex79", make_concept(), SNIPPET, {})
        for bad in ["", "   ", "hello world", None, "def broken(:"]:
            r = mod.grade(e, bad)
            self.assertFalse(r["pass"])
            self.assertEqual(r["score"], 0.0)

    def test_hostile_never_raises(self):
        e = mod.generate("ex79", make_concept(), SNIPPET, {})
        for bad_ex, bad_sub in [({}, "x"), (e, None),
                                ({"payload": {}}, "ABC"),
                                (None, None)]:
            r = mod.grade(bad_ex, bad_sub)
            self.assertFalse(r["pass"])
            self.assertIn("score", r)


class RenderStatusTest(unittest.TestCase):
    def test_render_widget(self):
        e = mod.generate("ex79", make_concept(), SNIPPET, {})
        body = mod.render(e)
        self.assertIn("name='answer'", body)
        self.assertIn("How grading works", body)
        self.assertIn("groundwork/cards.py:79", body)

    def test_render_escapes(self):
        e = mod.generate("ex79", make_concept(name="<b>"), ["x = 1"], {})
        body = mod.render(e)
        self.assertIn("&lt;b&gt;", body)

    def test_status_anchor(self):
        self.assertIn("id='status-b18-fluency'", mod.section_html())

    def test_tour_entry(self):
        self.assertEqual(mod.tour_entry(),
                         {"id": "reading-fluency", "kind": "feature",
                          "title": "Reading fluency",
                          "blurb": "Skim a snippet on a 90s budget, gist it in one line, then verify with three probes — keyword, locate, owner.",
                          "path": "/status", "anchor": "status-b18-fluency"})


class EffectTest(unittest.TestCase):
    """Type 79 renders in the due flow with grading honored; legacy untouched."""

    def _due_card(self, ex):
        return {"id": "due79", "exercise_type": 79,
                "payload": json.dumps({"probes": ex["payload"]["probes"],
                                       "key": ex["payload"]["key"],
                                       "hints": ex["hints"]}),
                "concept": ex["concept"], "front": ex["front"],
                "back": ex["back"], "due": "2000-01-01T00:00:00+00:00",
                "stability": 1.0, "difficulty": 0.5,
                "retrievability": 0.9, "lapses": 0}

    def test_due_widget_and_grading_honored(self):
        from groundwork import cards as cardsmod
        from groundwork import exercises as exmod
        from groundwork import grading as gradingmod
        e = mod.generate("ex79", make_concept(), SNIPPET, {})
        widget = cardsmod.answer_widget(self._due_card(e))
        self.assertIn("name='answer'", widget)  # generic else, no new branch
        self.assertIn("How grading works", widget)
        self.assertIn("probe letter", gradingmod.disclosure(79).lower())
        # Grading honored through the registry branch:
        self.assertTrue(exmod.grade(
            {"type": 79, "payload": {"probes": e["payload"]["probes"],
                                     "key": e["payload"]["key"]}},
            e["payload"]["reference"], None)["pass"])

    def test_legacy_fallback_pinned(self):
        from groundwork import cards as cardsmod
        from groundwork import exercises as exmod
        from groundwork import grading as gradingmod
        # Legacy type rows unchanged:
        self.assertEqual(exmod.TYPES[1], ("flashcard", "recall"))
        self.assertEqual(exmod.TYPES[72][0], "webhook")
        self.assertNotIn(79, [1, 2, 3, 4, 72])
        self.assertEqual(gradingmod.disclosure(4),
                         "Exact file text — pick where it lives.")
        legacy = {"id": "due1", "exercise_type": 1,
                  "payload": json.dumps({"hints": []}),
                  "due": "2000-01-01T00:00:00+00:00",
                  "stability": 1.0, "difficulty": 0.5,
                  "retrievability": 0.9, "lapses": 0}
        self.assertIn("Submit rating", cardsmod.answer_widget(legacy))


if __name__ == "__main__":
    unittest.main()
