"""Granular motivational opt-outs (F-139): per-element ?optout= gates."""
import unittest

from test_web import handler_for, make_module

from groundwork import history as histmod
from groundwork import optout as optoutmod


class ParseTest(unittest.TestCase):
    def test_none_empty_and_blank_show_everything(self):
        for cur in (None, "", "   ", {}, {"optout": []}, {"optout": [""]}):
            self.assertEqual(optoutmod.parse(cur), frozenset(), cur)

    def test_parse_qs_dict_single_and_repeated(self):
        self.assertEqual(optoutmod.parse({"optout": ["garden,bests"]}),
                         frozenset({"garden", "bests"}))
        self.assertEqual(optoutmod.parse({"optout": ["garden", "bests"]}),
                         frozenset({"garden", "bests"}))

    def test_unknown_keys_dropped_case_and_space_folded(self):
        self.assertEqual(
            optoutmod.parse({"optout": [" Garden , BOGUS, bests "]}),
            frozenset({"garden", "bests"}))

    def test_raw_query_string(self):
        self.assertEqual(optoutmod.parse("optout=hero,rest&mode=one"),
                         frozenset({"hero", "rest"}))

    def test_set_passthrough_filters_unknown(self):
        self.assertEqual(optoutmod.parse({"hero", "nope"}),
                         frozenset({"hero"}))

    def test_never_raises(self):
        for cur in (object(), 123, {"optout": [None, 5]}):
            self.assertIsInstance(optoutmod.parse(cur), frozenset)


class GateTest(unittest.TestCase):
    def test_show_defaults_open_unknown_keys_open(self):
        for key, _p, _l, _m in optoutmod.ELEMENTS:
            self.assertTrue(optoutmod.show(None, key))
        self.assertTrue(optoutmod.show({"optout": ["garden"]}, "bogus"))

    def test_show_gates_each_key(self):
        for key, _p, _l, _m in optoutmod.ELEMENTS:
            self.assertFalse(optoutmod.show({"optout": [key]}, key))

    def test_normalize_canonical_sorted(self):
        self.assertEqual(
            optoutmod.normalize({"optout": ["bests", "garden,bests"]}),
            "bests,garden")
        self.assertEqual(optoutmod.normalize(None), "")

    def test_toggle_flips_and_ignores_unknown(self):
        self.assertEqual(optoutmod.toggle("", "garden"), "garden")
        self.assertEqual(optoutmod.toggle("bests,garden", "garden"), "bests")
        self.assertEqual(optoutmod.toggle("garden", "bogus"), "garden")

    def test_elements_cover_both_pages(self):
        keys = [k for k, _p, _l, _m in optoutmod.ELEMENTS]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(len(keys), 19)
        self.assertEqual(len(optoutmod.elements_for("/due")), 7)
        self.assertEqual(len(optoutmod.elements_for("/reviews")), 12)


class CarryTest(unittest.TestCase):
    def test_empty_is_noop(self):
        self.assertEqual(optoutmod.carry("/due", ""), "/due")
        page = "<a href='/due'>x</a>"
        self.assertEqual(optoutmod.carry_html(page, None), page)

    def test_appends_and_never_doubles(self):
        self.assertEqual(optoutmod.carry("/due", "garden"),
                         "/due?optout=garden")
        self.assertEqual(optoutmod.carry("/due?mode=one", "garden"),
                         "/due?mode=one&optout=garden")
        self.assertEqual(optoutmod.carry("/due?optout=bests", "garden"),
                         "/due?optout=bests")
        self.assertEqual(
            optoutmod.carry("/reviews#optout-toggles", "garden"),
            "/reviews?optout=garden#optout-toggles")

    def test_skips_external_and_schemes(self):
        for href in ("https://x.example/", "#frag", "mailto:a@b.c", ""):
            self.assertEqual(optoutmod.carry(href, "garden"), href)

    def test_carry_html_rewrites_internal_only(self):
        html_text = "<a href='/due'>d</a> <a href='https://x.example/'>e</a>"
        out = optoutmod.carry_html(html_text, "garden")
        self.assertIn("/due?optout=garden", out)
        self.assertNotIn("x.example/?optout", out)


class BoxTest(unittest.TestCase):
    def test_box_lists_home_elements_with_flip_links(self):
        box = optoutmod.toggle_box_html("", "/due")
        self.assertIn(f"id='{optoutmod.BOX_ANCHOR}'", box)
        self.assertEqual(box.count("<li>"), 7)
        self.assertIn("[x] Mascot line", box)
        self.assertIn("/due?optout=mascot", box)
        self.assertEqual(
            optoutmod.toggle_box_html("", "/reviews").count("<li>"), 12)

    def test_hidden_row_offers_show_link(self):
        box = optoutmod.toggle_box_html("garden", "/reviews")
        self.assertIn("[ ] Knowledge garden (hidden)", box)
        self.assertIn("<a href='/reviews'>show</a>", box)
        self.assertIn("[x] Personal bests", box)

    def test_counts_and_cross_link(self):
        box = optoutmod.toggle_box_html("hero,rest", "/due")
        self.assertIn("5 of 7 showing", box)
        self.assertIn("/reviews#optout-toggles", box)

    def test_ascii_only(self):
        for body in (optoutmod.toggle_box_html("garden,bests", "/due"),
                     optoutmod.toggle_box_html("", "/reviews"),
                     optoutmod.section_html()):
            self.assertTrue(all(ord(c) < 128 for c in body), body[:80])

    def test_status_and_tour_shape(self):
        body = optoutmod.section_html()
        self.assertIn(f"id='{optoutmod.STATUS_ANCHOR}'", body)
        self.assertIn("optout.py", body)
        e = optoutmod.tour_entry()
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["path"], "/due")
        self.assertEqual(e["anchor"], optoutmod.BOX_ANCHOR)


class CallerEffectTest(unittest.TestCase):
    def test_history_gates_opted_out_sections_only(self):
        _tmp, db, _s, _out = make_module("optout history")
        plain = histmod.history_html(db)
        self.assertIn("id='knowledge-garden'", plain)
        self.assertIn("id='bests'", plain)
        self.assertIn(f"id='{optoutmod.BOX_ANCHOR}'", plain)
        gated = histmod.history_html(db, {"optout": ["garden,bests"]})
        self.assertNotIn("id='knowledge-garden'", gated)
        self.assertNotIn("id='bests'", gated)
        self.assertIn("id='milestones'", gated)
        self.assertIn(f"id='{optoutmod.BOX_ANCHOR}'", gated)

    def test_history_legacy_fallback_byte_identical(self):
        _tmp, db, _s, _out = make_module("optout legacy")
        base = histmod.history_html(db)
        self.assertEqual(histmod.history_html(db, {}), base)
        self.assertEqual(histmod.history_html(db, {"optout": [""]}), base)
        self.assertEqual(histmod.history_html(db, {"optout": ["bogus"]}),
                         base)

    def test_due_gates_serendipity_and_mascot(self):
        _tmp, db, _s, _out = make_module("optout due")
        plain = handler_for(db).due_html()
        self.assertIn("id='serendipity'", plain)
        self.assertIn("id='mascot'", plain)
        self.assertIn(f"id='{optoutmod.BOX_ANCHOR}'", plain)
        gated = handler_for(db).due_html(optout="mascot,serendipity")
        self.assertNotIn("id='serendipity'", gated)
        self.assertNotIn("id='mascot'", gated)
        self.assertIn(f"id='{optoutmod.BOX_ANCHOR}'", gated)
        self.assertEqual(handler_for(db).due_html(optout=""), plain)


if __name__ == "__main__":
    unittest.main()
