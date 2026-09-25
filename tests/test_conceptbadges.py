"""Collectible concept badges (F-113)."""
import unittest

from groundwork import conceptbadges as mod

from test_web import handler_for, make_module


class BadgeTest(unittest.TestCase):
    def test_deterministic(self):
        self.assertEqual(mod.badge_for("loops"), mod.badge_for("loops"))
        spec = mod.badge_for("loops")
        self.assertIn(spec["motif"], mod.MOTIFS)
        self.assertIn(spec["hue"], mod.HUES)

    def test_owned_badge_differs_from_plain_chip(self):
        owned = mod.badge_html("loops", True)
        self.assertIn("cbadge", owned)
        self.assertIn("loops", owned)
        self.assertEqual(mod.badge_html("loops", False), "")

    def test_no_rarity(self):
        for i in range(100):
            spec = mod.badge_for(f"concept-{i}")
            self.assertIn(spec["motif"], mod.MOTIFS)
        src = open("groundwork/conceptbadges.py", encoding="utf-8").read()
        for word in ("rare", "legendary", "epic", "common"):
            self.assertNotIn(word, src)

    def test_escaped_and_fail_closed(self):
        body = mod.badge_html("<i>x</i>", True)
        self.assertNotIn("<i>x</i>", body)
        self.assertIn("cbadge", mod.badge_html(None, True))
        self.assertEqual(mod.badge_html(123, False), "")

    def test_css_has_no_style_tags(self):
        self.assertNotIn("<style", mod.badge_css())

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "feature")
        self.assertEqual(entry["anchor"], mod.STATUS_ANCHOR)


class CallerEffectTest(unittest.TestCase):
    def test_module_page_shows_plain_chips(self):
        _tmp, db, _s, out = make_module("conceptbadges caller")
        body = handler_for(db).module_html(out["module_id"])
        self.assertIn("chip", body)
        self.assertNotIn("cbadge", body)

    def test_owned_concept_earns_emblem(self):
        from test_partytrick import _own, _cid
        _tmp, db, _s, out = make_module("conceptbadges owned")
        _own(db, _cid(db))
        body = handler_for(db).module_html(out["module_id"])
        self.assertIn("cbadge", body)


if __name__ == "__main__":
    unittest.main()
