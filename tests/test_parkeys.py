"""Touch-friendly drag plus keyboard reorder for Parsons (I-162)."""
import json
import unittest

from groundwork import cards as cardsmod
from groundwork import emoji as emojimod
from groundwork import parkeys as mod
from groundwork import parsons as parsonsmod


def _card(lines):
    return {"id": "c7", "exercise_type": 10,
            "payload": json.dumps({"lines": lines,
                                   "solution": list(range(len(lines)))})}


class ParkeysEffectTest(unittest.TestCase):
    def test_list_has_parkeys_class_and_reserve(self):
        out = mod.list_html("c7", ["a", "b"])
        self.assertIn("class='parsons parkeys'", out)
        self.assertIn("min-height:88px", out)

    def test_rows_rove_with_one_tab_stop(self):
        out = mod.list_html("c7", ["a", "b", "c"])
        self.assertIn("tabindex='0'", out)
        self.assertEqual(out.count("tabindex='-1'"), 2)
        self.assertIn("aria-posinset='1'", out)
        self.assertIn("aria-setsize='3'", out)
        self.assertIn("pkgrip", out)
        self.assertIn("Move up", out)
        self.assertIn("Move down", out)

    def test_block_keeps_sync_and_typed_fallback(self):
        out = mod.block_html("c7", ["a", "b"])
        self.assertIn("id='po-c7'", out)
        self.assertIn("name='answer_text'", out)

    def test_caller_widget_gains_parkeys(self):
        out = cardsmod.answer_widget(_card(["a", "b"]), 0, "/due")
        self.assertIn("parkeys", out)
        self.assertIn("__parkeysInit", out)
        self.assertIn("Move up", out)
        self.assertIn("Check order", out)

    def test_css_is_raw_declarations_with_grab_floor(self):
        css = mod.parkeys_css()
        self.assertIn("touch-action", css)
        self.assertIn("44px", css)
        self.assertNotIn("<style>", css)

    def test_js_reuses_order_sync(self):
        js = mod.parkeys_js()
        self.assertIn("ArrowUp", js)
        self.assertIn("pointerdown", js)
        self.assertIn("parsonsSync", js)


class ParkeysFallbackTest(unittest.TestCase):
    def test_block_off_is_legacy_bytes(self):
        lines = ["a", "b"]
        self.assertEqual(mod.block_html("c", lines, False),
                         parsonsmod.block_html("c", lines))

    def test_block_empty_is_legacy_bytes(self):
        self.assertEqual(mod.block_html("c", [], True),
                         parsonsmod.block_html("c", []))

    def test_list_off_is_legacy_bytes(self):
        lines = ["a", "b"]
        self.assertEqual(mod.list_html("c", lines, False),
                         parsonsmod.list_html("c", lines))

    def test_list_empty_is_legacy_bytes(self):
        self.assertEqual(mod.list_html("c", [], True),
                         parsonsmod.list_html("c", []))

    def test_hostile_never_raises(self):
        for bad in (None, 5, "x", {}, {"a"}):
            mod.block_html("c", bad)
            mod.list_html("c", bad)
        self.assertNotIn("data-i", mod.list_html("c", None))


class ParkeysShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["anchor"], mod.STATUS_ANCHOR)

    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])


if __name__ == "__main__":
    unittest.main()
