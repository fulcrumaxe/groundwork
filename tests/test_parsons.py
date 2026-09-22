"""Parsons layout-shift reserve (I-91): effect + legacy fallback."""
import html
import json
import unittest

from groundwork import cards as cardsmod
from groundwork import emoji as emojimod
from groundwork import parsons as parsonsmod


def _legacy_body(cid, lines):
    items = "".join(
        f"<li draggable='true' data-i='{i}'>"
        f"{emojimod.grip_html()} {html.escape(str(l))} "
        f"{emojimod.move_button('up', cid)}"
        f"{emojimod.move_button('down', cid)}</li>"
        for i, l in enumerate(lines))
    return ("<p>Drag the lines into order (or type the numbers):</p>"
            f"<ol class='parsons' id='pl-{cid}'>{items}</ol>"
            f"<input type='hidden' name='answer' id='po-{cid}' value=''>"
            "<label>Order (numbers): "
            "<input name='answer_text' size='30' "
            "placeholder='0 1 2 …'></label> ")


def _parsons_card(cid="t1", lines=("a = 1", "b = 2")):
    return {"id": cid, "exercise_type": 10,
            "payload": json.dumps({"lines": list(lines)})}


class ParsonsTest(unittest.TestCase):
    def test_reserve_scales_with_item_count(self):
        self.assertEqual(parsonsmod.reserve_px(["a"] * 6), 6 * 44)
        self.assertGreater(parsonsmod.reserve_px(["a"] * 6),
                           parsonsmod.reserve_px(["a"] * 2))

    def test_reserve_clamps_huge_lists(self):
        self.assertEqual(parsonsmod.reserve_px(["a"] * 500), 50 * 44)

    def test_effect_list_carries_count_based_min_height(self):
        ol = parsonsmod.list_html(7, ["x = 1", "y = 2", "z = 3"])
        self.assertIn("ol class='parsons'", ol)
        self.assertIn("style='min-height:132px'", ol)  # 3 * 44

    def test_effect_block_keeps_hidden_answer_and_order_label(self):
        body = parsonsmod.block_html(7, ["x = 1", "y = 2"])
        self.assertIn("id='po-7'", body)
        self.assertIn("answer_text", body)
        self.assertIn("min-height:88px", body)

    def test_effect_rows_have_no_glyph_icons(self):
        body = parsonsmod.block_html(9, ["a = 1"])
        self.assertIn("Move up", body)
        self.assertIn("Move down", body)
        self.assertEqual(emojimod.scan_text(body), [])

    def test_caller_answer_widget_carries_reserve(self):
        # I-91 caller: cards.answer_widget etype 10/11 on Due cards.
        widget = cardsmod.answer_widget(_parsons_card(), 0, "/due")
        self.assertIn("style='min-height:88px'", widget)
        self.assertIn("Move up", widget)
        self.assertIn("Check order", widget)
        self.assertEqual(emojimod.scan_text(widget), [])

    def test_legacy_fallback_empty_is_byte_identical(self):
        self.assertEqual(parsonsmod.block_html(9, []),
                         _legacy_body(9, []))
        self.assertEqual(parsonsmod.block_html(9, None),
                         _legacy_body(9, []))

    def test_legacy_fallback_no_reserve_without_lines(self):
        self.assertNotIn("min-height",
                         parsonsmod.list_html(9, []))

    def test_css_uses_min_height_never_height(self):
        css = parsonsmod.parsons_css()
        self.assertIn("min-height", css)
        self.assertNotIn("height:", css.replace("min-height:", ""))

    def test_hostile_input_never_raises(self):
        for bad in (None, 5, "lines", {"a": 1}):
            self.assertEqual(parsonsmod.reserve_px(bad), 0)
            self.assertIn("ol class='parsons'",
                          parsonsmod.list_html(1, bad))
            self.assertNotIn("data-i=",
                             parsonsmod.list_html(1, bad))

    def test_section_html_anchor(self):
        self.assertIn("id='status-b18-parsons'",
                      parsonsmod.section_html())

    def test_tour_entry_shape(self):
        entry = parsonsmod.tour_entry()
        self.assertEqual(
            set(entry), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(entry["kind"], "improvement")
        self.assertEqual(entry["path"], "/status")
        self.assertEqual(entry["anchor"], parsonsmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
