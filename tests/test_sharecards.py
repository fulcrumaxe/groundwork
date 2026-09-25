"""Milestone share-cards: opt-in PNG export (F-108)."""
import base64
import struct
import unittest
import zlib

from groundwork import sharecards as mod

from test_web import handler_for, make_module


def _ihdr(raw: bytes) -> tuple:
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    length = struct.unpack(">I", raw[8:12])[0]
    assert raw[12:16] == b"IHDR", "no IHDR first"
    w, h, depth, ctype, _comp, _fil, _lace = struct.unpack(
        ">IIBBBBB", raw[16:16 + length])
    return w, h, depth, ctype


class PngTest(unittest.TestCase):
    def test_valid_png_dimensions(self):
        raw = mod.card_for("first-owned", "FIRST OWNED", "2026-01-05")
        w, h, depth, ctype = _ihdr(raw)
        self.assertEqual((w, h), (mod.CARD_W, mod.CARD_H))
        self.assertEqual((depth, ctype), (8, 2))

    def test_png_decodes_to_pixels(self):
        raw = mod.card_for("first-owned", "FIRST OWNED", "2026-01-05")
        pos, scan = 8, []
        while pos < len(raw):
            ln = struct.unpack(">I", raw[pos:pos + 4])[0]
            ct = raw[pos + 4:pos + 8]
            if ct == b"IDAT":
                scan.append(raw[pos + 8:pos + 8 + ln])
            pos += 12 + ln
        data = zlib.decompress(b"".join(scan))
        self.assertEqual(len(data),
                         mod.CARD_H * (1 + mod.CARD_W * 3))

    def test_ink_actually_drawn(self):
        raw = mod.card_for("first-owned", "FIRST OWNED", "2026-01-05")
        blank = mod.png_bytes([])
        self.assertNotEqual(raw, blank)
        self.assertGreater(len(raw), 500)

    def test_hostile_blank_card(self):
        raw = mod.png_bytes(None)
        self.assertEqual(_ihdr(raw)[:2], (mod.CARD_W, mod.CARD_H))

    def test_font_coverage(self):
        for ch in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-.:/!,'()_? ":
            self.assertIn(ch, mod.FONT, ch)

    def test_sanitize(self):
        self.assertEqual(mod._sanitize("First Owned!"), "FIRST OWNED!")
        self.assertEqual(mod._sanitize("a/b_c"), "A/B_C")
        self.assertEqual(mod._sanitize(None), "")


class SectionTest(unittest.TestCase):
    def test_empty_explains_opt_in(self):
        _tmp, db, _s, _o = make_module("sharecards anchor")
        body = mod.section_html(db)
        self.assertIn("id='share-cards'", body)
        self.assertIn("private until you download", body)
        self.assertNotIn("Download PNG", body)

    def test_data_uri_shape(self):
        uri = mod.card_data_uri("first-owned", "FIRST OWNED",
                                "2026-01-05")
        self.assertTrue(uri.startswith("data:image/png;base64,"))
        raw = base64.b64decode(uri.split(",", 1)[1])
        self.assertEqual(_ihdr(raw)[:2], (mod.CARD_W, mod.CARD_H))

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(), {
            "id": "milestone-share-cards", "kind": "feature",
            "title": "Milestone share-cards",
            "blurb": ("Your proof as a PNG — private until you download, "
                      "yours to post."),
            "path": "/reviews", "anchor": "share-cards"})


class CallerEffectTest(unittest.TestCase):
    def test_history_carries_cards(self):
        _tmp, db, server, _o = make_module("sharecards caller")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        body = handler_for(db).history_html()
        self.assertIn("id='share-cards'", body)

    def test_empty_history_still_anchored(self):
        _tmp, db, _s, _o = make_module("sharecards empty")
        body = handler_for(db).history_html()
        self.assertIn("id='share-cards'", body)


if __name__ == "__main__":
    unittest.main()
