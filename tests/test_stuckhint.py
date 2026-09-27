"""Hint tiers unlock by attempts AND time stuck (I-187)."""
import json
import unittest

from groundwork import cards as cardsmod
from groundwork import emoji as emojimod
from groundwork import hinttiers as hinttiersmod
from groundwork import stuckhint as mod

HINTS = ["try the base case", "trace n=1 by hand", "worked: return 1"]


def _card(hints=HINTS):
    payload = {"code": "print(1)", "expected": "1", "hints": list(hints)}
    return {"id": "s1", "exercise_type": 8,
            "payload": json.dumps(payload)}


class VisibleCountTest(unittest.TestCase):
    def test_attempts_only_is_legacy(self):
        self.assertEqual(mod.visible_count(3, 0), 1)
        self.assertEqual(mod.visible_count(3, 1), 2)
        self.assertEqual(mod.visible_count(3, 99), 3)

    def test_stuck_adds_one_tier(self):
        self.assertEqual(mod.visible_count(3, 0, 150), 2)
        self.assertEqual(mod.visible_count(3, 1, 150), 3)

    def test_window_edges(self):
        self.assertEqual(mod.visible_count(3, 0, 119), 1)
        self.assertEqual(mod.visible_count(3, 0, 120), 2)
        self.assertEqual(mod.visible_count(3, 0, 600), 2)
        self.assertEqual(mod.visible_count(3, 0, 601), 1)

    def test_old_gap_is_fresh_not_stuck(self):
        self.assertEqual(mod.visible_count(3, 0, 9999), 1)
        self.assertEqual(mod.visible_count(3, 0, None), 1)

    def test_hostile_fails_closed(self):
        self.assertEqual(mod.visible_count(3, "x"), 1)
        self.assertEqual(mod.visible_count(3, 0, "x"), 1)
        self.assertEqual(mod.visible_count(3, None, None), 1)
        self.assertEqual(mod.visible_count(0, 0, 150), 0)
        self.assertEqual(mod.visible_count("x", 0, 150), 0)
        self.assertEqual(mod.visible_count(3, -99), 0)


class StuckMathTest(unittest.TestCase):
    def test_is_stuck_boundaries(self):
        self.assertFalse(mod.is_stuck(119))
        self.assertTrue(mod.is_stuck(120))
        self.assertTrue(mod.is_stuck(600))
        self.assertFalse(mod.is_stuck(601))
        self.assertFalse(mod.is_stuck(None))
        self.assertFalse(mod.is_stuck("x"))
        self.assertFalse(mod.is_stuck(float("nan")))

    def test_stuck_bonus(self):
        self.assertEqual(mod.stuck_bonus(150), 1)
        self.assertEqual(mod.stuck_bonus(30), 0)
        self.assertEqual(mod.stuck_bonus(None), 0)

    def test_stuck_seconds_since_fixed_stamps(self):
        secs = mod.stuck_seconds_since("2026-01-01T00:00:00Z",
                                       "2026-01-01T00:03:00Z")
        self.assertEqual(secs, 180.0)

    def test_stuck_seconds_since_clamps_and_fails_closed(self):
        self.assertEqual(mod.stuck_seconds_since("2026-01-01T00:03:00Z",
                                                 "2026-01-01T00:00:00Z"),
                         0.0)
        self.assertIsNone(mod.stuck_seconds_since("not-a-stamp"))
        self.assertIsNone(mod.stuck_seconds_since(None))
        self.assertIsNone(mod.stuck_seconds_since(
            "2026-01-01T00:00:00Z", "garbage"))

    def test_remaining_seconds(self):
        self.assertEqual(mod.remaining_seconds(None), 120)
        self.assertEqual(mod.remaining_seconds(0), 120)
        self.assertEqual(mod.remaining_seconds(60), 60)
        self.assertEqual(mod.remaining_seconds(119), 1)
        self.assertEqual(mod.remaining_seconds(150), 120)
        self.assertEqual(mod.remaining_seconds("x"), 120)


class HintsRenderTest(unittest.TestCase):
    def test_stuck_reveals_next_tier_in_html(self):
        base = mod.hints_html(HINTS, 0, None, timer=False)
        stuck = mod.hints_html(HINTS, 0, 150, timer=False)
        self.assertEqual(base.count("<details"), 1)
        self.assertEqual(stuck.count("<details"), 2)
        self.assertIn("Pointer", stuck)
        self.assertNotEqual(base, stuck)

    def test_window_cap_renders_legacy(self):
        self.assertEqual(mod.hints_html(HINTS, 0, 9999, timer=False),
                         mod.hints_html(HINTS, 0, None, timer=False))

    def test_timer_false_is_hinttiers_bytes(self):
        for attempts, stuck in ((0, None), (1, None), (0, 150), (5, None)):
            with self.subTest(attempts=attempts, stuck=stuck):
                want = hinttiersmod.hints_html(
                    HINTS, attempts + mod.stuck_bonus(stuck))
                self.assertEqual(
                    mod.hints_html(HINTS, attempts, stuck, timer=False),
                    want)

    def test_timer_arms_hidden_next_tier(self):
        out = mod.hints_html(HINTS, 0)
        self.assertIn("id='hints'", out)
        self.assertIn("hidden data-stuck-next", out)
        self.assertIn("data-stuck-secs='120'", out)
        self.assertIn("stuck-note", out)
        self.assertIn("currentScript", out)
        self.assertIn("trace n=1 by hand", out)  # next tier rides hidden

    def test_timer_shortens_with_partial_stuck(self):
        out = mod.hints_html(HINTS, 0, 60)
        self.assertIn("data-stuck-secs='60'", out)

    def test_all_visible_ships_no_timer(self):
        out = mod.hints_html(HINTS, 99)
        self.assertEqual(out, hinttiersmod.hints_html(HINTS, 99))
        self.assertNotIn("stuck-note", out)
        self.assertNotIn("data-stuck-next", out)

    def test_empty_and_hostile_render_nothing(self):
        self.assertEqual(mod.hints_html([], 0), "")
        self.assertEqual(mod.hints_html(None, 0), "")
        self.assertEqual(mod.hints_html("nope", 0), "")

    def test_hint_text_escapes(self):
        out = mod.hints_html(["<script>alert(1)</script>", "b"], 0)
        self.assertNotIn("<script>alert(1)", out)
        self.assertIn("&lt;script&gt;", out)

    def test_never_raises(self):
        self.assertEqual(mod.hints_html(None, "x", "y"), "")
        self.assertIsInstance(mod.timer_js(), str)
        self.assertIn("setTimeout", mod.timer_js())


class CallerWireTest(unittest.TestCase):
    def test_answer_widget_arms_timer_when_tier_locked(self):
        out = cardsmod.answer_widget(_card(), 0, "/due")
        self.assertIn("data-stuck-next", out)
        self.assertIn("stuck-note", out)
        self.assertIn("hint-nudge", out)

    def test_caller_stuck_shows_next_tier(self):
        out = cardsmod.hints_html(_card(), 0, 150)
        self.assertEqual(out.count("<details"), 3)  # 2 shown + 1 hidden

    def test_caller_hintless_card_has_no_stuck_markup(self):
        bare = {"id": "s9", "exercise_type": 8,
                "payload": json.dumps({"code": "print(1)",
                                       "expected": "1"})}
        out = cardsmod.answer_widget(bare, 0, "/due")
        self.assertNotIn("stuck-note", out)
        self.assertNotIn("data-stuck-next", out)
        self.assertEqual(cardsmod.hints_html(bare, 0), "")


class ShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["anchor"], mod.STATUS_ANCHOR)

    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_source_is_ascii_and_emoji_free(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])
        src.encode("ascii")


if __name__ == "__main__":
    unittest.main()
