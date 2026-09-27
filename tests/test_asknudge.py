"""Ask-for-a-nudge button: free next-tier reveal (I-188)."""
import json
import unittest

from groundwork import asknudge as askmod
from groundwork import cards as cardsmod
from groundwork import hinttiers as hintmod


class AskNudgeTest(unittest.TestCase):
    def test_legacy_no_data_path_pinned(self):
        self.assertEqual(askmod.button_html([]), "")
        self.assertEqual(askmod.button_html(None), "")
        self.assertEqual(askmod.button_html("nope"), "")
        # All tiers already shown: nothing appended, byte-identical.
        self.assertEqual(askmod.button_html(["a", "b"], attempts=9), "")
        self.assertEqual(askmod.button_html(["only"], attempts=0), "")
        self.assertEqual(askmod.hidden_count([], attempts=0), 0)
        self.assertEqual(askmod.hidden_count(None), 0)
        self.assertEqual(askmod.next_tier_label([]), "")

    def test_hidden_count_mirrors_prefix(self):
        hints = ["a", "b", "c"]
        self.assertEqual(askmod.hidden_count(hints, 0), 2)
        self.assertEqual(askmod.hidden_count(hints, 1), 1)
        self.assertEqual(askmod.hidden_count(hints, 2), 0)
        self.assertEqual(askmod.shown_count("x"), 1)
        self.assertEqual(askmod.shown_count(None), 1)
        self.assertEqual(askmod.shown_count(True), 1)

    def test_next_tier_label(self):
        hints = ["a", "b", "c"]
        self.assertEqual(askmod.next_tier_label(hints, 0), "Pointer")
        self.assertEqual(askmod.next_tier_label(hints, 1), "Worked step")
        self.assertEqual(askmod.next_tier_label(hints, 2), "")

    def test_button_reveals_only_withheld_tiers(self):
        out = askmod.button_html(["AAA-first", "BBB-mid", "CCC-last"], 0)
        self.assertIn("Ask for a nudge (2 left)", out)
        self.assertIn("asknudge-btn", out)
        # Withheld tiers ride hidden; the shown tier is not duplicated.
        self.assertIn("BBB-mid", out)
        self.assertIn("CCC-last", out)
        self.assertNotIn("AAA-first", out)
        self.assertEqual(out.count(" hidden>"), 2)
        self.assertIn("hint-pointer", out)
        self.assertIn("hint-worked", out)
        # Combined render carries every tier exactly once.
        full = (hintmod.hints_html(["AAA-first", "BBB-mid", "CCC-last"], 0)
                + askmod.button_html(["AAA-first", "BBB-mid", "CCC-last"], 0))
        for token in ("AAA-first", "BBB-mid", "CCC-last"):
            self.assertEqual(full.count(token), 1)

    def test_single_click_reveals_one(self):
        out = askmod.button_html(["a", "b", "c"], 1)
        self.assertIn("(1 left)", out)
        self.assertEqual(out.count(" hidden>"), 1)
        self.assertIn("hint-worked", out)
        self.assertNotIn("hint-pointer", out)

    def test_blank_withheld_hints_skipped(self):
        out = askmod.button_html(["a", "  ", "c"], 0)
        self.assertIn("(1 left)", out)
        self.assertIn("c", out)
        self.assertEqual(askmod.button_html(["a", " "], 0), "")

    def test_script_guarded_and_scoped(self):
        out = askmod.button_html(["a", "b"], 0)
        self.assertEqual(out.count("<script>"), 1)
        self.assertIn("window.__asknudge", out)
        self.assertIn("closest('.asknudge')", out)
        self.assertIn("querySelector('details[hidden]')", out)

    def test_html_escapes_hint_text(self):
        out = askmod.button_html(["a", "<script>alert(1)</script>"], 0)
        self.assertNotIn("<script>alert(1)", out)
        self.assertIn("&lt;script&gt;", out)

    def test_hostile_input_fails_closed(self):
        self.assertEqual(askmod.button_html({"h": 1}), "")
        self.assertEqual(askmod.hidden_count("x", "y"), 0)
        self.assertEqual(askmod.next_tier_label(None, "z"), "")
        self.assertIsInstance(askmod.button_html([None, "b"], 0), str)

    def test_section_and_tour_shape(self):
        self.assertIn("id='status-b28-asknudge'", askmod.section_html())
        entry = askmod.tour_entry()
        self.assertEqual(entry["kind"], "improvement")
        self.assertEqual(entry["path"], "/status")
        self.assertEqual(entry["anchor"], "status-b28-asknudge")
        for key in ("id", "kind", "title", "blurb", "path", "anchor"):
            self.assertTrue(entry[key])


class CallerTest(unittest.TestCase):
    """Behavioral effect on the real card path (parent-added)."""

    def _card(self):
        payload = {"code": "print(1)", "expected": "1",
                   "hints": ["AAA-first", "BBB-mid", "CCC-last"]}
        return {"id": "n1", "exercise_type": 8,
                "payload": json.dumps(payload)}

    def test_answer_widget_gains_nudge_button(self):
        out = cardsmod.answer_widget(self._card(), 0, "/due")
        self.assertIn("Ask for a nudge", out)
        self.assertIn("asknudge-btn", out)

    def test_no_tier_duplicated_with_stuck_hidden_copy(self):
        # I-187's stuck timer already carries the next tier hidden;
        # the nudge button must cover only the tiers beyond it.
        out = cardsmod.hints_html(self._card(), 0)
        for token in ("AAA-first", "BBB-mid", "CCC-last"):
            self.assertEqual(out.count(token), 1)
        self.assertIn("data-stuck-next", out)  # I-187 timer still arms

    def test_stuck_bonus_leaves_nothing_for_button(self):
        out = cardsmod.hints_html(self._card(), 0, 150)
        self.assertNotIn("asknudge-btn", out)
        self.assertEqual(out.count("BBB-mid"), 1)

    def test_hintless_card_has_no_button(self):
        bare = {"id": "n9", "exercise_type": 8,
                "payload": json.dumps({"code": "print(1)",
                                       "expected": "1"})}
        self.assertNotIn("asknudge-btn",
                         cardsmod.answer_widget(bare, 0, "/due"))


if __name__ == "__main__":
    unittest.main()
