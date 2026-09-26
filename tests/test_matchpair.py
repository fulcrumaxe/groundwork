"""Click-to-pair alternative for match-pairs cards (I-164)."""
import json
import unittest

from groundwork import cards as cardsmod
from groundwork import emoji as emojimod
from groundwork import exercises as exmod
from groundwork import matchpair as mod


def _card():
    return {"id": "m1", "exercise_type": 30,
            "payload": json.dumps(
                {"pairs": [["timeout", "config"], ["retries", "policy"]],
                 "left": ["timeout", "retries"],
                 "right": ["config", "policy"]})}


def _legacy_body(left, right):
    letters = " ".join(f"<b>{chr(ord('A') + i)}</b> {b}"
                       for i, b in enumerate(right))
    rows = "".join(
        f"<tr><td><b>{i}</b> {a}</td>"
        f"<td><input name='m{i}' size='3' placeholder='letter'></td></tr>"
        for i, a in enumerate(left))
    return f"<p>{letters}</p><table>{rows}</table>"


class MatchpairUnitTest(unittest.TestCase):
    def test_serialize_sorts_strips_uppers(self):
        self.assertEqual(mod.serialize({1: "b", 0: " a "}), "0=A\n1=B")

    def test_serialize_skips_empty_and_bad_keys(self):
        self.assertEqual(mod.serialize({0: ""}), "")
        self.assertEqual(mod.serialize({"x": "A", 2: "c"}), "2=C")
        self.assertEqual(mod.serialize(None), "")

    def test_letter_for(self):
        self.assertEqual(mod.letter_for(["x", "y"], "y"), "B")
        self.assertEqual(mod.letter_for(["x"], "z"), "")
        self.assertEqual(mod.letter_for(None, "y"), "")

    def test_pair_html_escapes_and_syncs(self):
        out = mod.pair_html("m1", ["<script>"], ["b"])
        self.assertIn("&lt;script&gt;", out)
        self.assertEqual(out.count("<script>"), 1)  # only the sync block
        self.assertIn("data-mp='l'", out)
        self.assertIn("data-mp='r'", out)
        self.assertIn("data-mp='clear'", out)
        self.assertIn("__mpInit", out)
        self.assertIn('input[name=\\"m', out)
        self.assertNotIn("type='hidden'", out)

    def test_pair_html_empty_is_legacy(self):
        self.assertEqual(mod.pair_html("m1", [], ["b"]), "")
        self.assertEqual(mod.pair_html("m1", ["a"], []), "")
        self.assertEqual(mod.pair_html("m1", None, None), "")


class MatchpairEffectTest(unittest.TestCase):
    def test_caller_widget_gains_pairing_with_typing_fallback(self):
        out = cardsmod.answer_widget(_card(), 0, "/due")
        self.assertIn("data-mp", out)
        self.assertIn("placeholder='letter'", out)
        # Single submission path: one m0 input only.
        self.assertEqual(out.count("name='m0'"), 1)

    def test_caller_widget_empty_lists_is_legacy(self):
        card = {"id": "m0", "exercise_type": 30,
                "payload": json.dumps({"pairs": [], "left": [], "right": []})}
        out = cardsmod.answer_widget(card, 0, "/due")
        self.assertNotIn("data-mp", out)
        self.assertIn(_legacy_body([], []), out)

    def test_serialized_pairs_grade_through_real_grader(self):
        ex = {"type": 30,
              "payload": {"pairs": [["timeout", "config"],
                                    ["retries", "policy"]],
                          "left": ["timeout", "retries"],
                          "right": ["config", "policy"]}}
        good = exmod.grade(ex, mod.serialize({0: "A", 1: "B"}))
        self.assertTrue(good["pass"])
        bad = exmod.grade(ex, mod.serialize({0: "B", 1: "A"}))
        self.assertFalse(bad["pass"])


class MatchpairShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "improvement")

    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])


if __name__ == "__main__":
    unittest.main()
