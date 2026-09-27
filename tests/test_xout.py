"""Odd-one-out strike-through elimination before committing (I-175)."""
import json
import unittest

from groundwork import cards as cardsmod
from groundwork import emoji as emojimod
from groundwork import xout as mod


def _card(etype, payload):
    return {"id": "x18", "exercise_type": etype,
            "payload": json.dumps(payload)}


CHOICES = {"choices": ["call_a", "call_b", "outsider"], "answer": "outsider"}


class XoutGatesTest(unittest.TestCase):
    def test_etype_of(self):
        self.assertEqual(mod.etype_of(_card(18, CHOICES)), "18")
        self.assertEqual(mod.etype_of(_card("18", CHOICES)), "18")
        self.assertEqual(mod.etype_of({}), "")
        self.assertEqual(mod.etype_of(None), "")

    def test_choices_of_gates(self):
        self.assertEqual(mod.choices_of(_card(18, CHOICES)),
                         ["call_a", "call_b", "outsider"])
        self.assertEqual(mod.choices_of(_card(16, CHOICES)), [])
        self.assertEqual(mod.choices_of(_card(18, {})), [])
        self.assertEqual(mod.choices_of(_card(18, {"choices": ["only"]})), [])
        self.assertEqual(mod.choices_of(_card(18, {"choices": "nope"})), [])
        self.assertEqual(mod.choices_of(None), [])

    def test_left_text(self):
        self.assertEqual(mod.left_text(3, 3), "3 of 3 left")
        self.assertEqual(mod.left_text(1, 3), "1 of 3 left")
        self.assertEqual(mod.left_text(0, 3),
                         "all ruled out - reset or commit anyway")
        self.assertEqual(mod.left_text(-1, 3), "")
        self.assertEqual(mod.left_text(None, None), "")


class XoutStripTest(unittest.TestCase):
    def test_strip_present_for_odd_one_out(self):
        out = mod.elim_html(_card(18, CHOICES))
        self.assertIn("Rule out:", out)
        self.assertIn("xout-t", out)
        self.assertIn("__xout", out)
        self.assertIn("type='button'", out)
        self.assertIn("aria-pressed", out)
        self.assertIn("3 of 3 left", out)

    def test_strip_posts_nothing(self):
        out = mod.elim_html(_card(18, CHOICES))
        # Zero named controls: nothing to post. The painter JS must still
        # name the answer-button selector, so check the markup only.
        markup = out.split("<script>", 1)[0]
        self.assertNotIn("name=", markup)

    def test_strip_empty_legacy(self):
        self.assertEqual(mod.elim_html(_card(16, CHOICES)), "")
        self.assertEqual(mod.elim_html(_card(18, {})), "")
        self.assertEqual(mod.elim_html({}), "")
        self.assertEqual(mod.elim_html(None), "")


class XoutEffectTest(unittest.TestCase):
    def test_caller_widget_gains_strip_on_type_18(self):
        out = cardsmod.answer_widget(_card(18, CHOICES), 0, "/due")
        self.assertIn("xout", out)
        self.assertIn("Rule out:", out)
        # Grading contract: exactly one answer button per choice;
        # the strip adds zero named controls.
        self.assertEqual(out.count("<button name='answer'"), 3)

    def test_sibling_choice_branch_is_legacy(self):
        out = cardsmod.answer_widget(_card(16, CHOICES), 0, "/due")
        self.assertNotIn("xout", out)

    def test_choiceless_type_18_is_legacy(self):
        out = cardsmod.answer_widget(_card(18, {}), 0, "/due")
        self.assertNotIn("xout", out)


class XoutShapeTest(unittest.TestCase):
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
